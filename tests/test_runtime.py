import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from engineering_team.model_config import MODEL_FALLBACKS
from engineering_team.model_provider import fallback_llm, is_empty_response, openai_compatible_messages
from engineering_team.program_options import PROGRAM_OPTIONS, choose_requirements
from engineering_team.resume import (
    ask_to_resume,
    first_incomplete_stage,
    load_requirements,
    save_requirements,
)
from engineering_team.tools.sandbox_tools import run_sandbox_python, write_sandbox_file


class ModelProviderTests(unittest.TestCase):
    def test_provider_order_and_coding_fallbacks(self):
        self.assertEqual(MODEL_FALLBACKS[0].model, "gemini-3.8-flash")
        models = [spec.model for spec in MODEL_FALLBACKS]
        self.assertIn("openai/gpt-oss-120b", models)
        self.assertIn("nvidia/nemotron-3-super-120b-a12b:free", models)

    def test_requires_at_least_one_key(self):
        with patch.dict(os.environ, {
            "GEMINI_API_KEY": "",
            "GROQ_API_KEY": "",
            "OPENROUTER_API_KEY": "",
        }, clear=False):
            with self.assertRaisesRegex(RuntimeError, "Configure at least one provider key"):
                fallback_llm()

    def test_removes_gemini_metadata_for_openai_compatible_provider(self):
        messages = [{
            "role": "assistant",
            "content": "",
            "tool_calls": [{"id": "call-1"}],
            "raw_tool_call_parts": [{"thought_signature": "opaque"}],
        }]
        cleaned = openai_compatible_messages(messages)  # type: ignore[arg-type]
        self.assertNotIn("raw_tool_call_parts", cleaned[0])
        self.assertEqual(cleaned[0]["tool_calls"], [{"id": "call-1"}])

    def test_empty_provider_responses_are_rejected(self):
        self.assertTrue(is_empty_response(None))
        self.assertTrue(is_empty_response("  \n"))
        self.assertFalse(is_empty_response("usable response"))


class SandboxToolTests(unittest.TestCase):
    def test_rejects_path_traversal(self):
        self.assertIn("inside the sandbox", write_sandbox_file.run("../escape.py", ""))
        self.assertIn("inside the sandbox", run_sandbox_python.run("../escape.py"))

    def test_docker_execution_is_constrained(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch("engineering_team.tools.sandbox_tools.SANDBOX_DIR", Path(directory)):
                write_sandbox_file.run("program.py", "print('ok')")
                with patch("engineering_team.tools.sandbox_tools.subprocess.run") as run:
                    run.return_value.returncode = 0
                    run.return_value.stdout = "ok\n"
                    run.return_value.stderr = ""
                    result = run_sandbox_python.run("program.py")

        command = run.call_args.args[0]
        self.assertIn("none", command)
        self.assertIn("1g", command)
        self.assertIn("no-new-privileges", command)
        self.assertIn("--read-only", command)
        self.assertIn("Exit code: 0", result)


class ProgramSelectionTests(unittest.TestCase):
    def test_exposes_five_presets(self):
        self.assertEqual(len(PROGRAM_OPTIONS), 5)

    def test_selects_a_preset(self):
        answers = iter(["3"])
        selected = choose_requirements(lambda _prompt: next(answers), lambda _text: None)
        self.assertEqual(selected.requirements, PROGRAM_OPTIONS[2][1])

    def test_option_zero_accepts_custom_requirements(self):
        answers = iter(["0", "Build a recipe editor"])
        selected = choose_requirements(lambda _prompt: next(answers), lambda _text: None)
        self.assertEqual(selected.requirements, "Build a recipe editor")

    def test_continue_option_is_only_available_with_previous_work(self):
        answers = iter(["6"])
        selected = choose_requirements(
            lambda _prompt: next(answers), lambda _text: None, can_resume=True
        )
        self.assertTrue(selected.resume)


class ResumeTests(unittest.TestCase):
    def test_detects_first_incomplete_stage(self):
        with tempfile.TemporaryDirectory() as directory:
            sandbox = Path(directory)
            self.assertEqual(first_incomplete_stage(sandbox), 0)
            (sandbox / "design.md").write_text("design", encoding="utf-8")
            self.assertEqual(first_incomplete_stage(sandbox), 1)
            (sandbox / "backend").mkdir()
            (sandbox / "backend" / "api.py").write_text("", encoding="utf-8")
            self.assertEqual(first_incomplete_stage(sandbox), 2)
            (sandbox / "frontend").mkdir()
            (sandbox / "frontend" / "app.py").write_text("", encoding="utf-8")
            (sandbox / "_validate.py").write_text("", encoding="utf-8")
            self.assertEqual(first_incomplete_stage(sandbox), 3)
            (sandbox / "test_summary.md").write_text("done", encoding="utf-8")
            self.assertEqual(first_incomplete_stage(sandbox), 4)

    def test_round_trips_requirements(self):
        with tempfile.TemporaryDirectory() as directory:
            sandbox = Path(directory)
            save_requirements("Build a scheduler", sandbox)
            self.assertEqual(load_requirements(sandbox), "Build a scheduler")

    def test_offers_immediate_resume_after_error(self):
        answers = iter(["maybe", "y"])
        messages = []
        accepted = ask_to_resume(lambda _prompt: next(answers), messages.append)
        self.assertTrue(accepted)
        self.assertTrue(any("work has been saved" in message for message in messages))

    def test_declining_resume_returns_false(self):
        self.assertFalse(ask_to_resume(lambda _prompt: "n", lambda _text: None))


if __name__ == "__main__":
    unittest.main()
