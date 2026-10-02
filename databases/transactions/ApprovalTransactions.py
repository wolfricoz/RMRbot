from datetime import datetime, timedelta, timezone

from sqlalchemy.sql import Select

from databases.current import Approvals
from databases.transactions.DatabaseTransactions import DatabaseTransactions


class ApprovalTransactions(DatabaseTransactions):

    def add_approval(self, user_id: int, guild_id: int, thread_id: int):
        with self.createsession() as session:
            session.add(Approvals(uid=user_id, guild=guild_id, thread=thread_id))
            self.commit(session)

    def get_all_approvals(self, days=30):
        check_date = datetime.now(timezone.utc) - timedelta(days=days)
        with self.createsession() as session:
            return session.scalars(Select(Approvals).filter(Approvals.created_at > check_date)).all()
