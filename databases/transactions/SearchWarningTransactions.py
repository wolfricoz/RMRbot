from abc import ABC, abstractmethod
from datetime import datetime, timedelta

from sqlalchemy.sql import Select

from databases.current import Warnings
from databases.session import session
from databases.transactions.DatabaseTransactions import DatabaseTransactions
from databases.transactions.UserTransactions import UserTransactions


class SearchWarningTransactions(ABC):
    @staticmethod
    @abstractmethod
    def get_total_warnings(userid: int):
        total = 0
        active = 0
        monthsago = datetime.now() - timedelta(days=90)
        userdata = session.scalars(Select(Warnings).where(Warnings.uid == userid, Warnings.type == "SEARCH")).all()
        session.close()
        for x in userdata:
            if monthsago < x.entry:
                active += 1
            total += 1
        return total, active

    @staticmethod
    @abstractmethod
    def add_warning(userid: int, reason: str = None):
        UserTransactions.add_user_empty(userid)
        search_warning = Warnings(uid=userid, reason=reason, type="SEARCH")
        session.add(search_warning)
        DatabaseTransactions.commit(session)
