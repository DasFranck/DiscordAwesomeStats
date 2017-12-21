#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import Counter, OrderedDict
from datetime import date, datetime, timedelta
import os
import sqlite3
import pytz

import plotly
import plotly.graph_objs as go
from jinja2 import Environment, FileSystemLoader


# UTILS
def cumultative_sum(values, start=0):
    for value in values:
        start += value
        yield start


class Plotify():
    """
    This class generates plots and html pages for a channel with into the output_path.
    The summary_dict describe this channel.
    """
    class EmptyChannelException(Exception):
        """ EmptyChannelException """
        pass

    def __init__(self, output_path, summary_dict):
        self.summary = summary_dict
        self.plots_dir = "{}/{}/{}/".format(
            output_path, self.summary["Server ID"], self.summary["Channel ID"]
            )

        self.plots = OrderedDict()
        self.stats = OrderedDict()

        if not os.path.exists("data"):
            os.makedirs("data")
        self.db = sqlite3.connect('data/database.db')

        cursor = self.db.cursor()
        cursor.execute("SELECT COUNT(*) FROM 'log_{}-{}'".format(self.summary["Server ID"],
                                                                 self.summary["Channel ID"]))
        msg_count = cursor.fetchone()[0]
        if msg_count == 0:
            raise self.EmptyChannelException

        self.get_date_array()
        self.counts = [self.get_count_per_date(date) for date in self.date_array]
        self.cumul = list(cumultative_sum(self.counts))
        if not os.path.exists(self.plots_dir):
            os.makedirs(self.plots_dir)
        self.top10_yesterday_plain = None
        self.top10_yesterday_tuple = None

        self.jinja_env = Environment(
            loader=FileSystemLoader('./templates')
        )

    def generate_plot(self, graph_dict, file_path):
        """
        Generate a plot from 'graph_dict', save it with plotlyjs
        embedded into 'file_path' and return it as a div without plotlyjs embedded.
        """
        try:
            template_plot_page = self.jinja_env.get_template('plot_page.html.j2')
            plot = plotly.offline.plot(
                graph_dict,
                show_link=False, auto_open=False,
                output_type="div", include_plotlyjs=False
                )

            with open(file_path, "w") as file:
                file.write(template_plot_page.render(plot=plot))
            return plot
        except:
            return ""

    def get_date_array(self):
        cursor = self.db.cursor()
        cursor.execute("SELECT MIN(time) FROM 'log_{}-{}'".format(self.summary["Server ID"],
                                                                  self.summary["Channel ID"]))
        first_message_timestamp = cursor.fetchone()[0]

        start = datetime.fromtimestamp(first_message_timestamp).date()
        end = datetime.today().date()
        delta = end - start

        datetime_array = [start + timedelta(days=i) for i in range(delta.days)]
        self.date_array = [x.strftime("%Y-%m-%d") for x in datetime_array]

    def get_count_per_date(self, target_date, user=None, timezone='Europe/Paris'):
        """
        Return the number of message at target_date.
        target_date can be str or datetime.datetime.

        It can be limited to the message of a user if specified.
        The timezone can also be specified.

        It must not be heavily used for a range of date, prefer get_count_per_date_array.
        """
        cursor = self.db.cursor()

        if isinstance(target_date, str):
            target_date = datetime.strptime(target_date, "%Y-%m-%d")

        day_begin = target_date + pytz.timezone(timezone).localize(target_date).utcoffset()
        day_end = target_date + pytz.timezone(timezone).localize(target_date + timedelta(days=1)).utcoffset() + timedelta(days=1)

        if user is None:
            cursor.execute("SELECT COUNT(*) FROM 'log_{}-{}' WHERE time >= ? AND time < ?".format(self.summary["Server ID"], self.summary["Channel ID"]),
                           (int(day_begin.timestamp()), int(day_end.timestamp())))
        else:
            cursor.execute("SELECT COUNT(*) FROM 'log_{}-{}' WHERE time >= ? AND time < ? AND author_id LIKE (?)".format(self.summary["Server ID"], self.summary["Channel ID"]),
                           (int(day_begin.timestamp()), int(day_end.timestamp()), user))
        return cursor.fetchone()[0]

    def get_count_per_date_array(self, start_date, end_date, user=None, timezone='Europe/Paris'):
        cursor = self.db.cursor()

        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
            

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
        self.plots["msgperday"] = (self.plot_msgperday("Plot-msg.html"), "Plot-msg.html", "Number of messages per day")
        self.plots["msgcumul"] = (self.plot_msgcumul("Plot-msgcumul.html"), "Plot-msgcumul.html", "Number of cumulatives messages")
        #self.plots["top10"] = (self.plot_usertopx(10, "Plot-top10.html"), "Plot-top10.html", "Number of cumulatives messages for the Top 10 users")
        #self.plots["top20"] = (self.plot_usertopx(20, "Plot-top20.html"), "Plot-top20.html", "Number of cumulatives messages for the Top 20 users")

#        self.stats["top10perday"] = (self.top10_per_day("Stats-top10perday.html"), "Stats-top10perday.html", "Standings history")

    def write_channel_main_html(self):
        template_channel_page = self.jinja_env.get_template('channel_page.html.j2')

        # Open's encoding must be specified because Windows...
        with open(self.plots_dir + "index.html", "w", encoding='utf-8') as file:
            file.write(template_channel_page.render(html_render_date_string=datetime.now().strftime("%T the %F"),
                                                    summary=self.summary,
                                                    top10_yesterday=self.top10_yesterday_tuple))

    def write_all_plots_html(self):
        template_all_plots = self.jinja_env.get_template('all_plots.html.j2')

        with open(self.plots_dir + "allplots.html", "w") as file:
            file.write(template_all_plots.render(plots=self.plots.items(),
                                                 html_render_date_string=datetime.now().strftime("%T the %F")))

    def write_standing_history_html(self):
        template_standing_history = self.jinja_env.get_template('standing_history.html.j2')

        with open(self.plots_dir + "standinghistory.html", "w") as file:
            file.write(template_standing_history.render(html_render_date_string=datetime.now().strftime("%T the %F")))

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

        return self.generate_plot({"data": [line1, line2],
                              "layout": go.Layout(title="Number of messages per day in #%s (%s)" % (self.summary["Channel name"], self.summary["Server name"]))},
                             self.plots_dir + path)

    def plot_msgcumul(self, path):
        return self.generate_plot({"data": [go.Scatter(x=self.date_array, y=self.cumul)],
                              "layout": go.Layout(title="Number of cumulatives messages in #%s (%s)" % (self.summary["Channel name"], self.summary["Server name"]))},
                             self.plots_dir + path)

    def plot_usertopx(self, max_users, path):
        cursor = self.db.cursor()
        cursor.execute("SELECT author_id FROM 'log_{}-{}';".format(self.summary["Server ID"], self.summary["Channel ID"]))

        top = Counter(elem[0] for elem in cursor.fetchall()).most_common(max_users)
        top_users_ids = [elem[0] for elem in top]
        users_line = []
        for i, user_id in enumerate(top_users_ids):
            print(i + 1)

            # Get daily message count for each top user 
            counts = [self.get_count_per_date(date, user=user_id) for date in self.date_array]
            cumul = list(cumultative_sum(counts))

            # Get nickname of a top user if it exist
            cursor.execute("SELECT name, nick FROM members_{} WHERE id LIKE '{}';".format(self.summary["Server ID"], user_id))
            user = cursor.fetchone()
            if not user:
                user = ("UNKNOWN ({})".format(user_id), None)

            line = go.Scatter(x=self.date_array,
                              y=cumul,
                              name=user[1] if user[1] else user[0])
            users_line.append(line)
        return self.generate_plot({"data": users_line,
                                   "layout": go.Layout(title="Number of cumulatives messages for the Top %d users in #%s (%s)" % (max_users, self.summary["Channel name"], self.summary["Server name"]))},
                                  self.plots_dir + path)

#    def top10_per_day(self, path):
#        # user_list = sort(list(set(([b for a,b in meta_list]))))
#        text = "<pre>"
#        meta_list = [(meta[0].split(" ")[0], meta[1]) for meta in meta_list]
#        meta_sorted = sorted(meta_list, key=operator.itemgetter(0))
#        meta_grouped = [list(group) for key, group in itertools.groupby(meta_sorted, operator.itemgetter(0))]
#        for meta_per_date in reversed(meta_grouped[:-1]):
#            count_map = {}
#            for meta in meta_per_date:
#                count_map[meta[1]] = count_map.get(meta[1], 0) + 1
#            top_list = sorted(count_map.items(), key=operator.itemgetter(1), reverse=True)[0:10]
#
#            text += "<b>" + meta_per_date[0][0] + "</b><br />"
#            for (i, elem) in enumerate(top_list):
#                text += "%d.\t%d\t%s<br />" % (i + 1, elem[1], html.escape(elem[0]))
#            if meta_per_date is not meta_grouped[0]:
#                text += "<br />"
#        text += "</pre>"
#        self.write_raw_text_in_html(text, path)
#        return (text)

    def get_top10_yesterday(self):
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

        if not top:
            plain = "No message has been posted in this channel yesterday"

        else:
            for (i, elem) in enumerate(top):
                cursor.execute("SELECT name, nick FROM members_{} WHERE id LIKE '{}';".format(self.summary["Server ID"], elem[0]))
                user_names = cursor.fetchone()
                user_name = user_names[1] if user_names[1] else user_names[0]
                standing.append((user_name, elem[1]))
                plain += "{}.\t{}\t{}\n".format(i + 1, elem[1], user_name)
        self.top10_yesterday_plain = plain
        self.top10_yesterday_tuple = standing

    def run(self):
        self.plotify()
        self.get_top10_yesterday()
#       self.write_standing_history_html()
        self.write_all_plots_html()
        self.write_channel_main_html()