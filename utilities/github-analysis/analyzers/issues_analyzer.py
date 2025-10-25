#!/usr/bin/env python3
"""
GitHub Issues Analyzer
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyzers.base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)

class IssuesAnalyzer(BaseAnalyzer):
    """Analyzer for GitHub repository issues"""

    def get_analysis_type(self):
        return "issues"

    def fetch_data(self, state: str = 'all', max_pages: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch issues from GitHub API with validation"""
        if state not in ['open', 'closed', 'all']:
            raise ValueError(f"Invalid state: {state}. Must be 'open', 'closed', or 'all'")

        try:
            endpoint = f"/repos/{self.owner}/{self.repo}/issues"
            params = {
                'state': state,
                'sort': 'created',
                'direction': 'desc'
            }

            logger.info(f"Fetching issues for {self.owner}/{self.repo} with state={state}")
            return self.client.paginate(endpoint, params, max_pages)

        except Exception as e:
            logger.error(f"Failed to fetch issues: {e}")
            raise

    def process_data(self, raw_data: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        """Process raw issues data into comprehensive analysis format"""
        if not raw_data or not isinstance(raw_data, list):
            logger.warning("No valid raw data provided for processing")
            return []

        processed_data = []

        for i, issue in enumerate(raw_data):
            try:
                if not isinstance(issue, dict):
                    logger.warning(f"Skipping invalid issue data at index {i}")
                    continue
                # Skip pull requests (they appear in issues API)
                if 'pull_request' in issue:
                    continue

                # Extract basic fields with safe access
                issue_number = issue.get('number', 0)
                title = issue.get('title', '')
                state = issue.get('state', 'unknown')

                user = issue.get('user', {})
                author = user.get('login', 'unknown') if user else 'unknown'

                created_at = issue.get('created_at', '')
                updated_at = issue.get('updated_at', '')
                closed_at = issue.get('closed_at')
                comments_count = issue.get('comments', 0)
                body = issue.get('body', '') or ''

                # Labels and assignees with safe extraction
                labels = []
                for label in issue.get('labels', []):
                    if isinstance(label, dict) and 'name' in label:
                        labels.append(label['name'])
                labels_str = ', '.join(labels) if labels else 'None'

                assignees = []
                for assignee in issue.get('assignees', []):
                    if isinstance(assignee, dict) and 'login' in assignee:
                        assignees.append(assignee['login'])
                assignees_str = ', '.join(assignees) if assignees else 'None'

                # Milestone with safe access
                milestone = issue.get('milestone', {})
                milestone_title = milestone.get('title', 'None') if milestone else 'None'

                # Time calculations with error handling
                age_days = self.calculate_age_days(created_at)

                try:
                    updated_dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                    now = datetime.now(timezone.utc)
                    days_since_update = (now - updated_dt).days
                except (ValueError, TypeError):
                    days_since_update = 'N/A'

                time_to_close_days = self.calculate_time_to_close(created_at, closed_at)

                # Advanced classifications
                issue_type = self.classify_issue_type(title, labels)
                priority = self.classify_priority(labels)
                complexity = self.estimate_complexity(title, body, labels)
                severity_level = self.classify_severity(labels, title, body)

                # Content analysis
                title_length = len(title)
                body_length = len(body)
                word_count = len((title + ' ' + body).split())
                has_code_snippets = '```' in body or '`' in body
                has_error_logs = any(word in body.lower() for word in ['error', 'exception', 'traceback', 'stack trace'])
                has_screenshots = any(word in body.lower() for word in ['screenshot', 'image', '![', '.png', '.jpg', '.gif'])
                question_marks_count = body.count('?') + title.count('?')
                exclamation_marks_count = body.count('!') + title.count('!')

                # Engagement & activity metrics with safe access
                reactions = issue.get('reactions', {})
                reactions_total = reactions.get('total_count', 0) if reactions else 0
                reactions_positive = 0
                reactions_negative = 0

                if reactions:
                    reactions_positive = (reactions.get('+1', 0) + reactions.get('heart', 0) +
                                        reactions.get('hooray', 0) + reactions.get('rocket', 0))
                    reactions_negative = reactions.get('-1', 0) + reactions.get('confused', 0)

                # Team & process metrics
                is_good_first_issue = any('good first issue' in label.lower() or 'beginner' in label.lower() for label in labels)
                has_help_wanted = any('help wanted' in label.lower() for label in labels)
                is_security_related = any(word in (title + ' ' + body + ' ' + labels_str).lower()
                                        for word in ['security', 'vulnerability', 'cve', 'exploit'])
                is_performance_related = any(word in (title + ' ' + body + ' ' + labels_str).lower()
                                           for word in ['performance', 'slow', 'memory', 'cpu', 'optimization'])
                is_breaking_change = any(word in (title + ' ' + body + ' ' + labels_str).lower()
                                       for word in ['breaking', 'breaking change', 'backward compatibility'])

                # Time-based analysis with error handling
                try:
                    created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    created_day_of_week = created_dt.strftime('%A')
                    created_hour = created_dt.hour
                    created_month = created_dt.strftime('%B')
                    is_weekend_created = created_dt.weekday() >= 5
                except (ValueError, TypeError):
                    created_day_of_week = 'N/A'
                    created_hour = 'N/A'
                    created_month = 'N/A'
                    is_weekend_created = False

                # User type analysis
                user_type = self.classify_user_type(author, assignees)

                # Component analysis
                component_affected = self.identify_component(title, body, labels)
                language_mentioned = self.extract_languages(title, body)

                # Relationship analysis
                linked_issues_count = body.count('#') + title.count('#')
                external_references = len([word for word in body.split() if word.startswith('http')])

                # Boolean flags
                has_labels = 'Yes' if labels else 'No'
                has_assignees = 'Yes' if assignees else 'No'
                has_milestone = 'Yes' if milestone_title != 'None' else 'No'
                has_body = 'Yes' if body.strip() else 'No'

                # Ordered data structure (descending importance)
                processed_data.append({
                # Most important - Core identification
                'title': title,
                'state': state,
                'issue_number': issue_number,
                'priority': priority,
                'severity_level': severity_level,
                'issue_type': issue_type,
                'complexity': complexity,

                # High importance - Status & timing
                'age_days': age_days,
                'days_since_update': days_since_update,
                'time_to_close_days': time_to_close_days,
                'author': author,
                'assignees': assignees_str,
                'milestone': milestone_title,

                # Medium-high importance - Engagement
                'comments_count': comments_count,
                'reactions_total': reactions_total,
                'reactions_positive': reactions_positive,
                'reactions_negative': reactions_negative,

                # Medium importance - Classification
                'labels': labels_str,
                'component_affected': component_affected,
                'language_mentioned': language_mentioned,
                'user_type': user_type,

                # Medium-low importance - Content analysis
                'word_count': word_count,
                'title_length': title_length,
                'body_length': body_length,
                'has_code_snippets': has_code_snippets,
                'has_error_logs': has_error_logs,
                'has_screenshots': has_screenshots,

                # Lower importance - Flags & metrics
                'is_security_related': is_security_related,
                'is_performance_related': is_performance_related,
                'is_breaking_change': is_breaking_change,
                'is_good_first_issue': is_good_first_issue,
                'has_help_wanted': has_help_wanted,

                # Temporal analysis
                'created_day_of_week': created_day_of_week,
                'created_hour': created_hour,
                'created_month': created_month,
                'is_weekend_created': is_weekend_created,

                # Content metrics
                'question_marks_count': question_marks_count,
                'exclamation_marks_count': exclamation_marks_count,
                'linked_issues_count': linked_issues_count,
                'external_references': external_references,

                # Boolean flags
                'has_labels': has_labels,
                'has_assignees': has_assignees,
                'has_milestone': has_milestone,
                'has_body': has_body,

                # Timestamps (raw data)
                'created_at': created_at,
                'updated_at': updated_at,
                'closed_at': closed_at or 'N/A',

                    # Repository context
                    'repo_name': self.repo,
                    'org_name': self.owner,
                    'url': issue.get('html_url', '')
                })

            except Exception as e:
                logger.error(f"Error processing issue {i}: {e}")
                continue

        return processed_data

    @staticmethod
    def classify_severity(labels, title, body):
        """Classify severity level"""
        text = (title + ' ' + body + ' ' + ' '.join(labels)).lower()

        if any(word in text for word in ['critical', 'urgent', 'blocker', 'p0']):
            return 'Critical'
        elif any(word in text for word in ['high', 'important', 'p1']):
            return 'High'
        elif any(word in text for word in ['low', 'minor', 'p3', 'p4']):
            return 'Low'

        return 'Medium'

    @staticmethod
    def classify_user_type(author, assignees):
        """Classify if user is internal team member or external"""
        # Simple heuristic - if author is also assignee, likely internal
        if author in assignees:
            return 'Internal'
        return 'External'

    @staticmethod
    def identify_component(title, body, labels):
        """Identify affected system component"""
        text = (title + ' ' + body + ' ' + ' '.join(labels)).lower()

        components = {
            'frontend': ['frontend', 'ui', 'web', 'react', 'vue', 'angular'],
            'backend': ['backend', 'api', 'server', 'service'],
            'database': ['database', 'db', 'sql', 'postgres', 'mysql'],
            'documentation': ['docs', 'documentation', 'readme'],
            'ci/cd': ['ci', 'cd', 'pipeline', 'build', 'deploy'],
            'security': ['security', 'auth', 'authentication'],
            'performance': ['performance', 'optimization', 'speed']
        }

        for component, keywords in components.items():
            if any(keyword in text for keyword in keywords):
                return component

        return 'general'

    @staticmethod
    def extract_languages(title, body):
        """Extract mentioned programming languages"""
        text = (title + ' ' + body).lower()
        languages = ['python', 'javascript', 'java', 'go', 'rust', 'c++', 'c#',
                    'typescript', 'php', 'ruby', 'swift', 'kotlin']

        found = [lang for lang in languages if lang in text]
        return ', '.join(found) if found else 'None'
