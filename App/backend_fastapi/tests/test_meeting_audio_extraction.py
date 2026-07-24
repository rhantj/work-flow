from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import patch

import pytest

from app.main import DocumentTextExtractionError, extract_audio_text, extract_uploaded_text


@dataclass
class FakeSegment:
    text: str


class FakeWhisperModel:
    def __init__(self, segments: list[FakeSegment]):
        self._segments = segments
        self.transcribe_calls: list[tuple[bytes, str]] = []

    def transcribe(self, audio, language=None, **kwargs):
        self.transcribe_calls.append((audio.read(), language))
        return iter(self._segments), object()


@pytest.mark.parametrize("file_name", ["meeting.mp3", "meeting.wav", "meeting.m4a", "meeting.ogg"])
def test_extract_uploaded_text_routes_audio_extensions_to_whisper(file_name):
    with patch("app.main.extract_audio_text", return_value="회의 내용 전사 결과") as mock_extract_audio:
        result = extract_uploaded_text(b"fake-audio-bytes", file_name)

    mock_extract_audio.assert_called_once_with(b"fake-audio-bytes")
    assert result == "회의 내용 전사 결과"


def test_extract_audio_text_joins_and_strips_segment_text():
    fake_model = FakeWhisperModel([FakeSegment(" 안녕하세요 "), FakeSegment("오늘 회의를 시작합니다.")])
    with patch("app.main.get_whisper_model", return_value=fake_model):
        result = extract_audio_text(b"fake-audio-bytes")

    assert result == "안녕하세요 오늘 회의를 시작합니다."
    assert fake_model.transcribe_calls == [(b"fake-audio-bytes", "ko")]


def test_extract_audio_text_raises_when_transcription_is_empty():
    fake_model = FakeWhisperModel([FakeSegment("   "), FakeSegment("")])
    with patch("app.main.get_whisper_model", return_value=fake_model):
        with pytest.raises(DocumentTextExtractionError):
            extract_audio_text(b"fake-audio-bytes")


def test_extract_audio_text_wraps_missing_dependency_as_extraction_error():
    with patch("app.main.get_whisper_model", side_effect=ImportError("faster_whisper missing")):
        with pytest.raises(DocumentTextExtractionError):
            extract_audio_text(b"fake-audio-bytes")


def test_extract_audio_text_wraps_unexpected_errors_as_extraction_error():
    with patch("app.main.get_whisper_model", side_effect=RuntimeError("decode failed")):
        with pytest.raises(DocumentTextExtractionError):
            extract_audio_text(b"fake-audio-bytes")
