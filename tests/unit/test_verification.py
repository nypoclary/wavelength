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

"""Unit tests for the song verification tool and candidate_verifier node."""

import json
from unittest.mock import MagicMock, patch
import pytest

from app.agent import (
    CandidateVerifierOutput,
    MoodAlignmentOutput,
    SongProfile,
    candidate_verifier,
)
from app.tools import verify_song_exists


def test_verify_song_exists_real() -> None:
    """Test that verify_song_exists returns True for a real, well-known song."""
    result = verify_song_exists("Bohemian Rhapsody", "Queen")
    assert result is True


def test_verify_song_exists_fake() -> None:
    """Test that verify_song_exists returns False for a clearly fake song."""
    result = verify_song_exists("Moonlight Fandango Serenade", "Zylo Krendrix")
    assert result is False


def test_candidate_verifier_silent_drop() -> None:
    """Test candidate_verifier node directly with a mocked candidate list to confirm silent-drop behavior."""
    # Mock Context and state containing the seed song profile
    mock_ctx = MagicMock()
    mock_ctx.state = {
        "song_profile": {
            "title": "Yesterday",
            "artist": "The Beatles",
            "tempo": 97,
            "genre": "Baroque pop",
            "key": "F Major",
            "release_year": 1965,
            "lyrics_theme": "Melancholic reflection on lost love.",
        }
    }

    # Prepare input strategy and reasoning
    node_input = MoodAlignmentOutput(
        strategy="mood_shift",
        reasoning="Transition from sad to happy.",
    )

    # Mock the LLM candidate generation response
    mock_llm_response = MagicMock()
    mock_llm_response.text = json.dumps(
        {
            "candidates": [
                {
                    "title": "Bohemian Rhapsody",
                    "artist": "Queen",
                    "reason": "Uplifting and well-known.",
                },
                {
                    "title": "Moonlight Fandango Serenade",
                    "artist": "Zylo Krendrix",
                    "reason": "An obviously fake song to test verification.",
                },
            ]
        }
    )

    # Patch the Client inside app.agent so it returns our mocked candidates
    with patch("app.agent.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.models.generate_content.return_value = mock_llm_response

        # Execute candidate_verifier node
        events = []
        for event in candidate_verifier(node_input, mock_ctx):
            events.append(event)

        # Confirm the output contains only the verified song
        output_events = [e for e in events if e.output is not None]
        assert len(output_events) == 1

        output = output_events[0].output
        assert isinstance(output, CandidateVerifierOutput)
        assert len(output.recommendations) == 1
        assert output.recommendations[0].title == "Bohemian Rhapsody"
        assert output.recommendations[0].artist == "Queen"
