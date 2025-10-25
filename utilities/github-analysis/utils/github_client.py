#!/usr/bin/env python3
"""
GitHub API client with authentication and rate limiting
"""

import requests
import time
import logging
from datetime import datetime
from typing import Tuple, Dict, List, Any, Optional
import sys
import os

# Add parent directory to path for imports
if __name__ == '__main__':
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .config import GITHUB_API_BASE, get_github_token

logger = logging.getLogger(__name__)

# Constants
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 1

class GitHubClient:
    """GitHub API client with authentication and rate limiting"""

    def __init__(self, token: Optional[str] = None, delay_seconds: float = 0.5):
        if delay_seconds < 0:
            raise ValueError("Delay seconds must be non-negative")

        self.token = token or get_github_token()
        self.delay_seconds = delay_seconds
        self.session = requests.Session()

        # Setup headers
        self.session.headers.update({
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'GitHub-Analyzer/1.0'
        })

        if self.token:
            self.session.headers['Authorization'] = f'token {self.token}'
            print("✓ Using authenticated API (higher rate limits)")
            logger.info("GitHub client initialized with authentication")
        else:
            print("⚠️  Using unauthenticated API (60 requests/hour limit)")
            print("   Set GITHUB_TOKEN environment variable for better limits")
            logger.warning("GitHub client initialized without authentication")

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Tuple[Any, int]:
        """Make GET request to GitHub API with rate limiting and retry logic"""
        if not endpoint or not isinstance(endpoint, str):
            raise ValueError("Endpoint must be a non-empty string")

        url = f"{GITHUB_API_BASE}{endpoint}"

        for attempt in range(MAX_RETRIES):
            try:
                logger.debug(f"Making request to {endpoint} (attempt {attempt + 1})")
                response = self.session.get(url, params=params, timeout=DEFAULT_TIMEOUT)

                # Check rate limits
                remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
                reset_time = int(response.headers.get('X-RateLimit-Reset', 0))

                if response.status_code == 403 and remaining == 0:
                    reset_dt = datetime.fromtimestamp(reset_time)
                    error_msg = f"Rate limit exceeded. Resets at {reset_dt}"
                    logger.error(error_msg)
                    raise Exception(error_msg)

                if response.status_code == 404:
                    logger.warning(f"Resource not found: {endpoint}")
                    return [], remaining

                response.raise_for_status()

                # Rate limiting
                time.sleep(self.delay_seconds)

                return response.json(), remaining

            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout for {endpoint} (attempt {attempt + 1})")
                if attempt == MAX_RETRIES - 1:
                    raise Exception(f"Request timeout after {MAX_RETRIES} attempts")
                time.sleep(RETRY_DELAY * (attempt + 1))

            except requests.exceptions.ConnectionError:
                logger.warning(f"Connection error for {endpoint} (attempt {attempt + 1})")
                if attempt == MAX_RETRIES - 1:
                    raise Exception(f"Connection failed after {MAX_RETRIES} attempts")
                time.sleep(RETRY_DELAY * (attempt + 1))

            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed for {endpoint}: {e}")
                raise Exception(f"API request failed: {e}")

        raise Exception(f"Failed to complete request after {MAX_RETRIES} attempts")

    def paginate(self, endpoint: str, params: Optional[Dict[str, Any]] = None, max_pages: Optional[int] = None) -> List[Any]:
        """Paginate through GitHub API results with error handling"""
        if not endpoint or not isinstance(endpoint, str):
            raise ValueError("Endpoint must be a non-empty string")

        if max_pages is not None and max_pages <= 0:
            raise ValueError("Max pages must be positive")

        page = 1
        all_data = []

        try:
            while True:
                if max_pages and page > max_pages:
                    logger.info(f"Reached max pages limit ({max_pages})")
                    break

                # Add pagination params
                page_params = (params or {}).copy()
                page_params.update({
                    'page': page,
                    'per_page': 100  # GitHub API max
                })

                print(f"Fetching page {page}: {endpoint}")
                logger.debug(f"Fetching page {page} for {endpoint}")

                data, remaining = self.get(endpoint, page_params)

                if not data:
                    print(f"No more data on page {page}")
                    logger.info(f"No data found on page {page}, stopping pagination")
                    break

                print(f"  Found {len(data)} items (Rate limit: {remaining} remaining)")
                logger.debug(f"Page {page}: {len(data)} items, {remaining} requests remaining")
                all_data.extend(data)

                # Check if there are more pages (GitHub returns empty array when no more data)
                if len(data) < page_params['per_page']:
                    print("Reached last page")
                    logger.info("Reached last page of results")
                    break

                page += 1

                # Safety check to prevent infinite loops
                if page > 1000:  # Reasonable upper limit
                    logger.warning("Reached safety limit of 1000 pages")
                    break

            logger.info(f"Pagination complete: {len(all_data)} total items")
            return all_data

        except Exception as e:
            logger.error(f"Pagination failed for {endpoint}: {e}")
            if all_data:
                logger.info(f"Returning partial data: {len(all_data)} items")
            return all_data
