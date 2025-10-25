# Legacy GitHub Analysis Tools

This folder contains older versions of the GitHub analysis tools for reference.

## Files

### `scrape_github_issues.py`
- **Type**: Web scraper (HTML parsing)
- **Method**: BeautifulSoup + requests
- **Speed**: Slow (2-second delays, ~25 issues per page)
- **Reliability**: Fragile (breaks when GitHub changes HTML)
- **Data**: Limited fields from web interface

## Migration to Modular Architecture

The current `github_analyzer.py` uses a modular architecture with:

- **Analyzers**: Separate classes for different analysis types
- **Utils**: Shared utilities (API client, exporters, config)
- **Extensibility**: Easy to add new analysis types

## Usage (Legacy - Not Recommended)

```bash
# Web scraper (slow, fragile)
python3 legacy/scrape_github_issues.py --max-pages 5
```

## Recommended Usage

Use the current modular version instead:

```bash
# Current modular architecture
python3 github_analyzer.py issues --repo grafana/loki --max-pages 10
```
