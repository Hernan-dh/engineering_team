# Operations

## Local setup

1. Install Python 3.10–3.13 and `uv`.
2. Start Docker Desktop with Linux containers enabled.
3. Run `uv sync`.
4. Copy `.env.example` to `.env` and configure at least one of `GEMINI_API_KEY`, `GROQ_API_KEY`, or `OPENROUTER_API_KEY`.
5. Run `uv run crewai run`.

The command displays five program presets. Select `0` to enter custom requirements. If the prior sandbox contains work, select `6` to preserve it and continue from the first incomplete stage. After an error, the still-running command also offers an immediate `[y/N]` resume prompt. Automated or hosted callers can set `ENGINEERING_REQUIREMENTS` to start a new program and skip the initial menu; without interactive stdin, a failed run exits after preserving its checkpoint.

The first run builds `engineering-team-sandbox:local`, which contains Python 3.13 and Gradio 6. Subsequent runs reuse that image and start with a clean `sandbox/`. Generated programs run without network access and are limited to one CPU, 1 GB RAM, 128 processes, and five minutes.

After CrewAI completes, the entry point independently runs `_validate.py` and unittest discovery inside the sandbox image. Any non-zero result records the frontend or test stage and its diagnostic as incomplete, injects that diagnostic into the resumed task, and enters the normal resume prompt. `test_summary.md` is replaced with a trusted pass summary only after both commands succeed.

Some free models serialize a requested sandbox write in their final text instead of returning a native tool call. The entry point recovers that narrow case before acceptance validation. Only a full `write_sandbox_file` envelope with a contained relative path is accepted; all other textual calls are ignored.

Runtime model order is defined in `src/engineering_team/model_config.py`. A provider failure advances to the next configured model for the current call. Tracing is disabled so generated code and requirements are not uploaded as CrewAI execution traces.
Anonymous CrewAI telemetry and OpenTelemetry export are also disabled by the entry point. The pinned Gradio runtime keeps API documentation off the execution path, so a documentation-service outage cannot stop the crew.

Generated files in `output/` and `sandbox*/` are local artifacts and are excluded from publication.

## Verification

Run `./scripts/verify.sh`, or on Windows run `uv run python scripts/verify.py`.

To rebuild the sandbox image after changing its Dockerfile:

```powershell
docker build --tag engineering-team-sandbox:local --file docker/sandbox.Dockerfile docker
```

Enable the repository-managed pre-commit hook once per clone with `uv run python scripts/install_hooks.py`. GitHub Actions runs the same verifier.

## Documentation

- Rebuild the changelog: `uv run python scripts/document.py changelog`.
- Create an ADR draft: `uv run python scripts/document.py decision "Decision title"`.

## Publishing

Preview a proposal with `uv run python scripts/publish.py --preview`. Running `python scripts/publish.py` is also supported: the publisher invokes verification through `uv` so tests always use the project's locked environment. Interactive publication verifies the repository, proposes an English Conventional Commit title through Gemini with Groq fallback, and requires typing `PUBLISH` before staging, committing, and pushing.

Provide `--title` and `--description` to avoid external metadata generation. Commits and pushes always require explicit user authorization.

## Recovery

- After a provider, quota, or connection failure, answer `y` at the immediate resume prompt. The process remains open and starts again at the first incomplete design, backend, frontend, or test task. If you exit, rerun `uv run crewai run` later and select option `6`.
- If verification fails, fix every reported item and rerun it.
- If metadata generation fails, inspect the provider attempt names, verify local keys and quotas, or provide commit metadata manually.
- Never recover with a force-push.
