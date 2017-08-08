#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import html
import itertools
import operator
import os
import plotly
import plotly.graph_objs as go
import re
from collections import Counter, OrderedDict
from datetime import date, datetime, timedelta
from yattag import Doc, indent


# UTILS
def generate_plot(graph_dict, file_path):
    try:
        plotly.offline.plot(graph_dict, filename=file_path, show_link=False, auto_open=False)
        return (plotly.offline.plot(graph_dict, filename=file_path, show_link=False, auto_open=False, output_type="div"))
    except:
        return ""


def cumultative_sum(values, start=0):
    for v in values:
        start += v
        yield start


# Plotify class
class Plotify():
    class EmptyChannelException(Exception):
        pass

    def __init__(self, output_path, summary_dict):
        self.summary = summary_dict
        self.log_path = summary_dict["Log path"]
        self.plots_dir = "{}/{}/{}/".format(output_path, summary_dict["Server ID"], summary_dict["Channel ID"])
        self.get_log_content()
        if len(self.meta_list) == 0:
            raise self.EmptyChannelException
        self.get_date_array()
        self.counts = [self.chat_log.count(x) for x in self.date_array]
        self.cumul = list(cumultative_sum(self.counts))
        if not (os.path.exists(self.plots_dir)):
            os.makedirs(self.plots_dir)

    def get_date_array(self):
        d1 = datetime.strptime(self.meta_list[0][0], "%Y-%m-%d %H:%M:%S").date()
        d2 = datetime.today().date()
        delta = d2 - d1

        date_array = []
        for i in range(delta.days):
            date_array.append(d1 + timedelta(days=i))
        self.date_array = [x.strftime("%Y-%m-%d") for x in date_array]

    def get_log_content(self):
        text = ""
        meta_list = []
        with open(self.log_path, "r") as file:
            for (i, line) in enumerate(file):
                if (re.match(r'^\d{4}-\d{2}-\d{2} \d\d:\d\d:\d\d\t', line)):
                    text += line
                    if (len(line.split("\t")) > 1):
                        (date, author, _) = line.split("\t")
                        meta_list.append((date, author))
        self.chat_log = text
        self.meta_list = meta_list
        print("OK")

    def plotify(self):
        self.plots = OrderedDict()
        self.plots["msgperday"] = (plot_msgperday(self, "Plot-msg.html"), "Plot-msg.html", "Number of messages per day")
        self.plots["msgcumul"] = (plot_msgcumul(self, "Plot-msgcumul.html"), "Plot-msgcumul.html", "Number of cumulatives messages")
        self.plots["top10"] = (plot_usertopx(self, 10, "Plot-top10.html"), "Plot-top10.html", "Number of cumulatives messages for the Top 10 users")
        self.plots["top20"] = (plot_usertopx(self, 20, "Plot-top20.html"), "Plot-top20.html", "Number of cumulatives messages for the Top 20 users")
        self.stats = OrderedDict()
        self.stats["top10perday"] = (top10_per_day(self, "Stats-top10perday.html"), "Stats-top10perday.html", "Standings history")

    def write_channel_main_html(self):
        doc, tag, text = Doc().tagtext()

        with tag('html'):
            # HEAD
            with tag('head'):
                doc.asis("<!DOCTYPE html>")
                doc.asis("<meta charset=\"UTF-8\">")
                doc.asis("<meta http-equiv=\"X-UA-Compatible\" content=\"IE=edge\">")
                doc.asis("<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, shrink-to-fit=no\">")
                doc.asis("<link rel=\"stylesheet\" href=\"https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0-alpha.5/css/bootstrap.min.css\" integrity=\"sha384-AysaV+vQoT3kOAXZkl02PThvDr8HYKPZhNT5h/CXfBThSRXQ6jW5DO2ekP5ViFdi\" crossorigin=\"anonymous\">")
                doc.asis("<link rel=\"stylesheet\" href=\"../../css/own.css\">")
                with tag('title'):
                    text("DiscoLog Monitoring for %s (#%s)" % (self.summary["Server name"], self.summary["Channel name"]))
            # BODY
            with tag('body'):
                with tag('h1', klass="page-header"):
                    text("DiscoLog Monitoring for %s (#%s)" % (self.summary["Server name"], self.summary["Channel name"]))
                with tag("div", klass="container"):
                    # Standing of yesterday
                    with tag('h3', klass="sub-header"):
                        text("Standings of yesterday")
                    with tag("table", klass="table table-sm"):
                        with tag("thead"):
                            with tag("tr"):
                                with tag("th"):
                                    text("#")
                                with tag("th"):
                                    text("Messages count")
                                with tag("th"):
                                    text("Nickname")
                        with tag("tbody"):
                            for (i, elem) in enumerate(top10_yesterday(self)):
                                with tag("tr"):
                                    with tag("td"):
                                        text(str(i + 1))
                                    with tag("td"):
                                        text(elem[0])
                                    with tag("td"):
                                        text(elem[1])
                    # Graphs
                    with tag('h3'):
                        text("Graphs")
                    with tag("ul", ("style", "list-style-type:none")):
                        with tag("li"):
                            with tag('a', href="allplots.html"):
                                doc.asis("All graphs")
                        for _, plot in self.plots.items():
                            if plot[1] and plot[2]:
                                with tag("li"):
                                    with tag('a', href=plot[1]):
                                        text(plot[2])
                    # Stats
                    with tag('h3'):
                        text("Stats")
                    with tag("ul", ("style", "list-style-type:none")):
                        for _, stat in self.stats.items():
                            if stat[1] and stat[2]:
                                with tag("li"):
                                    with tag('a', href=stat[1]):
                                        text(stat[2])
                    # Footer
                    with tag("footer", klass="footer"):
                        with tag("div", klass="container"):
                            with tag("span", klass="text-muted"):
                                text("Page generated at %s by DiscoLog (DasFranck#1168)" % datetime.now().strftime("%T the %F"))

        result = indent(doc.getvalue())
        with open(self.plots_dir + "index.html", "w") as file:
            file.write(result)

    def write_all_plots_html(self):
        doc, tag, text = Doc().tagtext()

        with tag('html'):
            with tag('head'):
                doc.asis('<meta http-equiv="content-type" content="text/html; charset=utf-8" />')
            with tag('body'):
                for _, plot in self.plots.items():
                    doc.asis(plot[0])
                doc.asis("<br />")
                text("Page generated at %s" % datetime.now().strftime("%T the %F"))

        result = doc.getvalue()
        with open(self.plots_dir + "allplots.html", "w") as file:
            file.write(result)

    def write_standing_history_html(self):
        doc, tag, text = Doc().tagtext()

        with tag('html'):
            with tag('head'):
                doc.asis('<meta http-equiv="content-type" content="text/html; charset=utf-8" />')
            with tag('body'):
                doc.asis(self.stats["top10perday"][0])
                doc.asis("<br />")
                doc.asis("<br />")
                text("Page generated at %s" % datetime.now().strftime("%T the %F"))

        result = doc.getvalue()
        with open(self.plots_dir + "standinghistory.html", "w") as file:
            file.write(result)


    def write_raw_text_in_html(self, content, path):
        doc, tag, text = Doc().tagtext()

        with tag('html'):
            with tag('head'):
                doc.asis('<meta http-equiv="content-type" content="text/html; charset=utf-8" />')
            with tag('body'):
                doc.asis(content)

        result = doc.getvalue()
        with open(self.plots_dir + path, "w") as file:
            file.write(result)


def plot_msgperday(plotify, path):
    msg_average = []
    for i, cum in enumerate(plotify.cumul):
        msg_average.append(int(cum / (i + 1)))

    line1 = go.Bar(x=plotify.date_array,
                   y=plotify.counts,
                   name="Messages per day")

    line2 = go.Scatter(x=plotify.date_array,
                       y=msg_average,
                       name="Average messages per day")

    return (generate_plot({"data": [line1, line2],
                           "layout": go.Layout(title="Number of messages per day in #%s (%s)" % (plotify.summary["Channel name"], plotify.summary["Server name"]))},
                          plotify.plots_dir + path))


def plot_msgcumul(plotify, path):
    return (generate_plot({"data": [go.Scatter(x=plotify.date_array, y=plotify.cumul)],
                           "layout": go.Layout(title="Number of cumulatives messages in #%s (%s)" % (plotify.summary["Channel name"], plotify.summary["Server name"]))},
                          plotify.plots_dir + path))


def plot_usertopx(plotify, max, path):
    top = Counter(elem[1] for elem in plotify.meta_list).most_common(max)
    top_users = [elem[0] for elem in top]
    users_line = []
    for i, user in enumerate(top_users):
        print(i + 1)
        counts = [len(re.findall(r'%s.+\t%s' % (re.escape(x), re.escape(user)), plotify.chat_log)) for x in plotify.date_array]
        cumul = list(cumultative_sum(counts))
        line = go.Scatter(x=plotify.date_array,
                          y=cumul,
                          name=user)
        users_line.append(line)
    return (generate_plot({"data": users_line,
                           "layout": go.Layout(title="Number of cumulatives messages for the Top %d users in #%s (%s)" % (max, plotify.summary["Channel name"], plotify.summary["Server name"]))},
                          plotify.plots_dir + path))


def top10_per_day(plotify, path):
    # user_list = sort(list(set(([b for a,b in meta_list]))))
    text = "<pre>"
    meta_list = [(meta[0].split(" ")[0], meta[1]) for meta in plotify.meta_list]
    meta_sorted = sorted(meta_list, key=operator.itemgetter(0))
    meta_grouped = [list(group) for key, group in itertools.groupby(meta_sorted, operator.itemgetter(0))]
    for meta_per_date in reversed(meta_grouped[:-1]):
        count_map = {}
        for t in meta_per_date:
            count_map[t[1]] = count_map.get(t[1], 0) + 1
        top_list = sorted(count_map.items(), key=operator.itemgetter(1), reverse=True)[0:10]

        text += "<b>" + meta_per_date[0][0] + "</b><br />"
        for (i, elem) in enumerate(top_list):
            text += "%d.\t%d\t%s<br />" % (i + 1, elem[1], html.escape(elem[0]))
        if meta_per_date is not meta_grouped[0]:
            text += "<br />"
    text += "</pre>"
    plotify.write_raw_text_in_html(text, path)
    return (text)


def top10_yesterday(plotify):
    # user_list = sort(list(set(([b for a,b in meta_list]))))
    standing = []
    count_map = {}
    plain = ""

    meta_list = [(meta[0].split(" ")[0], meta[1]) for meta in plotify.meta_list]
    meta_sorted = sorted(meta_list, key=operator.itemgetter(0))
    meta_grouped = [list(group) for key, group in itertools.groupby(meta_sorted, operator.itemgetter(0))]
    meta_yesterday = [lst for lst in meta_grouped if lst[0][0] == (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")]
    if (len(meta_yesterday) == 0):
        plain = "No message has been posted in this channel yesterday"
        return (standing)

    print(meta_yesterday)
    for t in meta_yesterday[0]:
        count_map[t[1]] = count_map.get(t[1], 0) + 1
    top_list = sorted(count_map.items(), key=operator.itemgetter(1), reverse=True)[0:10]
    # print(top_list)

    for (i, elem) in enumerate(top_list):
        standing.append((elem[1], elem[0]))
        plain += "%d.\t%d\t%s\n" % (i + 1, elem[1], elem[0])
    plotify.top10yesterday = plain
    return (standing)


def main():
    # Parsearg
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("log_path")
    args = parser.parse_args()

    plotify = Plotify(args.log_path)
    plotify.plotify()
    plotify.write_standing_history_html()
    plotify.write_all_plots_html()
    plotify.write_main_html()


if __name__ == '__main__':
    main()
