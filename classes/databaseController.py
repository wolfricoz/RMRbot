import datetime
import json
from abc import ABC, abstractmethod
from datetime import timezone, datetime, timedelta

import sqlalchemy.exc
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

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
    def add_user_full(userid, dob):
        try:
            item = db.Users(uid=userid, dob=datetime.strptime(dob, "%m/%d/%Y"), entry=datetime.now(tz=timezone.utc))
            session.merge(item)
            session.commit()
            return True
        except ValueError:
            return False

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
    def user_delete(userid: int):
        try:
            userdata: Users = session.scalar(Select(Users).where(Users.uid == userid))
            if userdata is None:
                return False
            session.delete(userdata)
            session.commit()
            return True
        except sqlalchemy.exc.IntegrityError:
            session.rollback()
            return False

    @staticmethod
    @abstractmethod
    def get_user(userid: int):
        userdata = session.scalar(Select(Users).where(Users.uid == userid))
        session.close()
        return userdata

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
        ConfigData().load_guild(guildid)
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

    #Warning related functions
    @staticmethod
    @abstractmethod
    def user_add_warning(userid: int, reason: str):
        item = db.Warnings(uid=userid, reason=reason, type="WARN")
        session.add(item)
        session.commit()
        return True

    @staticmethod
    @abstractmethod
    def user_get_warnings(userid: int, type):
        warning_dict = {}
        warning_list = []
        warnings = session.scalars(Select(Warnings).where(Warnings.uid == userid, Warnings.type == type.upper()).order_by(Warnings.uid)).all()
        session.close()
        if len(warnings) == 0 or warnings is None:
            return False
        for warnings in warnings:
            warning_dict[warnings.id] = warnings.reason
            warning_list.append(warnings.id)
        return warning_list, warning_dict

    @staticmethod
    @abstractmethod
    def user_remove_warning(id : int):
        warning = session.scalar(Select(Warnings).where(Warnings.id == id))
        session.delete(warning)
        session.commit()




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
        session.commit()
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
        session.commit()
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
        session.commit()
        ConfigData().load_guild(guildid)

    @staticmethod
    @abstractmethod
    def config_unique_remove(guildid: int, key: str):
        if ConfigTransactions.key_exists_check(guildid, key) is False:
            return False
        exists = session.scalar(
                Select(db.Config).where(db.Config.guild == guildid, db.Config.key == key))
        session.delete(exists)
        session.commit()
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
        session.commit()
        ConfigTransactions.welcome_add(guildid)
        ConfigData().load_guild(guildid)

    @staticmethod
    @abstractmethod
    def welcome_add(guildid):
        if ConfigTransactions.key_exists_check(guildid, "WELCOME") is True:
            return
        welcome = Config(guild=guildid, key="WELCOME", value="ENABLED")
        session.merge(welcome)
        session.commit()

    @staticmethod
    @abstractmethod
    def server_config_get(guildid):
        return session.scalars(Select(db.Config).where(db.Config.guild == guildid)).all()


class VerificationTransactions(ABC):

    @staticmethod
    @abstractmethod
    def get_id_info(userid: int):
        userdata = session.scalar(Select(IdVerification).where(IdVerification.uid == userid))
        session.close()
        return userdata

    @staticmethod
    @abstractmethod
    def update_check(userid, reason: str = None, idcheck=True):
        userdata = session.scalar(Select(IdVerification).where(IdVerification.uid == userid))
        if userdata is None:
            VerificationTransactions.add_idcheck(userid, reason, idcheck)
            return
        userdata.reason = reason
        userdata.idcheck = idcheck
        session.commit()

    @staticmethod
    @abstractmethod
    def add_idcheck(userid: int, reason: str = None, idcheck=True):
        UserTransactions.add_user_empty(userid, True)
        idcheck = IdVerification(uid=userid, reason=reason, idcheck=idcheck)
        session.add(idcheck)
        session.commit()

    @staticmethod
    @abstractmethod
    def set_idcheck_to_true(userid: int, reason):
        userdata: IdVerification = session.scalar(Select(IdVerification).where(IdVerification.uid == userid))
        if userdata is None:
            VerificationTransactions.add_idcheck(userid, reason)
            return
        userdata.idcheck = True
        userdata.reason = reason
        session.commit()

    @staticmethod
    @abstractmethod
    def set_idcheck_to_false(userid: int, ):
        userdata: IdVerification = session.scalar(Select(IdVerification).where(IdVerification.uid == userid))
        if userdata is None:
            VerificationTransactions.add_idcheck(userid, idcheck=False)
            return
        userdata.idcheck = False
        userdata.reason = None
        session.commit()

    @staticmethod
    @abstractmethod
    def idverify_add(userid: int, dob: str, idcheck=True):
        UserTransactions.add_user_empty(userid, True)
        idcheck = IdVerification(uid=userid, verifieddob=datetime.strptime(dob, "%m/%d/%Y"), idverified=idcheck)
        session.add(idcheck)
        session.commit()
        UserTransactions.update_user_dob(userid, dob)

    @staticmethod
    @abstractmethod
    def idverify_update(userid, dob: str, idcheck=True):

        userdata = session.scalar(Select(IdVerification).where(IdVerification.uid == userid))
        if userdata is None:
            VerificationTransactions.add_idcheck(userid, dob)
            return
        userdata.verifieddob = datetime.strptime(dob, "%m/%d/%Y")
        userdata.idverified = idcheck
        session.commit()
        UserTransactions.update_user_dob(userid, dob)


class ConfigData(ABC):
    """
    The goal of this class is to save the config to reduce database calls for the config; especially the roles.
    """
    conf = {}

    def __init__(self):
        pass

    def load_guild(self, guildid):
        config = ConfigTransactions.server_config_get(guildid)

        settings = config
        # settings = ConfigTransactions.server_config_get(guildid)
        self.conf[guildid] = {}
        self.conf[guildid]["SEARCH"] = {}

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

    def get_key_or_none(self, guildid: int, key: str):
        return self.conf[guildid].get(key.upper(), None)

    def output_to_json(self):
        """This is for debugging only."""
        if os.path.isdir('debug') is False:
            os.mkdir('debug')
        with open('debug/config.json', 'w') as f:
            json.dump(self.conf, f, indent=4)


class SearchWarningTransactions(ABC):
    @staticmethod
    @abstractmethod
    def get_total_warnings(userid: int):
        total = 0
        active = 0
        monthsago = datetime.now() - timedelta(days=120)
        userdata = session.scalars(Select(Warnings).where(Warnings.uid == userid)).all()
        session.close()
        for x in userdata:
            if x.entry > monthsago:
                active += 1
            total += 1
        return total, active



    @staticmethod
    @abstractmethod
    def add_warning(userid: int, reason: str = None):
        UserTransactions.add_user_empty(userid)
        search_warning = Warnings(uid=userid, reason=reason, type="SEARCH")
        session.add(search_warning)
        session.commit()
        total_warnings, active_warnings = SearchWarningTransactions.get_total_warnings(userid)
        return total_warnings, active_warnings

