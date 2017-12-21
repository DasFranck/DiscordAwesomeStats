#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import os
import yaml

import discord
from jinja2 import Environment, FileSystemLoader
from plotify import Plotify

from LogGetter import LogGetter
from classes import Logger


def write_indexes_html(server_channel_dict, output_path):
    env = Environment(
        loader=FileSystemLoader('./templates')
    )
    template_index = env.get_template('index.html.j2')
    template_server_page = env.get_template('server_page.html.j2')

    for id_server, server in server_channel_dict.items():
        with open(output_path + str(id_server) + "/index.html", "w") as file:
            file.write(template_server_page.render(server=server))

    with open(output_path + "index.html", "w") as file:
        file.write(template_index.render(server_channel_dict=server_channel_dict))
    return


class DiscordAwesomeStats(discord.Client):
    def __init__(self, args):
        super().__init__()
        self.args = args
        self.logger = Logger.Logger()
        with open(args.config_file, 'r') as file:
            self.config = yaml.load(file)

        assert "servers" in self.config

        if not os.path.isdir("chat_logs/"):
            os.mkdir("chat_logs")

    async def on_ready(self):
        print("Starting awesomness...")
        return


class SummaryWriter(discord.Client):
    def __init__(self, config, summaries):
        super().__init__()
        self.logger = Logger.Logger()
        self.config = config
        self.summaries = summaries

    async def on_ready(self):
        for summary_to_be_writed in self.summaries:
            for server in self.servers:
                if server.id == summary_to_be_writed[0]:
                    for channel in server.channels:
                        if channel.id == summary_to_be_writed[1]:
                            await self.send_message(channel, summary_to_be_writed[2])
        await self.logout()


def main():
    parser = argparse.ArgumentParser(description="DiscordAwesomeStats")
    parser.add_argument("config_file", default="./config.yaml")
    parser.add_argument("--no-getlog", action='store_true', default=False)
    parser.add_argument("--no-plotify", action='store_true', default=False)
    parser.add_argument("--silent", action='store_true', default=False)
    args = parser.parse_args()

    with open(args.config_file, 'r') as file:
        config = yaml.load(file)

    lg = LogGetter(config)
    lg.run(config["token"])
    with open("data/summary.json", 'w') as summary_file:
        json.dump(lg.summary, summary_file, indent=4)

    summaries_to_be_writed = []
    server_channel_dict = {}
    for channel in lg.summary:
        print("Doing plots for %s #%s" % (channel["Server name"], channel["Channel name"]))
        try:
            plotify = Plotify(config["outputdir"], channel)
        except Plotify.EmptyChannelException:
            print("Skipping it cause it's empty.")
        else:
            plotify.run()
            for server_config in config["servers"]:
                print(server_config)
                print(channel)
                if str(server_config["id"]) == str(channel["Server ID"]):
                    serv_conf = server_config
                    break
            else:
                serv_conf = None

            if not (args.silent or ("silent" in serv_conf and serv_conf["silent"])) \
               and (("report_all" in serv_conf and serv_conf["report_all"]) or ("report" in serv_conf and channel["Channel ID"] in str(serv_conf["report"]))) \
               and hasattr(plotify, "top10_yesterday"):
                text = """
                DiscoLog Awesome Stats has been updated.
                
                Message amount 'til now: **{length}**
                Standings of yesterday:
                ```
                {top10_yesterday_plain}
                ```
                More stats and graphs here : https://dasfranck.fr/DiscordAwesomeStats/{server_id}/{channel_id}/
                """.format(length=channel["Length"],
                           top10_yesterday_plain=plotify.top10_yesterday_plain,
                           server_id=channel["Server ID"],
                           channel_id=channel["Channel ID"]
                          )
                summaries_to_be_writed.append((channel["Server ID"], channel["Channel ID"], text))
        if channel["Server ID"] not in server_channel_dict:
            server_channel_dict[channel["Server ID"]] = {
                "Server name": channel["Server name"],
                "Channels": [{
                    "Channel name": channel["Channel name"],
                    "Channel ID": channel["Channel ID"]
                }]}
        else:
            server_channel_dict[channel["Server ID"]]["Channels"].append({
                "Channel name": channel["Channel name"],
                "Channel ID": channel["Channel ID"]
            })
    write_indexes_html(server_channel_dict, config["outputdir"])

    sw = SummaryWriter(config, summaries_to_be_writed)
    sw.run(config["token"])


if __name__ == '__main__':
    main()
