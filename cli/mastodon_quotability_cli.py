#!/usr/bin/env python3
"""
Mastodon Quotability Manager - CLI Version

A command-line tool to manage quote post settings on Mastodon.
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path to import the library
sys.path.insert(0, str(Path(__file__).parent.parent))

from mastodon_quotability import MastodonAuthManager, MastodonQuotabilityAPI


def authenticate(instance_url: str) -> MastodonAuthManager:
    """Handle the authentication flow."""
    auth_manager = MastodonAuthManager(instance_url)

    if auth_manager.is_authenticated():
        print(f"Already authenticated with {instance_url}")
        return auth_manager

    print(f"\nAuthenticating with {instance_url}...")
    print("=" * 60)

    # Register app if needed
    auth_manager.register_app()

    # Get auth URL
    auth_url = auth_manager.get_auth_url()

    print("\nPlease visit this URL to authorize the application:")
    print(f"\n{auth_url}\n")
    print("After authorizing, you'll receive an authorization code.")

    # Get code from user
    auth_code = input("Enter the authorization code: ").strip()

    # Complete authentication
    auth_manager.authenticate_with_code(auth_code)

    return auth_manager


def show_account_info(api: MastodonQuotabilityAPI):
    """Display account information."""
    info = api.get_account_info()
    print("\nAccount Information:")
    print("=" * 60)
    print(f"Display Name: {info['display_name']}")
    print(f"Username: @{info['username']}")
    print(f"Profile URL: {info['url']}")
    print(f"Posts: {info['posts_count']}")
    print(f"Followers: {info['followers_count']}")
    print(f"Following: {info['following_count']}")
    print()


def enable_quotability(api: MastodonQuotabilityAPI, policy: str):
    """Enable quotability for all posts."""
    print(f"\nThis will update ALL your posts to allow quoting with policy: '{policy}'")
    print("This is a ONE-TIME operation and cannot be easily undone.")
    print("\nQuote policies:")
    print("  - public: Anybody can quote your posts")
    print("  - followers: Only your followers can quote")
    print("  - nobody: Only you can quote (disables quoting)")

    confirm = input("\nDo you want to proceed? (yes/no): ").strip().lower()

    if confirm != 'yes':
        print("Operation cancelled.")
        return

    # Progress callback
    def progress_callback(current, total, success):
        status = "✓" if success else "✗"
        print(f"\r[{status}] Processing: {current}/{total} posts", end='', flush=True)

    # Update all posts
    results = api.enable_quotability_for_all_posts(policy, progress_callback)

    print("\n\nResults:")
    print("=" * 60)
    print(f"Total posts: {results['total']}")
    print(f"Successfully updated: {results['success']}")
    print(f"Failed: {results['failed']}")

    if results['failed'] > 0:
        print("\nNote: Some posts may have failed due to visibility settings")
        print("(private/direct posts cannot have their quote policy changed)")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Manage quote post settings on Mastodon",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Authenticate and view account info
  python mastodon_quotability_cli.py --instance mastodon.social info

  # Enable public quoting for all posts
  python mastodon_quotability_cli.py --instance mastodon.social enable --policy public

  # Enable quoting for followers only
  python mastodon_quotability_cli.py --instance mastodon.social enable --policy followers

  # Clear stored credentials
  python mastodon_quotability_cli.py --instance mastodon.social logout
        """
    )

    parser.add_argument(
        '--instance',
        required=True,
        help='Mastodon instance URL (e.g., mastodon.social or https://mastodon.social)'
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Info command
    subparsers.add_parser('info', help='Show account information and post count')

    # Enable command
    enable_parser = subparsers.add_parser('enable', help='Enable quotability for all posts')
    enable_parser.add_argument(
        '--policy',
        choices=['public', 'followers', 'nobody'],
        default='public',
        help='Quote approval policy (default: public)'
    )

    # Logout command
    subparsers.add_parser('logout', help='Clear stored credentials')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Normalize instance URL
    instance_url = args.instance
    if not instance_url.startswith('http'):
        instance_url = f'https://{instance_url}'

    # Handle logout separately (doesn't need API client)
    if args.command == 'logout':
        auth_manager = MastodonAuthManager(instance_url)
        auth_manager.clear_credentials()
        return

    try:
        # Authenticate
        auth_manager = authenticate(instance_url)

        # Get API client
        client = auth_manager.get_api_client()
        api = MastodonQuotabilityAPI(client)

        # Execute command
        if args.command == 'info':
            show_account_info(api)

        elif args.command == 'enable':
            show_account_info(api)
            enable_quotability(api, args.policy)

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
