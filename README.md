# Wavelength

A music recommendation agent that solves the cold-start problem. Give it one seed song and a target mood, and it recommends real, verified songs based on tempo, genre, and lyrical themes, with no listening history required.

Built with Google's Agent Development Kit (ADK) 2.0 as a 3-node graph workflow, and developed using Antigravity's architect-by-prompt pattern.

Agent generated with `agents-cli` version `0.6.1`.

## The Problem

Most recommendation systems rely on listening history. That breaks down for a new user, or for anyone who just wants a recommendation based on one song they like right now. Wavelength uses content-based filtering instead: it grounds recommendations in the seed song's own attributes rather than in other users' behavior.

## How It Works

Wavelength runs as a linear graph of three nodes, each backed by `gemini-2.5-flash`:

```
song_understanding → mood_alignment → candidate_verifier
```

**1. `song_understanding`**
Retrieves factual metadata (tempo, genre, key, release year) and lyric/theme interpretations for the seed song, using two separate Google Search-grounded calls so the model retrieves real information instead of guessing. A third call synthesizes both into a structured `SongProfile`.

**2. `mood_alignment`**
Compares the song profile against the user's target mood and decides between two strategies: `mood_match` (reinforce a similar feeling) or `mood_shift` (pivot toward the target mood), with reasoning attached.

**3. `candidate_verifier`**
Generates up to 5 content-based candidate songs, then independently verifies each one exists via a separate search-grounded call. Any candidate that can't be confirmed is silently dropped. Only real, verified songs ever reach the final output.

All data between nodes flows through strict Pydantic schemas (`WavelengthInput`, `SongProfile`, `MoodAlignmentOutput`, `CandidateVerifierOutput`), so a failed or malformed model call surfaces immediately as a validation error instead of silently passing bad data downstream.

## Known Limitations

- Seed-song metadata is not independently verified the way output candidates are. An ambiguous seed song title (with no artist specified) can produce a confident but ungrounded metadata guess. Always include the artist name in `seed_song` to avoid this.
- Search-grounded metadata can vary slightly between runs since it depends on live search results.
- The `mood_alignment` strategy decision is an LLM judgment call with no deterministic rule-based check behind it.

## Project Structure

```
wavelength/
├── app/                        # Core agent code
│   ├── agent.py                # Graph definition and node logic
│   ├── tools.py                # Search-grounded tools: metadata, lyrics, verification
│   ├── fast_api_app.py         # FastAPI backend server
│   └── app_utils/              # App utilities and helpers
├── tests/                      # Unit, integration, and load tests
├── GEMINI.md                   # AI-assisted development guide
└── pyproject.toml              # Project dependencies
```

> 💡 **Tip:** Use [Antigravity CLI](https://antigravity.google/) for AI-assisted development, project context is pre-configured in `GEMINI.md`.

## Requirements

Before you begin, ensure you have:
- **uv**: Python package manager (used for all dependency management in this project) - [Install](https://docs.astral.sh/uv/getting-started/installation/) ([add packages](https://docs.astral.sh/uv/concepts/dependencies/) with `uv add <package>`)
- **agents-cli**: Agents CLI - Install with `uv tool install google-agents-cli`
- **Google Cloud SDK**: For GCP services - [Install](https://cloud.google.com/sdk/docs/install)

## Quick Start

Install `agents-cli` and its skills if not already installed:
```bash
uvx google-agents-cli setup
```

Install required packages:
```bash
agents-cli install
```

Test the agent with a local web server:
```bash
agents-cli playground
```

The Playground UI sends chat input as a plain `Content` object, while the graph entry point expects a structured `WavelengthInput`. Type your input as raw JSON directly into the message box:
```json
{"seed_song": "Yesterday by The Beatles", "target_mood": "happy"}
```

You can also use features from the [ADK](https://adk.dev/) CLI with `uv run adk`.

## Running Tests

```bash
uv run pytest tests/unit tests/integration
```

The core verification logic is covered by dedicated tests in `tests/unit/test_verification.py`:
- `test_verify_song_exists_real` — confirms a real, well-known song verifies as existing
- `test_verify_song_exists_fake` — confirms a fabricated song verifies as not existing
- `test_candidate_verifier_silent_drop` — confirms the `candidate_verifier` node correctly filters a mixed real/fake candidate list down to only the real song

## Commands

| Command              | Description                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------------- |
| `agents-cli install` | Install dependencies using uv                                                         |
| `agents-cli playground` | Launch local development environment                                                  |
| `agents-cli lint`    | Run code quality checks                                                               |
| `agents-cli eval`    | Evaluate agent behavior (generate, grade, analyze, and more — see `agents-cli eval --help`) |
| `uv run pytest tests/unit tests/integration` | Run unit and integration tests |
| [A2A Inspector](https://github.com/a2aproject/a2a-inspector) | Launch A2A Protocol Inspector |

## 🛠️ Project Management

| Command | What It Does |
|---------|--------------|
| `agents-cli scaffold enhance` | Add CI/CD pipelines and Terraform infrastructure |
| `agents-cli infra cicd` | One-command setup of entire CI/CD pipeline + infrastructure |
| `agents-cli scaffold upgrade` | Auto-upgrade to latest version while preserving customizations |

---

## Development

Edit agent logic in `app/agent.py` and search-grounded tools in `app/tools.py`, then test with `agents-cli playground`, which auto-reloads on save.

## Deployment

```bash
gcloud config set project <your-project-id>
agents-cli deploy
```

To add CI/CD and Terraform, run `agents-cli scaffold enhance`.
To set up your production infrastructure, run `agents-cli infra cicd`.

## Observability

Built-in telemetry exports to Cloud Trace, BigQuery, and Cloud Logging.

## A2A Inspector

This agent supports the [A2A Protocol](https://a2a-protocol.org/). Use the [A2A Inspector](https://github.com/a2aproject/a2a-inspector) to test interoperability. See the [A2A Inspector docs](https://github.com/a2aproject/a2a-inspector) for details.

## Built For

This project was built as the capstone submission for Google's 5-Day AI Agents Intensive Vibe Coding Course on Kaggle.
