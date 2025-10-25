#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyzers.base_analyzer import BaseAnalyzer
from datetime import datetime

class ReleasesAnalyzer(BaseAnalyzer):
    def __init__(self, owner, repo, delay_seconds=0.5):
        super().__init__(owner, repo, delay_seconds)

    def get_analysis_type(self):
        return "releases"

    def fetch_data(self, **kwargs):
        """Fetch releases data from GitHub API"""
        try:
            data, remaining = self.client.get(f"/repos/{self.owner}/{self.repo}/releases", params={
                'per_page': 100
            })
            print(f"✓ Fetched {len(data)} releases (Rate limit: {remaining} remaining)")
            return data
        except Exception as e:
            print(f"Error fetching releases: {e}")
            return []

    def process_data(self, releases_data):
        """Process releases data and extract comprehensive fields"""
        processed_releases = []

        print(f"✓ Processing {len(releases_data)} releases...")

        for release in releases_data:
            # Parse dates
            created_at = self._parse_date(release.get('created_at', ''))

            # Calculate age
            age_days = self.calculate_age_days(release.get('created_at', '')) if release.get('created_at') else 'N/A'

            # Analyze content
            body = release.get('body') or ''
            name = release.get('name') or ''
            tag_name = release.get('tag_name') or ''

            processed_release = {
                'tag_name': tag_name,
                'name': name,
                'draft': release.get('draft', False),
                'prerelease': release.get('prerelease', False),
                'created_at': release.get('created_at', ''),
                'published_at': release.get('published_at', ''),
                'author_login': release.get('author', {}).get('login', '') if release.get('author') else '',
                'author_type': release.get('author', {}).get('type', '') if release.get('author') else '',
                'tarball_url': release.get('tarball_url', ''),
                'zipball_url': release.get('zipball_url', ''),
                'html_url': release.get('html_url', ''),
                'assets_count': len(release.get('assets', [])),
                'body_length': len(body),
                'name_length': len(name),
                'tag_length': len(tag_name),
                'age_days': age_days,
                'is_major_version': self._is_major_version(tag_name),
                'is_patch_version': self._is_patch_version(tag_name),
                'has_changelog': 'changelog' in body.lower() or 'changes' in body.lower(),
                'has_breaking_changes': 'breaking' in body.lower(),
                'repo_name': self.repo,
                'org_name': self.owner
            }

            # Add temporal analysis
            if created_at:
                processed_release.update({
                    'created_day_of_week': created_at.strftime('%A'),
                    'created_hour': created_at.hour,
                    'created_month': created_at.strftime('%B'),
                    'is_weekend_created': created_at.weekday() >= 5
                })

            processed_releases.append(processed_release)

        return processed_releases

    @staticmethod
    def _parse_date(date_str):
        """Parse ISO date string to datetime object"""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _is_major_version(tag):
        """Check if this is a major version (x.0.0)"""
        if not tag:
            return False
        # Simple heuristic: contains .0.0 or is v1, v2, etc.
        try:
            return '.0.0' in tag or (tag.startswith('v') and '.' not in tag[1:])
        except (AttributeError, TypeError):
            return False

    @staticmethod
    def _is_patch_version(tag):
        """Check if this is a patch version (x.y.z where z > 0)"""
        if not tag:
            return False
        # Simple heuristic: has 3 parts and last part is not 0
        parts = tag.replace('v', '').split('.')
        return len(parts) >= 3 and parts[-1] != '0'
