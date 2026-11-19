"""Optional cloud chat model. Off unless a key is set outside this repo.

The call is an OpenAI-compatible POST to {base}/chat/completions.
The base URL and the model name come from the config. The key comes from
the environment variable named in the config (default ODM_CLOUD_API_KEY).
Nothing in this file has a default host that would send text on its own.

A credential argument raises, and the error text does not include the value.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

_SECRET_WORDS = ("key", "token", "secret", "password", "credential")


class CloudError(OSError):
    """The cloud call failed. The message has no response body and no key."""


class LiveCloudLLM:
    def __init__(self, base_url="", model="", key_env="ODM_CLOUD_API_KEY", transport=None, timeout=20.0):
        self.base_url = (base_url or "").rstrip("/")
        self.model = model or ""
        self.key_env = key_env or "ODM_CLOUD_API_KEY"
        self.transport = transport
        self.timeout = float(timeout)
        self.calls = 0

    def ready(self):
        if not self.base_url or not self.model:
            return False
        return bool(os.environ.get(self.key_env, "").strip())

    def complete(self, text, *, tools, kid=False, **extra):
        banned = [name for name in extra if any(word in name.lower() for word in _SECRET_WORDS)]
        if banned:
            raise ValueError("credentials are not accepted")
        if kid:
            return {
                "said": "I can set a timer or a reminder.",
                "tool": None,
                "records": (),
                "configured": False,
            }
        if not self.ready():
            return {
                "said": "The cloud model stays off until a key is set outside this repo.",
                "tool": None,
                "records": (),
                "configured": False,
            }
        self.calls += 1
        key = os.environ.get(self.key_env, "").strip()
        url = self.base_url + "/chat/completions"
        headers = {"Authorization": "Bearer " + key, "Content-Type": "application/json"}
        body = {
            "model": self.model,
            "messages": [{"role": "user", "content": text}],
        }
        # tools is accepted so the call shape matches the mock. This client
        # does not send mail or calendar tools. Those stay on the mock.
        del tools
        try:
            if self.transport is not None:
                data = self.transport(url, headers, body)
            else:
                data = self._post(url, headers, body)
        except CloudError:
            raise
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise CloudError("cloud request failed") from exc
        said = str(data["choices"][0]["message"]["content"]).strip()
        if key and key in said:
            said = "The cloud model answered, and the reply was dropped because it echoed a secret."
        return {"said": said, "tool": None, "records": (), "configured": True}

    def _post(self, url, headers, body):
        raw = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=raw, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise CloudError("cloud request failed") from exc
