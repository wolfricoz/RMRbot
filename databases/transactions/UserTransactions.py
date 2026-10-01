from abc import ABC, abstractmethod
from datetime import datetime, timezone

import sqlalchemy.exc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import Select

import databases.current as db
from classes.encryption import Encryption
from databases.current import Users, Warnings
from databases.session import session
from databases.transactions.ConfigData import ConfigData
from databases.transactions.ConfigTransactions import ConfigTransactions
from databases.transactions.DatabaseTransactions import DatabaseTransactions


class UserTransactions(ABC):

    @staticmethod
    @abstractmethod
    def add_user_empty(userid: int, overwrite=False):
        if UserTransactions.user_exists(userid) is True and overwrite is False:
            return False
        item = db.Users(uid=userid)
        session.merge(item)
        DatabaseTransactions.commit(session)
        return True

    @staticmethod
    @abstractmethod
    def add_user_full(userid, dob, guildname):
        try:
            item = db.Users(uid=userid, entry=datetime.now(tz=timezone.utc), date_of_birth=Encryption().encrypt(dob), server=guildname)
            session.merge(item)
            DatabaseTransactions.commit(session)
            return True
        except ValueError:
            return False

    @staticmethod
    @abstractmethod
    def update_user_dob(userid: int, dob: str, guildname: str):
        userdata: Users = session.scalar(Select(Users).where(Users.uid == userid))
        if userdata is None:
            UserTransactions.add_user_full(userid, dob, guildname)
            return False
        userdata.date_of_birth = Encryption().encrypt(dob)
        userdata.entry = datetime.now(tz=timezone.utc)
        userdata.server = guildname
        DatabaseTransactions.commit(session)
        if userdata.date_of_birth is None:
            return False
        return True

    @staticmethod
    @abstractmethod
    def user_delete(userid: int):
        try:
            userdata: Users = session.scalar(Select(Users).where(Users.uid == userid))
            if userdata is None:
                return False
            session.delete(userdata)
            DatabaseTransactions.commit(session)
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
    def get_all_users():
        userdata = session.scalars(Select(Users)).all()
        session.close()
        return userdata

    @staticmethod
    @abstractmethod
    def update_entry_date(userid):
        try:
            userdata = session.scalar(Select(Users).where(Users.uid == userid))
            userdata.entry = datetime.now()
            DatabaseTransactions.commit(session)
        except SQLAlchemyError:
            session.rollback()
            session.close()

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
        DatabaseTransactions.commit(session)
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

    # Warning related functions
    @staticmethod
    @abstractmethod
    def user_add_warning(userid: int, reason: str):
        item = db.Warnings(uid=userid, reason=reason, type="WARN")
        session.add(item)
        DatabaseTransactions.commit(session)
        return True

    @staticmethod
    @abstractmethod
    def user_add_watchlist(userid: int, reason: str):
        item = db.Warnings(uid=userid, reason=reason, type="WATCH")
        session.add(item)
        DatabaseTransactions.commit(session)
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
    def user_remove_warning(id: int):
        warning = session.scalar(Select(Warnings).where(Warnings.id == id))
        session.delete(warning)
        DatabaseTransactions.commit(session)

