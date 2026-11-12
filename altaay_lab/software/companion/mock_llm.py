"""Stand-in for an optional cloud chat model with tool calls.

No network. No credentials. The records are canned so a demo can show the
shape of mail and calendar tools without an account.
"""

from __future__ import annotations

_SECRET_WORDS = ("key", "token", "secret", "password", "credential")


class MockCloudLLM:
    """Same call shape a tool-calling model would use. Nothing leaves the process."""

    def __init__(self):
        self.calls = 0

    def complete(self, text, *, tools, kid=False, **extra):
        banned = [name for name in extra if any(word in name.lower() for word in _SECRET_WORDS)]
        if banned:
            raise ValueError("credentials are not accepted")
        self.calls += 1
        if kid:
            return {
                "said": "I can set a timer or a reminder.",
                "tool": None,
                "records": (),
            }
        lowered = text.lower()
        allowed = set(tools)
        if any(word in lowered for word in ("email", "inbox", "mail")) and "list_inbox" in allowed:
            return {
                "said": "Here is the mock inbox.",
                "tool": "list_inbox",
                "records": ({"from": "mock", "subject": "Mock inbox note"},),
            }
        if any(word in lowered for word in ("calendar", "schedule")) and "list_calendar" in allowed:
            return {
                "said": "Here is the mock calendar.",
                "tool": "list_calendar",
                "records": ({"title": "Mock calendar item", "when": "tomorrow morning"},),
            }
        return {
            "said": "Mock answer. This is not a live model.",
            "tool": None,
            "records": (),
        }
