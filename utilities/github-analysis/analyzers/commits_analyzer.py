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

class CommitsAnalyzer(BaseAnalyzer):
    def __init__(self, owner: str, repo: str, delay_seconds: float = 0.5):
        super().__init__(owner, repo, delay_seconds)

    def get_analysis_type(self):
        return "commits"

    def fetch_data(self, **kwargs) -> List[Dict[str, Any]]:
        """Fetch commits data from GitHub API with validation"""
        max_pages = kwargs.get('max_pages', 3)
        branch = kwargs.get('branch', None)

        if max_pages is not None and max_pages <= 0:
            raise ValueError("Max pages must be positive")

        if branch and not isinstance(branch, str):
            raise ValueError("Branch must be a string")

        try:
            # Build API parameters
            api_params: Dict[str, Any] = {
                'per_page': 30
            }
            if branch:
                api_params['sha'] = branch
                print(f"📍 Fetching commits from branch: {branch}")
                logger.info(f"Fetching commits from branch: {branch}")
            else:
                print("📍 Fetching commits from default branch")
                logger.info("Fetching commits from default branch")

            endpoint = f"/repos/{self.owner}/{self.repo}/commits"
            commits = self.client.paginate(endpoint, api_params, max_pages)

            print(f"✓ Total commits fetched: {len(commits)}")
            logger.info(f"Successfully fetched {len(commits)} commits")
            return commits

        except Exception as e:
            logger.error(f"Failed to fetch commits: {e}")
            raise

    def process_data(self, commits_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process commits data and extract comprehensive fields"""
        if not commits_data or not isinstance(commits_data, list):
            logger.warning("No valid commits data provided for processing")
            return []

        processed_commits = []

        print(f"✓ Processing {len(commits_data)} commits...")
        logger.info(f"Processing {len(commits_data)} commits")

        for i, commit in enumerate(commits_data):
            try:
                if not isinstance(commit, dict):
                    logger.warning(f"Skipping invalid commit data at index {i}")
                    continue
                commit_data = commit.get('commit', {})
                if not commit_data:
                    logger.warning(f"Commit at index {i} missing commit data")
                    continue

                author_info = commit_data.get('author', {})
                committer_info = commit_data.get('committer', {})

                # Basic info with safe access
                sha = commit.get('sha', '')
                message = commit_data.get('message', '')
                author_name = author_info.get('name', '') if author_info else ''
                author_email = author_info.get('email', '') if author_info else ''
                committer_name = committer_info.get('name', '') if committer_info else ''

                # Dates with safe access
                author_date = author_info.get('date', '') if author_info else ''
                commit_date = committer_info.get('date', '') if committer_info else ''

                # Parse dates with error handling
                created_at = self._parse_date(author_date)

                # Message analysis
                lines = message.split('\n') if message else []
                title = lines[0] if lines else ''
                body = '\n'.join(lines[1:]).strip() if len(lines) > 1 else ''

                # Content analysis
                message_lower = message.lower()
                has_breaking_change = any(keyword in message_lower for keyword in ['breaking', 'break:', 'breaking:'])
                is_merge_commit = message_lower.startswith('merge')
                is_revert_commit = message_lower.startswith('revert')
                is_fix_commit = any(keyword in message_lower for keyword in ['fix', 'bug', 'patch'])
                is_feature_commit = any(keyword in message_lower for keyword in ['feat', 'feature', 'add'])

                # Extract issue references with error handling
                try:
                    issue_refs = re.findall(r'#(\d+)', message)
                except Exception as e:
                    logger.debug(f"Error extracting issue references from commit {sha}: {e}")
                    issue_refs = []

                processed_commit = {
                    'sha': sha,
                    'short_sha': sha[:7] if sha else '',
                    'title': title,
                    'message': message,
                    'body': body,
                    'author_name': author_name,
                    'author_email': author_email,
                    'committer_name': committer_name,
                    'author_date': author_date,
                    'commit_date': commit_date,
                    'is_merge_commit': is_merge_commit,
                    'is_revert_commit': is_revert_commit,
                    'is_fix_commit': is_fix_commit,
                    'is_feature_commit': is_feature_commit,
                    'has_breaking_change': has_breaking_change,
                    'issue_references': ','.join(issue_refs),
                    'issue_count': len(issue_refs),
                    'title_length': len(title),
                    'message_length': len(message),
                    'body_length': len(body),
                    'lines_count': len(lines),
                    'branch': 'default',
                    'repo_name': self.repo,
                    'org_name': self.owner,
                    'url': commit.get('html_url', '')
                }

                # Add temporal analysis with error handling
                if created_at:
                    try:
                        processed_commit.update({
                            'created_day_of_week': created_at.strftime('%A'),
                            'created_hour': created_at.hour,
                            'created_month': created_at.strftime('%B'),
                            'is_weekend_created': created_at.weekday() >= 5
                        })
                    except Exception as e:
                        logger.debug(f"Error processing temporal data for commit {sha}: {e}")
                        processed_commit.update({
                            'created_day_of_week': 'N/A',
                            'created_hour': 'N/A',
                            'created_month': 'N/A',
                            'is_weekend_created': False
                        })
                else:
                    processed_commit.update({
                        'created_day_of_week': 'N/A',
                        'created_hour': 'N/A',
                        'created_month': 'N/A',
                        'is_weekend_created': False
                    })

                processed_commits.append(processed_commit)

            except Exception as e:
                logger.error(f"Error processing commit {i}: {e}")
                continue

        return processed_commits

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
