from datetime import datetime, timedelta, timezone

from sqlalchemy.sql import Select

from databases.current import Interests
from databases.transactions.DatabaseTransactions import DatabaseTransactions
from databases.transactions.UserTransactions import UserTransactions


class InterestTransactions(DatabaseTransactions):
    """The "I'm interested" messages sent to advert authors, kept for statistics."""

    def add(self, guild_id: int, thread_id: int, author_id: int, sender_id: int) -> int:
        """Logs an interest message before it is sent; returns its id. It counts as undelivered until set_delivered."""
        # author_id and sender_id are foreign keys to users.uid, so both have to exist first.
        UserTransactions().add_user_empty(author_id)
        UserTransactions().add_user_empty(sender_id)
        with self.createsession() as session:
            interest = Interests(guild=guild_id, thread_id=thread_id, author_id=author_id, sender_id=sender_id)
            session.add(interest)
            self.commit(session)
            return interest.id

    def set_delivered(self, interest_id: int):
        return self._update(interest_id, delivered=True)

    def set_reported(self, interest_id: int):
        return self._update(interest_id, reported_at=datetime.now(tz=timezone.utc))

    def get_since(self, guild_id: int, days: int):
        """The guild's interest messages of the last days."""
        since = datetime.now(timezone.utc) - timedelta(days=days)
        with self.createsession() as session:
            return session.scalars(
                    Select(Interests).where(Interests.guild == guild_id, Interests.created_at >= since)
            ).all()

    def _update(self, interest_id: int, **values):
        with self.createsession() as session:
            interest = session.get(Interests, interest_id)
            if interest is None:
                return False
            for key, value in values.items():
                setattr(interest, key, value)
            self.commit(session)
        return True
