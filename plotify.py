#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import Counter, OrderedDict
from datetime import date, datetime, timedelta
import argparse
import html
import itertools
import operator
import os
import sqlite3
import pytz

import plotly
import plotly.graph_objs as go
from yattag import Doc, indent

# Now use a sqlite database instead of plain text
# Optimizations
# Bugfixs
# Rectifying some hideous design choices
# Timezone support


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


class Plotify():
    class EmptyChannelException(Exception):
        pass

    def __init__(self, output_path, summary_dict):
        self.summary = summary_dict
        self.plots_dir = "{}/{}/{}/".format(output_path, self.summary["Server ID"], self.summary["Channel ID"])

        if not (os.path.exists("data")):
            os.makedirs("data")
        self.db = sqlite3.connect('data/database.db')

        cursor = self.db.cursor()
        cursor.execute("SELECT COUNT(*) FROM 'log_{}-{}'".format(self.summary["Server ID"], self.summary["Channel ID"]))
        msg_count = cursor.fetchone()[0]
        if msg_count == 0:
            raise self.EmptyChannelException

        self.get_date_array()
        self.counts = [self.get_count_per_date(date) for date in self.date_array]
        self.cumul = list(cumultative_sum(self.counts))
        if not (os.path.exists(self.plots_dir)):
            os.makedirs(self.plots_dir)

    def get_date_array(self):
        cursor = self.db.cursor()
        cursor.execute("SELECT MIN(time) FROM 'log_{}-{}'".format(self.summary["Server ID"], self.summary["Channel ID"]))
        first_message_timestamp = cursor.fetchone()[0]

        d1 = datetime.fromtimestamp(first_message_timestamp).date()
        d2 = datetime.today().date()
        delta = d2 - d1

        datetime_array = [d1 + timedelta(days=i) for i in range(delta.days)]
        self.date_array = [x.strftime("%Y-%m-%d") for x in datetime_array]

    # TODO: Timezone support (other than just UTC)
    # date can be str or datetime.datetime
    def get_count_per_date(self, date, user=None, timezone='Europe/Paris'):
        cursor = self.db.cursor()

        if isinstance(date, str):
            date_time = datetime.strptime(date, "%Y-%m-%d")
        else:
            date_time = date

        day_begin = date_time + pytz.timezone(timezone).localize(date_time).utcoffset()
        day_end = date_time + pytz.timezone(timezone).localize(date_time + timedelta(days=1)).utcoffset() + timedelta(days=1)

        if user is None:
            cursor.execute("SELECT COUNT(*) FROM 'log_{}-{}' WHERE time >= ? AND time < ?".format(self.summary["Server ID"], self.summary["Channel ID"]),
                           (int(day_begin.timestamp()), int(day_end.timestamp())))
        else:
            cursor.execute("SELECT COUNT(*) FROM 'log_{}-{}' WHERE time >= ? AND time < ? AND author_id LIKE (?)".format(self.summary["Server ID"], self.summary["Channel ID"]),
                           (int(day_begin.timestamp()), int(day_end.timestamp()), user))
        return cursor.fetchone()[0]

    def plotify(self):
        # Generated Content | HMTL Path | Description
        self.plots = OrderedDict()
        self.plots["msgperday"] = (self.plot_msgperday("Plot-msg.html"), "Plot-msg.html", "Number of messages per day")
        self.plots["msgcumul"] = (self.plot_msgcumul("Plot-msgcumul.html"), "Plot-msgcumul.html", "Number of cumulatives messages")
        self.plots["top10"] = (self.plot_usertopx(10, "Plot-top10.html"), "Plot-top10.html", "Number of cumulatives messages for the Top 10 users")
        self.plots["top20"] = (self.plot_usertopx(20, "Plot-top20.html"), "Plot-top20.html", "Number of cumulatives messages for the Top 20 users")

#        self.stats = OrderedDict()
#        self.stats["top10perday"] = (self.top10_per_day("Stats-top10perday.html"), "Stats-top10perday.html", "Standings history")

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
                            for (i, elem) in enumerate(self.top10_yesterday()):
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
#                     with tag("ul", ("style", "list-style-type:none")):
                        # for _, stat in self.stats.items():
                            # if stat[1] and stat[2]:
                                # with tag("li"):
                                    # with tag('a', href=stat[1]):
#                                         text(stat[2])
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

    def plot_msgperday(self, path):
        msg_average = []
        for i, cum in enumerate(self.cumul):
            msg_average.append(int(cum / (i + 1)))

        line1 = go.Bar(x=self.date_array,
                       y=self.counts,
                       name="Messages per day")

        line2 = go.Scatter(x=self.date_array,
                           y=msg_average,
                           name="Average messages per day")

        return (generate_plot({"data": [line1, line2],
                               "layout": go.Layout(title="Number of messages per day in #%s (%s)" % (self.summary["Channel name"], self.summary["Server name"]))},
                              self.plots_dir + path))

    def plot_msgcumul(self, path):
        return (generate_plot({"data": [go.Scatter(x=self.date_array, y=self.cumul)],
                               "layout": go.Layout(title="Number of cumulatives messages in #%s (%s)" % (self.summary["Channel name"], self.summary["Server name"]))},
                              self.plots_dir + path))

    def plot_usertopx(self, max, path):
        cursor = self.db.cursor()
        cursor.execute("SELECT author_id FROM 'log_{}-{}';".format(self.summary["Server ID"], self.summary["Channel ID"]))

        top = Counter(elem[0] for elem in cursor.fetchall()).most_common(max)
        top_users_ids = [elem[0] for elem in top]
        print(top)
        print(top_users_ids)
        users_line = []
        for i, user_id in enumerate(top_users_ids):
            print(i + 1)

            counts = [self.get_count_per_date(date, user=user_id) for date in self.date_array]
            cumul = list(cumultative_sum(counts))

            cursor.execute("SELECT name, nick FROM members_{} WHERE id LIKE '{}';".format(self.summary["Server ID"], user_id))
            user = cursor.fetchone()
            if not user:
                user = ("UNKNOWN ({})".format(user_id), None)

            line = go.Scatter(x=self.date_array,
                              y=cumul,
                              name=user[1] if user[1] else user[0])
            users_line.append(line)
        return (generate_plot({"data": users_line,
                               "layout": go.Layout(title="Number of cumulatives messages for the Top %d users in #%s (%s)" % (max, self.summary["Channel name"], self.summary["Server name"]))},
                              self.plots_dir + path))

    def top10_per_day(self, path):
        # user_list = sort(list(set(([b for a,b in meta_list]))))
        text = "<pre>"
        meta_list = [(meta[0].split(" ")[0], meta[1]) for meta in self.meta_list]
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
        self.write_raw_text_in_html(text, path)
        return (text)

    def top10_yesterday(self):
        # user_list = sort(list(set(([b for a,b in meta_list]))))
        standing = []
        plain = ""

        # Not hardcoded please
        timezone = 'Europe/Paris'

        cursor = self.db.cursor()

        yesterday = datetime.combine(date.today() - timedelta(days=1), datetime.min.time())
        day_begin = yesterday + pytz.timezone(timezone).localize(yesterday).utcoffset()
        day_end = yesterday + pytz.timezone(timezone).localize(yesterday + timedelta(days=1)).utcoffset() + timedelta(days=1)

        cursor.execute("SELECT author_id FROM 'log_{}-{}' WHERE time >= ? AND time < ?".format(self.summary["Server ID"], self.summary["Channel ID"]),
                       (int(day_begin.timestamp()), int(day_end.timestamp())))

        top = Counter(elem[0] for elem in cursor.fetchall()).most_common(10)

        if (len(top) == 0):
            plain = "No message has been posted in this channel yesterday"
            return (standing)

        print(top)
        for (i, elem) in enumerate(top):
            cursor.execute("SELECT name, nick FROM members_{} WHERE id LIKE '{}';".format(self.summary["Server ID"], elem[0]))
            user_names = cursor.fetchone()
            user_name = user_names[1] if user_names[1] else user_names[0]
            standing.append((user_name, elem[1]))
            plain += "{}.\t{}\t{}\n".format(i + 1, elem[1], user_name)
        print(plain)
        self.top10yesterday = plain
        return (standing)


# Is this really useful?
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
