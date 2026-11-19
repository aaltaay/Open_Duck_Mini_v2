"""Voice pipeline checks. No model download and no network.

The engines here are stand-ins. The latency script measures the real ones.
"""

import array
import sys
import unittest

from altaay_lab.software.companion.assistant import Assistant
from altaay_lab.software.companion.audio_pcm import downsample_48k, read_wav, to_16k_mono, write_wav
from altaay_lab.software.companion.cloud_llm import LiveCloudLLM
from altaay_lab.software.companion.config import load_config
from altaay_lab.software.companion.pipeline import VoicePipeline
from altaay_lab.software.companion.stt import ScriptedSpeech
from altaay_lab.software.companion.tts import ScriptedSpeechOut
from altaay_lab.software.companion.wake import ScriptedWake


def _tone(n, value=1000):
    data = array.array("h", bytes(n * 2))
    for i in range(n):
        data[i] = value if (i // 10) % 2 == 0 else -value
    return data


class AudioTests(unittest.TestCase):
    def test_48k_averages_groups_of_three(self):
        samples = array.array("h", [0, 0, 3, 9, 9, 9])
        out = downsample_48k(samples)
        self.assertEqual(list(out), [1, 9])

    def test_stereo_48k_becomes_16k_mono(self):
        # Two channels, three frames: (0, 2), (0, 2), (0, 2) then (10, 10) x3.
        interleaved = array.array("h", [0, 2, 0, 2, 0, 2, 10, 10, 10, 10, 10, 10])
        out = to_16k_mono(interleaved, 48000, 2)
        self.assertEqual(list(out), [1, 10])

    def test_wav_round_trip(self):
        import tempfile
        from pathlib import Path

        samples = _tone(1600)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "clip.wav"
            write_wav(path, samples, 16000)
            back = read_wav(path)
        self.assertEqual(list(back[:10]), list(samples[:10]))
        self.assertEqual(len(back), len(samples))


class ConfigTests(unittest.TestCase):
    def test_config_rejects_a_key_field(self):
        with self.assertRaises(ValueError):
            load_config({"mode": "adult", "cloud": "off", "api_key": "plain-value"})

    def test_resident_and_isolate_cannot_both_be_on(self):
        with self.assertRaises(ValueError):
            load_config({"mode": "kid", "cloud": "off", "resident": True, "isolate": True})

    def test_isolate_child_round_trip(self):
        from altaay_lab.software.companion.isolate import IsolatedPipeline

        stub = (
            "import json, sys\n"
            "print(json.dumps({'woke': True, 'heard': 'set a timer', 'said': 'ok', "
            "'timings_s': {'total': 0.1}, 'phases': ['listening', 'done'], 'sample_rate': 16000}))\n"
        )
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as folder:
            script = Path(folder) / "stub.py"
            script.write_text(stub, encoding="utf-8")
            cfg = load_config(
                {
                    "mode": "kid",
                    "cloud": "off",
                    "isolate": True,
                    "vosk_model_dir": str(Path(folder) / "vosk-model-small-en-us-0.15"),
                    "piper_model": str(Path(folder) / "voice.onnx"),
                }
            )
            pipe = IsolatedPipeline(cfg, command=[sys.executable, str(script)])
            turn = pipe.run_pcm(_tone(1600), 16000)
        self.assertTrue(turn.woke)
        self.assertEqual(turn.heard, "set a timer")
        self.assertEqual(turn.as_dict()["said"], "ok")

    def test_wake_loader_skips_a_missing_package(self):
        import importlib.util
        import sys

        from altaay_lab.software.companion.wake import _wake_model

        if importlib.util.find_spec("openwakeword") is not None:
            self.skipTest("openwakeword is installed here")
        sys.modules.pop("sklearn", None)
        with self.assertRaises(ImportError):
            _wake_model("hey_jarvis")
        self.assertNotIn("sklearn", sys.modules)

    def test_example_config_loads(self):
        from pathlib import Path

        path = Path(__file__).resolve().parents[1] / "voice_config.example.json"
        cfg = load_config(path)
        self.assertEqual(cfg["mode"], "kid")
        self.assertEqual(cfg["cloud"], "off")
        self.assertEqual(cfg["wake_threshold"], 0.5)
        self.assertFalse(cfg["resident"])
        self.assertFalse(cfg["isolate"])
        self.assertNotIn("api_key", cfg)


class PipelineTests(unittest.TestCase):
    def _pipe(self, heard="set a timer for 5 minutes", mode="kid", cloud="off"):
        bot = Assistant(mode=mode, cloud=cloud)
        wake = ScriptedWake(at_sample=16000)
        stt = ScriptedSpeech(heard)
        tts = ScriptedSpeechOut()
        return VoicePipeline(bot, wake, stt, tts), bot, tts

    def test_heard_line_keeps_the_wake_phrase(self):
        pipe, bot, _tts = self._pipe(heard="hey jarvis remind me to stretch")
        turn = pipe.run_pcm(_tone(48000), 16000)
        self.assertEqual(turn.heard, "hey jarvis remind me to stretch")
        self.assertEqual(bot.reminders, ["stretch"])

    def test_timer_from_audio_sets_the_body(self):
        pipe, bot, tts = self._pipe()
        turn = pipe.run_pcm(_tone(48000), 16000)
        self.assertTrue(turn.woke)
        self.assertEqual(bot.timers, [5])
        self.assertEqual(turn.phases, ("listening", "speaking", "done"))
        self.assertEqual(turn.bodies["listening"]["expression"], "curious_tilt")
        self.assertEqual(turn.bodies["speaking"]["expression"], "nod")
        self.assertEqual(turn.bodies["done"]["expression"], "settle")
        self.assertIn("5", tts.texts[0])
        self.assertGreater(len(turn.audio), 0)
        self.assertIn("total", turn.timings_s)

    def test_no_wake_does_not_speak(self):
        bot = Assistant(mode="kid", cloud="off")
        wake = ScriptedWake(at_sample=10**9)
        pipe = VoicePipeline(bot, wake, ScriptedSpeech("set a timer for 5 minutes"), ScriptedSpeechOut())
        turn = pipe.run_pcm(_tone(8000), 16000)
        self.assertFalse(turn.woke)
        self.assertEqual(bot.timers, [])
        self.assertEqual(turn.phases, ())

    def test_sequential_closes_each_engine(self):
        closed = []

        class Wake(ScriptedWake):
            def close(self):
                closed.append("wake")

        class Speech(ScriptedSpeech):
            def close(self):
                closed.append("stt")

        class Talk(ScriptedSpeechOut):
            def close(self):
                closed.append("tts")

        pipe = VoicePipeline(
            Assistant(mode="kid", cloud="off"),
            factories={"wake": Wake, "stt": lambda: Speech("set a timer for 5 minutes"), "tts": Talk},
            resident=False,
        )
        turn = pipe.run_pcm(_tone(48000), 16000)
        self.assertEqual(turn.phases, ("listening", "speaking", "done"))
        self.assertEqual(closed[:3], ["wake", "stt", "tts"])
        self.assertIn("load_wake", turn.timings_s)

    def test_kid_mail_from_audio_is_refused(self):
        pipe, bot, tts = self._pipe(heard="check my email", mode="kid", cloud="mock")
        turn = pipe.run_pcm(_tone(48000), 16000)
        self.assertEqual(turn.phases, ("listening", "refused"))
        self.assertEqual(turn.bodies["refused"]["expression"], "shake")
        self.assertTrue(turn.reply["refused"])
        self.assertIn("off", tts.texts[0])

    def test_question_on_the_walk_thread_is_refused(self):
        pipe, bot, _tts = self._pipe(heard="what time is it")
        bot.personality.bind_walk_thread()
        with self.assertRaises(RuntimeError):
            pipe.run_pcm(_tone(48000), 16000)


class LiveCloudTests(unittest.TestCase):
    def test_transport_does_not_leak_the_key(self):
        seen = {}

        def transport(url, headers, body):
            seen["url"] = url
            seen["auth"] = headers["Authorization"]
            seen["body"] = body
            return {"choices": [{"message": {"content": "A duck is a bird."}}]}

        llm = LiveCloudLLM(
            base_url="https://example.invalid/v1",
            model="demo",
            key_env="ODM_TEST_CLOUD_KEY",
            transport=transport,
        )
        import os

        os.environ["ODM_TEST_CLOUD_KEY"] = "test-key-value"
        try:
            self.assertTrue(llm.ready())
            result = llm.complete("What is a duck?", tools=())
        finally:
            del os.environ["ODM_TEST_CLOUD_KEY"]
        self.assertEqual(result["said"], "A duck is a bird.")
        self.assertIn("test-key-value", seen["auth"])
        self.assertNotIn("test-key-value", result["said"])
        self.assertNotIn("test-key-value", seen["body"]["messages"][0]["content"])

    def test_echoed_secret_is_dropped(self):
        def transport(url, headers, body):
            return {"choices": [{"message": {"content": "the key is test-key-value"}}]}

        llm = LiveCloudLLM(
            base_url="https://example.invalid/v1",
            model="demo",
            key_env="ODM_TEST_CLOUD_KEY",
            transport=transport,
        )
        import os

        os.environ["ODM_TEST_CLOUD_KEY"] = "test-key-value"
        try:
            result = llm.complete("hello", tools=())
        finally:
            del os.environ["ODM_TEST_CLOUD_KEY"]
        self.assertNotIn("test-key-value", result["said"])

    def test_credential_argument_is_refused(self):
        value = "plain-value"
        with self.assertRaises(ValueError) as caught:
            LiveCloudLLM().complete("hello", tools=(), api_key=value)
        self.assertNotIn(value, str(caught.exception))


if __name__ == "__main__":
    unittest.main()
