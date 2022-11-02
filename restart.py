import sys
import os
from asyncio import sleep
from discord.ext import commands
os.execv(sys.executable, ['python'] + sys.argv)
