#!/usr/bin/env python3
# coding: utf-8

import argparse

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


    async def on_ready(self):
        """
        Launch the getter when the bot is ready
        """
        print("Sucessfully connected as %s (%s)\n" % (self.user.name, self.user.id))
        self.logger.logger.info("Sucessfully connected as %s (%s)" % (self.user.name, self.user.id))
        self.logger.logger.info("------------")

        await self.dsds()
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