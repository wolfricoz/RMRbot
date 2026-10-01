from abc import ABC, abstractmethod

from sqlalchemy.sql import Select

import databases.current as db
from databases.current import Config
from databases.session import session
from databases.transactions.ConfigData import ConfigData
from databases.transactions.DatabaseTransactions import DatabaseTransactions


class ConfigTransactions(ABC):

    @staticmethod
    @abstractmethod
    def config_unique_add(guildid: int, key: str, value, overwrite):
        # This function should check if the item already exists, if so it will override it or throw an error.
        value = str(value)
        if ConfigTransactions.key_exists_check(guildid, key) is True and overwrite is False:
            return False
        item = db.Config(guild=guildid, key=key.upper(), value=value)
        session.merge(item)
        DatabaseTransactions.commit(session)
        ConfigData().load_guild(guildid)
        return True

    @staticmethod
    @abstractmethod
    def toggle_welcome(guildid: int, key: str, value):
        # This function should check if the item already exists, if so it will override it or throw an error.
        value = str(value)
        guilddata = session.scalar(Select(Config).where(Config.guild == guildid, Config.key == key))
        if guilddata is None:
            ConfigTransactions.config_unique_add(guildid, key, value, overwrite=True)
            return
        guilddata.value = value
        DatabaseTransactions.commit(session)
        ConfigData().load_guild(guildid)
        return True

    @staticmethod
    @abstractmethod
    def config_unique_get(guildid: int, key: str):
        if ConfigTransactions.key_exists_check(guildid, key) is False:
            return
        exists = session.scalar(Select(db.Config).where(db.Config.guild == guildid, db.Config.key == key.upper()))
        return exists

    @staticmethod
    @abstractmethod
    def config_key_add(guildid: int, key: str, value, overwrite):
        value = str(value)
        if ConfigTransactions.key_multiple_exists_check(guildid, key, value) is True and overwrite is False:
            return False
        item = db.Config(guild=guildid, key=key.upper(), value=value)
        session.add(item)
        DatabaseTransactions.commit(session)
        ConfigData().load_guild(guildid)
        return True

    @staticmethod
    @abstractmethod
    def key_multiple_exists_check(guildid: int, key: str, value):
        exists = session.scalar(
                Select(db.Config).where(db.Config.guild == guildid, db.Config.key == key, db.Config.value == value))
        session.close()
        if exists is not None:
            return True
        return False

    @staticmethod
    @abstractmethod
    def config_key_remove(guildid: int, key: str, value):
        if ConfigTransactions.key_multiple_exists_check(guildid, key, value) is False:
            return False
        exists = session.scalar(
                Select(db.Config).where(db.Config.guild == guildid, db.Config.key == key, db.Config.value == value))
        session.delete(exists)
        DatabaseTransactions.commit(session)
        ConfigData().load_guild(guildid)

    @staticmethod
    @abstractmethod
    def config_unique_remove(guildid: int, key: str):
        if ConfigTransactions.key_exists_check(guildid, key) is False:
            return False
        exists = session.scalar(
                Select(db.Config).where(db.Config.guild == guildid, db.Config.key == key))
        session.delete(exists)
        DatabaseTransactions.commit(session)
        ConfigData().load_guild(guildid)

    @staticmethod
    @abstractmethod
    def key_exists_check(guildid: int, key: str):
        exists = session.scalar(
                Select(db.Config).where(db.Config.guild == guildid, db.Config.key == key))
        session.close()
        if exists is not None:
            return True
        return False

    @staticmethod
    @abstractmethod
    def server_add(guildid):
        g = db.Servers(guild=guildid)
        session.merge(g)
        DatabaseTransactions.commit(session)
        ConfigTransactions.welcome_add(guildid)
        ConfigData().load_guild(guildid)

    @staticmethod
    @abstractmethod
    def welcome_add(guildid):
        if ConfigTransactions.key_exists_check(guildid, "WELCOME") is True:
            return
        welcome = Config(guild=guildid, key="WELCOME", value="ENABLED")
        session.merge(welcome)
        DatabaseTransactions.commit(session)

    @staticmethod
    @abstractmethod
    def server_config_get(guildid):
        return session.scalars(Select(db.Config).where(db.Config.guild == guildid)).all()
