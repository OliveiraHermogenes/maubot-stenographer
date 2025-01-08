# maubot-stenographer

A simple plugin for [maubot](https://mau.bot) that automatically transcribes voice messages. Inspired by [mau_local_stt](https://github.com/ElishaAz/mau_local_stt). It needs access to an API compatible with [OpenAI's](https://platform.openai.com/docs/api-reference). You can host a compatible server yourself ([LocalAI](https://localai.io/features/audio-to-text/), [faster-whisper-server](https://github.com/fedirz/faster-whisper-server), [Open-WebUI](https://docs.openwebui.com/getting-started/advanced-topics/env-configuration#whisper-speech-to-text-local) etc.), and share it's transcription services with other tools (e.g. [Nextcloud](https://github.com/nextcloud/integration_openai) or whatever).

## Setup

1. Clone the repository and [build the plugin](https://docs.mau.fi/maubot/usage/cli/build.html)
2. [Upload the plugin, create a client and an instance](https://docs.mau.fi/maubot/usage/basic.html)
3. Configure the instance with the necessary fields

## Usage

Simply invite the bot to a room and it's going to automatically reply to voice messages with transcriptions.

## Roadmap

- ability to trigger transcription of a voice message with a command reply and/or emoji reaction
- ability to toggle on/off automatic transcriptions on a per room basis
- ability to set the default language on a per room basis
