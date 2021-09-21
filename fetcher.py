import argparse
import logging
import sqlite3

from datetime import datetime, timedelta
from typing import Dict, Any, List

import discord
import pytz
import yaml

class DiscoLog(discord.Client):
    db_client: sqlite3.Connection
    config: Dict[Any, Any]
    logger: logging.Logger

    def __init__(self, config_path: str = "config.yaml", *, loop=None, **options):
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(loop=loop, intents=intents, **options)
        self.setup_logger()
        self.load_config(config_path)
        self.init_db()

    def setup_logger(self) -> None:
        self.logger = logging.getLogger("DiscoLog")
        self.logger.setLevel(logging.INFO) 
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def load_config(self, config_path) -> None:
        with open(config_path) as fd:
            self.config = yaml.load(fd, Loader=yaml.FullLoader)

    def init_db(self) -> None:
        self.db_client = sqlite3.connect("das.db")
        db_cursor = self.db_client.cursor()
        db_cursor.executescript(
            """
            CREATE TABLE IF NOT EXISTS guild (guild_id INTEGER PRIMARY KEY, guild_name TEXT);
            CREATE TABLE IF NOT EXISTS channel (channel_id INTEGER PRIMARY KEY, guild_id INTEGER, channel_name TEXT, FOREIGN KEY (guild_id) REFERENCES guild (guild_id));
            CREATE TABLE IF NOT EXISTS member (member_id INTEGER PRIMARY KEY, member_name TEXT, discriminator INTEGER);
            CREATE TABLE IF NOT EXISTS daily_message_count (date DATE, channel_id INTEGER, member_id INTEGER, count INTEGER, 
                FOREIGN KEY (channel_id) REFERENCES channel (channel_id),
                FOREIGN KEY (member_id) REFERENCES member (member_id));
            """)

        self.db_client.commit()
        db_cursor.close()

    async def populate_guild_member_table(self, guild: discord.Guild):
        db_cursor = self.db_client.cursor()
        db_cursor.execute(f"INSERT OR REPLACE INTO guild (guild_id, guild_name) VALUES (?, ?);", (guild.id, guild.name))
        self.db_client.commit()

        async for member in guild.fetch_members(limit=None):
            db_cursor.execute(f"INSERT OR REPLACE INTO member (member_id, member_name, discriminator) VALUES (? , ?, ?);", (member.id, member.name, member.discriminator))
        self.db_client.commit()
        db_cursor.close()

    async def populate_channel_table(self, channel: discord.TextChannel):
        db_cursor = self.db_client.cursor()
        db_cursor.execute("INSERT OR REPLACE INTO channel (channel_id, guild_id, channel_name) VALUES (?, ?, ?);", (channel.id, channel.guild.id, channel.name))
        self.db_client.commit()
        db_cursor.close()

    def fetch_channels(self, guild: discord.Guild, guild_config: Dict[Any, Any]) -> List[discord.TextChannel]:
        channel_list = []
        if "run_on_all_channels" in guild_config and guild_config["run_on_all_channels"]:
            for channel in guild.channels:
                if isinstance(channel, discord.TextChannel):
                    if not ("blacklist_channels" in guild_config and channel.id in guild_config["blacklist_channels"]):
                        channel_list.append(channel)
        else:
            for channel_id in guild_config["channels"]:
                channel = guild.get_channel(channel_id)
                if isinstance(channel, discord.TextChannel):
                    channel_list.append(channel)
        return channel_list    

    def get_latest_count_date(self, channel_id: str = "", user_id: str = ""):
        db_cursor = self.db_client.cursor()
        if channel_id and user_id:
            result = db_cursor.execute("SELECT MAX(date) FROM daily_message_count WHERE channel_id IS ? AND user_id IS ?;", (channel_id, user_id)).fetchone()
        elif channel_id:
            result = db_cursor.execute("SELECT MAX(date) FROM daily_message_count WHERE channel_id IS ?;", (channel_id,)).fetchone()
        elif user_id:
            result = db_cursor.execute("SELECT MAX(date) FROM daily_message_count WHERE user_id IS ?;", (user_id,)).fetchone()
        else:
            result = db_cursor.execute("SELECT MAX(date) FROM daily_message_count;").fetchone()
        db_cursor.close()
        return result[0]

    async def process_messages(self, channel: discord.TextChannel, after=None, before=None, only_users: List[discord.User] = None, limit=None):
        metadata : Dict[datetime.date, Dict[discord.User, int]] = {}
        db_cursor = self.db_client.cursor()
        last_date = None
        async for message in channel.history(limit=limit, before=before, after=after, oldest_first=True):
            message_creation_date = message.created_at.astimezone(pytz.timezone("Europe/Paris")).date()

            if last_date and last_date != message_creation_date:
                if last_date in metadata:
                    self.logger.info(f"    {last_date.strftime('%Y-%m-%d')} - #{channel.name} on {channel.guild.name} ({channel.id}@{channel.guild.id}) - {sum(metadata[last_date].values())}")
                    for user in metadata[last_date]:
                        db_cursor.execute("INSERT OR REPLACE INTO daily_message_count (date, channel_id, member_id, count) VALUES (?, ?, ?, ?);", (last_date.strftime("%Y-%m-%d"), channel.id, user.id, metadata[last_date][user]))
                    self.db_client.commit()

            last_date = message_creation_date

            if message_creation_date not in metadata:
                metadata[message_creation_date] = {}
            if message.author not in metadata[message_creation_date]:
                metadata[message_creation_date][message.author] = 1
            else:
                metadata[message_creation_date][message.author] += 1
        db_cursor.close()


        for date in metadata:
            self.logger.info(f"{date} ({sum(metadata[date].values())} msgs)")
            for user in sorted(metadata[date], key=metadata[date].get, reverse=True):
                self.logger.info(f"  {user.name} {metadata[date][user]}")

    async def on_ready(self):
        for guild in self.guilds:
            if guild.id in self.config["guilds"]:
                self.logger.info(f"Running on Guild {guild.name} ({guild.id})")
                await self.populate_guild_member_table(guild)
                for channel in self.fetch_channels(guild, self.config["guilds"][guild.id]):
                    self.logger.info(f"  Running on Channel {channel.name} ({channel.id})")
                    await self.populate_channel_table(channel)
                    latest_count_date = self.get_latest_count_date(channel.id)
                    print(latest_count_date)
                    await self.process_messages(channel, after=(datetime.fromisoformat(latest_count_date) - timedelta(days=1)) if latest_count_date else None)
        await self.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config_path")
    args = parser.parse_args()

    disco = DiscoLog(config_path=args.config_path)
    disco.run(disco.config["discord_token"])

if __name__ == "__main__":
    main()