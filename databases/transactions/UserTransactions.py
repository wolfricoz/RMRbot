from datetime import datetime, timezone

from sqlalchemy.sql import Select

import databases.current as db
from classes.encryption import Encryption
from databases.current import Users, Warnings
from databases.exceptions.CommitError import CommitError
from databases.transactions.ConfigData import ConfigData
from databases.transactions.ConfigTransactions import ConfigTransactions
from databases.transactions.DatabaseTransactions import DatabaseTransactions


class UserTransactions(DatabaseTransactions):

    def add_user_empty(self, userid: int, overwrite=False):
        if self.user_exists(userid) is True and overwrite is False:
            return False
        with self.createsession() as session:
            session.merge(db.Users(uid=userid))
            self.commit(session)
        return True

    def add_user_full(self, userid, dob, guildname):
        try:
            with self.createsession() as session:
                item = db.Users(uid=userid, entry=datetime.now(tz=timezone.utc), date_of_birth=Encryption().encrypt(dob), server=guildname)
                session.merge(item)
                self.commit(session)
            return True
        except ValueError:
            return False

    def update_user_dob(self, userid: int, dob: str, guildname: str):
        with self.createsession() as session:
            userdata: Users = session.scalar(Select(Users).where(Users.uid == userid))
            if userdata is None:
                session.close()
                self.add_user_full(userid, dob, guildname)
                return False
            userdata.date_of_birth = Encryption().encrypt(dob)
            userdata.entry = datetime.now(tz=timezone.utc)
            userdata.server = guildname
            self.commit(session)
        if userdata.date_of_birth is None:
            return False
        return True

    def user_delete(self, userid: int):
        with self.createsession() as session:
            userdata: Users = session.scalar(Select(Users).where(Users.uid == userid))
            if userdata is None:
                return False
            session.delete(userdata)
            try:
                self.commit(session)
            except CommitError:
                return False
        return True

    def get_user(self, userid: int):
        with self.createsession() as session:
            return session.scalar(Select(Users).where(Users.uid == userid))

    def get_all_users(self):
        with self.createsession() as session:
            return session.scalars(Select(Users)).all()

    def update_entry_date(self, userid):
        with self.createsession() as session:
            userdata = session.scalar(Select(Users).where(Users.uid == userid))
            if userdata is None:
                return
            userdata.entry = datetime.now(tz=timezone.utc)
            try:
                self.commit(session)
            except CommitError:
                pass

    def update(self):
        raise NotImplementedError

    def config_unique_remove(self, guildid: int, key: str):
        if ConfigTransactions().key_exists_check(guildid, key) is False:
            return False
        with self.createsession() as session:
            exists = session.scalar(Select(db.Config).where(db.Config.guild == guildid, db.Config.key == key.upper()))
            if exists is None:
                return False
            session.delete(exists)
            self.commit(session)
        ConfigData().load_guild(guildid)
        return True

    def user_exists(self, userid: int):
        with self.createsession() as session:
            exists = session.scalar(Select(db.Users).where(db.Users.uid == userid))
        if exists is None:
            return False
        return True, exists

    # Warning related functions
    def user_add_warning(self, userid: int, reason: str):
        with self.createsession() as session:
            session.add(db.Warnings(uid=userid, reason=reason, type="WARN"))
            self.commit(session)
        return True

    def user_add_watchlist(self, userid: int, reason: str):
        with self.createsession() as session:
            session.add(db.Warnings(uid=userid, reason=reason, type="WATCH"))
            self.commit(session)
        return True

    def user_get_warnings(self, userid: int, type):
        warning_dict = {}
        warning_list = []
        with self.createsession() as session:
            warnings = session.scalars(Select(Warnings).where(Warnings.uid == userid, Warnings.type == type.upper()).order_by(Warnings.uid)).all()
        if len(warnings) == 0 or warnings is None:
            return False
        for warning in warnings:
            warning_dict[warning.id] = warning.reason
            warning_list.append(warning.id)
        return warning_list, warning_dict

    def user_remove_warning(self, id: int):
        with self.createsession() as session:
            warning = session.scalar(Select(Warnings).where(Warnings.id == id))
            if warning is None:
                return
            session.delete(warning)
            self.commit(session)
