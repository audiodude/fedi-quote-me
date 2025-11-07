"""
Flask backend for Mastodon Quotability Manager Web App
"""

import sys
import os
import secrets
from pathlib import Path
from flask import Flask, request, jsonify, session, redirect, send_from_directory
from flask_cors import CORS

# Add parent directory to path to import the library
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mastodon_quotability import MastodonAuthManager, MastodonQuotabilityAPI

# Determine if we're in production (deployed) or development
IS_PRODUCTION = os.environ.get('ENVIRONMENT') == 'production'
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5173')

# Static file directory (built frontend)
STATIC_DIR = Path(__file__).parent.parent / 'frontend' / 'dist'

# Create Flask app with static file serving if in production
if IS_PRODUCTION and STATIC_DIR.exists():
    app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path='')
else:
    app = Flask(__name__)

app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Configure CORS
if IS_PRODUCTION:
    # In production, allow same origin
    CORS(app, supports_credentials=True, origins=[BASE_URL])
else:
    # In development, allow frontend dev server
    CORS(app, supports_credentials=True, origins=['http://localhost:5173'])

# Store auth managers and states (in production, use Redis or similar)
auth_managers = {}
auth_states = {}  # Store state tokens for CSRF protection

# OAuth redirect URI
REDIRECT_URI = f'{BASE_URL}/oauth/callback'


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok'})


@app.route('/api/auth/start', methods=['POST'])
def start_auth():
    """
    Start the OAuth flow.

    Expects JSON body: { "instance_url": "mastodon.social" }
    Returns: { "auth_url": "https://...", "session_id": "..." }
    """
    try:
        data = request.json
        instance_url = data.get('instance_url', '').strip()

        if not instance_url:
            return jsonify({'error': 'Instance URL is required'}), 400

        # Normalize URL
        if not instance_url.startswith('http'):
            instance_url = f'https://{instance_url}'

        # Create session ID and state token for CSRF protection
        session_id = secrets.token_urlsafe(32)
        state = secrets.token_urlsafe(32)

        # Create auth manager with redirect URI
        auth_manager = MastodonAuthManager(
            instance_url,
            client_name="Mastodon Quotability Manager",
            redirect_uri=REDIRECT_URI
        )

        # Register app
        auth_manager.register_app()

        # Get auth URL with state parameter
        auth_url = auth_manager.get_auth_url(state=state)

        # Store auth manager and state
        auth_managers[session_id] = auth_manager
        auth_states[state] = session_id

        return jsonify({
            'auth_url': auth_url,
            'session_id': session_id,
            'state': state,
            'instance_url': instance_url
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/callback', methods=['GET', 'POST'])
def auth_callback():
    """
    Complete the OAuth flow.

    GET (OAuth redirect): Query params code, state
    POST (manual): JSON body { "session_id": "...", "auth_code": "..." }
    Returns: { "success": true, "session_id": "..." }
    """
    try:
        # Handle GET request from OAuth redirect
        if request.method == 'GET':
            auth_code = request.args.get('code')
            state = request.args.get('state')

            if not auth_code or not state:
                return jsonify({'error': 'Missing code or state parameter'}), 400

            # Verify state and get session ID
            session_id = auth_states.get(state)
            if not session_id:
                return jsonify({'error': 'Invalid or expired state token'}), 400

            # Clean up state after use
            del auth_states[state]

        # Handle POST request (legacy manual flow)
        else:
            data = request.json
            session_id = data.get('session_id')
            auth_code = data.get('auth_code')

            if not session_id or not auth_code:
                return jsonify({'error': 'Session ID and auth code are required'}), 400

        # Get auth manager
        auth_manager = auth_managers.get(session_id)
        if not auth_manager:
            return jsonify({'error': 'Invalid session ID'}), 400

        # Complete authentication
        auth_manager.authenticate_with_code(auth_code)

        return jsonify({
            'success': True,
            'session_id': session_id
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/account/info', methods=['GET'])
def get_account_info():
    """
    Get account information.

    Query params: session_id, breakdown (optional, 'true' to include quote breakdown)
    Returns: Account info JSON
    """
    try:
        session_id = request.args.get('session_id')
        include_breakdown = request.args.get('breakdown', 'false').lower() == 'true'

        if not session_id:
            return jsonify({'error': 'Session ID is required'}), 400

        # Get auth manager
        auth_manager = auth_managers.get(session_id)
        if not auth_manager:
            return jsonify({'error': 'Invalid session ID'}), 400

        # Check if authenticated
        if not auth_manager.is_authenticated():
            return jsonify({'error': 'Not authenticated'}), 401

        # Get API client
        client = auth_manager.get_api_client()
        api = MastodonQuotabilityAPI(client)

        # Get account info with or without breakdown
        if include_breakdown:
            info = api.get_account_info_with_breakdown()
        else:
            info = api.get_account_info()

        return jsonify(info)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/posts/count', methods=['GET'])
def get_post_count():
    """
    Get total post count.

    Query params: session_id
    Returns: { "count": 123 }
    """
    try:
        session_id = request.args.get('session_id')

        if not session_id:
            return jsonify({'error': 'Session ID is required'}), 400

        # Get auth manager
        auth_manager = auth_managers.get(session_id)
        if not auth_manager:
            return jsonify({'error': 'Invalid session ID'}), 400

        # Check if authenticated
        if not auth_manager.is_authenticated():
            return jsonify({'error': 'Not authenticated'}), 401

        # Get API client
        client = auth_manager.get_api_client()
        api = MastodonQuotabilityAPI(client)

        # Get post count
        count = api.get_post_count()

        return jsonify({'count': count})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/quotability/enable', methods=['POST'])
def enable_quotability():
    """
    Enable quotability for all posts.

    Expects JSON body: { "session_id": "...", "policy": "public" }
    Returns: Progress updates via Server-Sent Events
    """
    try:
        data = request.json
        session_id = data.get('session_id')
        policy = data.get('policy', 'public')

        if not session_id:
            return jsonify({'error': 'Session ID is required'}), 400

        # Get auth manager
        auth_manager = auth_managers.get(session_id)
        if not auth_manager:
            return jsonify({'error': 'Invalid session ID'}), 400

        # Check if authenticated
        if not auth_manager.is_authenticated():
            return jsonify({'error': 'Not authenticated'}), 401

        # Get API client
        client = auth_manager.get_api_client()
        api = MastodonQuotabilityAPI(client)

        # Enable quotability
        results = api.enable_quotability_for_all_posts(policy)

        return jsonify(results)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """
    Clear stored credentials.

    Expects JSON body: { "session_id": "..." }
    Returns: { "success": true }
    """
    try:
        data = request.json
        session_id = data.get('session_id')

        if not session_id:
            return jsonify({'error': 'Session ID is required'}), 400

        # Get auth manager
        auth_manager = auth_managers.get(session_id)
        if auth_manager:
            auth_manager.clear_credentials()
            del auth_managers[session_id]

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """
    Serve the Vue frontend in production.
    In development, this is handled by Vite dev server.
    """
    if not IS_PRODUCTION or not STATIC_DIR.exists():
        return jsonify({'error': 'Frontend not built. Run in development mode or build frontend first.'}), 404

    # If path is a file that exists, serve it
    if path and (STATIC_DIR / path).exists() and (STATIC_DIR / path).is_file():
        return send_from_directory(STATIC_DIR, path)

    # Otherwise serve index.html (for SPA routing)
    return send_from_directory(STATIC_DIR, 'index.html')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = not IS_PRODUCTION

    if IS_PRODUCTION:
        print(f"Starting in PRODUCTION mode on port {port}")
        print(f"Base URL: {BASE_URL}")
        print(f"Static files: {STATIC_DIR}")
    else:
        print(f"Starting in DEVELOPMENT mode on port {port}")
        print("Frontend should be running on http://localhost:5173")

    app.run(host='0.0.0.0', port=port, debug=debug)
