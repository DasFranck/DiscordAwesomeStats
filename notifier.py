#!/usr/bin/env python3
# coding: utf-8

import argparse

import datetime
import discord
import yaml

from database import (Guild, Channel, Member, Message,
                      MessageCountChannel, MessageCountUserChannel, database)
from classes import Logger

class Notifier(discord.Client):
    def __init__(self, config):
        super().__init__()
        self.logger = Logger.Logger()
        self.config = config
        self.database = database

    async def notify(self):
        """
        """
        await self.change_presence(activity=discord.Game(name="Notifying peoples..."))
        self.database.connect()

        for config_guild in self.config["guilds"]:
            print(f"Generating leaderboards counts for {config_guild['id']}... ", end='', flush=True)
            # Skip if the config specify to not notify this guild
            if "silent" in config_guild and config_guild["silent"]:
                print("skipped")
                continue

            print()

            # Get channel list to notify for this guild
            if "report_all" in config_guild and config_guild["report_all"]:
                channels_id = [channel.id for channel in Channel.select().where(Channel.guild_id == config_guild["id"])]
            else:
                channels_id = [channel for channel in config_guild["report"]]

            for channel_id in channels_id:
                print(f"\t{channel_id}")
                channel = self.get_channel(channel_id)
                leaderboard = []
                # Get top 10 user
                for i in MessageCountUserChannel.select().where((MessageCountUserChannel.channel_id == channel_id) & (MessageCountUserChannel.date == str(datetime.datetime.now().date() - datetime.timedelta(days=1)))).order_by(MessageCountUserChannel.count.desc()):
                    if i.count == 0:
                        break
                    leaderboard.append((i.author_id, i.count))

                message = f"***Leaderboards for #{str(channel)} ({str(channel.guild)}):***\n\n"
                if len(leaderboard):
                    for (i, (user_id, count)) in enumerate(leaderboard[:10]):
                        user = Member.get(Member.id == user_id)
                        message += f"**{i + 1}**. with {count} messages: **{user.name}**#{user.discriminator}\n"

                else:
                    message += "Nothing has been posted here since last time, that's pretty sad... :/"

                try:
                    await channel.send(message)
                except:
                    pass

    async def on_ready(self):
        """
        Launch the getter when the bot is ready
        """
        print("Sucessfully connected as %s (%s)\n" % (self.user.name, self.user.id))
        self.logger.logger.info("Sucessfully connected as %s (%s)" % (self.user.name, self.user.id))
        self.logger.logger.info("------------")

        await self.notify()
        await self.logout()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config_file", default="./config.yaml", help="Path to the config file")
    args = parser.parse_args()

    with open(args.config_file, 'r') as file:
        config = yaml.load(file)

    nt = Notifier(config)
    nt.run(config["token"])

if __name__ == '__main__':
    main()