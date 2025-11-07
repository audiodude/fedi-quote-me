"""
Mastodon API operations for managing post quotability.
"""

from typing import List, Dict, Optional, Callable
from mastodon import Mastodon
import time


class MastodonQuotabilityAPI:
    """Manages quote post settings via Mastodon API."""

    def __init__(self, mastodon_client: Mastodon):
        """
        Initialize the API manager.

        Args:
            mastodon_client: An authenticated Mastodon API client
        """
        self.client = mastodon_client
        self.account = self.client.account_verify_credentials()
        self._cached_posts: Optional[List[Dict]] = None
        self._instance_info: Optional[Dict] = None
        self._version_checked: bool = False

    def get_instance_info(self) -> Dict:
        """
        Get information about the Mastodon instance.

        Returns:
            Dict: Instance information including version
        """
        if self._instance_info is None:
            self._instance_info = self.client.instance()
        return self._instance_info

    def check_quote_policy_support(self) -> tuple[bool, str]:
        """
        Check if the instance supports quote policy management (Mastodon 4.5+).

        Returns:
            tuple[bool, str]: (supported, version_string)
        """
        if self._version_checked:
            return True, ""  # Already checked, assume supported

        try:
            instance = self.get_instance_info()
            version = instance.get('version', 'unknown')

            # Parse version (format: "4.5.0" or "4.5.0+glitch")
            version_parts = version.split('.')
            if len(version_parts) >= 2:
                major = int(version_parts[0])
                minor = int(version_parts[1].split('+')[0].split('-')[0])

                # Mastodon 4.5+ supports quote policies
                if major > 4 or (major == 4 and minor >= 5):
                    self._version_checked = True
                    return True, version
                else:
                    return False, version

            return False, version

        except Exception as e:
            print(f"Warning: Could not check instance version: {e}")
            return False, "unknown"

    def get_post_count(self) -> int:
        """
        Get the total count of user's posts.

        Returns:
            int: Total number of posts
        """
        return self.account['statuses_count']

    def get_all_posts(
        self,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        use_cache: bool = True
    ) -> List[Dict]:
        """
        Fetch all posts from the authenticated user.

        Args:
            progress_callback: Optional callback function(current, total) for progress updates
            use_cache: If True, return cached posts if available (default: True)

        Returns:
            List[Dict]: List of all post objects
        """
        # Return cached posts if available and cache is enabled
        if use_cache and self._cached_posts is not None:
            print(f"Using cached posts ({len(self._cached_posts)} posts)")
            return self._cached_posts

        all_posts = []
        total_count = self.get_post_count()
        account_id = self.account['id']

        print(f"Fetching {total_count} posts...")

        max_id = None
        while True:
            try:
                # Fetch a page of statuses
                statuses = self.client.account_statuses(
                    account_id,
                    max_id=max_id,
                    limit=40  # Max allowed by API
                )

                if not statuses:
                    break

                all_posts.extend(statuses)

                if progress_callback:
                    progress_callback(len(all_posts), total_count)

                # Get the ID of the last status for pagination
                max_id = statuses[-1]['id']

                # Be nice to the server
                time.sleep(0.5)

            except Exception as e:
                print(f"Error fetching posts: {e}")
                break

        # Cache the posts
        self._cached_posts = all_posts

        return all_posts

    def clear_post_cache(self) -> None:
        """Clear the cached posts, forcing a fresh fetch on next request."""
        self._cached_posts = None
        print("Post cache cleared")

    def update_post_quotability(
        self,
        status_id: str,
        policy: str = "public"
    ) -> bool:
        """
        Update the quote approval policy for a specific post.

        Args:
            status_id: The ID of the post to update
            policy: Quote approval policy ('public', 'followers', or 'nobody')

        Returns:
            bool: True if successful, False otherwise
        """
        valid_policies = ['public', 'followers', 'nobody']
        if policy not in valid_policies:
            raise ValueError(f"Invalid policy. Must be one of: {valid_policies}")

        try:
            # Use the interaction_policy endpoint
            endpoint = f'/api/v1/statuses/{status_id}/interaction_policy'
            params = {'quote_approval_policy': policy}

            # Use the internal API request method (name-mangled)
            response = self.client._Mastodon__api_request(
                'PUT',
                endpoint,
                params,
                use_json=True
            )
            return True
        except Exception as e:
            print(f"Error updating status {status_id}: {e}")
            return False

    def enable_quotability_for_all_posts(
        self,
        policy: str = "public",
        progress_callback: Optional[Callable[[int, int, bool], None]] = None
    ) -> Dict[str, int]:
        """
        Enable quotability for all user posts.

        Args:
            policy: Quote approval policy to set ('public', 'followers', or 'nobody')
            progress_callback: Optional callback function(current, total, success) for progress

        Returns:
            Dict with 'total', 'success', and 'failed' counts

        Raises:
            RuntimeError: If the instance doesn't support quote policies (Mastodon <4.5)
        """
        # Check if instance supports quote policies
        supported, version = self.check_quote_policy_support()
        if not supported:
            raise RuntimeError(
                f"This Mastodon instance (version {version}) does not support quote policy management.\n"
                f"Quote policies require Mastodon 4.5 or later.\n"
                f"Please ask your instance administrator to upgrade."
            )

        posts = self.get_all_posts()
        results = {
            'total': len(posts),
            'success': 0,
            'failed': 0
        }

        print(f"\nUpdating quotability for {results['total']} posts to '{policy}'...")

        for i, post in enumerate(posts, 1):
            success = self.update_post_quotability(post['id'], policy)

            if success:
                results['success'] += 1
            else:
                results['failed'] += 1

            if progress_callback:
                progress_callback(i, results['total'], success)

            # Rate limiting - be nice to the server
            time.sleep(0.3)

        return results

    def analyze_posts_by_quote_policy(self) -> Dict[str, int]:
        """
        Analyze all posts and categorize them by quote policy.

        Returns:
            Dict with counts for 'public', 'followers', 'nobody', and 'unknown'
        """
        print("Analyzing posts by quote policy...")

        posts = self.get_all_posts()

        counts = {
            'public': 0,
            'followers': 0,
            'nobody': 0,
            'unknown': 0
        }

        for post in posts:
            # Check if the post has quote_approval data
            quote_approval = post.get('quote_approval')

            if not quote_approval:
                counts['unknown'] += 1
                continue

            # The quote_approval object has automatic/manual approval lists
            # We need to check what the current policy is
            # If 'public' is in automatic, it's public
            # If 'followers' is in automatic but not public, it's followers-only
            # Otherwise, it's nobody

            automatic = quote_approval.get('automatic', [])

            if 'public' in automatic:
                counts['public'] += 1
            elif 'followers' in automatic or 'following' in automatic:
                counts['followers'] += 1
            else:
                counts['nobody'] += 1

        return counts

    def get_account_info(self) -> Dict:
        """
        Get information about the authenticated account.

        Returns:
            Dict: Account information
        """
        # Check version support
        supported, version = self.check_quote_policy_support()

        return {
            'username': self.account['username'],
            'display_name': self.account['display_name'],
            'acct': self.account['acct'],
            'url': self.account['url'],
            'posts_count': self.account['statuses_count'],
            'followers_count': self.account['followers_count'],
            'following_count': self.account['following_count'],
            'instance_version': version,
            'supports_quote_policies': supported
        }

    def get_account_info_with_breakdown(self) -> Dict:
        """
        Get account information with breakdown of posts by quote policy.

        Returns:
            Dict: Account information including post breakdown
        """
        info = self.get_account_info()

        # Add quote policy breakdown
        quote_breakdown = self.analyze_posts_by_quote_policy()
        info['quote_breakdown'] = quote_breakdown

        return info

    def set_default_quote_policy(self, policy: str = "public") -> bool:
        """
        Set the default quote policy for new posts.

        Args:
            policy: Quote approval policy ('public', 'followers', or 'nobody')

        Returns:
            bool: True if successful
        """
        valid_policies = ['public', 'followers', 'nobody']
        if policy not in valid_policies:
            raise ValueError(f"Invalid policy. Must be one of: {valid_policies}")

        try:
            self.client.account_update_credentials(
                source={'quote_policy': policy}
            )
            return True
        except Exception as e:
            print(f"Error setting default quote policy: {e}")
            return False
