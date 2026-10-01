from abc import ABC, abstractmethod
from datetime import datetime, timedelta

from sqlalchemy.sql import Select

import databases.current as db
from databases.current import Approvals
from databases.session import session
from databases.transactions.DatabaseTransactions import DatabaseTransactions


class ApprovalTransactions(ABC):

    @staticmethod
    @abstractmethod
    def add_approval(user_id: int, guild_id: int, thread_id: int,):
        approval = db.Approvals(uid=user_id, guild=guild_id, thread=thread_id)
        session.add(approval)
        DatabaseTransactions.commit(session)

    @staticmethod
    @abstractmethod
    def get_all_approvals(days = 30):
        check_date = datetime.now() - timedelta(days=days)
        return session.scalars(Select(db.Approvals).filter(Approvals.created_at > check_date)).all()
