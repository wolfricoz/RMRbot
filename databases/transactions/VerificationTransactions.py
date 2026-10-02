from datetime import datetime

from sqlalchemy.sql import Select

from databases.current import IdVerification
from databases.transactions.DatabaseTransactions import DatabaseTransactions
from databases.transactions.UserTransactions import UserTransactions


class VerificationTransactions(DatabaseTransactions):

    def get_id_info(self, userid: int):
        with self.createsession() as session:
            return session.scalar(Select(IdVerification).where(IdVerification.uid == userid))

    def update_check(self, userid, reason: str = None, idcheck=True):
        with self.createsession() as session:
            userdata = session.scalar(Select(IdVerification).where(IdVerification.uid == userid))
            if userdata is None:
                session.close()
                self.add_idcheck(userid, reason, idcheck)
                return
            userdata.reason = reason
            userdata.idcheck = idcheck
            self.commit(session)

    def add_idcheck(self, userid: int, reason: str = None, idcheck=True):
        UserTransactions().add_user_empty(userid, True)
        with self.createsession() as session:
            session.add(IdVerification(uid=userid, reason=reason, idcheck=idcheck))
            self.commit(session)

    def set_idcheck_to_true(self, userid: int, reason):
        with self.createsession() as session:
            userdata: IdVerification = session.scalar(Select(IdVerification).where(IdVerification.uid == userid))
            if userdata is None:
                session.close()
                self.add_idcheck(userid, reason)
                return
            userdata.idcheck = True
            userdata.reason = reason
            self.commit(session)

    def set_idcheck_to_false(self, userid: int, ):
        with self.createsession() as session:
            userdata: IdVerification = session.scalar(Select(IdVerification).where(IdVerification.uid == userid))
            if userdata is None:
                session.close()
                self.add_idcheck(userid, idcheck=False)
                return
            userdata.idcheck = False
            userdata.reason = None
            self.commit(session)

    def idverify_add(self, userid: int, dob: str, idcheck=True):
        UserTransactions().add_user_empty(userid, True)
        with self.createsession() as session:
            session.add(IdVerification(uid=userid, verifieddob=datetime.strptime(dob, "%m/%d/%Y"), idverified=idcheck))
            self.commit(session)
        UserTransactions().update_user_dob(userid, dob)

    def idverify_update(self, userid, dob: str, guildname, idverified=True):
        with self.createsession() as session:
            userdata = session.scalar(Select(IdVerification).where(IdVerification.uid == userid))
            if userdata is None:
                session.close()
                self.add_idcheck(userid, dob, idcheck=False)
                return
            userdata.verifieddob = datetime.strptime(dob, "%m/%d/%Y")
            userdata.idverified = idverified
            userdata.idcheck = False
            userdata.reason = "User ID Verified"
            self.commit(session)
        UserTransactions().update_user_dob(userid, dob, guildname=guildname)
