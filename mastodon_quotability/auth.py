"""
OAuth authentication manager for Mastodon instances.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict
from mastodon import Mastodon


class MastodonAuthManager:
    """Manages Mastodon OAuth authentication and credentials."""

    def __init__(self, instance_url: str, client_name: str = "Quotability Manager"):
        """
        Initialize the auth manager.

        Args:
            instance_url: The Mastodon instance URL (e.g., https://mastodon.social)
            client_name: Name of the application
        """
        self.instance_url = instance_url.rstrip('/')
        self.client_name = client_name
        self.credentials_dir = Path.home() / ".mastodon_quotability"
        self.credentials_dir.mkdir(exist_ok=True)

        # Secure the credentials directory (700 - owner only)
        os.chmod(self.credentials_dir, 0o700)

        # File paths for storing credentials
        self.client_cred_file = self.credentials_dir / f"{self._sanitize_url(instance_url)}_client.secret"
        self.user_cred_file = self.credentials_dir / f"{self._sanitize_url(instance_url)}_user.secret"

        # Secure existing credential files if they exist
        self._secure_file_permissions(self.client_cred_file)
        self._secure_file_permissions(self.user_cred_file)

    def _sanitize_url(self, url: str) -> str:
        """Sanitize URL for use as filename."""
        return url.replace('https://', '').replace('http://', '').replace('/', '_')

    def _secure_file_permissions(self, file_path: Path) -> None:
        """
        Set secure permissions (600 - owner read/write only) on a credential file.

        Args:
            file_path: Path to the credential file
        """
        if file_path.exists():
            os.chmod(file_path, 0o600)

    def is_authenticated(self) -> bool:
        """Check if user credentials exist."""
        return self.user_cred_file.exists()

    def register_app(self) -> str:
        """
        Register the application with the Mastodon instance.

        Returns:
            str: The client credentials file path
        """
        if self.client_cred_file.exists():
            print(f"App already registered for {self.instance_url}")
            return str(self.client_cred_file)

        print(f"Registering app with {self.instance_url}...")
        Mastodon.create_app(
            self.client_name,
            api_base_url=self.instance_url,
            to_file=str(self.client_cred_file),
            scopes=['read', 'write']
        )
        # Secure the newly created credential file
        self._secure_file_permissions(self.client_cred_file)
        print(f"App registered successfully!")
        return str(self.client_cred_file)

    def get_auth_url(self) -> str:
        """
        Get the OAuth authorization URL.

        Returns:
            str: The authorization URL for the user to visit
        """
        if not self.client_cred_file.exists():
            self.register_app()

        mastodon = Mastodon(
            client_id=str(self.client_cred_file),
            api_base_url=self.instance_url
        )

        return mastodon.auth_request_url(
            scopes=['read', 'write'],
            redirect_uris='urn:ietf:wg:oauth:2.0:oob'
        )

    def authenticate_with_code(self, auth_code: str) -> str:
        """
        Complete OAuth flow with the authorization code.

        Args:
            auth_code: The authorization code from the OAuth flow

        Returns:
            str: The access token
        """
        if not self.client_cred_file.exists():
            raise ValueError("App not registered. Call register_app() first.")

        mastodon = Mastodon(
            client_id=str(self.client_cred_file),
            api_base_url=self.instance_url
        )

        access_token = mastodon.log_in(
            code=auth_code,
            redirect_uri='urn:ietf:wg:oauth:2.0:oob',
            scopes=['read', 'write'],
            to_file=str(self.user_cred_file)
        )

        # Secure the newly created credential file
        self._secure_file_permissions(self.user_cred_file)

        print(f"Successfully authenticated!")
        return access_token

    def get_api_client(self) -> Mastodon:
        """
        Get an authenticated Mastodon API client.

        Returns:
            Mastodon: An authenticated API client

        Raises:
            ValueError: If not authenticated
        """
        if not self.is_authenticated():
            raise ValueError("Not authenticated. Complete OAuth flow first.")

        return Mastodon(
            access_token=str(self.user_cred_file),
            api_base_url=self.instance_url
        )

    def clear_credentials(self):
        """Clear stored credentials."""
        if self.client_cred_file.exists():
            self.client_cred_file.unlink()
        if self.user_cred_file.exists():
            self.user_cred_file.unlink()
        print("Credentials cleared.")
