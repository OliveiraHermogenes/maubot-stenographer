from typing import Tuple, Type, Optional, Any

import mautrix.crypto.attachments
from maubot import Plugin, MessageEvent
from maubot.handlers import command, event, web
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
    return mautrix.crypto.attachments.decrypt_attachment(await client.download_media(file.url), file.key.key,
                                                         file.hashes['sha256'], file.iv)


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialize variables
        self.model = None
        self.key = None
        self.language = None
        self.url = None

    allowed_msgtypes: Tuple[MessageType, ...] = (MessageType.AUDIO,)

    def on_config_update(self) -> None:
        """
        Called by `Config` when the configuration is updated
        """
        if OPENAI_INSTALLED:
            self.url = self.config['base_url']
            self.model = self.config['model_name']
            self.key = self.config['api_key']
            self.language = self.config['language']
        else:  # openai library is not installed
            self.log.error("The plugin needs OpenAI's offical library in order to send requests to the API. (pip install openai)")

    async def pre_start(self) -> None:
        """
        Called before the handlers are initialized
        :return:
        """
        # Make Config call self.on_config_update whenever the config is updated.
        self.config.set_on_update(self.on_config_update)
        # Load the config. This will call self.on_config_update, which will load the model.
        self.config.load_and_update()

    async def stop(self) -> None:
        self.model = None
        self.key = None
        self.language = None
        self.url = None        

    @command.passive("", msgtypes=(MessageType.AUDIO,))
    async def transcribe_audio_message(self, evt: MessageEvent, match: Tuple[str]) -> None:
        """
        Replies to any voice message with its transcription.
        """
        # Make sure that the message type is audio
        if evt.content.msgtype != MessageType.AUDIO:
            return

        content: MediaMessageEventContent = evt.content
        self.log.debug(F"Message received. MimeType: {content.info.mimetype}")

        if content.url:  # content.url exists. File is not encrypted
            data = await download_unencrypted_media(content.url, evt.client)
        elif content.file:  # content.file exists. File is encrypted
            data = await download_encrypted_media(content.file, evt.client)
        else:  # shouldn't happen
            self.log.warning("A message with AUDIO message type received, but it does not contain a file.")
            return

        # initialize the client
        client = AsyncOpenAI(base_url=self.url, api_key=self.key)

        # send audio for transcription
        if self.language == 'auto':
            transc = await client.audio.transcriptions.create(file=data, model=self.model, response_format="text")
        else:
            transc = await client.audio.transcriptions.create(file=data, model=self.model, language=self.language, response_format="text")

        self.log.debug(F"Message transcribed: {transc}")

        # send transcription as reply
        await evt.reply(transc)
        self.log.debug("Reply sent")

    @classmethod
    def get_config_class(cls) -> Type[BaseProxyConfig]:
        return Config
