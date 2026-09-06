# Engineering Team

A command-line team that designs and generates a Python application with a Gradio interface, validates it in Docker, and resumes from incomplete stages.

## Attribution

Project built from [Ed Donner's agentic AI engineering course](https://github.com/ed-donner/agents). The upstream MIT copyright notice is preserved in [LICENSE](LICENSE). No endorsement by the course author is implied.

## Run locally

Python 3.12 and uv are the documented development baseline. Docker is required for actual code generation, but not for unit tests. Run the following commands from this repository's root.

```sh
uv sync
```

Copy `.env.example` to `.env` (`Copy-Item .env.example .env` in PowerShell, or `cp .env.example .env` on Linux/macOS), then replace only the placeholders for the providers you intend to use. Leave unused credentials empty. Never commit the real `.env`.

Configure at least one model-provider key and start Docker. The first run builds `docker/sandbox.Dockerfile` and needs network access to install its dependencies. Select a preset or supply custom requirements; `ENGINEERING_REQUIREMENTS` supports non-interactive input.

```sh
uv run crewai run
```

## Architecture

```text
CLI requirements -> engineering lead -> backend engineer -> frontend engineer -> test engineer -> Docker acceptance gate
```

See [architecture](docs/ARCHITECTURE.md) for components, data flow and trust boundaries, and [operations](docs/OPERATIONS.md) for configuration and recovery.

## Technologies

Python, CrewAI, Gradio 6, Docker, YAML, uv and unittest; Gemini, Groq and OpenRouter providers.

## Reproducible tests

After installing the dependencies above:

```sh
uv run python -m unittest discover -v
uv run python scripts/verify.py
```

Coverage: Sandbox containment and container constraints, provider configuration, resume-stage detection, strict tool-call recovery and acceptance-gate failures; no live model or Docker dependency in unit tests. Tests run without real credentials or paid API calls. They do not measure model quality, live provider availability, or full browser behavior. CI installs dependencies and runs the same verifier on pushes and pull requests.

## Limitations

Generated code requires review. Acceptance checks verify construction and backend tests, not visual quality or all requirements. The runtime container has no network and only its preinstalled dependencies. Resuming relies on local artifacts. This is an experimental developer tool, not an autonomous production deployment service.

Prompts and relevant context are sent to external model/search providers. Do not submit secrets or confidential data. Provider names in source code are configuration, not promises of current availability, pricing, or free access.

## Public repository and license

The repository includes a placeholder-only [.env.example](.env.example); local credentials, caches and generated artifacts are excluded by [.gitignore](.gitignore). See [operations](docs/OPERATIONS.md) for verification and publication instructions.

The code is distributed under the [MIT license](LICENSE). Dependencies retain their own licenses. Biographical material, third-party documents, logos and linked content are not relicensed by this code license. Publishing scripts can send code diffs to external models when generating commit text; use explicit metadata to avoid that step.
