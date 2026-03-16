import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread

from prompt_tuner.client import AIClient, ChatMessage


MOCK_MODELS = [
    {"id": "gpt-5-mini", "name": "GPT-5 Mini", "owned_by": "openai"},
    {"id": "gemini-3-flash", "name": "Gemini 3 Flash", "owned_by": "google"},
]


class MockHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == "/models":
            self._json_response({"data": MOCK_MODELS})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        model = body.get("model", "unknown")
        self._json_response({
            "choices": [{"message": {"content": f"Response from {model}"}}],
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
    t = Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server, port


class TestAIClient:
    def setup_method(self):
        self.server, self.port = _start_server()
        self.client = AIClient(api_key="test-key", base_url=f"http://127.0.0.1:{self.port}")

    def teardown_method(self):
        self.client.close()
        self.server.shutdown()

    def test_fetch_models(self):
        models = self.client.fetch_models()
        assert len(models) == 2
        assert models[0].id == "gpt-5-mini"
        assert models[1].provider == "google"

    def test_chat(self):
        resp = self.client.chat("gpt-5-mini", [ChatMessage(role="user", content="Hi")])
        assert resp.content == "Response from gpt-5-mini"
        assert resp.model == "gpt-5-mini"
        assert resp.prompt_tokens == 10
