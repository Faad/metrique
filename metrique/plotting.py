#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
# Author: "Juraj Niznan" <jniznan@redhat.com>
# Author: "Chris Ward <cward@redhat.com>

'''
metrique.plotting
~~~~~~~~~~~~~~~~~

This module contains a plotter wrapper that provides
defaults and additional helper functionality for
quickly generating plots with pandas and matplotlib
'''

from __future__ import unicode_literals, absolute_import

try:
    from matplotlib import pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

from metrique.utils import utcnow

# Some nice colors, stored here for convenience.
COLORS = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
          '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
ALPHAS = ['#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5',
          '#c49c94', '#f7b6d2', '#c7c7c7', '#dbdb8d', '#9edae5']
CNAMES = {'blue': 0, 'b': 0,
          'orange': 1,
          'green': 2, 'g': 2,
          'red': 3, 'r': 3,
          'violet': 4,
          'brown': 5,
          'pink': 6,
          'grey': 7,
          'khaki': 8, 'y': 8,
          'cyan': 9}


def timestamp_figure(figure, stamp=True):
    # drop seconds:
    t = str(utcnow(as_datetime=True)).split('.')[0][:-3]
    if isinstance(stamp, basestring):
        t = '%s %s' % (stamp, t)
    figure.text(0.95, 0.05, t, fontsize=12, color='gray',
                ha='right', va='bottom', alpha=0.5)


class Plotter(object):
    ''' Convenince plotting wrapper '''

    def __init__(self, figsize=(10, 6), stacked=True, title='', stamp=True,
                 **kwargs):
        '''
        :param (int, int) figsize:
            The size of the figure.
        :param bool stacked:
            If true then the resulting graph will be stacked
        :param string title:
            Title of the graph
        :param boolean/string stamp:
            Put a timestamp in the bottom right corner.
            If True the current time will be stamped.
            If string then the string concatenated with the current time
            will be stamped.
        '''
        if not HAS_MATPLOTLIB:
            raise RuntimeError("`pip install matplotlib` required")
        self.counter = 0
        self.stacked = stacked
        self.running_sum = 0
        self.fig = plt.figure(figsize=figsize)
        if title:
            plt.title(title)
        if stamp:
            timestamp_figure(self.fig, stamp)

    def get_color(self, color):
        '''
        Returns a color to use.

        :param integer/string color:
            Color for the plot. Can be an index for the color from COLORS
            or a key(string) from CNAMES.
        '''
        if color is None:
            color = self.counter
        if isinstance(color, str):
            color = CNAMES[color]
        self.counter = color + 1
        color %= len(COLORS)
        return color

    def plot(self, series, label='', color=None, style=None):
        '''
        Wrapper around plot.

        :param pandas.Series series:
            The series to be plotted, all values must be positive if stacked
            is True.
        :param string label:
            The label for the series.
        :param integer/string color:
            Color for the plot. Can be an index for the color from COLORS
            or a key(string) from CNAMES.
        :param string style:
            Style forwarded to the plt.plot.
        '''
        color = self.get_color(color)
        if self.stacked:
            series += self.running_sum
            plt.fill_between(series.index, self.running_sum, series,
                             facecolor=ALPHAS[color])
            self.running_sum = series
            plt.gca().set_ylim(bottom=0, top=int(series.max() * 1.05))
        series.plot(label=label, c=COLORS[color], linewidth=2, style=style)

    def plots(self, series_list, label_list, colors=None):
        '''
        Plots all the series from the list.
        The assumption is that all of the series share the same index.

        :param list series_list:
            A list of series which should be plotted
        :param list label_list:
            A list of labels corresponding to the series
        :params list list_of_colors:
            A list of colors to use.
        '''
        colors = colors or range(len(series_list))
        for series, label, color in zip(series_list, label_list, colors):
            self.plot(series=series, label=label, color=color)

    def line(self, x, label=None, y='bottom', color='grey', ax=None, **kwargs):
        '''
        Creates a vertical line in the plot.

        :param x:
            The x coordinate of the line. Should be in the same units
            as the x-axis.
        :param string label:
            The label to be displayed.
        :param y:
            May be 'top', 'bottom' or int.
            The y coordinate of the text-label.
        :param color color:
            The color of the line.
        '''
        if ax is None:
            ax = plt
            y0, y1 = ax.ylim()
        else:
            y0, y1 = ax.get_ylim()
        ax.axvline(x, color=color, **kwargs)
        if label is not None:
            verticalalignment = 'bottom'
            if y == 'bottom':
                y = y0 + (y1 - y0) / 25.
            if y == 'top':
                verticalalignment = 'top'
                y = y0 + (y1 - y0) * 24 / 25.
            ax.annotate('\n' + label, (x, y), rotation=90,
                        verticalalignment=verticalalignment)

    def lines(self, lines_dict, y='bottom', color='grey', **kwargs):
        '''
        Creates vertical lines in the plot.

        :param lines_dict:
            A dictionary of label, x-coordinate pairs.
        :param y:
            May be 'top', 'bottom' or int.
            The y coordinate of the text-labels.
        :param color color:
            The color of the lines.
        '''
        for l, x in lines_dict.items():
            self.line(x, l, y, color, **kwargs)

    def legend(self, **kwargs):
        plt.legend(**kwargs)


class DiffPlotter(Plotter):
    def __init__(self, figsize=(10, 7), stacked=True, title='', stamp=True,
                 autodiffs=True, **kwargs):
        '''
        :param (int, int) figsize:
            The size of the figure.
        :param bool stacked:
            If true then the resulting graph will be stacked
        :param string title:
            Title of the graph
        :param boolean/string stamp:
            Put a timestamp in the bottom right corner.
            If True the current time will be stamped.
            If string then the string concatenated with the current time
            will be stamped.
        :param boolean autodiffs:
            Indicates whether the diffs should be computed automatically if
            they are not specified.
        '''
        super(DiffPlotter, self).__init__(figsize=figsize, stacked=stacked,
                                          title=title, stamp=stamp, **kwargs)
        self.autodiffs = autodiffs
        self.ax1 = plt.subplot2grid((4, 1), (0, 0), rowspan=3)
        #plt.title(title)
        plt.setp(self.ax1.get_xticklabels(), visible=False)
        self.ax2 = plt.subplot2grid((4, 1), (3, 0), sharex=self.ax1)
        plt.subplots_adjust(hspace=.15)

    def plot(self, series, series_diff=None, label='', color=None, style=None):
        '''
        :param pandas.Series series:
            The series to be plotted, all values must be positive if stacked
            is True.
        :param pandas.Series series_diff:
            The series representing the diff that will be plotted in the
            bottom part.
        :param string label:
            The label for the series.
        :param integer/string color:
            Color for the plot. Can be an index for the color from COLORS
            or a key(string) from CNAMES.
        :param string style:
            Style forwarded to the plt.plot.
        '''
        color = self.get_color(color)
        if series_diff is None and self.autodiffs:
            series_diff = series.diff()
        if self.stacked:
            series += self.running_sum
            self.ax1.fill_between(series.index, self.running_sum, series,
                                  facecolor=ALPHAS[color])
            self.running_sum = series
            self.ax1.set_ylim(bottom=0, top=int(series.max() * 1.05))
        series.plot(label=label, c=COLORS[color], linewidth=2, style=style,
                    ax=self.ax1)
        if series_diff is not None:
            series_diff.plot(label=label, c=COLORS[color], linewidth=2,
                             style=style, ax=self.ax2)

    def line(self, x, label=None, y='bottom', color='grey', **kwargs):
        '''
        Creates a vertical line in the plot.

        :param x:
            The x coordinate of the line. Should be in the same units
            as the x-axis.
        :param string label:
            The label to be displayed.
        :param y:
            May be 'top', 'bottom' or int.
            The y coordinate of the text-label.
        :param color color:
            The color of the line.
        '''
        super(DiffPlotter, self).line(x, label, y, color, self.ax1, **kwargs)
        super(DiffPlotter, self).line(x, '', 0, color, self.ax2, **kwargs)

    def legend(self, **kwargs):
        self.ax1.legend(**kwargs)


class BarPlot(object):
    def __init__(self, title='', figsize=(10, 5)):
        if not HAS_MATPLOTLIB:
            raise RuntimeError("`pip install matplotlib` required")
        self.counter = 0
        self.fig, self.ax1 = plt.subplots(figsize=figsize)
        self.ax2 = self.ax1.twinx()
        plt.title(title)
        self.bar_lim((0, 100))

    def get_color(self, color):
        '''
        Returns a color to use.

        :param integer/string color:
            Color for the plot. Can be an index for the color from COLORS
            or a key(string) from CNAMES.
        '''
        if color is None:
            color = self.counter
        if isinstance(color, str):
            color = CNAMES[color]
        self.counter = color + 1
        color %= len(COLORS)
        return color

    def plot(self, series, label='', linewidth=3, marker='o', color=None):
        color = self.get_color(color)
        xticks = range(len(series))
        self.ax1.plot(xticks,  series.values, label=label,
                      linewidth=linewidth, marker=marker, color=COLORS[color])

    def plot_label(self, label):
        self.ax1.set_ylabel(label)

    def plot_lim(self, (ymin, ymax)):
        self.ax1.set_ylim((ymin, ymax))

    def bar(self, series, label='', alpha=0.2, color=None):
        color = self.get_color(color)
        xticks = map(lambda v: v - 0.4, range(len(series)))
        self.ax2.bar(xticks, series.values, label=label,
                     alpha=alpha, color=COLORS[color])

    def bar_label(self, label):
        self.ax2.set_ylabel(label)

    def bar_lim(self, (ymin, ymax)):
        self.ax2.set_ylim((ymin, ymax))

    def xticks(self, names):
        self.ax1.set_xticks(range(len(names)))
        self.ax1.set_xticklabels(names)

    def xlabel(self, label):
        self.ax1.set_xlabel(label)

    def legend(self, **kwargs):
        lines, labels = self.ax1.get_legend_handles_labels()
        lines2, labels2 = self.ax2.get_legend_handles_labels()
        self.ax1.legend(lines + lines2, labels + labels2, **kwargs)
