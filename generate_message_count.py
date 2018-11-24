#!/usr/bin/env python3
# coding: utf-8

import argparse

import arrow
from peewee import fn
from pendulum import period
import yaml

from database import (Guild, Channel, Member, Message,
                      MessageCountChannel, MessageCountUserChannel, database)
from classes import Logger

class MessageCountGenerator():
    def __init__(self, config):
        self.logger = Logger.Logger()
        self.config = config
        self.database = database
        if 'timezone' not in self.config:
            self.config['timezone'] = 'UTC'

    def get_date_range(self, table, channel_id, user_id=None, reset=False):
        """
        """
        today = arrow.utcnow().to(self.config['timezone']).date()
        if user_id:
            last_count = (table.select(fn.MAX(table.date))
                               .where((table.channel_id == channel_id) &
                                      (table.author_id == user_id))
                               .scalar())
        else:
            last_count = (table.select(fn.MAX(table.date))
                               .where(table.channel_id == channel_id)
                               .scalar())

        if reset or not last_count:
            if user_id:
                print(f"{channel_id} {user_id}")
                first_message_timestamp = (Message.select(fn.MIN(Message.created_at))
                                                  .where((Message.channel_id == channel_id) &
                                                         (Message.author_id == user_id))
                                                  .scalar())
            else:
                first_message_timestamp = (Message.select(fn.MIN(Message.created_at))
                                                .where(Message.channel_id == channel_id)
                                                .scalar())
            if not first_message_timestamp:
                return None
            first_message_date = arrow.get(first_message_timestamp).to(self.config['timezone']).date()
            return [date for date in period(first_message_date, today).range("days")]
        else:
            last_count_date = arrow.get(last_count).to(self.config["timezone"]).date()
            return [date for date in period(last_count_date, today).range("days")]


    def generate_message_count_per_user_per_channel(self, user_list, channel_id, reset=False):
        """
        Generate the message count per user for channel_id for each day,
        Skip if no message exist for this channel.

        Reset means to recalculate everything.
        """
        print("\t\tGenerating message count per user... ", end='', flush=True)
        self.database.create_tables([MessageCountUserChannel])

        date_range = self.get_date_range(MessageCountUserChannel, channel_id, reset=reset)
        if not date_range:
            print("skipped.")
            return

        count_data = []
        count_fields = [MessageCountUserChannel.author_id, MessageCountUserChannel.channel_id,
                        MessageCountUserChannel.date, MessageCountUserChannel.count, MessageCountUserChannel.cumulative_count]
        for user_id in user_list:
            cumulated_count = 0
            date_range = self.get_date_range(MessageCountUserChannel, channel_id, user_id, reset)
            if not date_range:
                continue
            for date in date_range:
                date_begin = arrow.get(date).to(self.config["timezone"]).replace(hour=0, minute=0, second=0).timestamp
                date_end = arrow.get(date).to(self.config["timezone"]).replace(hour=23, minute=59, second=59).timestamp
                count = (Message.select()
                                .where((Message.channel_id == channel_id) & 
                                       (Message.created_at >= date_begin) & 
                                       (Message.created_at <= date_end) &
                                       (Message.author_id == user_id))
                                .count())
                cumulated_count += count
                count_data.append((
                    user_id,
                    channel_id,
                    date.to_date_string(),
                    count,
                    cumulated_count
                ))

        for idx in range(0, len(count_data), 300):
            (MessageCountUserChannel.insert_many(count_data[idx:idx+300], fields=count_fields)).on_conflict_replace().execute()

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

        date_range = self.get_date_range(MessageCountChannel, channel_id, reset=reset)
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
                                   (Message.created_at >= date_begin) &
                                   (Message.created_at <= date_end))
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

        for config_guild in self.config["guilds"]:
            guild = Guild.get(Guild.id == config_guild["id"])
            channels = Channel.select().where(Channel.guild_id == config_guild["id"])
            user_list = guild.members.split(',')
            print("{} ({})".format(guild.name, guild.id))
            for channel in channels:
                if ("channels" not in config_guild or
                    channel.id in [i["id"] for i in config_guild["channels"]]):
                        print("\t{} ({})".format(channel.name, channel.id))
                        self.generate_message_count_per_user_per_channel(user_list, channel.id)
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