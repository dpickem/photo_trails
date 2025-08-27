"""LLM integration placeholders for geo-location, description and person identification."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

try:
    import openai
except Exception:  # pragma: no cover
    openai = None  # type: ignore


def _get_client():
    if openai is None:
        raise RuntimeError("openai package is not installed")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable not set")
    openai.api_key = api_key
    return openai


def geo_locate_photo(image_path: Path) -> tuple[float, float] | None:
    """Use an LLM to estimate the photo location."""
    # This is a placeholder implementation. A real implementation would send
    # the image to a multimodal model and parse the returned location.
    return None


def describe_photo(image_path: Path) -> str | None:
    """Return a textual description of the photo using an LLM."""
    return None


def identify_people(image_path: Path) -> List[str]:
    """Identify known people in the image using an LLM."""
    return []
