import json
import tempfile
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from pathlib import Path

from prompt_tuner.client import AIClient
from prompt_tuner.runner import PromptRunner, load_task, TaskConfig


class MockHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        model = body.get("model", "unknown")
        self._json_response({
            "choices": [{"message": {"content": f"Summary by {model}"}}],
            "model": model,
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        })

    def _json_response(self, data):
        out = json.dumps(data).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)


def _start_server():
    server = HTTPServer(("127.0.0.1", 0), MockHandler)
    port = server.server_address[1]
    Thread(target=server.serve_forever, daemon=True).start()
    return server, port


class TestRunner:
    def setup_method(self):
        self.server, self.port = _start_server()
        self.client = AIClient(api_key="test-key", base_url=f"http://127.0.0.1:{self.port}")

    def teardown_method(self):
        self.client.close()
        self.server.shutdown()

    def test_run_basic(self):
        config = TaskConfig(
            task="test",
            input_text="Some text",
            models=["model-a", "model-b"],
            prompts=["Summarize:", "TL;DR:"],
            criteria=["relevance"],
        )
        runner = PromptRunner(self.client)
        results = runner.run(config)
        assert len(results) == 4  # 2 prompts x 2 models
        assert results[0].output == "Summary by model-a"
        assert results[1].output == "Summary by model-b"

    def test_model_override(self):
        config = TaskConfig(task="t", input_text="x", models=["a"], prompts=["P:"], criteria=[])
        runner = PromptRunner(self.client)
        results = runner.run(config, model_override=["override-model"])
        assert len(results) == 1
        assert results[0].model == "override-model"


class TestLoadTask:
    def test_load_yaml(self):
        content = {
            "task": "summarize",
            "input": "Hello world",
            "models": ["m1", "m2"],
            "prompts": ["P1", "P2"],
            "scoring": {"criteria": ["relevance"], "judge_models": ["m1", "m2"], "exclude_self_judge": True},
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            import yaml
            yaml.dump(content, f)
            path = f.name
        config = load_task(path)
        assert config.task == "summarize"
        assert config.models == ["m1", "m2"]
        assert config.judge_models == ["m1", "m2"]
        assert config.exclude_self_judge is True
        Path(path).unlink()

    def test_load_yaml_legacy_single_judge(self):
        content = {
            "task": "test",
            "input": "x",
            "models": ["m1"],
            "prompts": ["P"],
            "scoring": {"judge_model": "m1"},
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            import yaml
            yaml.dump(content, f)
            path = f.name
        config = load_task(path)
        assert config.judge_models == ["m1"]
        Path(path).unlink()
