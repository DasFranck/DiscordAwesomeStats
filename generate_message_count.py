#!/usr/bin/env python3
# coding: utf-8

from datetime import datetime
import asyncio
import argparse
import os
import sys
import time

import arrow
import discord
from peewee import fn
from pendulum import period
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

    def generate_message_count_per_user_per_channel(self, channel_id, reset=False):
        """
        Generate the message count per user for channel_id for each day,
        Skip if no message exist for this channel

        reset means to recalculate everything
        """
        print("\t\tGenerating message count per user... ", end='')
        self.database.create_tables([MessageCountUser])

        today = arrow.utcnow().to(self.config['timezone']).date()
        last_count = MessageCountUser.select(fn.MAX(MessageCountUser.date)).where(MessageCountUser.channel_id == channel_id).scalar()
        if reset or not last_count:
            first_message_timestamp = Message.select(fn.MIN(Message.timestamp)).where(Message.channel_id == channel_id).scalar()
            if not first_message_timestamp:
                print("skipped.")
                return
            first_message_date = arrow.get(first_message_timestamp).to(self.config['timezone']).date()
            date_range = period(first_message_date, today).range("days")
        else:
            date_range = period(last_count, today).range("days")
        print("done.")
        pass

    def generate_message_count_per_channel(self, channel_id, reset=False):
        """
        Generate the message count per user for each day,
        Skip if no message exist for this channel

        reset means to recalculate everything
        """
        print("\t\tGenerating message count of this channel... ", end='')
        self.database.create_tables([MessageCountChannel])

        today = arrow.utcnow().to(self.config['timezone']).date()
        last_count = MessageCountChannel.select(fn.MAX(MessageCountChannel.date)).where(MessageCountChannel.channel_id == channel_id).scalar()
        if reset or not last_count:
            first_message_timestamp = Message.select(fn.MIN(Message.timestamp)).where(Message.channel_id == channel_id).scalar()
            if not first_message_timestamp:
                print("skipped.")
                return
            first_message_date = arrow.get(first_message_timestamp).to(self.config['timezone']).date()
            date_range = period(first_message_date, today).range("days")
        else:
            date_range = period(last_count, today).range("days")
        
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
                        self.generate_message_count_per_user_per_channel(channel.id)
                        self.generate_message_count_per_channel(channel.id)
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