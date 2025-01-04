from typing import Type

import mautrix.crypto.attachments
from maubot import Plugin, MessageEvent
from maubot.handlers import command, event
from mautrix.client import Client as MatrixClient
from mautrix.types import MessageType, EventType, MediaMessageEventContent, EncryptedFile
from mautrix.util.config import BaseProxyConfig

from .config import Config

try:
    from openai import AsyncOpenAI
    OPENAI_INSTALLED = True
except ModuleNotFoundError:
    OPENAI_INSTALLED = False


async def download_encrypted_media(file: EncryptedFile, client: MatrixClient) -> bytes:
    """
    Download an encrypted media file
    :param file: The `EncryptedFile` instance, from MediaMessageEventContent.file.
    :param client: The Matrix client. Can be accessed via MessageEvent.client
    :return: The media file as bytes.
    """
    return mautrix.crypto.attachments.decrypt_attachment(
        await client.download_media(file.url),
        file.key.key,
        file.hashes['sha256'],
        file.iv
    )


async def download_unencrypted_media(url, client: MatrixClient) -> bytes:
    """
    Download an unencrypted media file
    :param url: The media file mxc url, from MediaMessageEventContent.url.
    :param client: The Matrix client. Can be accessed via MessageEvent.client
    :return: The media file as bytes.
    """
    return await client.download_media(url)


class Stenographer(Plugin):
    config: Config  # Set type for type hinting

    if not OPENAI_INSTALLED:
        self.log.error("The plugin needs OpenAI's offical library in order to send requests to the API. (pip install openai)")

    async def start(self) -> None:
        self.config.load_and_update()

    @event.on(EventType.ROOM_MESSAGE)
    async def transcribe_audio_message(self, evt: MessageEvent) -> None:
        """
        Replies to any voice message with its transcription.
        """
        # Only reply to voice messages
        if evt.content.msgtype != MessageType.AUDIO:
            return

        content: MediaMessageEventContent = evt.content
        self.log.debug("A voice message was received.")

        if content.url:  # content.url exists. media is not encrypted
            data = await download_unencrypted_media(content.url, evt.client)
        elif content.file:  # content.file exists. media is encrypted
            data = await download_encrypted_media(content.file, evt.client)
        else:
            self.log.warning("A message with type audio was received, but no media was found.")
            return

        # initialize the client
        client = AsyncOpenAI(base_url=self.config['base_url'], api_key=self.config['api_key'])

        # send audio for transcription
        if self.config['language'] == 'auto':
            transc = await client.audio.transcriptions.create(
                file=data,
                model=self.config['model_name'],
                response_format="text"
            )
        else:
            transc = await client.audio.transcriptions.create(
                file=data,
                model=self.config['model_name'],
                language=self.config['language'],
                response_format="text"
            )

        self.log.debug(F"Message transcribed: {transc}")

        # send transcription as reply
        await evt.reply(transc)
        self.log.debug("Reply sent")

    @classmethod
    def get_config_class(cls) -> Type[BaseProxyConfig]:
        return Config
