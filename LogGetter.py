#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
import asyncio
import os
import sqlite3
import sys
import time

import discord

from classes import Logger


class LogGetter(discord.Client):
    def __init__(self, config):
        super().__init__()
        self.logger = Logger.Logger()
        self.config = config
        if not (os.path.exists("data")):
            os.makedirs("data")
        self.db = sqlite3.connect('data/database.db')

    def run(self, *args, **kwargs):
        try:
            self.loop.run_until_complete(self.start(*args, **kwargs))
        except KeyboardInterrupt:
            self.loop.run_until_complete(self.logout())
            pending = asyncio.Task.all_tasks()
            gathered = asyncio.gather(*pending)
            try:
                gathered.cancel()
                self.loop.run_until_complete(gathered)
                gathered.exception()
            except:
                pass

    async def on_ready(self):
        await self.get_server_messages()
        await self.logout()

    async def get_members_from_server(self, server):
        cursor = self.db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS 'members_%s'(
                id INTEGER PRIMARY KEY ON CONFLICT REPLACE UNIQUE,
                name VALUE,
                nick VALUE,
                discriminator VALUE
            )
            """ % str(server.id)
        )

        members = []
        for member in server.members:
            members.append((
                member.id,
                member.name,
                member.nick,
                member.discriminator
            ))

        cursor.executemany("""
            INSERT INTO 'members_%s'(
                id, name, nick, discriminator
            )
            VALUES(?, ?, ?, ?)
            """ % server.id, members)
        self.db.commit()

    async def get_logs_from_channel(self, channel, cfg):
        print("\t{} ({})".format(channel.name, channel.id))

        cursor = self.db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS 'log_%s-%s'(
                id INTEGER PRIMARY KEY ON CONFLICT REPLACE UNIQUE,
                author_id INT,
                time INTEGER,
                content VALUE
            )
            """ % (str(cfg["id"]), channel.id))

        try:
            cursor.execute("select MAX(time) from 'log_%s-%s';" % (str(cfg["id"]), channel.id))
            last_message_timestamp = cursor.fetchone()[0]
            assert last_message_timestamp > 1431468000
            last_message_datetime = datetime.fromtimestamp(last_message_timestamp - 10)
        except:
            last_message_datetime = None

        log_buffer = []
        async for item in self.logs_from(channel, limit=sys.maxsize, after=last_message_datetime):
            log_buffer.append((
                item.id,
                item.author.id,
                int(time.mktime(item.timestamp.timetuple())),
                item.content
            ))
            if (len(log_buffer) % 1000 == 0):
                print("\t\t%d" % len(log_buffer))

        cursor.executemany("""
            INSERT INTO 'log_%s-%s'(
                id, author_id, time, content
            )
            VALUES(?, ?, ?, ?)
            """ % (str(cfg["id"]), channel.id), log_buffer)
        self.db.commit()

        cursor.execute("select count(*) from 'log_%s-%s'" % (str(cfg["id"]), channel.id))
        msg_count = cursor.fetchone()[0]

        # Make the header
        header = "Server name: " + cfg["name"] + "\n"
        header += "Server ID: " + str(cfg["id"]) + "\n"
        header += "Channel name: " + channel.name + "\n"
        header += "Channel ID: " + channel.id + "\n"
        header += channel.created_at.strftime("Created at: %A %d %b %Y %H:%M:%S UTC\n")
        header += "Length: %d messages\n\n" % msg_count

        self.summary.append({
            "Server name": cfg["name"],
            "Server ID": str(cfg["id"]),
            "Channel name": channel.name,
            "Channel ID": str(channel.id),
            "Length": msg_count
        })

        print("\t\t%d" % msg_count)

    # Launch the getter when the bot is ready
    async def get_server_messages(self):
        self.summary = []

        print("Sucessfully connected as %s (%s)\n" % (self.user.name, self.user.id))
        self.logger.logger.info("Sucessfully connected as %s (%s)" % (self.user.name, self.user.id))
        self.logger.logger.info("------------")

        await self.change_presence(game=discord.Game(name="Getting logs..."))
        for cfg in self.config["servers"]:
            for server in self.servers:
                if server.id == str(cfg["id"]):
                    print("{} ({})".format(server.name, server.id))
                    await self.get_members_from_server(server)
                    for channel in server.channels:
                        if (channel.type != discord.ChannelType.voice and
                            ("channels" not in cfg or
                             channel.id in [str(i["id"]) for i in cfg["channels"]])):
                            try:
                                await self.get_logs_from_channel(channel, cfg)
                            except discord.errors.Forbidden:
                                pass
                    print()

        print("Done.")
        self.logger.logger.info("Done.")
        self.logger.logger.info("#--------------END--------------#")
        return self.summary
