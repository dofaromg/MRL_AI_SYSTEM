import importlib.util
import os
from pathlib import Path
import socket
import subprocess
import time
import unittest
import urllib.request
import urllib.error
ROOT = Path(__file__).resolve().parents[1]
class RuntimeTests(unittest.TestCase):
    def test_chat(self):
        spec = importlib.util.spec_from_file_location("platform_server", ROOT / "MRL_Platform_Server.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        class Mother:
            def chat(self, msg): return self.result
        mother = Mother()
        module._MA = mother
        for result, expected in [({"error": "missing model"}, False), ("reply", True), ({"reply": "hello"}, True)]:
            mother.result = result
            self.assertEqual(module.api_chat({"message": "hello"})["ok"], expected)
    def test_gateway(self):
        for auth, opt, token, expected in [(False, False, None, 403), (False, True, None, 200), (True, True, None, 401), (True, False, "secret-test-token", 200)]:
            with socket.socket() as sock:
                sock.bind(("127.0.0.1", 0)); port = sock.getsockname()[1]
            env = dict(os.environ, MRL_PORT=str(port), MRL_AUTH_REQUIRED=str(auth).lower(), MRL_ALLOW_UNAUTHENTICATED_WRITES=str(opt).lower(), MRL_API_TOKEN="secret-test-token")
            proc = subprocess.Popen(["node", "MRL_RuntimeServer.js"], cwd=ROOT, env=env, stdout=subprocess.DEVNULL)
            try:
                url = f"http://127.0.0.1:{port}"
                for _ in range(100):
                    try:
                        self.assertEqual(urllib.request.urlopen(url + "/health").status, 200); break
                    except OSError: time.sleep(.05)
                else: self.fail("server did not start")
                headers = {"Content-Type": "application/json"}
                if token: headers["Authorization"] = "Bearer " + token
                req = urllib.request.Request(url + "/mrl/perceive", data=b'{}', headers=headers)
                try: status = urllib.request.urlopen(req).status
                except urllib.error.HTTPError as exc: status = exc.code
                self.assertEqual(status, expected)
            finally:
                proc.terminate(); proc.wait(timeout=10)
if __name__ == "__main__": unittest.main()
