from abc import ABC, abstractmethod
from datetime import datetime

from sqlalchemy.sql import Select

from databases.current import IdVerification
from databases.session import session
from databases.transactions.DatabaseTransactions import DatabaseTransactions
from databases.transactions.UserTransactions import UserTransactions


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
        DatabaseTransactions.commit(session)

    @staticmethod
    @abstractmethod
    def add_idcheck(userid: int, reason: str = None, idcheck=True):
        UserTransactions.add_user_empty(userid, True)
        idcheck = IdVerification(uid=userid, reason=reason, idcheck=idcheck)
        session.add(idcheck)
        DatabaseTransactions.commit(session)

    @staticmethod
    @abstractmethod
    def set_idcheck_to_true(userid: int, reason):
        userdata: IdVerification = session.scalar(Select(IdVerification).where(IdVerification.uid == userid))
        if userdata is None:
            VerificationTransactions.add_idcheck(userid, reason)
            return
        userdata.idcheck = True
        userdata.reason = reason
        DatabaseTransactions.commit(session)

    @staticmethod
    @abstractmethod
    def set_idcheck_to_false(userid: int, ):
        userdata: IdVerification = session.scalar(Select(IdVerification).where(IdVerification.uid == userid))
        if userdata is None:
            VerificationTransactions.add_idcheck(userid, idcheck=False)
            return
        userdata.idcheck = False
        userdata.reason = None
        DatabaseTransactions.commit(session)

    @staticmethod
    @abstractmethod
    def idverify_add(userid: int, dob: str, idcheck=True):
        UserTransactions.add_user_empty(userid, True)
        idcheck = IdVerification(uid=userid, verifieddob=datetime.strptime(dob, "%m/%d/%Y"), idverified=idcheck)
        session.add(idcheck)
        DatabaseTransactions.commit(session)
        UserTransactions.update_user_dob(userid, dob)

    @staticmethod
    @abstractmethod
    def idverify_update(userid, dob: str, guildname, idverified=True):

        userdata = session.scalar(Select(IdVerification).where(IdVerification.uid == userid))
        if userdata is None:
            VerificationTransactions.add_idcheck(userid, dob, idcheck=False)
            return
        userdata.verifieddob = datetime.strptime(dob, "%m/%d/%Y")
        userdata.idverified = idverified
        userdata.idcheck = False
        userdata.reason = "User ID Verified"
        DatabaseTransactions.commit(session)
        UserTransactions.update_user_dob(userid, dob, guildname=guildname)
