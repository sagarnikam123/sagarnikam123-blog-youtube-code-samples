#!/usr/bin/env python3
"""
Configuration management for GitHub Analyzer
"""

import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_REPO = 'grafana/loki'
DEFAULT_DELAY_SECONDS = 0.5
DEFAULT_MAX_PAGES = 10
GITHUB_API_BASE = 'https://api.github.com'

def get_github_token() -> Optional[str]:
    """Get GitHub token from environment variable or .env.github file with error handling"""
    # First try environment variable
    token = os.getenv('GITHUB_TOKEN')
    if token and token.strip():
        logger.info("GitHub token loaded from environment variable")
        return token.strip()

    # Try loading from .env.github file
    try:
        script_dir = Path(__file__).parent.parent
        env_file = script_dir / 'conf' / '.env.github'

        if not env_file.exists():
            logger.warning(f"Environment file not found: {env_file}")
            return None

        with open(env_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                if line.startswith('GITHUB_TOKEN='):
                    token = line.split('=', 1)[1].strip()
                    if token:
                        logger.info(f"GitHub token loaded from {env_file}")
                        return token
                    else:
                        logger.warning(f"Empty token found in {env_file} at line {line_num}")

        logger.warning(f"No valid GITHUB_TOKEN found in {env_file}")
        return None

    except PermissionError as e:
        logger.error(f"Permission denied reading config file: {e}")
        print(f"⚠️  Permission denied reading config file")
        return None
    except Exception as e:
        logger.error(f"Error reading config file: {e}")
        print(f"⚠️  Error reading config file: {e}")
        return None
