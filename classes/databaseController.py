import json
from abc import ABC, abstractmethod
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy.sql import Select
from sqlalchemy.exc import IntegrityError

import databases.current as db
from databases.current import *

session = Session(bind=db.engine)


class ConfigNotFound(Exception):
    """config item was not found or has not been added yet."""

    def __init__(self, message="guild config has not been loaded yet or has not been created yet."):
        self.message = message
        super().__init__(self.message)


class KeyNotFound(Exception):
    """config item was not found or has not been added yet."""

    def __init__(self, key):
        self.key = key
        self.message = f"`{key}` not found in config, please add it using /config"
        super().__init__(self.message)


class UserNotFound(Exception):
    """config item was not found or has not been added yet."""

    def __init__(self, key):
        self.key = key
        self.message = f"`{key}` not found in config, please add it using /config"
        super().__init__(self.message)


class UserTransactions(ABC):

    @staticmethod
    @abstractmethod
    def add_user_empty(userid: int, overwrite=False):
        if UserTransactions.user_exists(userid) is True and overwrite is False:
            return False
        item = db.Users(uid=userid)
        session.merge(item)
        session.commit()
        return True

    @staticmethod
    @abstractmethod
    def add_user_full(userid: int, dob):
        item = db.Users(uid=userid, dob=datetime.strptime(dob, "%m/%d/%Y"), entry=datetime.now(tz=timezone.utc))
        session.merge(item)
        session.commit()
        return True

    @staticmethod
    @abstractmethod
    def update_user_dob(userid: int, dob: str):
        userdata: Users = session.scalar(Select(Users).where(Users.uid == userid))
        if userdata is None:
            print("entry not found, making a new one.")
            UserTransactions.add_user_full(userid, dob)
            return False
        print("entry found, updating now")
        userdata.dob = datetime.strptime(dob, "%m/%d/%Y")
        userdata.entry = datetime.now(tz=timezone.utc)
        print(datetime.now(tz=timezone.utc))
        session.commit()
        return True

    @staticmethod
    @abstractmethod
    def add_idcheck(userid: int, reason: str):
        UserTransactions.add_user_empty(userid, True)
        idcheck = IdVerification(uid=userid, reason=reason, idcheck=True)
        session.add(idcheck)
        session.commit()


    @staticmethod
    @abstractmethod
    def set_idcheck_to_true(userid: int, reason):
        userdata: IdVerification = session.scalar(Select(IdVerification).where(IdVerification.uid == userid))
        if userdata is None:
            UserTransactions.add_idcheck(userid, reason)
            return
        userdata.idcheck = True
        userdata.reason = reason
        session.commit()

    @staticmethod
    @abstractmethod
    def set_idcheck_to_false(userid: int, ):
        userdata: IdVerification = session.scalar(Select(IdVerification).where(IdVerification.uid == userid))
        if userdata is None:
            pass
        userdata.idcheck = False
        userdata.reason = None
        session.commit()

    @staticmethod
    @abstractmethod
    def get_user(userid: int):
        userdata = session.scalar(Select(Users).where(Users.uid == userid))
        session.close()
        return userdata

    @staticmethod
    @abstractmethod
    def get_user_id_info(userid: int):
        userdata = session.scalar(Select(IdVerification).where(IdVerification.uid == userid))
        session.close()
        return userdata

    # def add_dob(guildid: int, key: str, value, overwrite):
    #     # This function should check if the item already exists, if so it will override it or throw an error.
    #     value = str(value)
    #     if db_user_transactions.user_exists(guildid, key) is True and overwrite is False:
    #         return
    #     item = db.Config(guild=guildid, key=key.upper(), value=value)
    #     session.merge(item)
    #     session.commit()
    #     configData().load_guild(guildid)
    #     return True

    @staticmethod
    @abstractmethod
    def update():
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def config_unique_remove(guildid: int, key: str):
        if ConfigTransactions.key_exists_check(guildid, key) is False:
            return False
        exists = session.scalar(Select(db.Config).where(db.Config.guild == guildid, db.Config.key == key.upper()))
        session.delete(exists)
        session.commit()
        configData().load_guild(guildid)
        return True

    @staticmethod
    @abstractmethod
    def user_exists(userid: int):
        exists = session.scalar(
                Select(db.Users).where(db.Users.uid == userid))
        session.close()
        if exists is None:
            return False
        return True, exists


# RULE: ALL db transactions have to go through this file. Keep to it dumbass
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
        session.commit()
        configData().load_guild(guildid)
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
        session.commit()
        configData().load_guild(guildid)
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
        session.close()
        configData().load_guild(guildid)

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
        session.commit()

    @staticmethod
    @abstractmethod
    def server_config_get(guildid):
        return session.scalars(Select(db.Config).where(db.Config.guild == guildid)).all()


class configData(ABC):
    """
    The goal of this class is to save the config to reduce database calls for the config; especially the roles.
    """
    conf = {}

    def __init__(self):
        pass

    def load_guild(self, guildid):
        settings = ConfigTransactions.server_config_get(guildid)
        self.conf[guildid] = {}
        self.conf[guildid]['MOD'] = []
        self.conf[guildid]['ADMIN'] = []
        for x in settings:
            if x.key in ['MOD', 'ADMIN']:
                self.conf[guildid][x.key].append(int(x.value))
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
            raise KeyNotFound(key)

    def get_key(self, guildid: int, key: str):
        try:
            return self.conf[guildid][key.upper()]
        except KeyError:
            raise KeyNotFound(key)

    def output_to_json(self):
        """This is for debugging only."""
        if os.path.isdir('debug') is False:
            os.mkdir('debug')
        with open('debug/config.json', 'w') as f:
            json.dump(self.conf, f, indent=4)
