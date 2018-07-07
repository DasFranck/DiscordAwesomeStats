#!/usr/bin/env python3
# coding: utf-8

from datetime import datetime
import asyncio
import argparse
import os
import sys
import time

import discord
from peewee import fn
import pytz
import yaml

from database import (Server, Channel, Member, Message,
                      MessageCountChannel, MessageCountUser, database)
from classes import Logger

class MessageCountGenerator():
    def __init__(self, config):
        self.logger = Logger.Logger()
        self.config = config
        self.database = database
        if 'timezone' not in self.config:
            self.config['timezone'] = 'UTC'

    def generate_message_count_per_user_per_channel(self):
        print("\t\tGenerating message count per user... ", end='')

        print("done.")
        pass

    def generate_message_count_per_channel(self):
        print("\t\tGenerating message count of this channel... ", end='')
        
        print("done.")
        pass

    def run(self):
        self.database.connect()

        for config_server in self.config["servers"]:
            server = Server.get(Server.id == config_server["id"])
            channels = Channel.select().where(Channel.server_id == config_server["id"])
            print("{} ({})".format(server.name, server.id))
            for channel in channels:
                if ("channels" not in config_server or
                    channel.id in [i["id"] for i in config_server["channels"]]):
                        print("\t{} ({})".format(channel.name, channel.id))
                        self.generate_message_count_per_channel()
                        self.generate_message_count_per_user_per_channel()
            print()

        self.database.close()
    pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config_file", default="./config.yaml", help="Path to the config file")
    args = parser.parse_args()

    with open(args.config_file, 'r') as file:
        config = yaml.load(file)

    mcg = MessageCountGenerator(config)
    mcg.run()

if __name__ == '__main__':
    main()