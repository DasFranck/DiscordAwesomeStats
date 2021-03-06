#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import discord
import json
import os
import yaml

from plotify import Plotify
from yattag import Doc, indent

from LogGetter import LogGetter
from classes import Logger


def write_indexes_html(server_channel_dict, output_path):
    for id_server, server in server_channel_dict.items():
        doc, tag, text = Doc().tagtext()

        with tag('html'):
            # HEAD
            with tag('head'):
                doc.asis("<!DOCTYPE html>")
                doc.asis("<meta charset=\"UTF-8\">")
                doc.asis("<meta http-equiv=\"X-UA-Compatible\" content=\"IE=edge\">")
                doc.asis("<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, shrink-to-fit=no\">")
                doc.asis("<link rel=\"stylesheet\" href=\"https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0-alpha.5/css/bootstrap.min.css\" integrity=\"sha384-AysaV+vQoT3kOAXZkl02PThvDr8HYKPZhNT5h/CXfBThSRXQ6jW5DO2ekP5ViFdi\" crossorigin=\"anonymous\">")
                doc.asis("<link rel=\"stylesheet\" href=\"../css/own.css\">")
                with tag('title'):
                    text("Channel index for %s" % (server["Server name"]))
            with tag('body'):
                with tag('h1', klass="page-header"):
                    with tag('b'):
                        text("Channel index for %s" % (server["Server name"]))
                with tag("div", klass="container"):
                    with tag('h2'):
                        text("Channel List:")
                    with tag("ul", ("style", "list-style-type:none")):
                        for channel in server["Channels"]:
                            with tag("li"):
                                with tag('h4'):
                                    with tag('a', href=str(channel["Channel ID"])):
                                        text("#" + str(channel["Channel name"]))

        result = indent(doc.getvalue())
        with open(output_path + str(id_server) + "/index.html", "w") as file:
            file.write(result)

    doc, tag, text = Doc().tagtext()
    with tag('html'):
        # HEAD
        with tag('head'):
            doc.asis("<!DOCTYPE html>")
            doc.asis("<meta charset=\"UTF-8\">")
            doc.asis("<meta http-equiv=\"X-UA-Compatible\" content=\"IE=edge\">")
            doc.asis("<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, shrink-to-fit=no\">")
            doc.asis("<link rel=\"stylesheet\" href=\"https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0-alpha.5/css/bootstrap.min.css\" integrity=\"sha384-AysaV+vQoT3kOAXZkl02PThvDr8HYKPZhNT5h/CXfBThSRXQ6jW5DO2ekP5ViFdi\" crossorigin=\"anonymous\">")
            doc.asis("<link rel=\"stylesheet\" href=\"css/own.css\">")
            with tag('title'):
                text("DiscoLog Monitoring Index")
        with tag('body'):
            with tag('h1', klass="page-header"):
                with tag('b'):
                    text("DiscoLog Monitoring Index")
            with tag("div", klass="container"):
                with tag('h2'):
                    text("Server List:")
                with tag("ul", ("style", "list-style-type:none")):
                    for id_server, server in server_channel_dict.items():
                        with tag("li"):
                            with tag('h4'):
                                with tag('a', href=str(id_server)):
                                    text(server["Server name"])
    print(doc.getvalue())
    result = indent(doc.getvalue())
    with open(output_path + "index.html", "w") as file:
        file.write(result)
    return


class DiscordAwesomeStats(discord.Client):
    def __init__(self, args):
        super().__init__()
        self.args = args
        self.logger = Logger.Logger()
        with open(args.config_file, 'r') as file:
            self.config = yaml.load(file)

        if "servers" not in self.config:
            return (1)

        if not os.path.isdir("chat_logs/"):
            os.mkdir("chat_logs")

    async def on_ready(self):
        print("HEY")
        return


class SummaryWriter(discord.Client):
    def __init__(self, config, summaries):
        super().__init__()
        self.logger = Logger.Logger()
        self.config = config
        self.summaries = summaries

    async def on_ready(self):
        for summary_to_be_writed in self.summaries:
            print(1)
            for server in self.servers:
                print(2)
                if server.id == summary_to_be_writed[0]:
                    print(3)
                    for channel in server.channels:
                        print(4)
                        if channel.id == summary_to_be_writed[1]:
                            print(5)
                            await self.send_message(channel, summary_to_be_writed[2])
        await self.logout()


def main():
    parser = argparse.ArgumentParser(description="BT-Monitor Script")
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
            plotify.plotify()
#            plotify.write_standing_history_html()
            plotify.write_all_plots_html()
            plotify.write_channel_main_html()
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
               and hasattr(plotify, "top10yesterday"):
                text = "DiscoLog Awesome Stats has been updated.\n\nMessage amount 'til now: **%d**\nStandings of yesterday:\n```\n" % channel["Length"]
                text += plotify.top10yesterday
                text += "```\n\nMore stats and graphs here : https://dasfranck.fr/DiscordAwesomeStats/%s/%s/" % (channel["Server ID"], channel["Channel ID"])
                summaries_to_be_writed.append((channel["Server ID"], channel["Channel ID"], text))
        if (channel["Server ID"] not in server_channel_dict):
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
