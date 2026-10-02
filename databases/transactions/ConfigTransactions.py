from sqlalchemy.sql import Select

import databases.current as db
from databases.current import Config
from databases.transactions.ConfigData import ConfigData
from databases.transactions.DatabaseTransactions import DatabaseTransactions


class ConfigTransactions(DatabaseTransactions):

    def config_unique_add(self, guildid: int, key: str, value, overwrite):
        # This function should check if the item already exists, if so it will override it or throw an error.
        value = str(value)
        if self.key_exists_check(guildid, key) is True and overwrite is False:
            return False
        with self.createsession() as session:
            session.merge(db.Config(guild=guildid, key=key.upper(), value=value))
            self.commit(session)
        ConfigData().load_guild(guildid)
        return True

    def toggle_welcome(self, guildid: int, key: str, value):
        # This function should check if the item already exists, if so it will override it or throw an error.
        value = str(value)
        with self.createsession() as session:
            guilddata = session.scalar(Select(Config).where(Config.guild == guildid, Config.key == key.upper()))
            if guilddata is None:
                session.close()
                self.config_unique_add(guildid, key, value, overwrite=True)
                return
            guilddata.value = value
            self.commit(session)
        ConfigData().load_guild(guildid)
        return True

    def config_unique_get(self, guildid: int, key: str):
        if self.key_exists_check(guildid, key) is False:
            return
        with self.createsession() as session:
            return session.scalar(Select(db.Config).where(db.Config.guild == guildid, db.Config.key == key.upper()))

    def config_key_add(self, guildid: int, key: str, value, overwrite):
        value = str(value)
        if self.key_multiple_exists_check(guildid, key, value) is True and overwrite is False:
            return False
        with self.createsession() as session:
            session.add(db.Config(guild=guildid, key=key.upper(), value=value))
            self.commit(session)
        ConfigData().load_guild(guildid)
        return True

    def key_multiple_exists_check(self, guildid: int, key: str, value):
        with self.createsession() as session:
            exists = session.scalar(
                    Select(db.Config).where(db.Config.guild == guildid, db.Config.key == key.upper(), db.Config.value == value))
        return exists is not None

    def config_key_remove(self, guildid: int, key: str, value):
        with self.createsession() as session:
            exists = session.scalar(
                    Select(db.Config).where(db.Config.guild == guildid, db.Config.key == key.upper(), db.Config.value == value))
            if exists is None:
                return False
            session.delete(exists)
            self.commit(session)
        ConfigData().load_guild(guildid)

    def config_unique_remove(self, guildid: int, key: str):
        with self.createsession() as session:
            exists = session.scalar(
                    Select(db.Config).where(db.Config.guild == guildid, db.Config.key == key.upper()))
            if exists is None:
                return False
            session.delete(exists)
            self.commit(session)
        ConfigData().load_guild(guildid)

    def key_exists_check(self, guildid: int, key: str):
        with self.createsession() as session:
            exists = session.scalar(
                    Select(db.Config).where(db.Config.guild == guildid, db.Config.key == key.upper()))
        return exists is not None

    def server_add(self, guildid):
        with self.createsession() as session:
            session.merge(db.Servers(guild=guildid))
            self.commit(session)
        self.welcome_add(guildid)
        ConfigData().load_guild(guildid)

    def welcome_add(self, guildid):
        if self.key_exists_check(guildid, "WELCOME") is True:
            return
        with self.createsession() as session:
            session.merge(Config(guild=guildid, key="WELCOME", value="ENABLED"))
            self.commit(session)

    def server_config_get(self, guildid):
        with self.createsession() as session:
            return session.scalars(Select(db.Config).where(db.Config.guild == guildid)).all()
