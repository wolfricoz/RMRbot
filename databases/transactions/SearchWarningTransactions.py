from datetime import datetime, timedelta, timezone

from sqlalchemy.sql import Select

from databases.current import Warnings
from databases.transactions.DatabaseTransactions import DatabaseTransactions
from databases.transactions.UserTransactions import UserTransactions


class SearchWarningTransactions(DatabaseTransactions):

    def get_total_warnings(self, userid: int):
        total = 0
        active = 0
        monthsago = datetime.now(timezone.utc) - timedelta(days=90)
        with self.createsession() as session:
            userdata = session.scalars(Select(Warnings).where(Warnings.uid == userid, Warnings.type == "SEARCH")).all()
        for x in userdata:
            if monthsago < x.entry.replace(tzinfo=timezone.utc):
                active += 1
            total += 1
        return total, active

    def add_warning(self, userid: int, reason: str = None):
        UserTransactions().add_user_empty(userid)
        with self.createsession() as session:
            session.add(Warnings(uid=userid, reason=reason, type="SEARCH"))
            self.commit(session)
