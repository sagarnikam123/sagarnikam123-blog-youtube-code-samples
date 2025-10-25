#!/usr/bin/env python3
"""
Base analyzer class with common functionality
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
import sys
import os
import logging
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
if __name__ == '__main__':
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.github_client import GitHubClient
from utils.exporters import save_to_csv, save_to_markdown, save_to_json, save_to_excel, generate_summary_stats

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BaseAnalyzer(ABC):
    """Base class for all GitHub analyzers"""

    def __init__(self, owner: str, repo: str, delay_seconds: float = 0.5):
        if not owner or not isinstance(owner, str):
            raise ValueError("Owner must be a non-empty string")
        if not repo or not isinstance(repo, str):
            raise ValueError("Repository name must be a non-empty string")
        if delay_seconds < 0:
            raise ValueError("Delay seconds must be non-negative")

        self.owner = owner.strip()
        self.repo = repo.strip()
        self.client = GitHubClient(delay_seconds=delay_seconds)
        self.data: List[Dict[str, Any]] = []
        logger.info(f"Initialized {self.__class__.__name__} for {self.owner}/{self.repo}")

    @abstractmethod
    def fetch_data(self, **kwargs):
        """Fetch data from GitHub API - must be implemented by subclasses"""
        pass

    @abstractmethod
    def process_data(self, raw_data):
        """Process raw API data into analysis format - must be implemented by subclasses"""
        pass

    @abstractmethod
    def get_analysis_type(self):
        """Return the analysis type name - must be implemented by subclasses"""
        pass

    def analyze(self, **kwargs) -> List[Dict[str, Any]]:
        """Main analysis method with comprehensive error handling"""
        try:
            print(f"🚀 Analyzing {self.get_analysis_type()} from {self.owner}/{self.repo}")
            logger.info(f"Starting analysis for {self.owner}/{self.repo}")

            # Fetch raw data
            raw_data = self.fetch_data(**kwargs)

            if not raw_data:
                print(f"❌ No {self.get_analysis_type()} found")
                logger.warning(f"No {self.get_analysis_type()} data found for {self.owner}/{self.repo}")
                return []

            # Process data
            self.data = self.process_data(raw_data)

            print(f"✓ Processed {len(self.data)} {self.get_analysis_type()}")
            logger.info(f"Successfully processed {len(self.data)} {self.get_analysis_type()}")
            return self.data

        except Exception as e:
            error_msg = f"Analysis failed for {self.owner}/{self.repo}: {str(e)}"
            print(f"❌ {error_msg}")
            logger.error(error_msg, exc_info=True)
            return []

    def save(self, output_file: str, format_type: str = 'csv') -> bool:
        """Save analysis results with error handling"""
        if not output_file or not isinstance(output_file, str):
            raise ValueError("Output file must be a non-empty string")

        if format_type not in ['csv', 'markdown', 'json', 'excel']:
            raise ValueError(f"Unsupported format: {format_type}")

        if not self.data:
            print("No data to save")
            logger.warning("No data available to save")
            return False

        try:
            if format_type == 'csv':
                save_to_csv(self.data, output_file)
            elif format_type == 'markdown':
                title = f"GitHub {self.get_analysis_type().title()} - {self.owner}/{self.repo}"
                metadata = {
                    'Repository': f"[{self.owner}/{self.repo}](https://github.com/{self.owner}/{self.repo})",
                    **generate_summary_stats(self.data),
                    'Tool': 'GitHub Analyzer'
                }
                save_to_markdown(self.data, output_file, title, metadata)
            elif format_type == 'json':
                save_to_json(self.data, output_file)
            elif format_type == 'excel':
                save_to_excel(self.data, output_file, f"{self.get_analysis_type().title()} Analysis")

            logger.info(f"Successfully saved {len(self.data)} items to {output_file}")
            return True

        except Exception as e:
            error_msg = f"Failed to save data to {output_file}: {str(e)}"
            print(f"❌ {error_msg}")
            logger.error(error_msg, exc_info=True)
            return False

    @staticmethod
    def classify_issue_type(title, labels):
        """Classify issue type based on title, labels, and body"""
        title_lower = title.lower()
        labels_lower = [label.lower() for label in labels]

        # Check labels first (most accurate)
        if any(label in labels_lower for label in ['bug', 'defect', 'error']):
            return 'bug'
        elif any(label in labels_lower for label in ['enhancement', 'feature', 'improvement']):
            return 'enhancement'
        elif any(label in labels_lower for label in ['documentation', 'docs']):
            return 'documentation'
        elif any(label in labels_lower for label in ['question', 'help', 'support']):
            return 'question'

        # Fallback to title/body analysis
        if any(word in title_lower for word in ['bug', 'error', 'crash', 'fail', 'broken']):
            return 'bug'
        elif any(word in title_lower for word in ['feature', 'enhancement', 'add', 'support', 'implement']):
            return 'enhancement'
        elif any(word in title_lower for word in ['doc', 'documentation', 'readme', 'guide']):
            return 'documentation'
        elif any(word in title_lower for word in ['question', 'help', 'how', 'why']):
            return 'question'

        return 'other'

    @staticmethod
    def classify_priority(labels):
        """Classify priority based on labels"""
        labels_lower = [label.lower() for label in labels]

        if any(word in ' '.join(labels_lower) for word in ['critical', 'urgent', 'high', 'p0', 'p1']):
            return 'high'
        elif any(word in ' '.join(labels_lower) for word in ['low', 'minor', 'p3', 'p4']):
            return 'low'

        return 'normal'

    @staticmethod
    def estimate_complexity(title, body, labels):
        """Estimate complexity based on various factors"""
        labels_lower = [label.lower() for label in labels]

        # Check for complexity labels
        if any(word in ' '.join(labels_lower) for word in ['complex', 'hard', 'difficult']):
            return 'high'
        elif any(word in ' '.join(labels_lower) for word in ['easy', 'simple', 'good first issue', 'beginner']):
            return 'low'

        # Estimate based on content length and keywords
        complexity_score = 0

        # Title complexity indicators
        if any(word in title.lower() for word in ['refactor', 'redesign', 'architecture', 'performance']):
            complexity_score += 2
        elif any(word in title.lower() for word in ['fix', 'update', 'improve']):
            complexity_score += 1

        # Body length indicator
        if len(body) > 1000:
            complexity_score += 1
        elif len(body) < 200:
            complexity_score -= 1

        if complexity_score >= 2:
            return 'high'
        elif complexity_score <= -1:
            return 'low'

        return 'medium'

    @staticmethod
    def calculate_age_days(created_at: Optional[str]) -> Any:
        """Calculate age in days from creation date"""
        if not created_at or not isinstance(created_at, str):
            return 'N/A'

        try:
            created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            return (now - created_dt).days
        except (ValueError, TypeError) as e:
            logger.debug(f"Failed to parse date '{created_at}': {e}")
            return 'N/A'

    @staticmethod
    def calculate_time_to_close(created_at: Optional[str], closed_at: Optional[str]) -> Any:
        """Calculate time to close in days"""
        if not closed_at or not created_at:
            return 'N/A'

        if not isinstance(created_at, str) or not isinstance(closed_at, str):
            return 'N/A'

        try:
            created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            closed_dt = datetime.fromisoformat(closed_at.replace('Z', '+00:00'))
            return (closed_dt - created_dt).days
        except (ValueError, TypeError) as e:
            logger.debug(f"Failed to parse dates '{created_at}' or '{closed_at}': {e}")
            return 'N/A'
