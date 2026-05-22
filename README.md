# MiniMax TTS for Home Assistant

A custom integration that adds [MiniMax](https://platform.minimax.io) cloud
**text-to-speech** as an engine for Home Assistant's Assist voice pipeline.
Configured entirely from the UI: paste your Personal Access Token and pick a
voice — the voice list is pulled live from your MiniMax account.

> **Speech-to-text?** MiniMax has **no** speech-to-text / ASR API, and its chat
> models (including MiniMax-M2.7) are text-only and cannot transcribe audio. So
> this integration is **TTS-only**. For voice *input*, pair it with Home
> Assistant's free, local [Whisper (faster-whisper)](https://www.home-assistant.io/integrations/wyoming/)
> add-on — the standard combination. MiniMax handles the spoken *replies*.

## Features

- Native Home Assistant `TextToSpeechEntity` — works anywhere TTS does
  (Assist, `tts.speak`, media players, automations).
- Voice dropdown populated from your account (system, cloned and generated
  voices), with free-text entry for voice IDs not yet listed.
- Selectable model (`speech-2.8-hd` … `speech-02-turbo`), speed, audio format,
  sample rate and language boost, changeable any time via the options dialog.
- International (`api.minimax.io`) and China (`api.minimaxi.com`) regions.

## Installation (HACS)

1. In HACS, open the three-dot menu → **Custom repositories**.
2. Add `https://github.com/tetsuo-repo/minimax-tts` with category
   **Integration**.
3. Install **MiniMax TTS**, then restart Home Assistant.

<details>
<summary>Manual installation</summary>

Copy `custom_components/minimax_tts` into your Home Assistant
`config/custom_components/` directory and restart.
</details>

## Configuration

1. **Settings → Devices & Services → Add Integration → MiniMax TTS.**
2. Enter your **Personal Access Token** (create one at
   <https://platform.minimax.io> → Account → API Keys), choose your **region**,
   and optionally a **Group ID**. The token is validated immediately by
   fetching your voices.
3. Pick a **default voice** and **model**.

Change the voice, model, speed, format, sample rate or language boost later via
the integration's **Configure** button — the engine reloads automatically.

### Using it

Pick **MiniMax TTS** as the text-to-speech engine in your Assist pipeline
(*Settings → Voice assistants*), or call it directly:

```yaml
action: tts.speak
target:
  entity_id: tts.minimax_tts
data:
  media_player_entity_id: media_player.living_room
  message: "Hello from MiniMax."
  options:
    voice: Wise_Woman      # optional, overrides the configured default
```

## Notes & limitations

- The API key and region are **region-bound** and must match, or MiniMax
  rejects the key.
- MiniMax bills per character; this integration makes one synchronous request
  per spoken message.
- Some accounts require the **Group ID** for certain endpoints — set it in the
  config if voice listing or synthesis fails with an auth error despite a valid
  token.

## Development

See [CLAUDE.md](CLAUDE.md) for architecture and commands. Run the unit tests
with:

```bash
pip install -r requirements_test.txt
python -m pytest tests/ -q
```

## License

[MIT](LICENSE). Not affiliated with MiniMax or Home Assistant.
