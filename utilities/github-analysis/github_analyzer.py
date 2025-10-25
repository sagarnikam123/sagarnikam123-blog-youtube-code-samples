#!/usr/bin/env python3
"""
GitHub Analyzer - Modular Architecture
Comprehensive GitHub repository analysis tool using GitHub REST API.
Support issues analysis with plans for PRs, commits, contributors, and more.

Author: Sagar Nikam
Email: sagarnikam123@gmail.com
Site: https://sagarnikam123.github.io
"""

import argparse
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.config import DEFAULT_REPO, DEFAULT_MAX_PAGES, DEFAULT_DELAY_SECONDS
from analyzers.issues_analyzer import IssuesAnalyzer
from analyzers.commits_analyzer import CommitsAnalyzer
from analyzers.contributors_analyzer import ContributorsAnalyzer
from analyzers.releases_analyzer import ReleasesAnalyzer
from analyzers.pulls_analyzer import PullsAnalyzer
from analyzers.compare_analyzer import CompareAnalyzer
from analyzers.health_analyzer import HealthAnalyzer

def analyze_issues(args):
    """Analyze repository issues"""
    # Parse repository
    if '/' not in args.repo:
        print("❌ Repository must be in format 'owner/repo'")
        return

    owner, repo = args.repo.split('/', 1)

    # Generate default filename
    if not args.output:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        ext_map = {'csv': 'csv', 'markdown': 'md', 'json': 'json', 'excel': 'xlsx'}
        extension = ext_map.get(args.format, 'csv')
        args.output = f'github-{repo}-issues-{timestamp}.{extension}'

    print(f"🚀 Analyzing issues from {owner}/{repo}")
    print(f"📊 State: {args.state}")
    print(f"📄 Format: {args.format}")
    print(f"📝 Output: {args.output}")
    print(f"📚 Max pages: {args.max_pages if args.max_pages > 0 else 'All'}")
    print("-" * 60)

    # Create analyzer and run analysis
    analyzer = IssuesAnalyzer(owner, repo, delay_seconds=args.delay)
    data = analyzer.analyze(state=args.state, max_pages=args.max_pages)

    if not data:
        print("\n❌ No issues found or API error occurred")
        return

    # Save results
    analyzer.save(args.output, args.format)

    print(f"\n🎉 Successfully analyzed {len(data)} issues!")
    print(f"💡 Tip: Set GITHUB_TOKEN environment variable for higher rate limits")

def main():
    parser = argparse.ArgumentParser(
        description='GitHub Repository Analyzer - Modular Architecture',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Analyze issues from grafana/loki
  python3 github_analyzer.py issues

  # Analyze different repo
  python3 github_analyzer.py issues --repo kubernetes/kubernetes

  # Analyze only open issues, first 5 pages
  python3 github_analyzer.py issues --state open --max-pages 5

  # Save to markdown format
  python3 github_analyzer.py issues --format markdown

  # Use GitHub token for higher rate limits
  export GITHUB_TOKEN=your_token_here
  python3 github_analyzer.py issues --max-pages 0

Future Commands (planned):
  python3 github_analyzer.py pulls      # Analyze pull requests
  python3 github_analyzer.py commits    # Analyze commit history
  python3 github_analyzer.py contributors # Analyze contributors
  python3 github_analyzer.py releases   # Analyze releases
        '''
    )

    # Add subcommands
    subparsers = parser.add_subparsers(dest='command', help='Analysis type')

    # Issues command
    issues_parser = subparsers.add_parser('issues', help='Analyze repository issues')

    issues_parser.add_argument(
        '--repo',
        default=DEFAULT_REPO,
        help=f'Repository in format owner/repo (default: {DEFAULT_REPO})'
    )

    issues_parser.add_argument(
        '--state',
        choices=['open', 'closed', 'all'],
        default='all',
        help='Issue state filter (default: all)'
    )

    issues_parser.add_argument(
        '--output',
        default=None,
        help='Output filename (default: auto-generated with timestamp)'
    )

    issues_parser.add_argument(
        '--format',
        choices=['csv', 'markdown', 'json', 'excel'],
        default='csv',
        help='Output format (default: csv)'
    )

    issues_parser.add_argument(
        '--max-pages',
        type=int,
        default=DEFAULT_MAX_PAGES,
        help=f'Maximum pages to fetch (default: {DEFAULT_MAX_PAGES}, use 0 for all)'
    )

    issues_parser.add_argument(
        '--delay',
        type=float,
        default=DEFAULT_DELAY_SECONDS,
        help=f'Delay between API calls in seconds (default: {DEFAULT_DELAY_SECONDS})'
    )

    # Commits command
    commits_parser = subparsers.add_parser('commits', help='Analyze repository commits')

    commits_parser.add_argument(
        '--repo',
        default=DEFAULT_REPO,
        help=f'Repository in format owner/repo (default: {DEFAULT_REPO})'
    )

    commits_parser.add_argument(
        '--max-pages',
        type=int,
        default=3,
        help='Maximum pages to fetch (default: 3, use 0 for all)'
    )

    commits_parser.add_argument(
        '--format',
        choices=['csv', 'markdown', 'json', 'excel'],
        default='csv',
        help='Output format (default: csv)'
    )

    commits_parser.add_argument(
        '--branch',
        default=None,
        help='Branch name to analyze (default: repository default branch)'
    )

    # Contributors command
    contributors_parser = subparsers.add_parser('contributors', help='Analyze repository contributors')

    contributors_parser.add_argument(
        '--repo',
        default=DEFAULT_REPO,
        help=f'Repository in format owner/repo (default: {DEFAULT_REPO})'
    )

    contributors_parser.add_argument(
        '--format',
        choices=['csv', 'markdown', 'json', 'excel'],
        default='csv',
        help='Output format (default: csv)'
    )

    # Releases command
    releases_parser = subparsers.add_parser('releases', help='Analyze repository releases')

    releases_parser.add_argument(
        '--repo',
        default=DEFAULT_REPO,
        help=f'Repository in format owner/repo (default: {DEFAULT_REPO})'
    )

    releases_parser.add_argument(
        '--format',
        choices=['csv', 'markdown', 'json', 'excel'],
        default='csv',
        help='Output format (default: csv)'
    )

    # Pulls command
    pulls_parser = subparsers.add_parser('pulls', help='Analyze repository pull requests')

    pulls_parser.add_argument(
        '--repo',
        default=DEFAULT_REPO,
        help=f'Repository in format owner/repo (default: {DEFAULT_REPO})'
    )

    pulls_parser.add_argument(
        '--state',
        choices=['open', 'closed', 'all'],
        default='all',
        help='PR state filter (default: all)'
    )

    pulls_parser.add_argument(
        '--max-pages',
        type=int,
        default=3,
        help='Maximum pages to fetch (default: 3, use 0 for all)'
    )

    pulls_parser.add_argument(
        '--format',
        choices=['csv', 'markdown', 'json', 'excel'],
        default='csv',
        help='Output format (default: csv)'
    )

    # Compare command
    compare_parser = subparsers.add_parser('compare', help='Compare multiple repositories')

    compare_parser.add_argument(
        '--repos',
        required=True,
        help='Comma-separated list of repositories (e.g., grafana/loki,prometheus/prometheus)'
    )

    compare_parser.add_argument(
        '--metric',
        choices=['issues', 'commits', 'contributors', 'releases', 'pulls'],
        default='issues',
        help='Metric to compare (default: issues)'
    )

    compare_parser.add_argument(
        '--max-pages',
        type=int,
        default=2,
        help='Maximum pages to fetch per repo (default: 2)'
    )

    compare_parser.add_argument(
        '--format',
        choices=['csv', 'markdown', 'json', 'excel'],
        default='csv',
        help='Output format (default: csv)'
    )

    # Health command
    health_parser = subparsers.add_parser('health', help='Analyze repository health dashboard')

    health_parser.add_argument(
        '--repo',
        default=DEFAULT_REPO,
        help=f'Repository in format owner/repo (default: {DEFAULT_REPO})'
    )

    health_parser.add_argument(
        '--format',
        choices=['csv', 'markdown', 'json', 'excel'],
        default='markdown',
        help='Output format (default: markdown)'
    )

    args = parser.parse_args()

    # Check if command is provided
    if not args.command:
        parser.print_help()
        print("\n❌ Please specify a command (currently available: issues, commits, contributors, releases, pulls, compare, health)")
        return

    # Handle commands
    if args.command == 'issues':
        analyze_issues(args)
    elif args.command == 'commits':
        # Parse repository
        if '/' not in args.repo:
            print("❌ Repository must be in format 'owner/repo'")
            return

        owner, repo = args.repo.split('/', 1)

        # Generate default filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        ext_map = {'csv': 'csv', 'markdown': 'md', 'json': 'json', 'excel': 'xlsx'}
        extension = ext_map.get(args.format, 'csv')
        output_file = f'github-{repo}-commits-{timestamp}.{extension}'

        print(f"🚀 Analyzing commits from {owner}/{repo}")
        print(f"📊 Max pages: {args.max_pages if args.max_pages > 0 else 'All'}")
        print("-" * 60)

        # Create analyzer and run analysis
        analyzer = CommitsAnalyzer(owner, repo)
        data = analyzer.analyze(max_pages=args.max_pages, branch=args.branch)

        if not data:
            print("\n❌ No commits found or API error occurred")
            return

        # Save results
        analyzer.save(output_file, args.format)

        print(f"\n🎉 Successfully analyzed {len(data)} commits!")
        print(f"💡 Tip: Set GITHUB_TOKEN environment variable for higher rate limits")

    elif args.command == 'contributors':
        # Parse repository
        if '/' not in args.repo:
            print("❌ Repository must be in format 'owner/repo'")
            return

        owner, repo = args.repo.split('/', 1)

        # Generate default filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        ext_map = {'csv': 'csv', 'markdown': 'md', 'json': 'json', 'excel': 'xlsx'}
        extension = ext_map.get(args.format, 'csv')
        output_file = f'github-{repo}-contributors-{timestamp}.{extension}'

        print(f"🚀 Analyzing contributors from {owner}/{repo}")
        print("-" * 60)

        # Create analyzer and run analysis
        analyzer = ContributorsAnalyzer(owner, repo)
        data = analyzer.analyze()

        if not data:
            print("\n❌ No contributors found or API error occurred")
            return

        # Save results
        analyzer.save(output_file, args.format)

        print(f"\n🎉 Successfully analyzed {len(data)} contributors!")
        print(f"💡 Tip: Set GITHUB_TOKEN environment variable for higher rate limits")

    elif args.command == 'releases':
        # Parse repository
        if '/' not in args.repo:
            print("❌ Repository must be in format 'owner/repo'")
            return

        owner, repo = args.repo.split('/', 1)

        # Generate default filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        ext_map = {'csv': 'csv', 'markdown': 'md', 'json': 'json', 'excel': 'xlsx'}
        extension = ext_map.get(args.format, 'csv')
        output_file = f'github-{repo}-releases-{timestamp}.{extension}'

        print(f"🚀 Analyzing releases from {owner}/{repo}")
        print("-" * 60)

        # Create analyzer and run analysis
        analyzer = ReleasesAnalyzer(owner, repo)
        data = analyzer.analyze()

        if not data:
            print("\n❌ No releases found or API error occurred")
            return

        # Save results
        analyzer.save(output_file, args.format)

        print(f"\n🎉 Successfully analyzed {len(data)} releases!")
        print(f"💡 Tip: Set GITHUB_TOKEN environment variable for higher rate limits")

    elif args.command == 'pulls':
        # Parse repository
        if '/' not in args.repo:
            print("❌ Repository must be in format 'owner/repo'")
            return

        owner, repo = args.repo.split('/', 1)

        # Generate default filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        ext_map = {'csv': 'csv', 'markdown': 'md', 'json': 'json', 'excel': 'xlsx'}
        extension = ext_map.get(args.format, 'csv')
        output_file = f'github-{repo}-pulls-{timestamp}.{extension}'

        print(f"🚀 Analyzing pull requests from {owner}/{repo}")
        print(f"📊 State: {args.state}")
        print(f"📊 Max pages: {args.max_pages if args.max_pages > 0 else 'All'}")
        print("-" * 60)

        # Create analyzer and run analysis
        analyzer = PullsAnalyzer(owner, repo)
        data = analyzer.analyze(state=args.state, max_pages=args.max_pages)

        if not data:
            print("\n❌ No pull requests found or API error occurred")
            return

        # Save results
        analyzer.save(output_file, args.format)

        print(f"\n🎉 Successfully analyzed {len(data)} pull requests!")
        print(f"💡 Tip: Set GITHUB_TOKEN environment variable for higher rate limits")

    elif args.command == 'compare':
        # Parse repositories
        repos = [repo.strip() for repo in args.repos.split(',')]

        # Validate repositories
        invalid_repos = [repo for repo in repos if '/' not in repo]
        if invalid_repos:
            print(f"❌ Invalid repository format: {', '.join(invalid_repos)}")
            print("Use format: owner/repo (e.g., grafana/loki,prometheus/prometheus)")
            return

        # Generate default filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        ext_map = {'csv': 'csv', 'markdown': 'md', 'json': 'json', 'excel': 'xlsx'}
        extension = ext_map.get(args.format, 'csv')
        output_file = f'github-comparison-{args.metric}-{timestamp}.{extension}'

        print(f"🚀 Comparing {len(repos)} repositories on '{args.metric}' metric")
        print(f"📊 Repositories: {', '.join(repos)}")
        print("-" * 60)

        # Create analyzer and run comparison
        analyzer = CompareAnalyzer()

        # Set up kwargs based on metric
        kwargs = {'max_pages': args.max_pages}
        if args.metric in ['issues', 'pulls']:
            kwargs['state'] = 'all'

        data = analyzer.compare_repositories(repos, args.metric, **kwargs)

        if not data:
            print("\n❌ No comparison data generated")
            return

        # Save results
        analyzer.save_comparison(data, output_file, args.format)

        print(f"\n🎉 Successfully compared {len(repos)} repositories!")
        print(f"📊 Comparison saved to: {output_file}")
        print(f"💡 Tip: Use --metric to compare different aspects (issues, commits, contributors, releases, pulls)")

    elif args.command == 'health':
        # Parse repository
        if '/' not in args.repo:
            print("❌ Repository must be in format 'owner/repo'")
            return

        owner, repo = args.repo.split('/', 1)

        # Generate default filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        ext_map = {'csv': 'csv', 'markdown': 'md', 'json': 'json', 'excel': 'xlsx'}
        extension = ext_map.get(args.format, 'md')
        output_file = f'github-{repo}-health-{timestamp}.{extension}'

        print(f"🏥 Analyzing repository health for {owner}/{repo}")
        print("-" * 60)

        # Create analyzer and run health analysis
        analyzer = HealthAnalyzer(owner, repo)
        data = analyzer.analyze_health()

        if not data:
            print("\n❌ No health data generated")
            return

        # Save results
        analyzer.save_health_report(data, output_file, args.format)

        # Display summary
        report = data[0]
        print(f"\n🏆 Health Analysis Complete!")
        print(f"📊 Overall Score: {report['overall_score']}/100 (Grade: {report['overall_grade']})")
        print(f"📊 Status: {report['overall_status'].title()}")
        print(f"📊 Recommendations: {report['recommendations_count']}")
        print(f"📊 Dashboard saved to: {output_file}")
        print(f"💡 Tip: Use --format markdown for detailed dashboard report")
    else:
        print(f"❌ Command '{args.command}' not implemented yet")
        print("Available commands: issues, commits, contributors, releases, pulls, compare, health")

if __name__ == '__main__':
    main()
