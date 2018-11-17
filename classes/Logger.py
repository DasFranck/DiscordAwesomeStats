#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nothing here for now.
"""

import logging
import os


class Logger():
    logger = logging.getLogger('discord')

    # Logger Initialization
    def __init__(self, on_stdout=False, logging_type=logging.INFO):
        # Set logger level to INFO
        self.logger.setLevel(logging_type)

        if not os.path.exists("logs"):
            os.makedirs("logs")

        # Setting handler (Log File)
        handler = logging.FileHandler(filename='logs/discord.log', encoding='utf-8', mode='a')
        handler.setFormatter(logging.Formatter("%(asctime)s :: %(levelname)s :: %(message)s"))
        self.logger.addHandler(handler)

        # Setting stream_handler (Stdout)
        if on_stdout:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            self.logger.addHandler(stream_handler)

        self.logger.info("#-------------START-------------#")
        return

    # Add an entry in the log with info level.
    def log_info_command(self, string, message):
        if message.channel.is_private:
            self.logger.info(string + " in a Private Channel")
        else:
            self.logger.info(string + " in #" + message.channel.name + " on " + message.guild.name + " (%s)" % message.guild.id)

    def log_error_command(self, string, message):
        if message.channel.is_private:
            self.logger.error(string + " in a Private Channel")
        else:
            self.logger.error(string + " in #" + message.channel.name + " on " + message.guild.name + " (%s)" % message.guild.id)

    def log_warn_command(self, string, message):
        if message.channel.is_private:
            self.logger.warning(string + " in a Private Channel")
        else:
            self.logger.warning(string + " in #" + message.channel.name + " on " + message.guild.name + " (%s)" % message.guild.id)

    def log_info_print(self, string):
        self.logger.info(string)
        print(string)

    def log_warn_print(self, string):
        self.logger.warning(string)
        print(string)

    def log_error_print(self, string):
        self.logger.error(string)
        print(string)
