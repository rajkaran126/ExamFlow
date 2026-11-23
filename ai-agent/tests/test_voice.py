
"""Automated tests for EXAMFLOW AI voice services."""

from app.voice.voice_service import voice_service


def test_transcribe_rejects_empty_audio():
    result = voice_service.transcribe_audio(b"")

    assert result["status"] == "error"
    assert result["text"] == ""
    assert result["confidence"] == 0.0


def test_transcribe_rejects_corrupted_short_audio():
    result = voice_service.transcribe_audio(b"\x00" * 50)

    assert result["status"] == "error"
    assert "corrupted" in result["error"].lower()


def test_transcribe_rejects_unsupported_mime_type():
    result = voice_service.transcribe_audio(
        b"\x00" * 300,
        mime_type="application/pdf",
    )

    assert result["status"] == "error"
    assert "unsupported" in result["error"].lower()


def test_transcribe_does_not_fake_success_without_provider():
    result = voice_service.transcribe_audio(
        b"\x00" * 300,
        mime_type="audio/webm",
    )

    assert result["status"] == "unavailable"
    assert result["text"] == ""
    assert result["confidence"] == 0.0
    assert result["provider_configured"] is False
    assert "not configured" in result["error"].lower()


def test_synthesize_cleans_markdown():
    text = (
        "### Investigation Report\n"
        "Candidate **CAND-1001** has raw score `85.5` | Qualified."
    )

    result = voice_service.synthesize_speech(text)

    assert result["status"] == "ready"
    assert "###" not in result["speakable_text"]
    assert "**" not in result["speakable_text"]
    assert "`" not in result["speakable_text"]
    assert "|" not in result["speakable_text"]
    assert "CAND-1001" in result["speakable_text"]


def test_synthesize_rejects_empty_text():
    result = voice_service.synthesize_speech("   ")

    assert result["status"] == "error"
    assert result["speakable_text"] == ""


def test_synthesize_truncates_long_text():
    long_text = "EXAMFLOW investigation finding. " * 50

    result = voice_service.synthesize_speech(long_text)

    assert result["status"] == "ready"
    assert result["truncated"] is True
    assert len(result["speakable_text"]) < len(long_text)
    assert "complete detailed breakdown" in result["speakable_text"]


def test_synthesize_declares_frontend_playback_ownership():
    result = voice_service.synthesize_speech(
        "The examination report is ready."
    )

    assert result["status"] == "ready"
    assert result["playback_owner"] == "frontend"
    assert result["audio_generated"] is False
