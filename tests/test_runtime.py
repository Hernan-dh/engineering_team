import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from engineering_team.model_config import MODEL_FALLBACKS
from engineering_team.model_provider import fallback_llm, is_empty_response, openai_compatible_messages
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


if __name__ == "__main__":
    unittest.main()
