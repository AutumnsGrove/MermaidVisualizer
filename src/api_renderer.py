"""
Mermaid.ink API-based diagram renderer.

This module provides the default rendering backend using the mermaid.ink
public API. This approach requires zero external dependencies beyond Python
packages - no Node.js, Chrome, or Puppeteer needed.

Uses Rich for beautiful console output and progress feedback.

API: https://mermaid.ink
"""

import base64
import json
import logging
import zlib
from pathlib import Path
from typing import Optional

from rich.console import Console

logger = logging.getLogger(__name__)

# Console for rich output
console = Console()

# mermaid.ink API endpoint
MERMAID_INK_BASE = "https://mermaid.ink"


def _encode_diagram(mermaid_content: str, theme: str = "default") -> str:
    """
    Encode mermaid diagram content for the mermaid.ink API.

    Uses pako deflate compression + base64 encoding (same as mermaid.live).
    Wraps the diagram in the JSON format expected by the API.

    Args:
        mermaid_content: Raw mermaid diagram syntax
        theme: Mermaid theme (default, dark, forest, neutral)

    Returns:
        URL-safe encoded string for the API
    """
    # Wrap content in JSON object format expected by API
    json_obj = {
        "code": mermaid_content,
        "mermaid": {
            "theme": theme
        }
    }
    json_str = json.dumps(json_obj)

    # Compress with zlib (pako compatible)
    compressed = zlib.compress(json_str.encode("utf-8"), level=9)
    # Base64 encode and make URL-safe
    encoded = base64.urlsafe_b64encode(compressed).decode("ascii")
    return encoded


def generate_diagram_api(
    mermaid_content: str,
    output_path: Path,
    format: str = "png",
    theme: str = "default",
    background_color: Optional[str] = "white",
) -> bool:
    """
    Generate a diagram using the mermaid.ink API.

    This is a lightweight alternative to local mermaid-cli rendering that
    requires only the 'requests' package (no Node.js, Chrome, or Puppeteer).

    Args:
        mermaid_content: The Mermaid diagram syntax as a string
        output_path: Path where the output diagram should be saved
        format: Output format, either "png" or "svg" (default: "png")
        theme: Mermaid theme (default, dark, forest, neutral)
        background_color: Background color (default: "white")

    Returns:
        True if diagram generation was successful, False otherwise
    """
    try:
        import requests
    except ImportError:
        logger.error(
            "The 'requests' package is required but not found. "
            "Install with: pip install mermaid-visualizer"
        )
        return False

    if not mermaid_content or not mermaid_content.strip():
        logger.error("Cannot generate diagram: Mermaid content is empty")
        return False

    if format not in ["png", "svg"]:
        logger.error(f"Unsupported output format: {format}. Use 'png' or 'svg'")
        return False

    output_path = Path(output_path)
    output_dir = output_path.parent

    # Create output directory if needed
    if not output_dir.exists():
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created output directory: {output_dir}")
        except PermissionError:
            logger.error(f"Permission denied: Cannot create directory {output_dir}")
            return False
        except Exception as e:
            logger.error(f"Failed to create output directory: {e}")
            return False

    try:
        # Encode the diagram content
        encoded = _encode_diagram(mermaid_content, theme)

        # Build the API URL
        endpoint = "svg" if format == "svg" else "img"
        url = f"{MERMAID_INK_BASE}/{endpoint}/pako:{encoded}"

        # Add theme parameter if not default
        params = {}
        if theme and theme != "default":
            params["theme"] = theme
        if background_color and background_color != "white":
            params["bgColor"] = background_color

        logger.info("Fetching diagram from mermaid.ink API...")
        logger.debug(f"API URL length: {len(url)} characters")

        # Make the request
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        # Write the response to file
        with open(output_path, "wb") as f:
            f.write(response.content)

        # Verify file was created with content
        if not output_path.exists() or output_path.stat().st_size == 0:
            logger.error("API returned empty response")
            if output_path.exists():
                output_path.unlink()
            return False

        logger.info(f"Successfully generated diagram: {output_path}")
        return True

    except ImportError:
        logger.error(
            "requests package not installed. Install with: pip install requests"
        )
        return False

    except Exception as e:
        error_msg = str(e)
        if "HTTPError" in type(e).__name__ or "requests" in type(e).__module__:
            if "400" in error_msg:
                logger.error("Invalid Mermaid syntax - API returned 400 Bad Request")
            elif "413" in error_msg:
                logger.error("Diagram too large for API - consider using local rendering")
            elif "429" in error_msg:
                logger.error("Rate limited by API - try again later")
            else:
                logger.error(f"API request failed: {error_msg}")
        else:
            logger.error(f"Unexpected error during API rendering: {error_msg}")
        return False


def check_api_available() -> bool:
    """
    Check if the mermaid.ink API is available.

    Returns:
        True if API is reachable, False otherwise
    """
    try:
        import requests

        response = requests.get(
            f"{MERMAID_INK_BASE}/img/pako:eNpLSS1OLSrLz0kFABfgBC0", timeout=5
        )
        return response.status_code == 200
    except Exception:
        return False
