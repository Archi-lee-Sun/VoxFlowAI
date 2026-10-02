"""Launch the VoxFlow AI desktop assistant."""

import os
import logging
import sys
import tempfile

from PySide6.QtCore import QObject, QThread, QTimer, QUrl, Qt, Signal, Slot
from PySide6.QtGui import QColor, QFont
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QMainWindow, QPushButton,
    QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from audio_recorder import AudioRecorder

logger = logging.getLogger(__name__)


class MicButton(QPushButton):
    """A simple drawn microphone control with a clear listening halo."""

    def __init__(self):
        super().__init__("")
        self.setObjectName("micButton")
        self.setFixedSize(106, 106)
        self.setAccessibleName("Start recording")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def paintEvent(self, event):
        super().paintEvent(event)
        from PySide6.QtGui import QPainter, QPen
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        active = bool(self.property("recording"))
        ink = QColor("#261d17" if not active else "#2a1717")
        painter.setPen(QPen(ink, 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                            Qt.PenJoinStyle.RoundJoin))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        cx, cy = self.width() / 2, self.height() / 2
        painter.drawRoundedRect(int(cx - 11), int(cy - 25), 22, 39, 11, 11)
        painter.drawArc(int(cx - 21), int(cy - 12), 42, 34, 190 * 16, 160 * 16)
        painter.drawLine(int(cx), int(cy + 22), int(cx), int(cy + 31))
        painter.drawLine(int(cx - 11), int(cy + 31), int(cx + 11), int(cy + 31))
        painter.end()


class ProcessWorker(QObject):
    succeeded = Signal(object)
    failed = Signal(str)
    finished = Signal()

    def __init__(self, audio_path):
        super().__init__()
        self.audio_path = audio_path

    @Slot()
    def run(self):
        try:
            from app import process_audio
            self.succeeded.emit(process_audio(self.audio_path))
        except Exception as exc:
            logger.exception("process_audio failed for recording %s", self.audio_path)
            self.failed.emit(str(exc) or "The assistant could not process that recording.")
        finally:
            try:
                os.unlink(self.audio_path)
            except OSError:
                pass
            self.finished.emit()


class AssistantWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VoxFlow AI")
        self.setMinimumSize(720, 680)
        self.resize(920, 800)
        self.recorder = AudioRecorder()
        self.recorder.errorOccurred.connect(self._recorder_error)
        self.is_recording = False
        self.busy = False
        self.thread = None
        self.worker = None
        self.backend_audio_path = None
        self.close_when_finished = False
        self.playback_path = None

        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.player.playbackStateChanged.connect(self._playback_state_changed)
        self.player.errorOccurred.connect(self._playback_error)

        self._build_ui()
        self._apply_style()

    def _build_ui(self):
        root = QWidget()
        root.setObjectName("root")
        page = QVBoxLayout(root)
        page.setContentsMargins(54, 36, 54, 36)
        page.setSpacing(0)

        header = QHBoxLayout()
        brand = QLabel("V / F")
        brand.setObjectName("brandMark")
        title = QLabel("VOXFLOW <span>AI</span>")
        title.setObjectName("brandTitle")
        brandline = QVBoxLayout()
        brandline.setSpacing(2)
        brandline.addWidget(title)
        subtitle = QLabel("VOICE INTERFACE  /  FIELD 01")
        subtitle.setObjectName("eyebrow")
        brandline.addWidget(subtitle)
        header.addWidget(brand)
        header.addLayout(brandline)
        header.addStretch()
        self.ready_label = QLabel("●  SYSTEM READY")
        self.ready_label.setObjectName("ready")
        header.addWidget(self.ready_label, alignment=Qt.AlignmentFlag.AlignTop)
        page.addLayout(header)
        page.addSpacing(30)

        self.orbit = QFrame()
        self.orbit.setObjectName("orbit")
        orbit_layout = QVBoxLayout(self.orbit)
        orbit_layout.setContentsMargins(24, 32, 24, 30)
        orbit_layout.setSpacing(10)
        self.orb_title = QLabel("A quiet place to think.")
        self.orb_title.setObjectName("heroTitle")
        self.orb_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status = QLabel("Press the microphone and speak naturally")
        self.status.setObjectName("status")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        orbit_layout.addWidget(self.orb_title)
        orbit_layout.addWidget(self.status)
        orbit_layout.addStretch(1)
        mic_row = QHBoxLayout()
        mic_row.addStretch()
        self.mic = MicButton()
        self.mic.clicked.connect(self._toggle_recording)
        mic_row.addWidget(self.mic)
        mic_row.addStretch()
        orbit_layout.addLayout(mic_row)
        self.hint = QLabel("CLICK TO BEGIN  ·  CLICK AGAIN TO FINISH")
        self.hint.setObjectName("hint")
        self.hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        orbit_layout.addWidget(self.hint)
        orbit_layout.addStretch(1)
        page.addWidget(self.orbit, 1)
        page.addSpacing(22)

        response_header = QHBoxLayout()
        response_label = QLabel("CONVERSATION")
        response_label.setObjectName("sectionLabel")
        response_header.addWidget(response_label)
        response_header.addStretch()
        self.play_button = QPushButton("▶   PLAY RESPONSE")
        self.play_button.setObjectName("playButton")
        self.play_button.setVisible(False)
        self.play_button.clicked.connect(self._toggle_playback)
        response_header.addWidget(self.play_button)
        page.addLayout(response_header)
        page.addSpacing(12)

        self.transcript_panel = QFrame()
        self.transcript_panel.setObjectName("transcriptPanel")
        transcript_layout = QVBoxLayout(self.transcript_panel)
        transcript_layout.setContentsMargins(22, 18, 22, 20)
        transcript_layout.setSpacing(8)
        you_label = QLabel("YOU SAID")
        you_label.setObjectName("eyebrow")
        self.user_text = QLabel("Your words will appear here after a recording.")
        self.user_text.setObjectName("userText")
        self.user_text.setWordWrap(True)
        self.user_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        separator = QFrame()
        separator.setObjectName("separator")
        separator.setFixedHeight(1)
        answer_label = QLabel("VOXFLOW")
        answer_label.setObjectName("eyebrowAccent")
        self.response_text = QLabel("The response will find its way here.")
        self.response_text.setObjectName("responseText")
        self.response_text.setWordWrap(True)
        self.response_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        transcript_layout.addWidget(you_label)
        transcript_layout.addWidget(self.user_text)
        transcript_layout.addSpacing(6)
        transcript_layout.addWidget(separator)
        transcript_layout.addSpacing(8)
        transcript_layout.addWidget(answer_label)
        transcript_layout.addWidget(self.response_text)
        page.addWidget(self.transcript_panel)
        page.addSpacing(16)
        footer = QLabel("LOCAL MICROPHONE  ·  PRIVATE SESSION  ·  VOICE ASSISTANT")
        footer.setObjectName("footer")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        page.addWidget(footer)
        self.setCentralWidget(root)

    def _apply_style(self):
        self.setStyleSheet("""
            QWidget#root { background: #0b1018; color: #e9edf1; }
            QLabel { background: transparent; }
            QLabel#brandMark { color: #101720; background: #e5ad66; font-size: 13px;
                font-weight: 900; padding: 10px 9px; border-radius: 6px; }
            QLabel#brandTitle { color: #e8edf1; font-size: 18px; font-weight: 800; letter-spacing: 2px; }
            QLabel#brandTitle span { color: #65d2d1; }
            QLabel#eyebrow, QLabel#eyebrowAccent { color: #768593; font-size: 10px;
                font-weight: 700; letter-spacing: 1.5px; }
            QLabel#eyebrowAccent { color: #69d1ce; }
            QLabel#ready { color: #91b9a4; font-size: 10px; font-weight: 700; letter-spacing: 1px; }
            QFrame#orbit { border: 1px solid #263542; border-radius: 14px;
                background-color: #101923; }
            QLabel#heroTitle { color: #f1f0e9; font-size: 26px; font-weight: 600; }
            QLabel#status { color: #97a8b6; font-size: 14px; }
            QLabel#hint { color: #8798a4; font-size: 10px; font-weight: 700; letter-spacing: 1.4px; }
            QPushButton#micButton { color: #14202a; background: #e9b46f; border: 5px solid #574a3b;
                border-radius: 53px; font-size: 40px; font-weight: 500; }
            QPushButton#micButton:hover { background: #f2c789; border-color: #806646; }
            QPushButton#micButton:pressed { background: #d59c54; }
            QPushButton#micButton:focus { outline: 3px solid #70d9d7; }
            QPushButton#micButton[recording="true"] { background: #ef7f72; border-color: #6e4543; }
            QPushButton#playButton { color: #84d8d4; background: #14232b; border: 1px solid #2a565b;
                border-radius: 6px; padding: 8px 12px; font-size: 10px; font-weight: 700; }
            QPushButton#playButton:hover { background: #1c343d; }
            QPushButton#playButton:focus { outline: 2px solid #70d9d7; }
            QLabel#sectionLabel { color: #c4cdd4; font-size: 11px; font-weight: 800; letter-spacing: 1.8px; }
            QFrame#transcriptPanel { background: #111922; border: 1px solid #25313c; border-radius: 10px; }
            QLabel#userText { color: #c7d0d7; font-size: 15px; }
            QLabel#responseText { color: #f0eee8; font-size: 16px; }
            QFrame#separator { background: #293540; border: 0; }
            QLabel#footer { color: #596875; font-size: 9px; letter-spacing: 1px; }
        """)

    def _set_state(self, state, detail=None):
        if state == "listening":
            self.status.setText("Listening · your microphone is active")
            self.orb_title.setText("I’m here. Take your time.")
            self.hint.setText("CLICK TO FINISH RECORDING")
            self.ready_label.setText("●  LISTENING")
            self.mic.setProperty("recording", True)
            self.mic.setAccessibleName("Stop recording")
        elif state == "processing":
            self.status.setText("Transcribing and preparing a response…")
            self.orb_title.setText("Finding the right words.")
            self.hint.setText("PROCESSING YOUR REQUEST")
            self.ready_label.setText("●  WORKING")
            self.mic.setProperty("recording", False)
            self.mic.setAccessibleName("Recording in progress")
        elif state == "error":
            self.status.setText(detail or "Something went wrong. Please try again.")
            self.orb_title.setText("Let’s try that again.")
            self.hint.setText("PRESS THE MICROPHONE TO RETRY")
            self.ready_label.setText("●  NEEDS ATTENTION")
            self.mic.setProperty("recording", False)
            self.mic.setAccessibleName("Start recording")
        else:
            self.status.setText(detail or "Press the microphone and speak naturally")
            self.orb_title.setText("A quiet place to think.")
            self.hint.setText("CLICK TO BEGIN  ·  CLICK AGAIN TO FINISH")
            self.ready_label.setText("●  SYSTEM READY")
            self.mic.setProperty("recording", False)
            self.mic.setAccessibleName("Start recording")
        self.mic.style().unpolish(self.mic)
        self.mic.style().polish(self.mic)

    def _toggle_recording(self):
        if self.busy and not self.is_recording:
            return
        if not self.is_recording:
            try:
                self.recorder.start()
            except Exception as exc:
                self._set_state("error", str(exc))
                return
            self.is_recording = True
            self.busy = True
            self._set_state("listening")
            return

        self.is_recording = False
        try:
            self.recorder.stop()
        except Exception as exc:
            self.recorder.discard()
            self.busy = False
            self._set_state("error", str(exc))
            return
        self._set_state("processing")
        self._wait_for_recording_to_finish()

    def _wait_for_recording_to_finish(self, previous_size=None, stable_checks=0, attempts=0):
        if self.recorder.last_error:
            self.recorder.discard()
            self.busy = False
            self._set_state("error", self.recorder.last_error)
            return

        path = self.recorder.output_path
        size = os.path.getsize(path) if path and os.path.isfile(path) else 0
        if size > 0 and size == previous_size:
            stable_checks += 1
        else:
            stable_checks = 0

        if (
            stable_checks >= 2
            and self.recorder.is_finalized()
        ):
            try:
                audio_path = self.recorder.finish()
            except Exception as exc:
                self.busy = False
                self._set_state("error", str(exc))
                return
            self._run_backend(audio_path)
            return

        if attempts >= 40:
            self.recorder.discard()
            self.busy = False
            self._set_state("error", "Qt did not finish writing a valid WAV recording.")
            return

        QTimer.singleShot(
            50,
            lambda: self._wait_for_recording_to_finish(size, stable_checks, attempts + 1),
        )

    def _run_backend(self, audio_path):
        if self.thread is not None:
            logger.error("Ignoring duplicate backend start for recording %s", audio_path)
            return
        self.backend_audio_path = audio_path
        self.thread = QThread(self)
        self.worker = ProcessWorker(audio_path)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.succeeded.connect(self._show_result)
        self.worker.failed.connect(self._show_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self._worker_finished)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    @Slot(object)
    def _show_result(self, result):
        user_text = result.get("user_text") or "No speech was recognized."
        answer = result.get("response_text") or "No response was returned."
        self.user_text.setText(user_text)
        self.response_text.setText(answer)
        audio = result.get("audio")
        self.play_button.setVisible(bool(audio))
        if audio:
            self._save_playback(audio)
            self._set_state("ready", "Response ready · tap play to listen")
        else:
            self._set_state("ready", "Response ready · text only")

    def _save_playback(self, audio):
        self._remove_playback_file()
        handle, path = tempfile.mkstemp(prefix="voxflow-response-", suffix=".mp3")
        try:
            with os.fdopen(handle, "wb") as output:
                output.write(audio)
            self.playback_path = path
        except Exception:
            try:
                os.unlink(path)
            except OSError:
                pass
            self.play_button.setVisible(False)
            self._show_error("The response audio could not be saved for playback.")

    def _toggle_playback(self):
        if not self.playback_path:
            return
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.play_button.setText("▶   PLAY RESPONSE")
        else:
            self.player.setSource(QUrl.fromLocalFile(self.playback_path))
            self.player.play()
            self.play_button.setText("Ⅱ   PAUSE RESPONSE")

    def _playback_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.StoppedState:
            self.play_button.setText("▶   PLAY RESPONSE")

    def _playback_error(self, _error, _message):
        self.player.stop()
        self._set_state("error", "Response audio could not play. You can still read the text response.")
        self._remove_playback_file()
        self.play_button.setVisible(False)

    def _remove_playback_file(self):
        if self.playback_path:
            try:
                os.unlink(self.playback_path)
            except OSError:
                pass
            self.playback_path = None

    @Slot(str)
    def _show_error(self, message):
        self.play_button.setVisible(False)
        self._set_state("error", f"Could not complete that request: {message}")

    @Slot(str)
    def _recorder_error(self, message):
        self.is_recording = False
        self.busy = False
        self.recorder.discard()
        self._set_state("error", message)

    def _worker_finished(self):
        self.busy = False
        self.thread = None
        self.worker = None
        self.backend_audio_path = None
        if self.close_when_finished:
            self.close()

    def closeEvent(self, event):
        if self.thread is not None and self.thread.isRunning():
            self.close_when_finished = True
            self.status.setText("Finishing the current request before closing…")
            event.ignore()
            return
        if self.is_recording:
            self.recorder.discard()
            self.is_recording = False
        self.player.stop()
        self._remove_playback_file()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("VoxFlow AI")
    app.setFont(QFont("Segoe UI", 10))
    window = AssistantWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
