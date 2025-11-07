# Mastodon Quotability Manager

A tool to enable quote post functionality (Mastodon 4.5+ feature) for all your existing posts on Mastodon-compatible servers.

## Features

- **OAuth Authentication**: Secure authentication with any Mastodon-compatible server
- **Bulk Update**: Enable quotability for all your posts with one click
- **Flexible Policies**: Choose from public, followers-only, or disable quoting
- **CLI & Web Interface**: Use either the command-line tool or the web application
- **Shared Python Library**: Both interfaces use the same underlying library

## Requirements

- Python 3.7+
- Node.js 18+ (for web app frontend only)
- Pipenv (for Python dependency management)
- A Mastodon 4.5+ compatible server

## Project Structure

```
fedi-quote-me/
├── mastodon_quotability/    # Shared Python library
│   ├── __init__.py
│   ├── auth.py              # OAuth authentication
│   └── api.py               # Mastodon API operations
├── cli/                      # Command-line interface
│   └── mastodon_quotability_cli.py
├── webapp/                   # Web application
│   ├── backend/             # Flask backend
│   │   └── app.py
│   └── frontend/            # Vue.js frontend
│       ├── src/
│       │   ├── App.vue
│       │   ├── main.js
│       │   └── style.css
│       ├── index.html
│       ├── vite.config.js
│       └── package.json
├── Pipfile                  # Python dependencies
└── README.md
```

## Installation

### 1. Install Python Dependencies

```bash
# Install Pipenv if you don't have it
pip install pipenv

# Install project dependencies
pipenv install
```

### 2. Install Frontend Dependencies (for web app only)

```bash
cd webapp/frontend
npm install
```

## Usage

### CLI Version

The CLI is a simple command-line tool for managing quotability.

#### Activate the virtual environment

```bash
pipenv shell
```

#### View account information

```bash
python cli/mastodon_quotability_cli.py --instance mastodon.social info
```

#### Enable quotability for all posts

```bash
# Public: Anyone can quote
python cli/mastodon_quotability_cli.py --instance mastodon.social enable --policy public

# Followers only
python cli/mastodon_quotability_cli.py --instance mastodon.social enable --policy followers

# Disable quoting
python cli/mastodon_quotability_cli.py --instance mastodon.social enable --policy nobody
```

#### Logout

```bash
python cli/mastodon_quotability_cli.py --instance mastodon.social logout
```

### Web App Version

The web app provides a user-friendly interface with the same functionality.

#### 1. Start the Flask backend

In one terminal:

```bash
# Activate virtual environment
pipenv shell

# Run the backend
python webapp/backend/app.py
```

The backend will run on `http://localhost:5000`

#### 2. Start the Vue frontend

In another terminal:

```bash
cd webapp/frontend

# Install dependencies (first time only)
npm install

# Start the development server
npm run dev
```

The frontend will run on `http://localhost:5173`

#### 3. Open your browser

Navigate to `http://localhost:5173` and follow the on-screen instructions:

1. Enter your Mastodon instance URL
2. Authorize the application
3. View your account information
4. Enable quotability for all posts

## Quote Policies

Mastodon 4.5+ supports three quote policies:

- **Public**: Anyone can quote your posts
- **Followers**: Only your followers can quote your posts
- **Nobody**: Only you can quote your posts (effectively disables quoting)

Note: Private and direct messages cannot have their quote policy changed.

## How It Works

1. **OAuth Flow**: The app registers with your Mastodon instance and requests authorization
2. **Fetch Posts**: Retrieves all your posts using the Mastodon API
3. **Update Policy**: Uses the `PUT /api/v1/statuses/:id/interaction_policy` endpoint to update the quote policy for each post
4. **One-Time Operation**: This is designed as a one-time bulk update for existing posts

## Security

- Credentials are stored locally in `~/.mastodon_quotability/`
- OAuth tokens are never exposed to the frontend
- The web app uses session-based authentication
- All communication with Mastodon uses HTTPS

## Development

### Running in Development Mode

Backend:
```bash
pipenv shell
python webapp/backend/app.py
```

Frontend:
```bash
cd webapp/frontend
npm run dev
```

### Building for Production

Frontend:
```bash
cd webapp/frontend
npm run build
```

The built files will be in `webapp/frontend/dist/`

## Troubleshooting

### "Not authenticated" error
- Make sure you completed the OAuth flow
- Try logging out and authenticating again

### "Invalid session ID" error
- The backend may have restarted. Refresh the page and authenticate again

### Posts failing to update
- Private and direct messages cannot have their quote policy changed
- Some servers may have rate limiting - the tool includes delays to be respectful

### CORS errors in web app
- Make sure both backend (port 5000) and frontend (port 5173) are running
- Check that the backend CORS settings allow the frontend origin

## License

MIT License - feel free to use and modify as needed.

## Credits

Built with:
- [Mastodon.py](https://github.com/halcy/Mastodon.py) - Python wrapper for Mastodon API
- [Flask](https://flask.palletsprojects.com/) - Backend web framework
- [Vue.js](https://vuejs.org/) - Frontend framework
- [TailwindCSS](https://tailwindcss.com/) - CSS framework
- [Vite](https://vitejs.dev/) - Build tool

## Support

For issues and questions:
- Check the [Mastodon API documentation](https://docs.joinmastodon.org/)
- Review the [Mastodon 4.5 developer blog post](https://blog.joinmastodon.org/2025/10/mastodon-4-5-for-devs/)
