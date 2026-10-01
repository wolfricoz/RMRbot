import json
import os
from abc import ABC

from databases.exceptions.ConfigNotFound import ConfigNotFound
from databases.exceptions.KeyNotFound import KeyNotFound


class ConfigData(ABC):
    """
    The goal of this class is to save the config to reduce database calls for the config; especially the roles.
    """
    conf = {}

    def __init__(self):
        pass

    def load_guild(self, guildid):
        # Imported here because ConfigTransactions imports ConfigData to reload the cache after changes.
        from databases.transactions.ConfigTransactions import ConfigTransactions
        config = ConfigTransactions.server_config_get(guildid)

        settings = config
        # settings = ConfigTransactions.server_config_get(guildid)
        self.conf[guildid] = {}
        self.conf[guildid]["SEARCH"] = {}
        self.conf[guildid]["BAN"] = {}

        add_to_config = ['MOD', 'ADMIN', 'ADD', 'REM', "RETURN", "FORUM"]
        for add in add_to_config:
            self.conf[guildid][add] = []

        for x in settings:
            if x.key in add_to_config:
                self.conf[guildid][x.key].append(int(x.value))
                continue
            if x.key.upper().startswith("SEARCH"):
                self.conf[guildid]["SEARCH"][x.key.replace('SEARCH-', '')] = x.value
                continue
            if x.key.upper().startswith("BAN"):
                self.conf[guildid]["BAN"][x.key.replace('BAN-', '')] = x.value
                continue
            self.conf[guildid][x.key] = x.value

    def get_config(self, guildid):
        try:
            return self.conf[guildid]
        except KeyError:
            raise ConfigNotFound

    def get_key_int(self, guildid: int, key: str):
        try:
            return int(self.conf[guildid][key.upper()])
        except KeyError:
            raise KeyNotFound(key.upper())

    def get_key(self, guildid: int, key: str):
        try:
            return self.conf[guildid][key.upper()]

        except KeyError:
            raise KeyNotFound(key.upper())

    def get_key_or_none(self, guildid: int, key: str):
        return self.conf[guildid].get(key.upper(), None)

    def output_to_json(self):
        """This is for debugging only."""
        if os.path.isdir('debug') is False:
            os.mkdir('debug')
        with open('debug/config.json', 'w') as f:
            json.dump(self.conf, f, indent=4)
