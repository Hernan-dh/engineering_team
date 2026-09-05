# Architecture

## Purpose

`engineering_team` is a CrewAI project whose agents and tasks are configured in YAML and orchestrated from Python.

## Components

- `src/engineering_team/config/agents.yaml`: agent roles, goals, and backstories.
- `src/engineering_team/config/tasks.yaml`: task descriptions and expected outputs.
- `src/engineering_team/crew.py`: CrewAI agent, task, and crew construction.
- `src/engineering_team/main.py`: command-line entry points and kickoff inputs.
- `src/engineering_team/program_options.py`: five curated program choices and custom-input selection.
- `src/engineering_team/resume.py`: local requirement checkpoint and artifact-based incomplete-stage detection.
- `src/engineering_team/validation.py`: deterministic Docker acceptance gate for Gradio construction and backend tests.
- `src/engineering_team/model_config.py`: version-controlled provider and model fallback order.
- `src/engineering_team/model_provider.py`: per-call Gemini, Groq, and OpenRouter failover shared by all agents.
- `src/engineering_team/tools/sandbox_tools.py`: constrained workspace tools and Docker execution.
- `docker/sandbox.Dockerfile`: reproducible Python 3.13 and Gradio 6 runtime for generated applications.
- `knowledge/`: versioned knowledge supplied to the crew.
- `output/` and `sandbox*/`: generated execution artifacts excluded from Git.
- `scripts/`: shared verification, documentation, hook installation, and safe publishing commands.

## Trust boundaries

- Prompts, model responses, tool results, generated code, and generated reports are untrusted.
- Credentials are loaded from the environment and must not enter Git, prompts, logs, or documentation.
- CrewAI model and tool providers are external services.
- Generated code executes without network access in an ephemeral container with a read-only root filesystem, dropped capabilities, and bounded CPU, memory, process count, and execution time. Only `sandbox/` is mounted read-write.
- Resume state contains requirements only, remains inside ignored `sandbox/`, and is never published.
- LLM task completion is advisory: the entry point only reports success after the generated validation script and unittest discovery both exit successfully in Docker.

## Model routing

All four agents share a `FallbackLLM`. Each failed call advances through the configured Gemini, Groq, and OpenRouter models without restarting completed tasks. Native Gemini preserves tool-call thought signatures; provider-only metadata is removed before an OpenAI-compatible fallback receives the conversation.

## Related decisions

- [Continuous documentation and safe publishing](decisions/0001-continuous-documentation-and-safe-publishing.md)
