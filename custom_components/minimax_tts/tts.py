"""Text-to-speech platform for MiniMax."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.tts import TextToSpeechEntity, Voice
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import MiniMaxConfigEntry
from .api import MiniMaxError, MiniMaxVoice
from .const import (
    CONF_FORMAT,
    CONF_LANGUAGE_BOOST,
    CONF_MODEL,
    CONF_SAMPLE_RATE,
    CONF_SPEED,
    CONF_VOICE,
    DEFAULT_FORMAT,
    DEFAULT_LANGUAGE,
    DEFAULT_LANGUAGE_BOOST,
    DEFAULT_MODEL,
    DEFAULT_SAMPLE_RATE,
    DEFAULT_SPEED,
    DOMAIN,
    SUPPORTED_LANGUAGES,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MiniMaxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the MiniMax TTS entity from a config entry."""
    client = entry.runtime_data
    try:
        voices = await client.get_voices()
    except MiniMaxError as err:
        _LOGGER.debug("Could not fetch MiniMax voices at setup: %s", err)
        voices = []
    async_add_entities([MiniMaxTTSEntity(entry, voices)])


class MiniMaxTTSEntity(TextToSpeechEntity):
    """A MiniMax cloud text-to-speech engine."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_languages = SUPPORTED_LANGUAGES
    _attr_default_language = DEFAULT_LANGUAGE
    _attr_supported_options = [CONF_VOICE, CONF_MODEL, CONF_SPEED]

    def __init__(
        self, entry: MiniMaxConfigEntry, voices: list[MiniMaxVoice]
    ) -> None:
        self._entry = entry
        self._client = entry.runtime_data
        self._voices = voices
        self._attr_unique_id = entry.entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="MiniMax TTS",
            manufacturer="MiniMax",
            entry_type=DeviceEntryType.SERVICE,
        )

    @callback
    def async_get_supported_voices(self, language: str) -> list[Voice] | None:
        """Expose the account's voices to the UI (language-independent)."""
        if not self._voices:
            return None
        return [Voice(voice_id=v.voice_id, name=v.name) for v in self._voices]

    async def async_get_tts_audio(
        self, message: str, language: str, options: dict[str, Any]
    ) -> tuple[str | None, bytes | None]:
        """Synthesise speech, resolving per-call options over entry defaults."""
        opts = self._entry.options
        voice = options.get(CONF_VOICE) or opts.get(CONF_VOICE)
        model = options.get(CONF_MODEL) or opts.get(CONF_MODEL, DEFAULT_MODEL)
        speed = options.get(CONF_SPEED) or opts.get(CONF_SPEED, DEFAULT_SPEED)
        audio_format = opts.get(CONF_FORMAT, DEFAULT_FORMAT)
        sample_rate = opts.get(CONF_SAMPLE_RATE, DEFAULT_SAMPLE_RATE)
        language_boost = opts.get(CONF_LANGUAGE_BOOST, DEFAULT_LANGUAGE_BOOST)

        if not voice:
            raise HomeAssistantError("No MiniMax voice configured")

        try:
            return await self._client.synthesize(
                message,
                voice,
                model,
                speed=float(speed),
                audio_format=audio_format,
                sample_rate=int(sample_rate),
                language_boost=language_boost,
            )
        except MiniMaxError as err:
            raise HomeAssistantError(f"MiniMax TTS failed: {err}") from err
