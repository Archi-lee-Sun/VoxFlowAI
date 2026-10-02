"""Record microphone input to a temporary WAV file with Qt Multimedia."""

import logging
import os
import tempfile
import wave

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtMultimedia import (
    QAudioInput,
    QMediaCaptureSession,
    QMediaDevices,
    QMediaFormat,
    QMediaRecorder,
)


logger = logging.getLogger(__name__)


class AudioRecorder(QObject):
    """Capture one mono WAV recording from the default microphone."""

    errorOccurred = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.session = QMediaCaptureSession(self)
        self.audio_input = QAudioInput(self)
        self.recorder = QMediaRecorder(self)
        self.recorder.errorOccurred.connect(self._handle_error)
        self.session.setAudioInput(self.audio_input)
        self.session.setRecorder(self.recorder)
        self.output_path = None
        self.last_error = None
        self.stop_requested = False

    def _handle_error(self, error, error_string):
        self.last_error = error_string or str(error)
        message = f"Qt recorder error {error}: {self.last_error}"
        logger.error(message)
        self.errorOccurred.emit(message)

    def start(self):
        recorder_active = (
            self.recorder.recorderState()
            != QMediaRecorder.RecorderState.StoppedState
        )
        if self.output_path is not None or recorder_active:
            raise RuntimeError("A recording is already active or being finalized.")

        device = QMediaDevices.defaultAudioInput()
        if device.isNull():
            raise RuntimeError("No microphone is available. Connect a microphone and try again.")

        self.last_error = None
        self.stop_requested = False
        self.audio_input.setDevice(device)

        media_format = QMediaFormat(QMediaFormat.FileFormat.Wave)
        media_format.setAudioCodec(QMediaFormat.AudioCodec.Wave)
        if not media_format.isSupported(QMediaFormat.ConversionMode.Encode):
            raise RuntimeError("Qt's multimedia backend does not support WAV recording.")

        self.recorder.setMediaFormat(media_format)
        self.recorder.setAudioSampleRate(16000)
        self.recorder.setAudioChannelCount(1)

        handle, path = tempfile.mkstemp(prefix="voxflow-recording-", suffix=".wav")
        os.close(handle)
        os.unlink(path)
        self.output_path = path
        self.recorder.setOutputLocation(QUrl.fromLocalFile(path))
        self.recorder.record()

        if self.recorder.error() != QMediaRecorder.Error.NoError:
            self.discard()
            raise RuntimeError(self.last_error or self.recorder.errorString())

        if self.recorder.recorderState() != QMediaRecorder.RecorderState.RecordingState:
            self.discard()
            raise RuntimeError("Qt did not enter the recording state.")

    def stop(self):
        if self.output_path is None or self.stop_requested:
            raise RuntimeError("Recording is not active.")

        self.stop_requested = True
        self.recorder.stop()
        return self.output_path

    def finish(self):
        if self.output_path is None or not self.stop_requested:
            raise RuntimeError("There is no recording to finish.")
        path = self.output_path
        if self.last_error:
            self.discard()
            raise RuntimeError(self.last_error)
        if not self.is_finalized():
            raise RuntimeError("Qt is still finalizing the recording.")

        self.output_path = None
        self.stop_requested = False
        return path

    def is_finalized(self):
        """Return true only after Qt stops and the WAV header contains audio frames."""
        if (
            self.output_path is None
            or not self.stop_requested
            or self.recorder.recorderState() != QMediaRecorder.RecorderState.StoppedState
        ):
            return False
        if self.last_error or not os.path.isfile(self.output_path):
            return False
        try:
            if os.path.getsize(self.output_path) == 0:
                return False
            with wave.open(self.output_path, "rb") as audio_file:
                return audio_file.getnframes() > 0
        except (wave.Error, EOFError, OSError):
            # Qt may still be flushing the WAV header after its state changes.
            return False

    def discard(self):
        if (
            not self.stop_requested
            and self.recorder.recorderState() != QMediaRecorder.RecorderState.StoppedState
        ):
            self.recorder.stop()
        if self.output_path and os.path.exists(self.output_path):
            try:
                os.unlink(self.output_path)
            except OSError:
                logger.exception("Could not remove incomplete recording: %s", self.output_path)
        self.output_path = None
        self.stop_requested = False
