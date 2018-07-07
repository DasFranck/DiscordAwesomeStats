#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
import asyncio
import argparse
import os
import sys
import time

import discord
from peewee import fn
import yaml

from database import (Server, Channel, Member, Nick, Message, database)
from classes import Logger


class Getter(discord.Client):
    """
    """
    def __init__(self, config):
        super().__init__()
        self.logger = Logger.Logger()
        self.config = config
        self.database = database

        if 'timezone' not in self.config:
            self.config['timezone'] = 'UTC'

    async def on_ready(self):
        """
        Launch the getter when the bot is ready
        """
        print("Sucessfully connected as %s (%s)\n" % (self.user.name, self.user.id))
        self.logger.logger.info("Sucessfully connected as %s (%s)" % (self.user.name, self.user.id))
        self.logger.logger.info("------------")

        await self.get_data()
        await self.logout()

    async def get_metadata_from_server(self, server, config_server):
        """
        Get every channels, members and their nick from the server provided and write them to the database.
        """
        self.database.create_tables([Server, Channel, Member, Nick])

        nick_data = []
        members_data = []
        for member in server.members:
            members_data.append((
                member.id,
                member.name,
                member.discriminator
            ))
            if member.nick:
                nick_data.append((
                    member.id,
                    server.id,
                    member.nick
                ))

        channels_data = []
        for channel in server.channels:
            if (channel.type != discord.ChannelType.voice and
                ("channels" not in config_server or
                channel.id in [str(i["id"]) for i in config_server["channels"]])):
                channels_data.append((
                    channel.id,
                    channel.name,
                    channel.server.id
                ))

        channel_fields = [Channel.id, Channel.name, Channel.server]
        members_fields = [Member.id, Member.name, Member.discriminator]
        nick_fields = [Nick.member_id, Nick.server_id, Nick.nick]

        (Server.insert(id=server.id, name=server.name)).on_conflict_replace().execute()
        (Channel.insert_many(channels_data, fields=channel_fields)).on_conflict_replace().execute()
        for idx in range(0, len(members_data), 300):
            (Member.insert_many(members_data[idx:idx+300], fields=members_fields)).on_conflict_replace().execute()
        for idx in range(0, len(nick_data), 300):
            (Nick.insert_many(nick_data[idx:idx+300], fields=nick_fields)).on_conflict_replace().execute()

    async def get_messages_from_channel(self, channel, timezone):
        """
        Get messages from channel and write it into the sqlite database (data/database.db)
        """
        print("\t{} ({})".format(channel.name, channel.id))

        self.database.create_tables([Message])

        try:
            last_message_timestamp = Message.select(fn.MAX(Message.timestamp)).where(Message.channel_id == channel.id).scalar()
            assert last_message_timestamp and last_message_timestamp > 1431468000
            print("\t\tLast message:",last_message_timestamp)
            last_message_datetime = datetime.fromtimestamp(last_message_timestamp - 10)
        except AssertionError:
            last_message_datetime = None

        message_fields = [Message.id, Message.channel_id, Message.author_id, Message.timestamp]
        message_data = []
        message_count = 0
        print("\t\tLast message:",last_message_datetime)
        
        async for item in self.logs_from(channel, limit=sys.maxsize, after=last_message_datetime):
            message_data.append((
                item.id,
                channel.id,
                item.author.id,
                int(time.mktime(item.timestamp.timetuple())),
            ))
            if len(message_data) % 200 == 0:
                message_count += 200
                print("\t\t%d" % message_count)
                (Message.insert_many(message_data, fields=message_fields)).on_conflict_replace().execute()
                message_data = []

        if len(message_data):
            (Message.insert_many(message_data, fields=message_fields)).on_conflict_replace().execute()
            print("\t\t%d" % (message_count + len(message_data)))

    async def get_data(self):
        """
        Get:
        - Servers, channels, users and their nickname by calling self.get_metadata_from_server on each.
        - Messages by calling self.get_messages_from_channel on every marked chanel.
        """
        await self.change_presence(game=discord.Game(name="Getting logs..."))

        self.database.connect()
        for config_server in self.config["servers"]:
            server = discord.utils.get(self.servers, id=str(config_server["id"]))
            if server is None:
                print("{} was not found.\n".format(config_server["id"]))
                continue
            print("{} ({})".format(server.name, server.id))
            await self.get_metadata_from_server(server, config_server)

            for channel in server.channels:
                if (channel.type != discord.ChannelType.voice and
                    ("channels" not in config_server or
                    channel.id in [str(i["id"]) for i in config_server["channels"]])):
                    # Catch error if the bot have access to this channel
                    try:
                        await self.get_messages_from_channel(channel, self.config['timezone'])
                    except discord.errors.Forbidden:
                        print(f"\t\tACCESS FORBIDDEN")
                        pass
            print()
        self.database.close()
        
        print("Done.")
        self.logger.logger.info("Done.")
        self.logger.logger.info("#--------------END--------------#")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config_file", default="./config.yaml", help="Path to the config file")
    args = parser.parse_args()

    with open(args.config_file, 'r') as file:
        config = yaml.load(file)

    gt = Getter(config)
    gt.run(config["token"])

if __name__ == '__main__':
    main()