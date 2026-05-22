"""Config and options flow for MiniMax TTS."""

from __future__ import annotations

import hashlib
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import MiniMaxAuthError, MiniMaxClient, MiniMaxError, MiniMaxVoice
from .const import (
    AUDIO_FORMATS,
    CONF_API_KEY,
    CONF_FORMAT,
    CONF_GROUP_ID,
    CONF_HOST,
    CONF_LANGUAGE_BOOST,
    CONF_MODEL,
    CONF_SAMPLE_RATE,
    CONF_SPEED,
    CONF_VOICE,
    DEFAULT_FORMAT,
    DEFAULT_HOST,
    DEFAULT_LANGUAGE_BOOST,
    DEFAULT_MODEL,
    DEFAULT_SAMPLE_RATE,
    DEFAULT_SPEED,
    DOMAIN,
    FALLBACK_VOICES,
    HOSTS,
    MAX_SPEED,
    MIN_SPEED,
    MODELS,
    SAMPLE_RATES,
)


def _unique_id(user_input: dict[str, Any]) -> str:
    """Stable id per account so the same token can't be added twice."""
    raw = (
        f"{user_input[CONF_HOST]}:"
        f"{user_input.get(CONF_GROUP_ID, '')}:"
        f"{user_input[CONF_API_KEY]}"
    )
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _voice_options(voices: list[MiniMaxVoice]) -> list[SelectOptionDict]:
    """Build dropdown options, falling back to a small built-in list."""
    items = voices or [
        MiniMaxVoice(voice_id, name) for voice_id, name in FALLBACK_VOICES.items()
    ]
    return [
        SelectOptionDict(
            value=v.voice_id,
            label=v.voice_id if v.name == v.voice_id else f"{v.name} ({v.voice_id})",
        )
        for v in items
    ]


def _host_selector() -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(
            options=[SelectOptionDict(value=key, label=key) for key in HOSTS],
            mode=SelectSelectorMode.DROPDOWN,
            translation_key="host",
        )
    )


def _voice_selector(voices: list[MiniMaxVoice]) -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(
            options=_voice_options(voices),
            mode=SelectSelectorMode.DROPDOWN,
            custom_value=True,
            sort=True,
        )
    )


class MiniMaxConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial setup."""

    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
        self._voices: list[MiniMaxVoice] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Collect and validate credentials."""
        errors: dict[str, str] = {}
        if user_input is not None:
            client = MiniMaxClient(
                session=async_get_clientsession(self.hass),
                api_key=user_input[CONF_API_KEY],
                host=HOSTS[user_input[CONF_HOST]],
                group_id=user_input.get(CONF_GROUP_ID),
            )
            try:
                self._voices = await client.get_voices()
            except MiniMaxAuthError:
                errors["base"] = "invalid_auth"
            except MiniMaxError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(_unique_id(user_input))
                self._abort_if_unique_id_configured()
                self._data = {
                    CONF_API_KEY: user_input[CONF_API_KEY],
                    CONF_HOST: user_input[CONF_HOST],
                }
                if user_input.get(CONF_GROUP_ID):
                    self._data[CONF_GROUP_ID] = user_input[CONF_GROUP_ID]
                return await self.async_step_voice()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): str,
                    vol.Required(CONF_HOST, default=DEFAULT_HOST): _host_selector(),
                    vol.Optional(CONF_GROUP_ID): str,
                }
            ),
            errors=errors,
        )

    async def async_step_voice(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Pick the default voice and model."""
        if user_input is not None:
            return self.async_create_entry(
                title="MiniMax TTS",
                data=self._data,
                options={
                    CONF_VOICE: user_input[CONF_VOICE],
                    CONF_MODEL: user_input[CONF_MODEL],
                    CONF_SPEED: DEFAULT_SPEED,
                    CONF_FORMAT: DEFAULT_FORMAT,
                    CONF_SAMPLE_RATE: DEFAULT_SAMPLE_RATE,
                    CONF_LANGUAGE_BOOST: DEFAULT_LANGUAGE_BOOST,
                },
            )

        return self.async_show_form(
            step_id="voice",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_VOICE): _voice_selector(self._voices),
                    vol.Required(CONF_MODEL, default=DEFAULT_MODEL): vol.In(MODELS),
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> MiniMaxOptionsFlow:
        return MiniMaxOptionsFlow()


class MiniMaxOptionsFlow(OptionsFlowWithReload):
    """Let users change voice and audio settings; reloads on save."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        # Best-effort refresh of the account voice list for the dropdown.
        voices: list[MiniMaxVoice] = []
        try:
            client = MiniMaxClient(
                session=async_get_clientsession(self.hass),
                api_key=self.config_entry.data[CONF_API_KEY],
                host=HOSTS[self.config_entry.data.get(CONF_HOST, DEFAULT_HOST)],
                group_id=self.config_entry.data.get(CONF_GROUP_ID),
            )
            voices = await client.get_voices()
        except MiniMaxError:
            voices = []

        opts = self.config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_VOICE, default=opts.get(CONF_VOICE)
                    ): _voice_selector(voices),
                    vol.Required(
                        CONF_MODEL, default=opts.get(CONF_MODEL, DEFAULT_MODEL)
                    ): vol.In(MODELS),
                    vol.Required(
                        CONF_SPEED, default=opts.get(CONF_SPEED, DEFAULT_SPEED)
                    ): vol.All(vol.Coerce(float), vol.Range(min=MIN_SPEED, max=MAX_SPEED)),
                    vol.Required(
                        CONF_FORMAT, default=opts.get(CONF_FORMAT, DEFAULT_FORMAT)
                    ): vol.In(AUDIO_FORMATS),
                    vol.Required(
                        CONF_SAMPLE_RATE,
                        default=opts.get(CONF_SAMPLE_RATE, DEFAULT_SAMPLE_RATE),
                    ): vol.In(SAMPLE_RATES),
                    vol.Optional(
                        CONF_LANGUAGE_BOOST,
                        default=opts.get(CONF_LANGUAGE_BOOST, DEFAULT_LANGUAGE_BOOST),
                    ): str,
                }
            ),
        )
