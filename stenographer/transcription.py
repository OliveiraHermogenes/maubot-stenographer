from typing import Type

import aiohttp
import mautrix.crypto.attachments
from maubot import Plugin, MessageEvent
from maubot.handlers import command, event
from mautrix.client import Client as MatrixClient
from mautrix.types import MessageType, EventType, GenericEvent, MediaMessageEventContent, EncryptedFile

from mautrix.util.config import BaseProxyConfig

from .config import Config

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
    config: Config

    async def start(self) -> None:
        self.config.load_and_update()

    @event.on(EventType.ALL)
    async def should_respond(self, evt: GenericEvent) -> None:
        """Respond to events when appropriate."""

        match evt.type:
            case EventType.REACTION:
                # Check whether the reaction should trigger a response
                if evt.content.relates_to.key == self.config['reaction']:
                    reacted_event = await evt.client.get_event(evt.room_id, evt.content.relates_to.event_id)
                    self.log.debug("Reaction detected. Transcribing parent event %s.", reacted_event.event_id)
                    await self.transcribe_audio_message(reacted_event)
                else:
                    return
            case EventType.ROOM_MESSAGE: 
                # Check whether messages should be automatically sent for transcription.
                # The `transcribe_audio_message` function will ignore anything that's not an audio message.
                if  self.config['auto']:
                    await self.transcribe_audio_message(evt)
                else:
                    return
            case _:
                return
            
    async def transcribe_audio_message(self, evt: MessageEvent) -> None:
        """
        Reply to voice message with its transcription.
        """
        # Consider only voice messages
        if evt.content.msgtype != MessageType.AUDIO:
            self.log.debug("Event %s is not an audio message. Ignoring.", evt.event_id)
            return

        content: MediaMessageEventContent = evt.content
        self.log.debug("A voice message was detected.")

        if content.url:  # content.url exists. media is not encrypted
            data = await download_unencrypted_media(content.url, evt.client)
        elif content.file:  # content.file exists. media is encrypted
            data = await download_encrypted_media(content.file, evt.client)
        else:
            self.log.warning("A message with type audio was detected, but no media was found.")
            return

        # POST endpoint
        api_endpoint = self.config['base_url'] + '/audio/transcriptions'

        # Header for API KEY
        self.http.headers["Authorization"] = "Bearer " + self.config['api_key']

        # initialize data for the POST request
        request_data = aiohttp.FormData()


        request_data.add_field(
            'file',
            data,
            content_type=content.info.mimetype
            )

        request_data.add_field('model', self.config['model_name'])
        
        if self.config['language'] != 'auto':
            request_data.add_field('language', self.config['language'])

        # send audio for transcription
        response = await self.http.post(api_endpoint, data=request_data)

        response_json = await response.json()
        transc = str(response_json["text"])
        
        self.log.debug(F"Message transcribed: {transc}")

        # send transcription as reply
        await evt.reply(transc)
        self.log.debug("Reply sent")

    @classmethod
    def get_config_class(cls) -> Type[BaseProxyConfig]:
        return Config
