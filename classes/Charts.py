"""Charts for the admin statistics commands, drawn with matplotlib into PNG files to attach to a message.

Uses matplotlib's object API instead of pyplot, so charts can be drawn in a worker thread (see modules/stats.py)
without blocking the bot or sharing pyplot's global state."""
import io
from datetime import date

import discord
from matplotlib.dates import AutoDateLocator, ConciseDateFormatter
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

# Discord's own colours first, so the charts sit well next to embeds.
COLORS = ["#5865F2", "#57F287", "#ED4245", "#FEE75C", "#EB459E", "#3BA55C", "#FAA61A", "#99AAB5", "#2C2F33"]


def daily(title: str, days: list[date], series: dict[str, list[int]], filename: str, stacked: bool = True) -> discord.File :
	"""Counts per day: stacked bars, or lines when stacked is False. Each series has one value per day."""
	figure = Figure(figsize=(10, 4.5), dpi=120)
	axes = figure.subplots()
	bottom = [0] * len(days)
	for (label, values), color in zip(series.items(), COLORS * 2) :
		if stacked :
			axes.bar(days, values, bottom=bottom, label=label, color=color, width=0.8)
			bottom = [b + v for b, v in zip(bottom, values)]
		else :
			axes.plot(days, values, label=label, color=color, marker="o" if len(days) <= 31 else None, linewidth=2)
	locator = AutoDateLocator()
	axes.xaxis.set_major_locator(locator)
	axes.xaxis.set_major_formatter(ConciseDateFormatter(locator))
	_finish(axes, title, legend=len(series) > 1)
	return _file(figure, filename)


def ranking(title: str, labels: list[str], values: list[int], filename: str) -> discord.File :
	"""Horizontal bars, the largest on top."""
	figure = Figure(figsize=(10, max(2.5, 0.45 * len(labels) + 1.2)), dpi=120)
	axes = figure.subplots()
	axes.barh(labels[: :-1], values[: :-1], color=COLORS[0])
	for index, value in enumerate(values[: :-1]) :
		axes.text(value, index, f" {value}", va="center")
	_finish(axes, title, legend=False, integer_axis="x")
	return _file(figure, filename)


def _finish(axes, title: str, legend: bool, integer_axis: str = "y") :
	axes.set_title(title, loc="left", fontsize=13, fontweight="bold")
	(axes.xaxis if integer_axis == "x" else axes.yaxis).set_major_locator(MaxNLocator(integer=True))
	axes.grid(axis=integer_axis, alpha=0.3)
	axes.spines[["top", "right"]].set_visible(False)
	if legend :
		axes.legend(frameon=False, loc="upper left", bbox_to_anchor=(1, 1))


def _file(figure: Figure, filename: str) -> discord.File :
	buffer = io.BytesIO()
	figure.savefig(buffer, format="png", bbox_inches="tight")
	buffer.seek(0)
	return discord.File(buffer, filename=filename)
