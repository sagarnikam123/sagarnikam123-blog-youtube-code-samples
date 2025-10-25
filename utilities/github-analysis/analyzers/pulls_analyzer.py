#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyzers.base_analyzer import BaseAnalyzer
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
import re

logger = logging.getLogger(__name__)

class PullsAnalyzer(BaseAnalyzer):
    def __init__(self, owner: str, repo: str, delay_seconds: float = 0.5):
        super().__init__(owner, repo, delay_seconds)

    def get_analysis_type(self):
        return "pulls"

    def fetch_data(self, **kwargs) -> List[Dict[str, Any]]:
        """Fetch pull requests data from GitHub API with validation"""
        max_pages = kwargs.get('max_pages', 3)
        state = kwargs.get('state', 'all')

        if state not in ['open', 'closed', 'all']:
            raise ValueError(f"Invalid state: {state}. Must be 'open', 'closed', or 'all'")

        if max_pages is not None and max_pages <= 0:
            raise ValueError("Max pages must be positive")

        try:
            endpoint = f"/repos/{self.owner}/{self.repo}/pulls"
            params = {
                'state': state,
                'per_page': 30
            }

            logger.info(f"Fetching pull requests for {self.owner}/{self.repo} with state={state}")
            pulls = self.client.paginate(endpoint, params, max_pages)

            print(f"✓ Total PRs fetched: {len(pulls)}")
            logger.info(f"Successfully fetched {len(pulls)} pull requests")
            return pulls

        except Exception as e:
            logger.error(f"Failed to fetch pull requests: {e}")
            raise

    def process_data(self, pulls_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process pull requests data and extract comprehensive fields"""
        if not pulls_data or not isinstance(pulls_data, list):
            logger.warning("No valid pull requests data provided for processing")
            return []

        processed_pulls = []

        print(f"✓ Processing {len(pulls_data)} pull requests...")
        logger.info(f"Processing {len(pulls_data)} pull requests")

        for i, pr in enumerate(pulls_data):
            try:
                if not isinstance(pr, dict):
                    logger.warning(f"Skipping invalid PR data at index {i}")
                    continue
                # Basic info with safe access
                number = pr.get('number', 0)
                title = pr.get('title', '')
                body = pr.get('body') or ''
                state = pr.get('state', '')

                # Dates with safe access
                created_at = pr.get('created_at', '')
                updated_at = pr.get('updated_at', '')
                closed_at = pr.get('closed_at', '')
                merged_at = pr.get('merged_at', '')

                # Parse dates with error handling
                created_dt = self._parse_date(created_at)

                # Calculate metrics with error handling
                age_days = self.calculate_age_days(created_at) if created_at else 'N/A'
                days_since_update = self.calculate_age_days(updated_at) if updated_at else 'N/A'

                # Time to merge/close
                time_to_merge_days = 'N/A'
                time_to_close_days = 'N/A'

                try:
                    if merged_at and created_at:
                        time_to_merge_days = self.calculate_time_to_close(created_at, merged_at)
                    elif closed_at and created_at:
                        time_to_close_days = self.calculate_time_to_close(created_at, closed_at)
                except Exception as e:
                    logger.debug(f"Error calculating time metrics for PR {number}: {e}")

                # Author info with safe access
                author = pr.get('user', {})
                author_login = author.get('login', '') if author else ''
                author_type = author.get('type', '') if author else ''

                # PR metrics
                comments = pr.get('comments', 0)
                review_comments = pr.get('review_comments', 0)
                commits = pr.get('commits', 0)
                additions = pr.get('additions', 0)
                deletions = pr.get('deletions', 0)
                changed_files = pr.get('changed_files', 0)

                # Calculate PR size
                total_changes = additions + deletions
                pr_size = self._classify_pr_size(total_changes, changed_files)

                # Content analysis
                has_breaking_change = any(keyword in (title + body).lower() for keyword in ['breaking', 'break:', 'breaking:'])
                is_hotfix = any(keyword in title.lower() for keyword in ['hotfix', 'urgent', 'critical'])
                is_feature = any(keyword in title.lower() for keyword in ['feat', 'feature', 'add'])
                is_bugfix = any(keyword in title.lower() for keyword in ['fix', 'bug', 'patch'])

                # Extract linked issues with error handling
                try:
                    issue_refs = re.findall(r'#(\d+)', title + body)
                except Exception as e:
                    logger.debug(f"Error extracting issue references from PR {number}: {e}")
                    issue_refs = []

                # Draft status
                is_draft = pr.get('draft', False)

                # Merge info
                is_merged = pr.get('merged', False)
                mergeable = pr.get('mergeable', None)

                # Base and head branches
                base_branch = pr.get('base', {}).get('ref', '') if pr.get('base') else ''
                head_branch = pr.get('head', {}).get('ref', '') if pr.get('head') else ''

                processed_pr = {
                    'number': number,
                    'title': title,
                    'state': state,
                    'is_draft': is_draft,
                    'is_merged': is_merged,
                    'mergeable': mergeable,
                    'author_login': author_login,
                    'author_type': author_type,
                    'base_branch': base_branch,
                    'head_branch': head_branch,
                    'created_at': created_at,
                    'updated_at': updated_at,
                    'closed_at': closed_at,
                    'merged_at': merged_at,
                    'age_days': age_days,
                    'days_since_update': days_since_update,
                    'time_to_merge_days': time_to_merge_days,
                    'time_to_close_days': time_to_close_days,
                    'comments_count': comments,
                    'review_comments_count': review_comments,
                    'commits_count': commits,
                    'additions': additions,
                    'deletions': deletions,
                    'changed_files': changed_files,
                    'total_changes': total_changes,
                    'pr_size': pr_size,
                    'title_length': len(title),
                    'body_length': len(body),
                    'has_breaking_change': has_breaking_change,
                    'is_hotfix': is_hotfix,
                    'is_feature': is_feature,
                    'is_bugfix': is_bugfix,
                    'linked_issues_count': len(issue_refs),
                    'linked_issues': ','.join(issue_refs),
                    'repo_name': self.repo,
                    'org_name': self.owner,
                    'url': pr.get('html_url', '')
                }

                # Add temporal analysis with error handling
                if created_dt:
                    try:
                        processed_pr.update({
                            'created_day_of_week': created_dt.strftime('%A'),
                            'created_hour': created_dt.hour,
                            'created_month': created_dt.strftime('%B'),
                            'is_weekend_created': created_dt.weekday() >= 5
                        })
                    except Exception as e:
                        logger.debug(f"Error processing temporal data for PR {number}: {e}")
                        processed_pr.update({
                            'created_day_of_week': 'N/A',
                            'created_hour': 'N/A',
                            'created_month': 'N/A',
                            'is_weekend_created': False
                        })

                processed_pulls.append(processed_pr)

            except Exception as e:
                logger.error(f"Error processing PR {i}: {e}")
                continue

        return processed_pulls

    @staticmethod
    def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO date string to datetime object with error handling"""
        if not date_str or not isinstance(date_str, str):
            return None

        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except (ValueError, TypeError) as e:
            logger.debug(f"Failed to parse date '{date_str}': {e}")
            return None

    @staticmethod
    def _classify_pr_size(total_changes: int, changed_files: int) -> str:
        """Classify PR size based on changes and files with validation"""
        try:
            total_changes = int(total_changes) if total_changes else 0
            changed_files = int(changed_files) if changed_files else 0

            if total_changes > 1000 or changed_files > 20:
                return 'XL'
            elif total_changes > 500 or changed_files > 10:
                return 'L'
            elif total_changes > 100 or changed_files > 5:
                return 'M'
            elif total_changes > 20 or changed_files > 2:
                return 'S'
            else:
                return 'XS'
        except (ValueError, TypeError):
            logger.debug(f"Error classifying PR size with changes={total_changes}, files={changed_files}")
            return 'Unknown'
