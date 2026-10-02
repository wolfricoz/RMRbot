from datetime import datetime, timezone

from sqlalchemy.sql import Select

from databases.current import Advertisements
from databases.transactions.DatabaseTransactions import DatabaseTransactions
from databases.transactions.UserTransactions import UserTransactions


class AdvertisementTransactions(DatabaseTransactions):
    """Index of the adverts posted in the server; an advert is sent to the website when it has consent, is approved
    and is not deleted."""

    def add(self, message_id: int, thread_id: int, forum_id: int, user_id: int):
        # user_id is a foreign key to users.uid, so the user has to exist first.
        UserTransactions().add_user_empty(user_id)
        with self.createsession() as session:
            session.merge(Advertisements(id=message_id, thread_id=thread_id, forum_id=forum_id, user_id=user_id))
            self.commit(session)
        return True

    def get(self, message_id: int):
        with self.createsession() as session:
            return session.get(Advertisements, message_id)

    def get_by_thread(self, thread_id: int):
        with self.createsession() as session:
            return session.scalars(Select(Advertisements).where(Advertisements.thread_id == thread_id)).all()

    def get_by_user(self, user_id: int, include_deleted=False):
        query = Select(Advertisements).where(Advertisements.user_id == user_id)
        if not include_deleted:
            query = query.where(Advertisements.deleted.is_(None))
        with self.createsession() as session:
            return session.scalars(query).all()

    def get_unpublished(self):
        """Adverts that can be sent to the website but haven't been received by it yet."""
        with self.createsession() as session:
            return session.scalars(Select(Advertisements).where(
                    Advertisements.consent_at.is_not(None),
                    Advertisements.approved.is_(True),
                    Advertisements.deleted.is_(None),
                    Advertisements.published_at.is_(None),
            )).all()

    def set_consent(self, message_id: int, consent: bool):
        return self._update(message_id, consent_at=datetime.now(tz=timezone.utc) if consent else None)

    def set_approved(self, message_id: int, approved: bool):
        return self._update(message_id, approved=approved)

    def set_published(self, message_id: int, published: bool = True):
        return self._update(message_id, published_at=datetime.now(tz=timezone.utc) if published else None)

    def set_deleted(self, message_id: int, deleted: bool = True):
        return self._update(message_id, deleted=datetime.now(tz=timezone.utc) if deleted else None)

    def _update(self, message_id: int, **values):
        with self.createsession() as session:
            advert = session.get(Advertisements, message_id)
            if advert is None:
                return False
            for key, value in values.items():
                setattr(advert, key, value)
            self.commit(session)
        return True
