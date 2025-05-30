# maubot-stenographer

A simple [maubot](https://mau.bot) plugin for transcribing voice messages. Inspired by [mau_local_stt](https://github.com/ElishaAz/mau_local_stt). It needs access to an API compatible with [OpenAI's](https://platform.openai.com/docs/api-reference). You can host a compatible server yourself ([LocalAI](https://localai.io/features/audio-to-text/), [Speaches](https://github.com/speaches-ai/speaches), [Open-WebUI](https://docs.openwebui.com/getting-started/advanced-topics/env-configuration#whisper-speech-to-text-local) etc.), and share it's transcription services with other tools (e.g. [Nextcloud](https://github.com/nextcloud/integration_openai) or whatever).

## Setup

1. Grab the `mbp` plugin file from [releases](../../releases), or clone the repository and [build the plugin yourself](https://docs.mau.fi/maubot/usage/cli/build.html)
2. [Upload the plugin, create a client and an instance](https://docs.mau.fi/maubot/usage/basic.html)
3. Configure the instance with the necessary fields

## Usage

Simply invite the bot to a room and it's going to reply to voice messages. Transcriptions can be triggered either automatically or in response to a reaction.
