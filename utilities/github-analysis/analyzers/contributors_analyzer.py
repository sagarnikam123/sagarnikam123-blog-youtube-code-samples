#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyzers.base_analyzer import BaseAnalyzer
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class ContributorsAnalyzer(BaseAnalyzer):
    def __init__(self, owner: str, repo: str, delay_seconds: float = 0.5):
        super().__init__(owner, repo, delay_seconds)

    def get_analysis_type(self):
        return "contributors"

    def fetch_data(self, **kwargs) -> List[Dict[str, Any]]:
        """Fetch contributors data from GitHub API with error handling"""
        try:
            endpoint = f"/repos/{self.owner}/{self.repo}/contributors"
            params = {'per_page': 100}

            logger.info(f"Fetching contributors for {self.owner}/{self.repo}")
            data, remaining = self.client.get(endpoint, params)

            if not isinstance(data, list):
                logger.warning(f"Unexpected data format for contributors: {type(data)}")
                return []

            print(f"✓ Fetched {len(data)} contributors (Rate limit: {remaining} remaining)")
            logger.info(f"Successfully fetched {len(data)} contributors")
            return data

        except Exception as e:
            error_msg = f"Error fetching contributors: {e}"
            print(error_msg)
            logger.error(error_msg)
            return []

    def process_data(self, contributors_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process contributors data and extract comprehensive fields"""
        if not contributors_data or not isinstance(contributors_data, list):
            logger.warning("No valid contributors data provided for processing")
            return []

        processed_contributors = []

        print(f"✓ Processing {len(contributors_data)} contributors...")
        logger.info(f"Processing {len(contributors_data)} contributors")

        for i, contributor in enumerate(contributors_data):
            try:
                if not isinstance(contributor, dict):
                    logger.warning(f"Skipping invalid contributor data at index {i}")
                    continue
                # Safe extraction of contributor data
                contributions = contributor.get('contributions', 0)
                try:
                    contributions = int(contributions) if contributions else 0
                except (ValueError, TypeError):
                    logger.debug(f"Invalid contributions value for contributor {i}: {contributions}")
                    contributions = 0

                processed_contributor = {
                    'login': contributor.get('login', ''),
                    'id': contributor.get('id', ''),
                    'avatar_url': contributor.get('avatar_url', ''),
                    'gravatar_id': contributor.get('gravatar_id', ''),
                    'url': contributor.get('url', ''),
                    'html_url': contributor.get('html_url', ''),
                    'followers_url': contributor.get('followers_url', ''),
                    'following_url': contributor.get('following_url', ''),
                    'gists_url': contributor.get('gists_url', ''),
                    'starred_url': contributor.get('starred_url', ''),
                    'subscriptions_url': contributor.get('subscriptions_url', ''),
                    'organizations_url': contributor.get('organizations_url', ''),
                    'repos_url': contributor.get('repos_url', ''),
                    'events_url': contributor.get('events_url', ''),
                    'received_events_url': contributor.get('received_events_url', ''),
                    'type': contributor.get('type', ''),
                    'site_admin': contributor.get('site_admin', False),
                    'contributions': contributions,
                    'repo_name': self.repo,
                    'org_name': self.owner
                }

                processed_contributors.append(processed_contributor)

            except Exception as e:
                logger.error(f"Error processing contributor {i}: {e}")
                continue

        # Sort by contributions descending with error handling
        try:
            processed_contributors.sort(key=lambda x: x.get('contributions', 0), reverse=True)
        except Exception as e:
            logger.error(f"Error sorting contributors: {e}")

        logger.info(f"Successfully processed {len(processed_contributors)} contributors")
        return processed_contributors
