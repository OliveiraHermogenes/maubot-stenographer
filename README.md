# maubot-stenographer
A simple plugin for [maubot](https://mau.bot/) that automatically transcribes voice messages by sending them to an API compatible with [OpenAI's](https://platform.openai.com/docs/api-reference). Inspired by [mau_local_stt](https://github.com/ElishaAz/mau_local_stt). However, this plugin does not perform any transcriptions on its own. It relies on a backend serving a compatible API. 

## Setup
[OpenAI's official python library](https://pypi.org/project/openai/) is used to send requests to the backend API. But you can host a compatible server yourself ([LocalAI](https://localai.io/features/audio-to-text/), [faster-whisper-server](https://github.com/fedirz/faster-whisper-server) etc.), preferably in a resorceful machine.

1. Run `pip install openai` inside maubot's environment (python venv, some container or whatever)
2. Clone the repository and [build the plugin](https://docs.mau.fi/maubot/usage/cli/build.html)
3. [Upload the plugin, create a client and an instance](https://docs.mau.fi/maubot/usage/basic.html)
4. Configure the instance with the necessary fields

## Usage
Simply invite the bot to a room and it's going to automatically reply to voice messages with transcriptions.

## Roadmap

- a command to toggle on/off automatic transcriptions on a per room basis
- a command to trigger transcription of a voice message with a command reply and/or emoji reaction
- a command to set the default language on a per room basis
