#!/usr/bin/env python3
"""
GitHub Issues Scraper
Scrapes all open/closed issues from any GitHub repository issues page
and saves them to a CSV file with title and link.

Author: Sagar Nikam
Email: sagarnikam123@gmail.com
Site: https://sagarnikam123.github.io
"""

import requests
from bs4 import BeautifulSoup
import csv
import argparse
import time
from datetime import datetime
from urllib.parse import urljoin

# Configuration
DEFAULT_GITHUB_ISSUES_URL = 'https://github.com/grafana/loki/issues'
DEFAULT_DELAY_SECONDS = 2
DEFAULT_MAX_PAGES = 10

def scrape_issues_page(url, max_pages=None, delay_seconds=DEFAULT_DELAY_SECONDS):
    """
    Scrape issues from GitHub issues page

    Args:
        url: Base URL of the issues page
        max_pages: Maximum number of pages to scrape (None for all)

    Returns:
        List of tuples containing (status, issue_number, title, author, created_date, age_days, labels, has_labels, comments_count, issue_type, priority, title_length, repo_name, org_name, link)
    """
    issues_data = []
    page = 1

    while True:
        if max_pages and max_pages > 0 and page > max_pages:
            break

        # Add page parameter to URL - always include page parameter
        separator = '&' if '?' in url else '?'
        page_url = f"{url}{separator}page={page}"

        print(f"Scraping page {page}: {page_url}")

        try:
            # Send request with headers to avoid being blocked
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
            }

            response = requests.get(page_url, headers=headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all issue items - use the working approach
            issue_links = soup.select('a[href*="/issues/"]')
            if issue_links:
                # Convert links to their parent containers
                issues = [link.find_parent('div') for link in issue_links]
                issues = [issue for issue in issues if issue]  # Remove None values
            else:
                issues = []

            if not issues:
                print(f"No more issues found on page {page}")
                break

            page_count = 0
            for issue in issues:
                # Find the issue title and link - try multiple selectors
                title_elem = issue.select_one('a[data-hovercard-type="issue"]')

                if not title_elem:
                    title_elem = issue.find('a', class_='Link--primary')

                if not title_elem:
                    title_elem = issue.select_one('.js-navigation-open')

                if not title_elem:
                    # Look for any link with /issues/ in href
                    title_elem = issue.select_one('a[href*="/issues/"]')

                if title_elem:
                    title = title_elem.text.strip()
                    link = urljoin('https://github.com', title_elem.get('href', ''))

                    # Skip if not actually an issue link
                    if '/issues/' not in link:
                        continue

                    # Extract issue number from link
                    issue_number = link.split('/')[-1] if '/' in link else 'N/A'

                    # Extract status (open/closed) - try multiple methods
                    status = 'open'  # default

                    # Method 1: Look for state span
                    status_elem = issue.find('span', class_='State')
                    if status_elem:
                        status_text = status_elem.get('title', '').lower()
                        if 'closed' in status_text:
                            status = 'closed'

                    # Method 2: Look for octicon classes
                    if status == 'open':
                        closed_icon = issue.select_one('.octicon-issue-closed, .octicon-skip')
                        if closed_icon:
                            status = 'closed'

                    # Method 3: Check for closed class or text
                    if status == 'open':
                        if 'closed' in issue.get('class', []) or 'closed' in str(issue).lower():
                            status = 'closed'

                    # Extract labels
                    labels = []
                    label_elems = issue.select('.IssueLabel, .Label')
                    for label_elem in label_elems:
                        label_text = label_elem.text.strip()
                        if label_text:
                            labels.append(label_text)
                    labels_str = ', '.join(labels) if labels else 'None'

                    # Extract author
                    author = 'N/A'
                    author_elem = issue.select_one('a[data-hovercard-type="user"]')
                    if author_elem:
                        author = author_elem.text.strip()

                    # Extract created date (relative time)
                    created_date = 'N/A'
                    time_elem = issue.select_one('relative-time, time')
                    if time_elem:
                        created_date = time_elem.get('datetime', time_elem.text.strip())

                    # Extract comments count
                    comments_count = 0
                    comments_elem = issue.select_one('.octicon-comment')
                    if comments_elem and comments_elem.parent:
                        comments_text = comments_elem.parent.text.strip()
                        try:
                            comments_count = int(''.join(filter(str.isdigit, comments_text)))
                        except:
                            comments_count = 0

                    # Compute additional fields for analysis
                    repo_name = url.split('/')[-2] if '/' in url else 'unknown'
                    org_name = url.split('/')[-3] if '/' in url else 'unknown'

                    # Issue type classification
                    issue_type = 'issue'  # default
                    if any(word in title.lower() for word in ['bug', 'error', 'crash', 'fail']):
                        issue_type = 'bug'
                    elif any(word in title.lower() for word in ['feature', 'enhancement', 'add', 'support']):
                        issue_type = 'enhancement'
                    elif any(word in title.lower() for word in ['doc', 'documentation', 'readme']):
                        issue_type = 'documentation'
                    elif any(word in title.lower() for word in ['question', 'help', 'how']):
                        issue_type = 'question'

                    # Priority classification based on labels
                    priority = 'normal'
                    if any(word in labels_str.lower() for word in ['critical', 'urgent', 'high']):
                        priority = 'high'
                    elif any(word in labels_str.lower() for word in ['low', 'minor']):
                        priority = 'low'

                    # Age calculation (days since creation)
                    age_days = 'N/A'
                    if created_date != 'N/A':
                        try:
                            from dateutil.parser import parse
                            created_dt = parse(created_date)
                            age_days = (datetime.now(created_dt.tzinfo) - created_dt).days
                        except:
                            age_days = 'N/A'

                    # Title length for analysis
                    title_length = len(title)

                    # Has labels flag
                    has_labels = 'Yes' if labels_str != 'None' else 'No'

                    issues_data.append((status, issue_number, title, author, created_date, age_days,
                                      labels_str, has_labels, comments_count, issue_type, priority,
                                      title_length, repo_name, org_name, link))
                    page_count += 1

            print(f"  Found {page_count} issues on page {page}")

            if page_count == 0:
                break

            # Check if there's a next page - try multiple methods
            has_next = False

            # Method 1: Look for Next button
            next_button = soup.find('a', string='Next')
            if next_button and 'disabled' not in next_button.get('class', []):
                has_next = True
                print(f"  Found Next button, continuing to page {page + 1}")

            # Method 2: Look for pagination with rel="next"
            if not has_next:
                next_link = soup.find('a', {'rel': 'next'})
                if next_link:
                    has_next = True
                    print(f"  Found rel=next link, continuing to page {page + 1}")

            # Method 3: Look for any pagination links
            if not has_next:
                pagination_links = soup.select('.pagination a, .paginate-container a')
                for link in pagination_links:
                    if 'next' in link.get('aria-label', '').lower() or 'next' in link.text.lower():
                        has_next = True
                        print(f"  Found pagination next link, continuing to page {page + 1}")
                        break

            # Method 4: Continue if we got issues (assume more pages exist)
            if not has_next and page_count > 0:
                has_next = True
                print(f"  Got {page_count} issues, assuming more pages exist")

            if not has_next:
                print("No more pages available")
                break

            page += 1

            # Be respectful to GitHub servers
            time.sleep(delay_seconds)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching page {page}: {e}")
            break

    return issues_data

def save_to_csv(issues_data, output_file):
    """
    Save issues data to CSV file

    Args:
        issues_data: List of tuples (status, issue_number, title, author, created_date, labels, link)
        output_file: Output CSV filename
    """
    with open(output_file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['index', 'status', 'issue_number', 'title', 'author', 'created_date', 'age_days',
                        'labels', 'has_labels', 'comments_count', 'issue_type', 'priority',
                        'title_length', 'repo_name', 'org_name', 'link'])
        for i, (status, issue_number, title, author, created_date, age_days, labels, has_labels,
                comments_count, issue_type, priority, title_length, repo_name, org_name, link) in enumerate(issues_data, 1):
            writer.writerow([i, status, issue_number, title, author, created_date, age_days,
                           labels, has_labels, comments_count, issue_type, priority,
                           title_length, repo_name, org_name, link])

    print(f"\nSaved {len(issues_data)} issues to {output_file}")

def save_to_markdown(issues_data, output_file, source_url):
    """
    Save issues data to Markdown file

    Args:
        issues_data: List of tuples (status, issue_number, title, author, created_date, labels, link)
        output_file: Output Markdown filename
        source_url: Source URL that was scraped
    """
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write("# GitHub Issues\n\n")

        # Add metadata section
        file.write(f"- **Source URL**: {source_url}\n")
        file.write(f"- **Total Issues**: {len(issues_data)}\n")
        file.write(f"- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        file.write(f"- **Tool**: GitHub Issues Scraper\n\n")

        file.write("---\n\n")

        # Create table header
        file.write("| Index | Status | Issue # | Title | Author | Age (Days) | Type | Priority | Comments |\n")
        file.write("|-------|--------|---------|-------|--------|------------|------|----------|----------|\n")

        # Add table rows
        for i, (status, issue_number, title, author, created_date, age_days, labels, has_labels,
                comments_count, issue_type, priority, title_length, repo_name, org_name, link) in enumerate(issues_data, 1):
            file.write(f"| {i} | {status} | #{issue_number} | [{title}]({link}) | {author} | {age_days} | {issue_type} | {priority} | {comments_count} |\n")

    print(f"Saved {len(issues_data)} issues to {output_file}")

def main():
    parser = argparse.ArgumentParser(
        description='Scrape Grafana Loki GitHub issues',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Scrape all open issues to CSV
  python scrape_loki_issues.py

  # Scrape first 5 pages only
  python scrape_loki_issues.py --max-pages 5

  # Save to Markdown format
  python scrape_loki_issues.py --format markdown

  # Custom output filename
  python scrape_loki_issues.py --output my_issues.csv
        '''
    )

    parser.add_argument(
        '--url',
        default='https://github.com/grafana/loki/issues',
        help='GitHub issues URL (default: https://github.com/grafana/loki/issues)'
    )

    parser.add_argument(
        '--output',
        default=None,
        help='Output filename (default: auto-generated with timestamp)'
    )

    parser.add_argument(
        '--format',
        choices=['csv', 'markdown'],
        default='csv',
        help='Output format: csv or markdown (default: csv)'
    )

    parser.add_argument(
        '--max-pages',
        type=int,
        default=DEFAULT_MAX_PAGES,
        help=f'Maximum number of pages to scrape (default: {DEFAULT_MAX_PAGES}, use 0 for all pages, ~74 pages for Loki)'
    )

    parser.add_argument(
        '--delay',
        type=float,
        default=DEFAULT_DELAY_SECONDS,
        help=f'Delay between requests in seconds (default: {DEFAULT_DELAY_SECONDS})'
    )

    parser.add_argument(
        '--state',
        choices=['open', 'closed', 'all'],
        default='all',
        help='Issue state filter (default: all)'
    )

    args = parser.parse_args()

    # Normalize URL to ensure it ends with /issues
    if not args.url.endswith('/issues'):
        if args.url.endswith('/'):
            args.url = args.url + 'issues'
        else:
            args.url = args.url + '/issues'

    # Generate default filename if not provided
    if not args.output:
        # Extract tool name from URL
        url_parts = args.url.split('/')
        if len(url_parts) >= 5:
            toolname = url_parts[4]  # e.g., 'loki' from 'github.com/grafana/loki'
        else:
            toolname = 'issues'

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        args.output = f'github-{toolname}-{timestamp}.csv'

    # Modify URL based on state filter
    if args.state == 'open':
        separator = '&' if '?' in args.url else '?'
        args.url = f"{args.url}{separator}q=is%3Aissue+is%3Aopen"
    elif args.state == 'closed':
        separator = '&' if '?' in args.url else '?'
        args.url = f"{args.url}{separator}q=is%3Aissue+is%3Aclosed"

    print(f"Scraping issues from: {args.url}")
    print(f"Output format: {args.format}")
    print(f"Max pages: {args.max_pages if args.max_pages else 'All'}")
    print(f"State filter: {args.state}")
    print("-" * 60)

    # Scrape issues
    issues_data = scrape_issues_page(args.url, args.max_pages, args.delay)

    if not issues_data:
        print("\nNo issues found. This might be due to:")
        print("1. GitHub's rate limiting")
        print("2. Changes in GitHub's HTML structure")
        print("3. Network connectivity issues")
        print("\nTry using GitHub's API instead or reduce the number of pages.")
        return

    # Save to file
    if args.format == 'csv':
        save_to_csv(issues_data, args.output)
    else:
        # Change extension to .md for markdown
        output_file = args.output.rsplit('.', 1)[0] + '.md'
        save_to_markdown(issues_data, output_file, args.url)

    print("\n✓ Scraping completed successfully!")

if __name__ == '__main__':
    main()
