from typing import Type

import aiohttp
import mautrix.crypto.attachments
from maubot import Plugin, MessageEvent
from maubot.handlers import command, event
from mautrix.client import Client as MatrixClient
from mautrix.types import MessageType, EventType, GenericEvent, MediaMessageEventContent, EncryptedFile

from mautrix.util.config import BaseProxyConfig
from mautrix.util.async_db import UpgradeTable

from .config import Config
from .db import DB, upgrade_table

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
    db: DB

    async def start(self) -> None:
        self.config.load_and_update()
        self.db = DB(self.database)

    @event.on(EventType.ALL)
    async def should_respond(self, evt: GenericEvent) -> None:
        """Respond to events when appropriate."""

        match evt.type:
            case EventType.REACTION:
                # Check whether the reaction should trigger a response
                if evt.content.relates_to.key == self.config['reaction']:
                    reacted_event = await evt.client.get_event(evt.room_id, evt.content.relates_to.event_id)
                    # Check whether the reaction was to a voice message
                    if reacted_event.content.msgtype != MessageType.AUDIO:
                        self.log.debug("Event %s is not an audio message. Ignoring.", reacted_event.event_id)
                        return

                    self.log.debug("Reaction detected. Transcribing parent event %s.", reacted_event.event_id)
                    await self.transcribe_audio_message(reacted_event)
                else:
                    return
            case EventType.ROOM_MESSAGE:
                # Check whether it is a voice message
                if evt.content.msgtype != MessageType.AUDIO:
                    self.log.debug("Event %s is not an audio message. Ignoring.", evt.event_id)
                    return
                # Check whether voice messages should be automatically sent for transcription.
                custom_auto_setting = await self.db.get_auto(evt.room_id)
                if  custom_auto_setting != None:
                    if custom_auto_setting:
                        await self.transcribe_audio_message(evt)
                    else:
                        return
                elif self.config['auto']:
                    await self.transcribe_audio_message(evt)
            case _:
                return
            
    async def transcribe_audio_message(self, evt: MessageEvent) -> None:
        """
        Replies to voice message with its transcription.
        """

        content: MediaMessageEventContent = evt.content

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

        custom_language = await self.db.get_language(evt.room_id)

        if custom_language != None:
            language = self.config['language']
        else:
            language = custom_language

        if language != 'auto':
            request_data.add_field('language', self.config['language'])

        # send audio for transcription
        response = await self.http.post(api_endpoint, data=request_data)

        response_json = await response.json()
        transc = str(response_json["text"])
        
        self.log.debug(F"Message transcribed: {transc}")

        # send transcription as reply
        await evt.reply(transc)
        self.log.debug("Reply sent")

    @command.new(name='stgr', help='A stenographer to transcribe your voice messages.')
    async def stenographer(self, evt: MessageEvent) -> None:
        # we require a subcommand
        pass

    @stenographer.subcommand(name='transcribe', help='Trigger transcription of related voice message.')
    async def trigger_transciption(self, evt: MessageEvent) -> None:
        """Transcribe the voice message replied to."""
        if not evt.content.relates_to:
            await evt.reply("You need to reply to a voice message to transcribe it.")
            return

        replied_event = await evt.client.get_event(evt.room_id, evt.content.get_reply_to())

        if replied_event.content.msgtype != MessageType.AUDIO:
            await evt.reply("The replied-to message is not a voice message.")
            return

        await self.transcribe_audio_message(replied_event)

    @stenographer.subcommand(name='language', help='Set a custom language for this room.')
    @command.argument('language', 'ISO 639-1')
    async def set_language_for_room(self, evt: MessageEvent, language: str) -> None:
        """Store language preference for the room in the database."""
        self.log.debug("Setting custom language for room %s to %s", evt.room_id, language)
        await self.db.put_language(evt.room_id, language)

    @stenographer.subcommand(name='auto', help='Toggle automatic transcriptions for this room.')
    @command.argument('toggle', 'on / off')
    async def toggle_auto_transcription(self, evt: MessageEvent, toggle: str) -> None:
        """Store auto preference for the room in the database."""
        if toggle == 'on':
            await self.db.put_auto(evt.room_id, True)
        elif toggle == 'off':
            await self.db.put_auto(evt.room_id, False)

    @classmethod
    def get_config_class(cls) -> Type[BaseProxyConfig]:
        return Config

    @classmethod
    def get_db_upgrade_table(cls) -> UpgradeTable:
        return upgrade_table
