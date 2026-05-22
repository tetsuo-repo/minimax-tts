"""The MiniMax TTS integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MiniMaxClient
from .const import CONF_API_KEY, CONF_GROUP_ID, CONF_HOST, DEFAULT_HOST, HOSTS

PLATFORMS: list[Platform] = [Platform.TTS]

MiniMaxConfigEntry = ConfigEntry[MiniMaxClient]


async def async_setup_entry(hass: HomeAssistant, entry: MiniMaxConfigEntry) -> bool:
    """Set up MiniMax TTS from a config entry."""
    session = async_get_clientsession(hass)
    host = HOSTS.get(entry.data.get(CONF_HOST, DEFAULT_HOST), HOSTS[DEFAULT_HOST])
    entry.runtime_data = MiniMaxClient(
        session=session,
        api_key=entry.data[CONF_API_KEY],
        host=host,
        group_id=entry.data.get(CONF_GROUP_ID),
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: MiniMaxConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
