#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyzers.issues_analyzer import IssuesAnalyzer
from analyzers.commits_analyzer import CommitsAnalyzer
from analyzers.contributors_analyzer import ContributorsAnalyzer
from analyzers.releases_analyzer import ReleasesAnalyzer
from analyzers.pulls_analyzer import PullsAnalyzer
from datetime import datetime
import statistics

class CompareAnalyzer:
    def __init__(self, delay_seconds=0.5):
        self.delay_seconds = delay_seconds
        self.results = {}

    def compare_repositories(self, repos, metric='issues', **kwargs):
        """Compare multiple repositories on a specific metric"""
        print(f"🔍 Comparing {len(repos)} repositories on '{metric}' metric")
        print("-" * 60)

        for repo in repos:
            if '/' not in repo:
                print(f"❌ Invalid repo format: {repo} (should be owner/repo)")
                continue

            owner, repo_name = repo.split('/', 1)
            print(f"📊 Analyzing {owner}/{repo_name}...")

            try:
                # Get analyzer based on metric
                analyzer = self._get_analyzer(metric, owner, repo_name)
                data = analyzer.analyze(**kwargs)

                # Calculate comparison metrics
                comparison_data = self._calculate_metrics(data, metric, repo)
                self.results[repo] = comparison_data

                print(f"✓ {repo}: {len(data)} {metric} analyzed")

            except Exception as e:
                print(f"❌ Error analyzing {repo}: {e}")
                self.results[repo] = {'error': str(e)}

        return self._generate_comparison_report()

    def _get_analyzer(self, metric, owner, repo):
        """Get appropriate analyzer based on metric"""
        analyzers = {
            'issues': IssuesAnalyzer,
            'commits': CommitsAnalyzer,
            'contributors': ContributorsAnalyzer,
            'releases': ReleasesAnalyzer,
            'pulls': PullsAnalyzer
        }

        if metric not in analyzers:
            raise ValueError(f"Unsupported metric: {metric}")

        return analyzers[metric](owner, repo, self.delay_seconds)

    def _calculate_metrics(self, data, metric, repo):
        """Calculate comparison metrics for the data"""
        if not data:
            return {'total_count': 0, 'error': 'No data found'}

        base_metrics = {
            'repository': repo,
            'total_count': len(data),
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # Metric-specific calculations
        if metric == 'issues':
            return {**base_metrics, **self._calculate_issues_metrics(data)}
        elif metric == 'commits':
            return {**base_metrics, **self._calculate_commits_metrics(data)}
        elif metric == 'contributors':
            return {**base_metrics, **self._calculate_contributors_metrics(data)}
        elif metric == 'releases':
            return {**base_metrics, **self._calculate_releases_metrics(data)}
        elif metric == 'pulls':
            return {**base_metrics, **self._calculate_pulls_metrics(data)}

        return base_metrics

    @staticmethod
    def _calculate_issues_metrics(data):
        """Calculate issues-specific metrics"""
        open_issues = [item for item in data if item.get('state') == 'open']
        closed_issues = [item for item in data if item.get('state') == 'closed']

        # Age analysis
        ages = [item.get('age_days', 0) for item in data if isinstance(item.get('age_days'), (int, float))]

        return {
            'open_count': len(open_issues),
            'closed_count': len(closed_issues),
            'open_ratio': round(len(open_issues) / len(data) * 100, 1) if data else 0,
            'avg_age_days': round(statistics.mean(ages), 1) if ages else 0,
            'median_age_days': round(statistics.median(ages), 1) if ages else 0,
            'total_comments': sum(item.get('comments_count', 0) for item in data),
            'avg_comments': round(statistics.mean([item.get('comments_count', 0) for item in data]), 1) if data else 0
        }

    @staticmethod
    def _calculate_commits_metrics(data):
        """Calculate commits-specific metrics"""
        feature_commits = [item for item in data if item.get('is_feature_commit')]
        fix_commits = [item for item in data if item.get('is_fix_commit')]
        merge_commits = [item for item in data if item.get('is_merge_commit')]

        return {
            'feature_commits': len(feature_commits),
            'fix_commits': len(fix_commits),
            'merge_commits': len(merge_commits),
            'feature_ratio': round(len(feature_commits) / len(data) * 100, 1) if data else 0,
            'fix_ratio': round(len(fix_commits) / len(data) * 100, 1) if data else 0,
            'unique_authors': len(set(item.get('author_name', '') for item in data if item.get('author_name'))),
            'avg_message_length': round(statistics.mean([item.get('message_length', 0) for item in data]), 1) if data else 0
        }

    @staticmethod
    def _calculate_contributors_metrics(data):
        """Calculate contributors-specific metrics"""
        contributions = [item.get('contributions', 0) for item in data if item.get('contributions')]

        return {
            'total_contributors': len(data),
            'total_contributions': sum(contributions),
            'avg_contributions': round(statistics.mean(contributions), 1) if contributions else 0,
            'median_contributions': round(statistics.median(contributions), 1) if contributions else 0,
            'top_contributor_contributions': max(contributions) if contributions else 0,
            'bot_contributors': len([item for item in data if item.get('type') == 'Bot'])
        }

    @staticmethod
    def _calculate_releases_metrics(data):
        """Calculate releases-specific metrics"""
        prereleases = [item for item in data if item.get('prerelease')]
        drafts = [item for item in data if item.get('draft')]

        return {
            'total_releases': len(data),
            'prerelease_count': len(prereleases),
            'draft_count': len(drafts),
            'stable_releases': len(data) - len(prereleases) - len(drafts),
            'avg_assets': round(statistics.mean([item.get('assets_count', 0) for item in data]), 1) if data else 0,
            'releases_with_assets': len([item for item in data if item.get('assets_count', 0) > 0])
        }

    @staticmethod
    def _calculate_pulls_metrics(data):
        """Calculate pull requests-specific metrics"""
        merged_prs = [item for item in data if item.get('is_merged')]
        open_prs = [item for item in data if item.get('state') == 'open']

        # Size analysis
        sizes = {'XS': 0, 'S': 0, 'M': 0, 'L': 0, 'XL': 0}
        for item in data:
            size = item.get('pr_size', 'XS')
            if size in sizes:
                sizes[size] += 1

        return {
            'merged_count': len(merged_prs),
            'open_count': len(open_prs),
            'merge_ratio': round(len(merged_prs) / len(data) * 100, 1) if data else 0,
            'avg_comments': round(statistics.mean([item.get('comments_count', 0) for item in data]), 1) if data else 0,
            'avg_review_comments': round(statistics.mean([item.get('review_comments_count', 0) for item in data]), 1) if data else 0,
            **{f'size_{k.lower()}': v for k, v in sizes.items()}
        }

    def _generate_comparison_report(self):
        """Generate comparison report from results"""
        if not self.results:
            return []

        # Convert to list format for export
        comparison_data = []

        for repo, metrics in self.results.items():
            if 'error' in metrics:
                comparison_data.append({
                    'repository': repo,
                    'status': 'error',
                    'error_message': metrics['error']
                })
            else:
                comparison_data.append(metrics)

        return comparison_data

    @staticmethod
    def save_comparison(data, output_file, format_type='csv'):
        """Save comparison results"""
        if format_type == 'csv':
            from utils.exporters import save_to_csv
            save_to_csv(data, output_file)
        elif format_type == 'markdown':
            from utils.exporters import save_to_markdown
            title = "Repository Comparison Analysis"
            metadata = {
                'Repositories Compared': len(data),
                'Analysis Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'Tool': 'GitHub Analyzer - Compare Mode'
            }
            save_to_markdown(data, output_file, title, metadata)
        elif format_type == 'json':
            from utils.exporters import save_to_json
            save_to_json(data, output_file)
        elif format_type == 'excel':
            from utils.exporters import save_to_excel
            save_to_excel(data, output_file, "Repository Comparison")
