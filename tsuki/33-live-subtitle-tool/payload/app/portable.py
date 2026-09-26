import ctypes
import html
import json
import logging
import os
import queue
import re
import subprocess
import sys
import threading
import time
import traceback
from collections import deque
from pathlib import Path

import numpy as np
import opencc
import pyaudiowpatch as pyaudio
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QComboBox, QHBoxLayout, QLabel, QPushButton
from llama_cpp import Llama, llama_cpp


class PortableRuntime:
    """Keep runtime state and generated files beside the executable."""

    def __init__(self) -> None:
        self.root = Path(sys.executable).resolve().parent
        os.chdir(self.root)
        for directory in ("config", "logs", "temp", "cache", "models"):
            (self.root / directory).mkdir(exist_ok=True)
        for key, value in {
            "TEMP": self.root / "temp",
            "TMP": self.root / "temp",
            "CRISPASR_CACHE_DIR": self.root / "cache" / "crispasr",
        }.items():
            os.environ[key] = str(value)
        self.config_path = self.root / "config" / "settings.json"
        self.config = json.loads(self.config_path.read_text(encoding="utf-8-sig"))
        self.started = time.perf_counter()
        self.events = []
        self.translations = []
        self.errors = []
        self.audio_devices = []
        self.gpu_lines = []
        self.asr_ready = threading.Event()
        self.self_test = "--self-test" in sys.argv
        self.log_path = self.root / "logs" / "live-subtitle.log"
        if self.log_path.exists() and self.log_path.stat().st_size > 8388608:
            previous = self.root / "logs" / "live-subtitle.previous.log"
            previous.unlink(missing_ok=True)
            self.log_path.rename(previous)
        descriptor = os.open(self.log_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND)
        os.dup2(descriptor, 1)
        os.dup2(descriptor, 2)
        os.close(descriptor)
        sys.stdout = open(1, "w", encoding="utf-8", buffering=1, closefd=False)
        sys.stderr = open(2, "w", encoding="utf-8", buffering=1, closefd=False)
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", stream=sys.stdout, force=True)
        logging.info("Live Subtitle Tool v2.1 + portable integration 1.0; root=%s; PID=%s", self.root, os.getpid())
        self.select_gpu()

    def select_gpu(self) -> None:
        """Select the configured GPU by name rather than assuming an index."""
        command = [str(self.root / "CrispASR" / "crispasr.exe"), "--diagnostics"]
        environment = dict(os.environ)
        environment.pop("GGML_VK_VISIBLE_DEVICES", None)
        result = subprocess.run(command, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=30, env=environment)
        output = (result.stdout + result.stderr).decode("utf-8", errors="replace")
        (self.root / "logs" / "gpu-selection.log").write_text(output, encoding="utf-8")
        preferred = self.config["gpu_name"]
        devices = re.findall(r"ggml_vulkan:\s*(\d+)\s*=\s*(.+?)\s*\(", output)
        matching = [index for index, name in devices if preferred.lower() in name.lower()]
        if not matching:
            raise RuntimeError(f"Required Vulkan GPU not found: {preferred}. See logs/gpu-selection.log")
        self.gpu_index = int(matching[0])
        os.environ["GGML_VK_VISIBLE_DEVICES"] = str(self.gpu_index)
        logging.info("GPU backend: Vulkan; physical device=%s; selected GPU=%s", self.gpu_index, preferred)

    def record_error(self, message: str) -> None:
        """Preserve failures for diagnostics and validation."""
        self.errors.append(message)
        logging.error(message)

    def save_config(self) -> None:
        """Save relative model paths and user preferences without registry state."""
        self.config_path.write_text(json.dumps(self.config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


class PortableWorker(UPSTREAM.SubtitleWorker):
    """Reuse the upstream overlay signals with the current CrispASR contract."""

    def __init__(self, audio_queue: queue.Queue, crisp_exe_path: str, runtime: PortableRuntime) -> None:
        super().__init__(audio_queue, crisp_exe_path)
        self.runtime = runtime
        self.converter = opencc.OpenCC("t2s")
        self.translation_context = deque(maxlen=runtime.config["translation_context_sentences"])
        self.finalized_ids = set()
        self.current_id = None
        self.partial_translation = ""
        self.last_partial_translation_time = 0.0
        self.last_translated_partial = ""
        self.stop_requested = threading.Event()

    def load_llm_model(self) -> None:
        """Load all translation layers on the selected Vulkan device once."""
        if self.llm_model is not None:
            return
        model_path = Path(self.llm_path)
        if not model_path.is_file():
            raise FileNotFoundError(str(model_path))
        config = self.runtime.config
        logging.info("LLM loading: %s; gpu_layers=all; context=%s; batch=%s", model_path.name, config["llm_context"], config["llm_batch"])
        if not llama_cpp.llama_supports_gpu_offload():
            raise RuntimeError("Bundled llama.cpp does not support GPU offload")
        self.llm_model = Llama(
            model_path=str(model_path), n_ctx=config["llm_context"], n_batch=config["llm_batch"],
            n_gpu_layers=-1, main_gpu=0, split_mode=llama_cpp.LLAMA_SPLIT_MODE_NONE,
            n_threads=config["threads"], n_threads_batch=config["threads"], verbose=True,
        )
        logging.info("LLM initialized: %s", model_path.name)

    def translate_text(self, text: str, final: bool = False) -> str:
        """Use the model author's context prompt without a system message."""
        if not self.target_lang or not self.llm_model or not text.strip():
            return ""
        target = self.target_lang
        prompt = f"Translate the following text into {target}. Note that you should only output the translated result without any additional explanation:\n{text}"
        if self.translation_context:
            background = "\n".join(f"{source}\n{translation}" for source, translation in self.translation_context)
            prompt = f"[Background Information]\n{background}\nPlease translate the following text into {target}, taking the provided background information into consideration. Only output the translation of the Source Text.\n[Source Text]\n{text}"
        started = time.perf_counter()
        with self.llm_lock:
            output = self.llm_model.create_chat_completion(
                messages=[{"role": "user", "content": prompt}], max_tokens=self.runtime.config["translation_max_tokens"],
                temperature=float(self.runtime.config.get("translation_temperature", 0.1)), top_p=0.6, top_k=20, repeat_penalty=1.05,
            )
        translated = output["choices"][0]["message"]["content"] or ""
        translated = re.sub(r"<think>.*?</think>", "", translated, flags=re.DOTALL).strip()
        if "Simplified Chinese" in target:
            translated = self.converter.convert(translated)
        elapsed = time.perf_counter() - started
        logging.info("Translation %.3fs: %s -> %s", elapsed, text, translated)
        self.runtime.translations.append({"text": text, "translation": translated, "seconds": round(elapsed, 3), "final": final})
        if final:
            self.translation_context.append((text, translated))
        return translated

    def _build_display_list(self) -> list:
        """Render committed utterances and one replaceable draft."""
        result = list(self.history_buffer)
        if self.current_partial_text:
            result.append([self.current_partial_text, self.partial_translation])
        return result[-self.max_history:]

    def _read_stdout_loop(self) -> None:
        """Treat final.text as authoritative and deduplicate by utterance ID."""
        try:
            while self.running and self.process is not None:
                line = self.process.stdout.readline()
                if not line:
                    break
                try:
                    event = json.loads(line.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    logging.info("ASR stdout: %s", line.decode("utf-8", errors="replace").strip())
                    continue
                self.runtime.events.append(dict(event, received_seconds=round(time.perf_counter() - self.runtime.started, 3)))
                event_type = event.get("type", event.get("event", "partial"))
                text = str(event.get("text", "")).strip()
                utterance_id = event.get("utterance_id")
                if event_type == "silence" or not text or utterance_id in self.finalized_ids:
                    continue
                if event_type == "final":
                    translated = self.translate_text(text, final=True)
                    self.history_buffer.append([text, translated])
                    self.history_buffer = self.history_buffer[-self.max_history:]
                    self.finalized_ids.add(utterance_id)
                    self.current_partial_text = ""
                    self.partial_translation = ""
                    self.last_translated_partial = ""
                    logging.info("ASR final [%s]: %s", utterance_id, text)
                elif event_type == "partial":
                    self.current_id = utterance_id
                    self.current_partial_text = text
                    now = time.perf_counter()
                    interval = self.runtime.config["partial_translation_interval_ms"] / 1000
                    if text != self.last_translated_partial and now - self.last_partial_translation_time >= interval:
                        self.partial_translation = self.translate_text(text)
                        self.last_translated_partial = text
                        self.last_partial_translation_time = now
                    logging.info("ASR partial [%s]: %s", utterance_id, text)
                self.new_subtitle_signal.emit(self._build_display_list())
        except Exception as error:
            self.runtime.record_error(f"Stream output error: {error}")
            self.error_signal.emit(str(error))

    def _read_stderr_loop(self) -> None:
        """Expose backend initialization and GPU allocations in the log."""
        while self.process is not None:
            line = self.process.stderr.readline()
            if not line:
                break
            message = line.decode("utf-8", errors="replace").strip()
            logging.info("CrispASR: %s", message)
            if any(word in message.lower() for word in ("vulkan", "gpu", "buffer size")):
                self.runtime.gpu_lines.append(message)
            if "stream" in message.lower() and any(word in message.lower() for word in ("reading", "mode", "stdin", "initialized")):
                self.runtime.asr_ready.set()

    def run(self) -> None:
        """Keep one ASR process and one LLM instance for the whole session."""
        self.stop_requested.clear()
        self.finalized_ids.clear()
        self.translation_context.clear()
        self.runtime.asr_ready.clear()
        try:
            self.load_llm_model()
            config = self.runtime.config
            command = [
                self.crisp_exe_path, "-m", str(Path(self.asr_model_path).resolve()),
                "--gpu-backend", "vulkan", "-dev", "0", "--verbose",
                "--stream", "--stream-json", "--stream-step", str(config["stream_step_ms"]),
                "--stream-length", str(config["stream_context_ms"]),
                "--stream-final-on-silence-ms", str(config["final_silence_ms"]),
                "--stream-final-mode", "redecode", "--stream-utterance-max-sec", "20",
                "--vad", "--vad-model", "webrtc", "--require-vad",
                "-t", str(config["threads"]), "-l", self.src_lang or "auto",
                "--cache-dir", str(self.runtime.root / "cache" / "crispasr"),
            ]
            logging.info("ASR command: %s", subprocess.list2cmdline(command))
            self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                            cwd=Path(self.crisp_exe_path).parent, creationflags=subprocess.CREATE_NO_WINDOW, bufsize=0)
            self.running = True
            self.stdout_thread = threading.Thread(target=self._read_stdout_loop, daemon=True)
            self.stderr_thread = threading.Thread(target=self._read_stderr_loop, daemon=True)
            self.stdout_thread.start()
            self.stderr_thread.start()
            last_audio_time = time.perf_counter()
            while not self.stop_requested.is_set() and self.process.poll() is None:
                try:
                    samples = self.audio_queue.get(timeout=0.2)
                    last_audio_time = time.perf_counter()
                except queue.Empty:
                    # WASAPI can stop callbacks when the render endpoint becomes idle.
                    if time.perf_counter() - last_audio_time < 0.5:
                        continue
                    samples = np.zeros(3200, dtype=np.float32)
                self.process.stdin.write((np.clip(samples, -1, 1) * 32767).astype(np.int16).tobytes())
                self.process.stdin.flush()
            if not self.stop_requested.is_set():
                raise RuntimeError(f"CrispASR exited unexpectedly ({self.process.returncode}). See logs/live-subtitle.log")
        except Exception as error:
            if not self.stop_requested.is_set():
                self.runtime.record_error(f"ASR initialization/stream error: {error}")
                self.error_signal.emit(str(error))
        finally:
            self.running = False
            if self.process is not None and self.process.poll() is None:
                self.process.terminate()
                self.process.wait(timeout=10)

    def stop(self) -> None:
        """Wait for the child process and stream threads before shutdown."""
        self.stop_requested.set()
        process = self.process
        if process is not None and process.poll() is None:
            process.terminate()
        self.wait(15000)
        if process is not None and process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        for thread in (self.stdout_thread, self.stderr_thread):
            if thread is not None and thread is not threading.current_thread():
                thread.join(timeout=3)
        if process is not None:
            for pipe in (process.stdin, process.stdout, process.stderr):
                if pipe is not None:
                    pipe.close()
        self.process = None
        self.running = False
        self.history_buffer.clear()
        self.current_partial_text = ""
        logging.info("ASR stopped; child process reaped")


class PortableRecorder(UPSTREAM.AudioRecorder):
    """Capture only WASAPI loopback with continuous sample-rate conversion."""

    def __init__(self, audio_queue: queue.Queue, runtime: PortableRuntime) -> None:
        super().__init__(audio_queue, sample_rate=16000, chunk_duration=0.2)
        self.runtime = runtime
        self.selected_name = runtime.config["audio_device"]
        self.device_name = ""
        self.input_buffer = np.zeros(0, dtype=np.float32)
        self.position = 0.0
        self.peak = 0.0
        self.dropped_chunks = 0

    @staticmethod
    def enumerate_devices() -> list:
        """Refresh PortAudio's view so Windows device changes are visible."""
        with pyaudio.PyAudio() as interface:
            return list(interface.get_loopback_device_info_generator())

    def _get_loopback_device(self) -> dict:
        """Resolve the current default or the explicitly selected loopback."""
        if self.selected_name == "default":
            return self.p.get_default_wasapi_loopback()
        matching = [device for device in self.p.get_loopback_device_info_generator() if device["name"] == self.selected_name]
        if not matching:
            raise RuntimeError(f"Selected WASAPI output unavailable: {self.selected_name}")
        return matching[0]

    def start(self) -> bool:
        """Open the speaker's native format and resample to 16 kHz mono."""
        self.p = pyaudio.PyAudio()
        device = self._get_loopback_device()
        self.device_name = device["name"]
        channels = device["maxInputChannels"]
        rate = int(device["defaultSampleRate"])
        self.buffer = np.zeros(0, dtype=np.float32)
        self.input_buffer = np.zeros(0, dtype=np.float32)
        self.position = 0.0
        self.recording = True
        logging.info("Audio: WASAPI Loopback; name=%s; index=%s; channels=%s; native_rate=%s", self.device_name, device["index"], channels, rate)
        self.runtime.audio_devices.append({"name": self.device_name, "index": device["index"], "channels": channels, "sample_rate": rate})

        def callback(in_data: bytes, frame_count: int, time_info: dict, status: int) -> tuple:
            if not self.recording:
                return None, pyaudio.paComplete
            samples = np.frombuffer(in_data, dtype=np.int16).astype(np.float32) / 32768
            samples = samples.reshape(-1, channels).mean(axis=1)
            self.peak = max(self.peak, float(np.max(np.abs(samples)))) if len(samples) else self.peak
            self.input_buffer = np.concatenate((self.input_buffer, samples))
            positions = np.arange(self.position, len(self.input_buffer) - 1, rate / 16000)
            if len(positions):
                converted = np.interp(positions, np.arange(len(self.input_buffer)), self.input_buffer).astype(np.float32)
                next_position = positions[-1] + rate / 16000
                consumed = min(int(next_position), len(self.input_buffer) - 1)
                self.position = next_position - consumed
                self.input_buffer = self.input_buffer[consumed:]
                self.buffer = np.concatenate((self.buffer, converted))
            while len(self.buffer) >= self.chunk_size:
                chunk = self.buffer[:self.chunk_size]
                self.buffer = self.buffer[self.chunk_size:]
                try:
                    self.audio_queue.put_nowait(chunk)
                except queue.Full:
                    self.dropped_chunks += 1
            return None, pyaudio.paContinue

        self.stream = self.p.open(format=pyaudio.paInt16, channels=channels, rate=rate, input=True,
                                  input_device_index=device["index"], frames_per_buffer=max(512, rate // 20), stream_callback=callback)
        return True


class PortableWindow(UPSTREAM.SubtitleWindow):
    """Keep the upstream overlay and add portable preferences and device controls."""

    def __init__(self, runtime: PortableRuntime) -> None:
        self.runtime = runtime
        super().__init__()
        self.worker.deleteLater()
        self.audio_queue = queue.Queue(maxsize=150)
        self.crisp_exe_path = str(runtime.root / "CrispASR" / "crispasr.exe")
        self.worker = PortableWorker(self.audio_queue, self.crisp_exe_path, runtime)
        self.worker.new_subtitle_signal.connect(self.update_subtitles)
        self.worker.error_signal.connect(self.on_worker_error)
        self.recorder = PortableRecorder(self.audio_queue, runtime)
        self.cb_src.setCurrentText(runtime.config["source_language"])
        self.cb_target.setCurrentText(runtime.config["target_language"])
        self.chk_trans_only.setChecked(False)
        self.sp_lines.setValue(3)
        self.sp_font_size.setValue(23)
        self.resize(1120, 300)
        self.setWindowTitle("Live Subtitle Tool v2.1 Portable Vulkan")
        controls = QHBoxLayout()
        controls.addWidget(QLabel("System audio:"))
        self.cb_audio = QComboBox()
        self.cb_audio.setMinimumWidth(480)
        self.cb_audio.setStyleSheet(self.cb_src.styleSheet())
        controls.addWidget(self.cb_audio, 1)
        refresh = QPushButton("Refresh outputs")
        refresh.setStyleSheet("QPushButton { color: white; background: #2b5c8f; border-radius: 3px; padding: 3px 8px; }")
        refresh.clicked.connect(self.refresh_devices)
        controls.addWidget(refresh)
        self.panel.layout().insertLayout(1, controls)
        self.refresh_devices()
        self.cb_audio.currentIndexChanged.connect(self.change_audio_device)
        self.device_timer = QTimer(self)
        self.device_timer.timeout.connect(self.check_default_device)
        self.device_timer.start(3000)
        if runtime.config.get("autostart", True):
            QTimer.singleShot(200, self.toggle_captioning)
        if runtime.self_test:
            self.test_timer = QTimer(self)
            self.test_timer.timeout.connect(self.test_tick)
            self.test_timer.start(1000)
            self.test_played = False
            self.test_play_time = 0.0
            self.test_audio_switched = False
            self.test_audio_restored = False

    def auto_find_models(self) -> tuple:
        """Select exact configured filenames without renaming GGUFs."""
        return str(self.runtime.root / self.runtime.config["asr_model"]), str(self.runtime.root / self.runtime.config["translation_model"])

    def refresh_devices(self) -> None:
        """Offer all current WASAPI loopback outputs by name."""
        self.cb_audio.blockSignals(True)
        self.cb_audio.clear()
        self.cb_audio.addItem("Windows default playback device (automatic)", "default")
        for device in PortableRecorder.enumerate_devices():
            self.cb_audio.addItem(device["name"], device["name"])
        index = self.cb_audio.findData(self.recorder.selected_name)
        self.cb_audio.setCurrentIndex(max(0, index))
        self.cb_audio.blockSignals(False)

    def change_audio_device(self) -> None:
        """Switch capture without reloading GPU models."""
        self.recorder.selected_name = self.cb_audio.currentData()
        self.runtime.config["audio_device"] = self.recorder.selected_name
        self.runtime.save_config()
        if self.recorder.recording:
            self.restart_capture()

    def restart_capture(self) -> None:
        """Discard queued samples from the previous output device."""
        self.recorder.stop()
        while not self.audio_queue.empty():
            self.audio_queue.get_nowait()
        try:
            self.recorder.start()
        except Exception as error:
            self.runtime.record_error(f"Audio switch failed: {error}")
            self.text_display.setPlainText(str(error))

    def check_default_device(self) -> None:
        """Follow Windows default output changes without polling the microphone."""
        if not self.recorder.recording or self.recorder.selected_name != "default":
            return
        try:
            with pyaudio.PyAudio() as interface:
                name = interface.get_default_wasapi_loopback()["name"]
            if name != self.recorder.device_name:
                self.restart_capture()
                self.refresh_devices()
        except (OSError, RuntimeError):
            logging.exception("Default playback device refresh failed")

    def update_subtitles(self, subtitles_list: list) -> None:
        """Escape recognized text before passing it to the upstream HTML view."""
        super().update_subtitles([[html.escape(source), html.escape(translation)] for source, translation in subtitles_list])

    def on_worker_error(self, message: str) -> None:
        """Show initialization failures without falling back to CPU."""
        self.runtime.record_error(message)
        self.recorder.stop()
        self.worker.stop()
        self.btn_toggle.setText("Start")
        self.btn_toggle.setEnabled(True)
        self.text_display.setPlainText(message)

    def test_tick(self) -> None:
        """Play an English sample through the real default system output."""
        elapsed = time.perf_counter() - self.runtime.started
        if not self.test_played and self.runtime.asr_ready.is_set():
            sample = self.runtime.root / "app" / "test-audio.wav"
            if not sample.is_file():
                self.runtime.record_error("Self-test audio sample missing")
                self.close()
                return
            while not self.audio_queue.empty():
                self.audio_queue.get_nowait()
            logging.info("SELF-TEST: playing English sample through Windows default playback")
            player = os.environ.get("LIVE_SUBTITLE_TEST_PLAYER")
            if player:
                video = self.runtime.root / "app" / "test-video.mp4"
                subprocess.Popen([player, "-autoexit", "-loglevel", "error", "-window_title", "Live Subtitle English video test", str(video)],
                                 creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                ctypes.windll.winmm.PlaySoundW(str(sample), None, 0x00020000 | 0x0001 | 0x0002)
            self.test_played = True
            self.test_play_time = time.perf_counter()
        if self.test_played and time.perf_counter() - self.test_play_time > 25 and not self.test_audio_switched:
            alternate = next((index for index in range(1, self.cb_audio.count()) if self.cb_audio.itemData(index) != self.recorder.device_name), 1)
            if self.cb_audio.count() > 1:
                self.cb_audio.setCurrentIndex(alternate)
            self.test_audio_switched = True
            logging.info("SELF-TEST: audio selector switched; ASR PID=%s", self.worker.process.pid if self.worker.process else None)
        if self.test_played and time.perf_counter() - self.test_play_time > 28 and not self.test_audio_restored:
            self.cb_audio.setCurrentIndex(0)
            self.test_audio_restored = True
            logging.info("SELF-TEST: default audio restored; ASR PID=%s", self.worker.process.pid if self.worker.process else None)
        if self.test_played and time.perf_counter() - self.test_play_time > 45:
            self.grab().save(str(self.runtime.root / "logs" / "subtitle-test.png"))
            self.close()
        elif not self.test_played and elapsed > 150:
            self.runtime.record_error("Self-test timed out waiting for ASR initialization")
            self.close()

    def closeEvent(self, event: object) -> None:
        """Save local settings and wait for all model/capture resources."""
        self.device_timer.stop()
        if self.runtime.self_test:
            self.test_timer.stop()
        self.runtime.config["source_language"] = self.cb_src.currentText()
        self.runtime.config["target_language"] = self.cb_target.currentText()
        self.runtime.save_config()
        self.recorder.stop()
        self.worker.stop()
        if self.worker.llm_model is not None:
            self.worker.llm_model.close()
            self.worker.llm_model = None
        report = {
            "root": str(self.runtime.root), "gpu_name": self.runtime.config["gpu_name"], "physical_gpu_index": self.runtime.gpu_index,
            "backend": "vulkan", "audio_devices": self.runtime.audio_devices, "audio_peak": self.recorder.peak,
            "dropped_audio_chunks": self.recorder.dropped_chunks, "events": self.runtime.events,
            "translations": self.runtime.translations, "gpu_log_lines": self.runtime.gpu_lines,
            "errors": self.runtime.errors, "child_process_closed": self.worker.process is None,
        }
        name = "validation.json" if self.runtime.self_test else "last-session.json"
        (self.runtime.root / "logs" / name).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        logging.info("Shutdown complete; validation=%s", name)
        event.accept()


def main() -> int:
    """Start the official overlay using its bundled runtime and native libraries."""
    runtime = PortableRuntime()
    missing = [runtime.config[key] for key in ("asr_model", "translation_model")
               if not (runtime.root / runtime.config[key]).is_file()]
    if missing:
        message = "Place the following GGUF files in the models folder, then restart:\n\n" + "\n".join(missing)
        logging.error(message)
        ctypes.windll.user32.MessageBoxW(None, message, "Live Subtitle - models required", 0x30)
        return 2
    UPSTREAM.TRANS_LANG_MAP["Simplified Chinese"] = "Simplified Chinese"
    application = QApplication(sys.argv)
    window = PortableWindow(runtime)
    window.show()
    return application.exec()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        ctypes.windll.user32.MessageBoxW(None, "Startup failed. Open logs/live-subtitle.log and logs/gpu-selection.log.", "Live Subtitle Portable", 0x10)
        sys.exit(1)
