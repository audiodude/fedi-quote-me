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

    def get_post_count(self) -> int:
        """
        Get the total count of user's posts.

        Returns:
            int: Total number of posts
        """
        return self.account['statuses_count']

    def get_all_posts(self, progress_callback: Optional[Callable[[int, int], None]] = None) -> List[Dict]:
        """
        Fetch all posts from the authenticated user.

        Args:
            progress_callback: Optional callback function(current, total) for progress updates

        Returns:
            List[Dict]: List of all post objects
        """
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

        return all_posts

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
            url = f"/api/v1/statuses/{status_id}/interaction_policy"
            params = {'quote_approval_policy': policy}

            response = self.client.request('PUT', url, params)
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
        """
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

    def get_account_info(self) -> Dict:
        """
        Get information about the authenticated account.

        Returns:
            Dict: Account information
        """
        return {
            'username': self.account['username'],
            'display_name': self.account['display_name'],
            'acct': self.account['acct'],
            'url': self.account['url'],
            'posts_count': self.account['statuses_count'],
            'followers_count': self.account['followers_count'],
            'following_count': self.account['following_count']
        }

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
