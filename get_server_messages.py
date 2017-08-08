#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Setting up some strings globals
NAME = "DiscoLog"

import asyncio
import discord
import os
import sys
from datetime import timedelta

from classes import Logger


class MessageGetter(discord.Client):
    def __init__(self, config):
        super().__init__()
        self.logger = Logger.Logger()
        self.config = config

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

    async def get_logs_from_channel(self, channel, cfg):
        if not (os.path.exists("chat_logs")):
            os.makedirs("chat_logs")

        log_file = open("chat_logs/%s-%s.log" % (str(cfg["id"]), channel.id), 'w')
        i = 0
        messages = []
        async for item in self.logs_from(channel, limit=sys.maxsize):
            i += 1
            if (i % 1000 == 0):
                print("\t\t" + str(i))
            messages.append(item)

        # Make the header
        header = "Server name: " + cfg["name"] + "\n"
        header += "Server ID: " + str(cfg["id"]) + "\n"
        header += "Channel name: " + channel.name + "\n"
        header += "Channel ID: " + channel.id + "\n"
        header += channel.created_at.strftime("Created at: %A %d %b %Y %H:%M:%S UTC\n")
        header += "Length: %d messages\n\n" % len(messages)

        log_file.write(header)
        for msg in reversed(messages):
            log_file.write((msg.timestamp + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S\t"))
            log_file.write(msg.author.name + "\t")
            log_file.write(msg.content + "\n")
        log_file.close()

        self.summary.append({
            "Server name": cfg["name"],
            "Server ID": str(cfg["id"]),
            "Channel name": channel.name,
            "Channel ID": str(channel.id),
            "Length": len(messages),
            "Log path": "chat_logs/%s-%s.log" % (str(cfg["id"]), channel.id)
        })

    # Launch the getter when the bot is ready
    async def get_server_messages(self):
        self.summary = []
        print("Sucessfully connected as %s (%s)\n" % (self.user.name, self.user.id))
        self.logger.logger.info("Sucessfully connected as %s (%s)" % (self.user.name, self.user.id))
        self.logger.logger.info("------------")
        # yield from self.change_status(game=discord.Game(name="Ketchup Splash Simulator"))
        for cfg in self.config["servers"]:
            for server in self.servers:
                if server.id == str(cfg["id"]):
                    print("{} ({})".format(server.name, server.id))
                    for channel in server.channels:
                        if (channel.type != discord.ChannelType.voice and
                            ("channels" not in cfg or
                             channel.id in [str(i["id"]) for i in cfg["channels"]])):
                            try:
                                print("\t{} ({})".format(channel.name, channel.id))
                                await self.get_logs_from_channel(channel, cfg)
                            except discord.errors.Forbidden:
                                pass
                    print()

        print("Done.")
        self.logger.logger.info("Done.")
        self.logger.logger.info("#--------------END--------------#")
        return self.summary
