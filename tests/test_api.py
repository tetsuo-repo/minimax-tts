"""Unit tests for the MiniMax HTTP client (no Home Assistant required)."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest

from minimax_tts.api import (
    MiniMaxAuthError,
    MiniMaxClient,
    MiniMaxError,
    MiniMaxRateLimitError,
    MiniMaxVoice,
)


class _FakeResp:
    """Stands in for an aiohttp response used as an async context manager."""

    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    async def __aenter__(self) -> "_FakeResp":
        return self

    async def __aexit__(self, *exc: object) -> bool:
        return False

    status = 200

    def raise_for_status(self) -> None:
        return None

    async def text(self) -> str:
        return json.dumps(self._payload)

    async def json(self, content_type: Any = None) -> dict[str, Any]:
        return self._payload


class _FakeSession:
    """Captures the request and returns a canned payload."""

    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload
        self.calls: list[dict[str, Any]] = []

    def post(self, url: str, headers: Any = None, json: Any = None) -> _FakeResp:
        self.calls.append({"url": url, "headers": headers, "json": json})
        return _FakeResp(self._payload)


def _client(payload: dict[str, Any], **kwargs: Any) -> tuple[MiniMaxClient, _FakeSession]:
    session = _FakeSession(payload)
    client = MiniMaxClient(session, "secret-token", "https://api.minimax.io", **kwargs)
    return client, session


def test_synthesize_decodes_hex_audio() -> None:
    payload = {
        "data": {"audio": "deadbeef", "status": 2},
        "base_resp": {"status_code": 0, "status_msg": "success"},
    }
    client, _ = _client(payload)
    fmt, audio = asyncio.run(
        client.synthesize("hi", "Wise_Woman", "speech-2.6-turbo")
    )
    assert fmt == "mp3"
    assert audio == bytes.fromhex("deadbeef")


def test_synthesize_builds_request_body_and_groupid() -> None:
    payload = {
        "data": {"audio": "00", "status": 2},
        "base_resp": {"status_code": 0},
    }
    client, session = _client(payload, group_id="12345")
    asyncio.run(
        client.synthesize(
            "hello",
            "Calm_Woman",
            "speech-2.8-hd",
            speed=1.5,
            audio_format="wav",
            sample_rate=16000,
            language_boost="English",
        )
    )
    call = session.calls[0]
    assert call["url"].endswith("/v1/t2a_v2?GroupId=12345")
    assert call["headers"]["Authorization"] == "Bearer secret-token"
    body = call["json"]
    assert body["text"] == "hello"
    assert body["model"] == "speech-2.8-hd"
    assert body["language_boost"] == "English"
    assert body["voice_setting"] == {"voice_id": "Calm_Woman", "speed": 1.5}
    assert body["audio_setting"]["format"] == "wav"
    assert body["audio_setting"]["sample_rate"] == 16000


def test_synthesize_missing_audio_raises() -> None:
    payload = {"data": {"status": 1}, "base_resp": {"status_code": 0}}
    client, _ = _client(payload)
    with pytest.raises(MiniMaxError):
        asyncio.run(client.synthesize("hi", "v", "speech-2.6-turbo"))


@pytest.mark.parametrize("code", [1004, 2049])
def test_auth_errors(code: int) -> None:
    payload = {"base_resp": {"status_code": code, "status_msg": "nope"}}
    client, _ = _client(payload)
    with pytest.raises(MiniMaxAuthError):
        asyncio.run(client.get_voices())


@pytest.mark.parametrize("code", [1002, 1039, 1041, 2045, 2056])
def test_rate_limit_errors(code: int) -> None:
    payload = {"base_resp": {"status_code": code, "status_msg": "slow down"}}
    client, _ = _client(payload)
    with pytest.raises(MiniMaxRateLimitError):
        asyncio.run(client.synthesize("hi", "v", "speech-2.6-turbo"))


def test_generic_error_for_unknown_code() -> None:
    payload = {"base_resp": {"status_code": 1024, "status_msg": "boom"}}
    client, _ = _client(payload)
    with pytest.raises(MiniMaxError) as excinfo:
        asyncio.run(client.get_voices())
    assert not isinstance(excinfo.value, (MiniMaxAuthError, MiniMaxRateLimitError))


def test_get_voices_parses_all_categories() -> None:
    payload = {
        "system_voice": [
            {"voice_id": "Wise_Woman", "voice_name": "Wise Woman"},
            {"voice_id": "", "voice_name": "skip-me"},
        ],
        "voice_cloning": [{"voice_id": "clone-1"}],
        "voice_generation": [{"voice_id": "gen-1", "voice_name": "Generated"}],
        "base_resp": {"status_code": 0},
    }
    client, _ = _client(payload)
    voices = asyncio.run(client.get_voices())
    assert MiniMaxVoice("Wise_Woman", "Wise Woman") in voices
    assert MiniMaxVoice("clone-1", "clone-1") in voices  # name falls back to id
    assert MiniMaxVoice("gen-1", "Generated") in voices
    assert all(v.voice_id for v in voices)  # the empty id was skipped
    assert len(voices) == 3
