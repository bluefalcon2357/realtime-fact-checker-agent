"""Wrapper around Gemini's built-in google_search grounding tool.

ADK exposes this differently depending on version. Importing lazily so the
project doesn't hard-crash on import when ADK isn't installed (e.g., CI).
"""
from __future__ import annotations


def google_search_tool():
    """Return a configured grounding Tool for use in LlmAgent definitions."""
    from google.genai import types

    return types.Tool(google_search=types.GoogleSearch())
