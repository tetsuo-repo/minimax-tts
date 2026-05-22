"""Async client for the MiniMax speech (T2A) API.

This module is the only place that performs HTTP against MiniMax. It is kept
free of any Home Assistant imports so it can be unit-tested in isolation.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import json
import logging
from typing import Any

import aiohttp

from .const import PATH_GET_VOICE, PATH_T2A, REQUEST_TIMEOUT

_LOGGER = logging.getLogger(__name__)

# MiniMax returns business errors inside the JSON body (base_resp), usually
# with HTTP 200. These codes get mapped to dedicated exceptions.
AUTH_STATUS_CODES: frozenset[int] = frozenset({1004, 2049})
RATE_LIMIT_STATUS_CODES: frozenset[int] = frozenset({1002, 1039, 1041, 2045, 2056})


@dataclass(frozen=True)
class MiniMaxVoice:
    """A voice available to the account (system, cloned or generated)."""

    voice_id: str
    name: str


class MiniMaxError(Exception):
    """Base error for MiniMax API failures."""


class MiniMaxAuthError(MiniMaxError):
    """Authentication failed (invalid token or token/region mismatch)."""


class MiniMaxRateLimitError(MiniMaxError):
    """The account hit a rate or quota limit."""


class MiniMaxClient:
    """Thin async wrapper around the MiniMax speech API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        api_key: str,
        host: str,
        group_id: str | None = None,
    ) -> None:
        """Initialise the client.

        ``host`` is the full base URL (e.g. ``https://api.minimax.io``).
        """
        self._session = session
        self._api_key = api_key
        self._host = host.rstrip("/")
        self._group_id = group_id or None

    def _url(self, path: str) -> str:
        url = f"{self._host}{path}"
        if self._group_id:
            url = f"{url}?GroupId={self._group_id}"
        return url

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        """POST JSON and return the parsed body, raising on any error."""
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                async with self._session.post(
                    self._url(path), headers=self._headers, json=payload
                ) as resp:
                    _LOGGER.debug("POST %s -> HTTP %s", path, resp.status)
                    resp.raise_for_status()
                    body = await resp.text()
        except TimeoutError as err:
            raise MiniMaxError("Timeout contacting MiniMax") from err
        except aiohttp.ClientResponseError as err:
            if err.status in (401, 403):
                raise MiniMaxAuthError(f"HTTP {err.status}") from err
            raise MiniMaxError(f"HTTP {err.status}: {err.message}") from err
        except aiohttp.ClientError as err:
            raise MiniMaxError(f"Connection error: {err}") from err

        try:
            data: dict[str, Any] = json.loads(body)
        except ValueError as err:
            raise MiniMaxError(f"Invalid (non-JSON) response from MiniMax: {body[:200]}") from err

        self._check_base_resp(data)
        return data

    @staticmethod
    def _check_base_resp(data: dict[str, Any]) -> None:
        """Raise a typed error if base_resp signals failure."""
        base = data.get("base_resp") or {}
        code = base.get("status_code", 0)
        if code == 0:
            return
        msg = base.get("status_msg", "unknown error")
        if code in AUTH_STATUS_CODES:
            raise MiniMaxAuthError(f"{code}: {msg}")
        if code in RATE_LIMIT_STATUS_CODES:
            raise MiniMaxRateLimitError(f"{code}: {msg}")
        raise MiniMaxError(f"{code}: {msg}")

    async def get_voices(self) -> list[MiniMaxVoice]:
        """Return all voices available to the account.

        Doubles as a credential check during the config flow: a bad token
        raises :class:`MiniMaxAuthError`.
        """
        data = await self._post(PATH_GET_VOICE, {"voice_type": "all"})
        voices: list[MiniMaxVoice] = []
        for key in ("system_voice", "voice_cloning", "voice_generation"):
            for item in data.get(key) or []:
                voice_id = item.get("voice_id")
                if not voice_id:
                    continue
                name = item.get("voice_name") or voice_id
                voices.append(MiniMaxVoice(voice_id=voice_id, name=name))
        return voices

    async def synthesize(
        self,
        text: str,
        voice_id: str,
        model: str,
        *,
        speed: float = 1.0,
        audio_format: str = "mp3",
        sample_rate: int = 32000,
        language_boost: str = "auto",
    ) -> tuple[str, bytes]:
        """Synthesise ``text`` and return ``(format, audio_bytes)``.

        MiniMax returns the audio as a hex-encoded string in ``data.audio``;
        it is decoded to raw bytes here.
        """
        payload: dict[str, Any] = {
            "model": model,
            "text": text,
            "stream": False,
            "output_format": "hex",
            "language_boost": language_boost,
            "voice_setting": {
                "voice_id": voice_id,
                "speed": speed,
            },
            "audio_setting": {
                "sample_rate": sample_rate,
                "format": audio_format,
                "channel": 1,
            },
        }
        _LOGGER.debug(
            "Synthesizing %d chars with voice=%s model=%s format=%s rate=%s",
            len(text), voice_id, model, audio_format, sample_rate,
        )
        data = await self._post(PATH_T2A, payload)
        audio_hex = (data.get("data") or {}).get("audio")
        if not audio_hex:
            raise MiniMaxError(
                f"MiniMax returned no audio data (extra_info={data.get('extra_info')})"
            )
        try:
            audio = bytes.fromhex(audio_hex)
        except ValueError as err:
            raise MiniMaxError("Failed to decode audio payload") from err
        _LOGGER.debug("Received %d bytes of %s audio", len(audio), audio_format)
        return audio_format, audio
