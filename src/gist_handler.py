"""
GitHub Gist handler module for fetching markdown files from Gists.

This module provides utilities to:
- Identify GitHub Gist URLs
- Extract Gist IDs from URLs
- Fetch markdown files from Gists via the GitHub API
"""

import re
import tempfile
from pathlib import Path
from typing import List, Optional

import requests


def is_gist_url(url: str) -> bool:
    """
    Check if a string is a valid GitHub Gist URL.

    Args:
        url: String to check (URL or path)

    Returns:
        True if the string matches a GitHub Gist URL pattern, False otherwise

    Examples:
        >>> is_gist_url("https://gist.github.com/username/abc123def456")
        True
        >>> is_gist_url("https://gist.github.com/abc123def456")
        True
        >>> is_gist_url("gist.github.com/username/abc123")
        True
        >>> is_gist_url("https://github.com/user/repo")
        False
    """
    if not isinstance(url, str):
        return False

    # Pattern matches:
    # - https://gist.github.com/username/gist_id
    # - https://gist.github.com/username/gist_id.git
    # - https://gist.github.com/gist_id (anonymous)
    # - gist.github.com/username/gist_id (without protocol)
    pattern = r'(https?://)?gist\.github\.com/([a-zA-Z0-9_-]+/)?[a-f0-9]+(\.git)?/?$'
    return bool(re.search(pattern, url.strip()))


def extract_gist_id(gist_url: str) -> Optional[str]:
    """
    Extract the Gist ID from a GitHub Gist URL.

    Args:
        gist_url: A GitHub Gist URL

    Returns:
        The Gist ID (hex string) or None if extraction fails

    Examples:
        >>> extract_gist_id("https://gist.github.com/user/abc123def456")
        'abc123def456'
        >>> extract_gist_id("https://gist.github.com/abc123def456")
        'abc123def456'
        >>> extract_gist_id("https://gist.github.com/user/abc123.git")
        'abc123'
    """
    if not isinstance(gist_url, str):
        return None

    # Clean the URL
    url = gist_url.strip().rstrip('/')

    # Remove .git suffix if present
    if url.endswith('.git'):
        url = url[:-4]

    # Pattern to extract gist ID (last segment that's a hex string)
    # Matches both user gists and anonymous gists
    pattern = r'gist\.github\.com/(?:[a-zA-Z0-9_-]+/)?([a-f0-9]+)'
    match = re.search(pattern, url)

    if match:
        return match.group(1)

    return None


def fetch_gist_files(gist_url: str, github_token: Optional[str] = None) -> List[Path]:
    """
    Fetch markdown files from a GitHub Gist.

    Args:
        gist_url: GitHub Gist URL
        github_token: Optional GitHub personal access token for private gists
                     or to increase rate limits

    Returns:
        List of Path objects pointing to saved markdown files in a temporary directory

    Raises:
        ValueError: If the gist URL is invalid or gist ID cannot be extracted
        ConnectionError: If network request fails or GitHub API is unreachable
        PermissionError: If the gist is private and no valid token is provided

    Examples:
        >>> files = fetch_gist_files("https://gist.github.com/user/abc123")
        >>> isinstance(files, list)
        True
        >>> all(isinstance(f, Path) for f in files)
        True
    """
    # Validate URL and extract ID
    if not is_gist_url(gist_url):
        raise ValueError(f"Invalid GitHub Gist URL: {gist_url}")

    gist_id = extract_gist_id(gist_url)
    if not gist_id:
        raise ValueError(f"Could not extract Gist ID from URL: {gist_url}")

    # Prepare API request
    api_url = f"https://api.github.com/gists/{gist_id}"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    # Fetch gist data from GitHub API
    try:
        response = requests.get(api_url, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise ConnectionError(f"Request timed out while fetching gist: {gist_id}")
    except requests.exceptions.ConnectionError as e:
        raise ConnectionError(f"Network error while fetching gist: {e}")
    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            raise ValueError(f"Gist not found: {gist_id}")
        elif response.status_code == 403:
            # Check if it's a rate limit or permission issue
            if 'rate limit' in response.text.lower():
                raise ConnectionError(f"GitHub API rate limit exceeded. Consider using a GitHub token.")
            else:
                raise PermissionError(f"Access denied to gist {gist_id}. It may be private - provide a GitHub token.")
        elif response.status_code == 401:
            raise PermissionError(f"Invalid GitHub token or authentication failed")
        else:
            raise ConnectionError(f"HTTP error {response.status_code}: {e}")

    # Parse response
    try:
        gist_data = response.json()
    except ValueError as e:
        raise ConnectionError(f"Invalid JSON response from GitHub API: {e}")

    # Extract markdown files
    files = gist_data.get("files", {})
    markdown_files = {
        filename: file_data
        for filename, file_data in files.items()
        if filename.lower().endswith(('.md', '.markdown'))
    }

    if not markdown_files:
        # Not an error, just no markdown files found
        return []

    # Create temporary directory for storing files
    temp_dir = Path(tempfile.mkdtemp(prefix="mermaid_gist_"))
    saved_files = []

    # Save markdown files to temp directory (alphabetically sorted)
    for filename in sorted(markdown_files.keys()):
        file_data = markdown_files[filename]
        content = file_data.get("content", "")

        # Save to temp directory
        file_path = temp_dir / filename
        try:
            file_path.write_text(content, encoding='utf-8')
            saved_files.append(file_path)
        except IOError as e:
            # Clean up already saved files
            for saved_file in saved_files:
                saved_file.unlink(missing_ok=True)
            temp_dir.rmdir()
            raise ConnectionError(f"Failed to save file {filename}: {e}")

    return saved_files
