#!/usr/bin/env python3

from .issues_analyzer import IssuesAnalyzer
from .commits_analyzer import CommitsAnalyzer
from .contributors_analyzer import ContributorsAnalyzer
from .releases_analyzer import ReleasesAnalyzer
from .pulls_analyzer import PullsAnalyzer
from datetime import datetime, timedelta
import statistics

class HealthAnalyzer:
    def __init__(self, owner, repo, delay_seconds=0.5):
        self.owner = owner
        self.repo = repo
        self.delay_seconds = delay_seconds
        self.health_data = {}
        self.recommendations = []

    def analyze_health(self):
        """Comprehensive repository health analysis"""
        print(f"🏥 Analyzing repository health for {self.owner}/{self.repo}")
        print("-" * 60)

        # Collect data from all analyzers
        self._collect_issues_health()
        self._collect_commits_health()
        self._collect_contributors_health()
        self._collect_releases_health()
        self._collect_pulls_health()

        # Calculate overall health score
        self._calculate_health_score()

        # Generate recommendations
        self._generate_recommendations()

        return self._format_health_report()

    def _collect_issues_health(self):
        """Analyze issues health metrics"""
        try:
            analyzer = IssuesAnalyzer(self.owner, self.repo, self.delay_seconds)
            issues = analyzer.analyze(state='all', max_pages=3)

            if not issues:
                self.health_data['issues'] = {'status': 'no_data', 'score': 50}
                return

            open_issues = [i for i in issues if i.get('state') == 'open']

            # Calculate metrics
            total_issues = len(issues)
            open_ratio = len(open_issues) / total_issues if total_issues > 0 else 0

            # Age analysis
            ages = [i.get('age_days', 0) for i in open_issues if isinstance(i.get('age_days'), (int, float))]
            avg_age = statistics.mean(ages) if ages else 0
            old_issues = len([age for age in ages if age > 90])  # Issues older than 3 months

            # Response analysis
            total_comments = sum(i.get('comments_count', 0) for i in issues)
            avg_comments = total_comments / total_issues if total_issues > 0 else 0

            # Calculate score (0-100)
            score = 100
            if open_ratio > 0.7: score -= 30  # Too many open issues
            elif open_ratio > 0.5: score -= 15
            if avg_age > 180: score -= 25  # Very old issues
            elif avg_age > 90: score -= 15
            if old_issues > total_issues * 0.3: score -= 20  # Too many stale issues
            if avg_comments < 1: score -= 10  # Low engagement

            self.health_data['issues'] = {
                'total_issues': total_issues,
                'open_issues': len(open_issues),
                'open_ratio': round(open_ratio * 100, 1),
                'avg_age_days': round(avg_age, 1),
                'old_issues_count': old_issues,
                'avg_comments': round(avg_comments, 1),
                'score': max(0, min(100, score)),
                'status': 'healthy' if score >= 70 else 'warning' if score >= 40 else 'critical'
            }

        except Exception as e:
            self.health_data['issues'] = {'status': 'error', 'error': str(e), 'score': 0}

    def _collect_commits_health(self):
        """Analyze commits health metrics"""
        try:
            analyzer = CommitsAnalyzer(self.owner, self.repo, self.delay_seconds)
            commits = analyzer.analyze(max_pages=3)

            if not commits:
                self.health_data['commits'] = {'status': 'no_data', 'score': 50}
                return

            # Activity analysis
            total_commits = len(commits)
            unique_authors = len(set(c.get('author_name', '') for c in commits if c.get('author_name')))

            # Commit type analysis
            feature_commits = len([c for c in commits if c.get('is_feature_commit')])
            fix_commits = len([c for c in commits if c.get('is_fix_commit')])

            # Calculate ratios
            feature_ratio = feature_commits / total_commits if total_commits > 0 else 0
            fix_ratio = fix_commits / total_commits if total_commits > 0 else 0

            # Calculate score
            score = 100
            if unique_authors < 2: score -= 30  # Single contributor risk
            elif unique_authors < 5: score -= 15
            if feature_ratio < 0.3: score -= 20  # Low innovation
            if fix_ratio > 0.6: score -= 25  # Too many fixes (quality issues)

            self.health_data['commits'] = {
                'total_commits': total_commits,
                'unique_authors': unique_authors,
                'feature_ratio': round(feature_ratio * 100, 1),
                'fix_ratio': round(fix_ratio * 100, 1),
                'score': max(0, min(100, score)),
                'status': 'healthy' if score >= 70 else 'warning' if score >= 40 else 'critical'
            }

        except Exception as e:
            self.health_data['commits'] = {'status': 'error', 'error': str(e), 'score': 0}

    def _collect_contributors_health(self):
        """Analyze contributors health metrics"""
        try:
            analyzer = ContributorsAnalyzer(self.owner, self.repo, self.delay_seconds)
            contributors = analyzer.analyze()

            if not contributors:
                self.health_data['contributors'] = {'status': 'no_data', 'score': 50}
                return

            total_contributors = len(contributors)
            contributions = [c.get('contributions', 0) for c in contributors]
            total_contributions = sum(contributions)

            # Bus factor analysis (top contributor dominance)
            top_contributor_ratio = max(contributions) / total_contributions if total_contributions > 0 else 0
            top_3_ratio = sum(sorted(contributions, reverse=True)[:3]) / total_contributions if total_contributions > 0 else 0

            # Calculate score
            score = 100
            if total_contributors < 3: score -= 40  # Very low contributor count
            elif total_contributors < 10: score -= 20
            if top_contributor_ratio > 0.8: score -= 30  # Single person dependency
            elif top_contributor_ratio > 0.6: score -= 15
            if top_3_ratio > 0.9: score -= 20  # Top 3 dominance

            self.health_data['contributors'] = {
                'total_contributors': total_contributors,
                'total_contributions': total_contributions,
                'top_contributor_ratio': round(top_contributor_ratio * 100, 1),
                'top_3_ratio': round(top_3_ratio * 100, 1),
                'bus_factor': 'high' if top_contributor_ratio < 0.5 else 'medium' if top_contributor_ratio < 0.7 else 'low',
                'score': max(0, min(100, score)),
                'status': 'healthy' if score >= 70 else 'warning' if score >= 40 else 'critical'
            }

        except Exception as e:
            self.health_data['contributors'] = {'status': 'error', 'error': str(e), 'score': 0}

    def _collect_releases_health(self):
        """Analyze releases health metrics"""
        try:
            analyzer = ReleasesAnalyzer(self.owner, self.repo, self.delay_seconds)
            releases = analyzer.analyze()

            if not releases:
                self.health_data['releases'] = {'status': 'no_data', 'score': 50}
                return

            total_releases = len(releases)
            stable_releases = len([r for r in releases if not r.get('prerelease') and not r.get('draft')])

            # Recent activity (last 6 months)
            recent_releases = []
            six_months_ago = datetime.now() - timedelta(days=180)
            for release in releases:
                if release.get('created_at'):
                    try:
                        created_dt = datetime.fromisoformat(release['created_at'].replace('Z', '+00:00'))
                        if created_dt.replace(tzinfo=None) > six_months_ago:
                            recent_releases.append(release)
                    except (ValueError, TypeError):
                        pass

            # Calculate score
            score = 100
            if total_releases == 0: score = 30  # No releases
            elif total_releases < 3: score -= 20  # Few releases
            if len(recent_releases) == 0: score -= 30  # No recent activity
            elif len(recent_releases) < 2: score -= 15
            if stable_releases / total_releases < 0.5: score -= 20  # Too many prereleases

            self.health_data['releases'] = {
                'total_releases': total_releases,
                'stable_releases': stable_releases,
                'recent_releases': len(recent_releases),
                'release_frequency': 'active' if len(recent_releases) >= 3 else 'moderate' if len(recent_releases) >= 1 else 'inactive',
                'score': max(0, min(100, score)),
                'status': 'healthy' if score >= 70 else 'warning' if score >= 40 else 'critical'
            }

        except Exception as e:
            self.health_data['releases'] = {'status': 'error', 'error': str(e), 'score': 0}

    def _collect_pulls_health(self):
        """Analyze pull requests health metrics"""
        try:
            analyzer = PullsAnalyzer(self.owner, self.repo, self.delay_seconds)
            pulls = analyzer.analyze(state='all', max_pages=3)

            if not pulls:
                self.health_data['pulls'] = {'status': 'no_data', 'score': 50}
                return

            total_pulls = len(pulls)
            merged_pulls = len([p for p in pulls if p.get('is_merged')])
            open_pulls = len([p for p in pulls if p.get('state') == 'open'])

            # Review activity
            total_comments = sum(p.get('comments_count', 0) + p.get('review_comments_count', 0) for p in pulls)
            avg_review_activity = total_comments / total_pulls if total_pulls > 0 else 0

            # Merge ratio
            merge_ratio = merged_pulls / total_pulls if total_pulls > 0 else 0

            # Calculate score
            score = 100
            if merge_ratio < 0.5: score -= 25  # Low merge rate
            elif merge_ratio < 0.7: score -= 10
            if avg_review_activity < 2: score -= 20  # Low review activity
            if open_pulls > total_pulls * 0.3: score -= 15  # Too many open PRs

            self.health_data['pulls'] = {
                'total_pulls': total_pulls,
                'merged_pulls': merged_pulls,
                'merge_ratio': round(merge_ratio * 100, 1),
                'avg_review_activity': round(avg_review_activity, 1),
                'score': max(0, min(100, score)),
                'status': 'healthy' if score >= 70 else 'warning' if score >= 40 else 'critical'
            }

        except Exception as e:
            self.health_data['pulls'] = {'status': 'error', 'error': str(e), 'score': 0}

    def _calculate_health_score(self):
        """Calculate overall repository health score"""
        scores = []
        weights = {'issues': 0.25, 'commits': 0.2, 'contributors': 0.25, 'releases': 0.15, 'pulls': 0.15}

        for category, weight in weights.items():
            if category in self.health_data and 'score' in self.health_data[category]:
                scores.append(self.health_data[category]['score'] * weight)

        overall_score = sum(scores) if scores else 0

        self.health_data['overall'] = {
            'score': round(overall_score, 1),
            'grade': 'A' if overall_score >= 85 else 'B' if overall_score >= 70 else 'C' if overall_score >= 55 else 'D' if overall_score >= 40 else 'F',
            'status': 'excellent' if overall_score >= 85 else 'good' if overall_score >= 70 else 'fair' if overall_score >= 55 else 'poor' if overall_score >= 40 else 'critical'
        }

    def _generate_recommendations(self):
        """Generate actionable recommendations based on health analysis"""
        self.recommendations = []

        # Issues recommendations
        if 'issues' in self.health_data:
            issues = self.health_data['issues']
            if issues.get('open_ratio', 0) > 50:
                self.recommendations.append("🔴 High open issue ratio - Consider triaging and closing stale issues")
            if issues.get('avg_age_days', 0) > 90:
                self.recommendations.append("🟡 Old open issues detected - Implement regular issue cleanup")
            if issues.get('avg_comments', 0) < 1:
                self.recommendations.append("🟡 Low issue engagement - Encourage community participation")

        # Contributors recommendations
        if 'contributors' in self.health_data:
            contributors = self.health_data['contributors']
            if contributors.get('bus_factor') == 'low':
                self.recommendations.append("🔴 High bus factor risk - Encourage more contributors")
            if contributors.get('total_contributors', 0) < 5:
                self.recommendations.append("🟡 Limited contributor base - Focus on community building")

        # Releases recommendations
        if 'releases' in self.health_data:
            releases = self.health_data['releases']
            if releases.get('release_frequency') == 'inactive':
                self.recommendations.append("🟡 Inactive release schedule - Consider regular releases")
            if releases.get('total_releases', 0) == 0:
                self.recommendations.append("🔴 No releases found - Implement release management")

        # Overall recommendations
        overall_score = self.health_data.get('overall', {}).get('score', 0)
        if overall_score < 70:
            self.recommendations.append("🔴 Overall health needs improvement - Focus on critical areas")
        elif overall_score >= 85:
            self.recommendations.append("🟢 Excellent repository health - Maintain current practices")

    def _format_health_report(self):
        """Format health data for export"""
        report = {
            'repository': f"{self.owner}/{self.repo}",
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'overall_score': self.health_data.get('overall', {}).get('score', 0),
            'overall_grade': self.health_data.get('overall', {}).get('grade', 'F'),
            'overall_status': self.health_data.get('overall', {}).get('status', 'unknown'),
            'recommendations_count': len(self.recommendations),
            'recommendations': ' | '.join(self.recommendations)
        }

        # Add category scores
        for category in ['issues', 'commits', 'contributors', 'releases', 'pulls']:
            if category in self.health_data:
                data = self.health_data[category]
                report[f'{category}_score'] = data.get('score', 0)
                report[f'{category}_status'] = data.get('status', 'unknown')

        return [report]  # Return as list for consistency with other analyzers

    def save_health_report(self, data, output_file, format_type='csv'):
        """Save health report with custom formatting"""
        if format_type == 'markdown':
            self._save_health_markdown(data[0], output_file)
        else:
            # Use standard exporters for other formats
            if format_type == 'csv':
                from ..utils.exporters import save_to_csv
                save_to_csv(data, output_file)
            elif format_type == 'json':
                from ..utils.exporters import save_to_json
                save_to_json(data, output_file)
            elif format_type == 'excel':
                from ..utils.exporters import save_to_excel
                save_to_excel(data, output_file, "Repository Health Dashboard")

    def _save_health_markdown(self, report, output_file):
        """Save detailed health report in Markdown format"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# Repository Health Dashboard\n\n")
            f.write(f"**Repository:** [{report['repository']}](https://github.com/{report['repository']})  \n")
            f.write(f"**Analysis Date:** {report['analysis_date']}  \n")
            f.write(f"**Overall Score:** {report['overall_score']}/100 (Grade: {report['overall_grade']})  \n")
            f.write(f"**Status:** {report['overall_status'].title()}  \n\n")

            f.write("## 📊 Health Metrics\n\n")
            f.write("| Category | Score | Status | Key Metrics |\n")
            f.write("|----------|-------|--------|--------------|\n")

            categories = {
                'issues': 'Issues Management',
                'commits': 'Development Activity',
                'contributors': 'Community Health',
                'releases': 'Release Management',
                'pulls': 'Code Review Process'
            }

            for key, name in categories.items():
                if key in self.health_data:
                    data = self.health_data[key]
                    score = data.get('score', 0)
                    status = data.get('status', 'unknown').title()

                    # Key metrics summary
                    if key == 'issues':
                        metrics = f"Open: {data.get('open_ratio', 0)}%, Avg Age: {data.get('avg_age_days', 0)} days"
                    elif key == 'commits':
                        metrics = f"Authors: {data.get('unique_authors', 0)}, Features: {data.get('feature_ratio', 0)}%"
                    elif key == 'contributors':
                        metrics = f"Total: {data.get('total_contributors', 0)}, Bus Factor: {data.get('bus_factor', 'unknown')}"
                    elif key == 'releases':
                        metrics = f"Total: {data.get('total_releases', 0)}, Frequency: {data.get('release_frequency', 'unknown')}"
                    elif key == 'pulls':
                        metrics = f"Merge Rate: {data.get('merge_ratio', 0)}%, Review Activity: {data.get('avg_review_activity', 0)}"
                    else:
                        metrics = "N/A"

                    f.write(f"| {name} | {score}/100 | {status} | {metrics} |\n")

            f.write(f"\n## 💡 Recommendations ({len(self.recommendations)})\n\n")
            if self.recommendations:
                for rec in self.recommendations:
                    f.write(f"- {rec}\n")
            else:
                f.write("- 🟢 No specific recommendations - repository health is good!\n")

            f.write(f"\n---\n*Generated by GitHub Analyzer - Health Dashboard*")

        print(f"✓ Saved health dashboard to {output_file}")
