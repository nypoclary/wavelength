# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tools for retrieving music metadata, lyrics/themes, and verifying song existence."""

import json
import logging
import re
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


def clean_json_string(text: str) -> str:
    """Helper to extract the JSON object/array from a potentially conversational or markdown-fenced string."""
    text = text.strip()
    match = re.search(r"(\{.*?\}|\[.*?\])", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text


def retrieve_music_metadata(song_title: str, artist: str = "") -> dict:
    """Retrieve factual music metadata (tempo, genre, key, release year) for a song.

    Args:
        song_title: The title of the song.
        artist: Optional artist name.

    Returns:
        A dict containing 'tempo' (int), 'genre' (str), 'key' (str), and 'release_year' (int).
    """
    client = genai.Client()
    query = f"""Find the factual music metadata for the song "{song_title}" {f"by {artist}" if artist else ""}.
You must search and return:
- tempo (as an integer BPM)
- genre (as a string)
- key (musical key, e.g., "C Major", "A Minor")
- release_year (as an integer)

Provide your response in raw JSON format with the keys:
"tempo", "genre", "key", "release_year".

Do not add markdown formatting or backticks around the JSON, return ONLY the raw JSON string."""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=query,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
            ),
        )
        cleaned_text = clean_json_string(response.text)
        data = json.loads(cleaned_text)
        return {
            "tempo": int(data.get("tempo", 120)),
            "genre": str(data.get("genre", "Unknown")),
            "key": str(data.get("key", "Unknown")),
            "release_year": int(data.get("release_year", 2000)),
        }
    except Exception as e:
        logger.error(f"Error retrieving music metadata for '{song_title}': {e}")
        return {
            "tempo": 120,
            "genre": "Unknown",
            "key": "Unknown",
            "release_year": 2000,
        }


def retrieve_lyrics_theme(song_title: str, artist: str = "") -> dict:
    """Retrieve lyric interpretations and themes from search sources.

    Args:
        song_title: The title of the song.
        artist: Optional artist name.

    Returns:
        A dict containing 'lyrics_theme' (str).
    """
    client = genai.Client()
    query = f"""Search and find existing lyric interpretations, meaning, and key themes for the song "{song_title}" {f"by {artist}" if artist else ""}.
Do not generate your own interpretation; retrieve and pull the interpretations from web sources.

Provide your response in raw JSON format with the key:
"lyrics_theme" (a string summarizing the retrieved interpretations).
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=query,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
            ),
        )
        if not response.text or not response.text.strip():
            return {
                "lyrics_theme": "No lyric theme interpretation found.",
            }

        cleaned_text = clean_json_string(response.text)
        try:
            data = json.loads(cleaned_text)
            lyrics_theme = (
                data.get("lyrics_theme")
                or data.get("theme")
                or data.get("interpretation")
            )
            if not lyrics_theme:
                lyrics_theme = response.text
        except Exception:
            lyrics_theme = response.text

        return {
            "lyrics_theme": str(lyrics_theme).strip(),
        }
    except Exception as e:
        logger.error(f"Error retrieving lyrics theme for '{song_title}': {e}")
        return {
            "lyrics_theme": "No lyric theme interpretation found.",
        }


def verify_song_exists(title: str, artist: str) -> bool:
    """Verify if a recommended candidate song actually exists via search.

    Args:
        title: The title of the song.
        artist: The artist of the song.

    Returns:
        True if the song is verified to exist, False otherwise.
    """
    client = genai.Client()
    query = f"""Does the song "{title}" by "{artist}" actually exist? 
Search to verify.
Provide your response in raw JSON format with the key:
"exists" (boolean: true or false).

Do not add markdown formatting or backticks around the JSON, return ONLY the raw JSON string."""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=query,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
            ),
        )
        cleaned_text = clean_json_string(response.text)
        data = json.loads(cleaned_text)
        return bool(data.get("exists", False))
    except Exception as e:
        logger.error(f"Error verifying song '{title}' by '{artist}': {e}")
        return False
