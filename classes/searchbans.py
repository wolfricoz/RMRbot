import json
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands, tasks
import logging
import classes.databaseController
from classes import permissions
from classes.databaseController import ConfigData, TimersTransactions

async def remove(member: discord.Member, role, timer):
    await member.remove_roles(role)
    TimersTransactions.remove_timer(timer.id)
    logging.debug(f"Removed searchban from {member.name}")
