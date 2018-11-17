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

    def get_date_range(self, table, channel_id, reset):
        today = arrow.utcnow().to(self.config['timezone']).date()
        last_count = (table.select(fn.MAX(table.date))
                           .where(table.channel_id == channel_id)
                           .scalar())
        if reset or not last_count:
            first_message_timestamp = (Message.select(fn.MIN(Message.timestamp))
                                              .where(Message.channel_id == channel_id)
                                              .scalar())
            if not first_message_timestamp:
                return None
            first_message_date = arrow.get(first_message_timestamp).to(self.config['timezone']).date()
            return period(first_message_date, today).range("days")
        else:
            last_count_date = arrow.get(last_count).to(self.config["timezone"]).date()
            return period(last_count_date, today).range("days")


    def generate_message_count_per_user_per_channel(self, channel_id, reset=False):
        """
        Generate the message count per user for channel_id for each day,
        Skip if no message exist for this channel.

        Reset means to recalculate everything.
        """
        print("\t\tGenerating message count per user... ", end='', flush=True)
        self.database.create_tables([MessageCountUser])

        date_range = self.get_date_range(MessageCountUser, channel_id, reset)
        if not date_range:
            print("skipped.")
            return

        for date in date_range:
            date_begin = arrow.get(date).to(self.config["timezone"]).replace(hour=0, minute=0, second=0).timestamp
            date_end = arrow.get(date).to(self.config["timezone"]).replace(hour=23, minute=59, second=59).timestamp

        print("done.")
        pass

    def generate_message_count_per_channel(self, channel_id, reset=False):
        """
        Generate the message count in this channel for each day,
        Skip if no message exist for this channel.

        Reset means recalculate and overwrite everything.
        """
        print("\t\tGenerating message count of this channel... ", end='', flush=True)
        self.database.create_tables([MessageCountChannel])

        date_range = self.get_date_range(MessageCountChannel, channel_id, reset)
        if not date_range:
            print("skipped.")
            return

        count_data = []
        count_fields = [MessageCountChannel.channel_id, MessageCountChannel.date,
                        MessageCountChannel.count, MessageCountChannel.cumulative_count]
        cumulated_count = 0
        for date in date_range:
            date_begin = arrow.get(date).to(self.config["timezone"]).replace(hour=0, minute=0, second=0).timestamp
            date_end = arrow.get(date).to(self.config["timezone"]).replace(hour=23, minute=59, second=59).timestamp
            count = (Message.select()
                            .where((Message.channel_id == channel_id) & 
                                   (Message.timestamp >= date_begin) & 
                                   (Message.timestamp <= date_end))
                            .count())
            cumulated_count += count
            count_data.append((
                channel_id,
                date.to_date_string(),
                count,
                cumulated_count
            ))

        for idx in range(0, len(count_data), 300):
            (MessageCountChannel.insert_many(count_data[idx:idx+300], fields=count_fields)).on_conflict_replace().execute()

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
                        self.generate_message_count_per_user_per_channel(channel.id, True)
                        self.generate_message_count_per_channel(channel.id, True)
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