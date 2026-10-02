from datetime import datetime, timedelta, timezone

from sqlalchemy.sql import Select

from databases.current import Approvals
from databases.transactions.DatabaseTransactions import DatabaseTransactions
from databases.transactions.UserTransactions import UserTransactions


class ApprovalTransactions(DatabaseTransactions):

    def add_approval(self, user_id: int, guild_id: int, thread_id: int, content: str | None = None):
        """Logs an approval; with content, the advert's text as approved (what later edits are diffed against)."""
        # uid is a foreign key to users.uid (the bot itself is the approver of auto-approved bumps).
        UserTransactions().add_user_empty(user_id)
        with self.createsession() as session:
            session.add(Approvals(uid=user_id, guild=guild_id, thread=thread_id, content=content))
            self.commit(session)

    def get_all_approvals(self, days=30):
        check_date = datetime.now(timezone.utc) - timedelta(days=days)
        with self.createsession() as session:
            return session.scalars(Select(Approvals).filter(Approvals.created_at > check_date)).all()

    def get_by_guild(self, guild_id: int, days: int):
        """The guild's approvals of the last days."""
        check_date = datetime.now(timezone.utc) - timedelta(days=days)
        with self.createsession() as session:
            return session.scalars(
                    Select(Approvals).where(Approvals.guild == guild_id, Approvals.created_at > check_date)
            ).all()

    def get_threads_without_content(self, guild_id: int) -> list[int]:
        """Threads (as logged) that were approved in this guild but have no approval with the text stored."""
        with self.createsession() as session:
            with_content = Select(Approvals.thread).where(Approvals.content.is_not(None))
            return session.scalars(
                    Select(Approvals.thread).distinct()
                    .where(Approvals.guild == guild_id, Approvals.thread.not_in(with_content))
            ).all()

    def fill_content(self, thread_id: int, content: str) -> bool:
        """Stores the text on the thread's latest approval (for approvals logged before the text was kept)."""
        with self.createsession() as session:
            approval = session.scalars(
                    Select(Approvals).where(Approvals.thread == thread_id)
                    .order_by(Approvals.created_at.desc(), Approvals.id.desc())
                    .limit(1)
            ).first()
            if approval is None:
                return False
            approval.content = content
            self.commit(session)
        return True

    def get_approved_content(self, thread_id: int) -> str | None:
        """The advert's text at its latest approval, or None if it was never approved with its text stored."""
        with self.createsession() as session:
            return session.scalars(
                    Select(Approvals.content)
                    .where(Approvals.thread == thread_id, Approvals.content.is_not(None))
                    .order_by(Approvals.created_at.desc(), Approvals.id.desc())
                    .limit(1)
            ).first()
