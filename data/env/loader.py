"""This file makes global environment variables from a .env file available throughout the bot."""

import os
from dotenv import load_dotenv

def load_environment(env_file: str = '.env', override: bool = False):
		"""Load environment variables from a .env file."""

		load_dotenv(env_file, override=override)
		#important note: ALL environment variables will be made global, an environment variable is always a string so you must take that into account.

def env(key: str, default = None):
	"""A simple helper function to get the environment variable, this can be expanded to catch certain words to create types (example: TRUE being converted to a boolean)"""
	return os.getenv(key.upper(), default)


