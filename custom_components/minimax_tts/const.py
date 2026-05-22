"""Constants for the MiniMax TTS integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "minimax_tts"

# --- API hosts -------------------------------------------------------------
# The API key and host are region-bound and must match, otherwise MiniMax
# returns an "invalid api key" error.
HOST_INTERNATIONAL: Final = "https://api.minimax.io"
HOST_CHINA: Final = "https://api.minimaxi.com"
HOSTS: Final = {
    "international": HOST_INTERNATIONAL,
    "china": HOST_CHINA,
}
DEFAULT_HOST: Final = "international"

# --- Endpoints -------------------------------------------------------------
PATH_T2A: Final = "/v1/t2a_v2"
PATH_GET_VOICE: Final = "/v1/get_voice"

# --- Config / option keys --------------------------------------------------
CONF_API_KEY: Final = "api_key"
CONF_GROUP_ID: Final = "group_id"
CONF_HOST: Final = "host"
CONF_VOICE: Final = "voice"
CONF_MODEL: Final = "model"
CONF_SPEED: Final = "speed"
CONF_FORMAT: Final = "format"
CONF_SAMPLE_RATE: Final = "sample_rate"
CONF_LANGUAGE_BOOST: Final = "language_boost"

# --- Models ----------------------------------------------------------------
MODELS: Final = [
    "speech-2.8-hd",
    "speech-2.8-turbo",
    "speech-2.6-hd",
    "speech-2.6-turbo",
    "speech-02-hd",
    "speech-02-turbo",
]
DEFAULT_MODEL: Final = "speech-2.8-hd"

# --- Audio settings --------------------------------------------------------
AUDIO_FORMATS: Final = ["mp3", "wav", "flac", "pcm"]
DEFAULT_FORMAT: Final = "mp3"

SAMPLE_RATES: Final = [8000, 16000, 22050, 24000, 32000, 44100]
DEFAULT_SAMPLE_RATE: Final = 32000

DEFAULT_SPEED: Final = 1.0
MIN_SPEED: Final = 0.5
MAX_SPEED: Final = 2.0

DEFAULT_LANGUAGE_BOOST: Final = "auto"

# --- Networking ------------------------------------------------------------
REQUEST_TIMEOUT: Final = 60  # seconds

# --- Languages -------------------------------------------------------------
# Conversation languages MiniMax can synthesise. The chosen voice determines
# the accent; language_boost defaults to "auto" so MiniMax detects the text.
SUPPORTED_LANGUAGES: Final = [
    "en",
    "zh",
    "de",
    "es",
    "fr",
    "ru",
    "pt",
    "ar",
    "it",
    "ja",
    "ko",
    "id",
    "vi",
    "tr",
    "nl",
    "uk",
    "th",
    "pl",
    "ro",
    "el",
    "cs",
    "fi",
    "hi",
    "yue",
]
DEFAULT_LANGUAGE: Final = "en"

# Used only when /v1/get_voice returns nothing (e.g. a brand-new account).
# The user normally selects from their live account voice list instead.
FALLBACK_VOICES: Final = {
    "Wise_Woman": "Wise Woman",
    "Friendly_Person": "Friendly Person",
    "Deep_Voice_Man": "Deep Voice Man",
    "Calm_Woman": "Calm Woman",
    "Chinese (Mandarin)_News_Anchor": "Mandarin News Anchor",
    "Chinese (Mandarin)_Reliable_Executive": "Mandarin Reliable Executive",
}
