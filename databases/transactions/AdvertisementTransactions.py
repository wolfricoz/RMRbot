from abc import ABC, abstractmethod
from datetime import datetime, timezone

from sqlalchemy.sql import Select

from databases.current import Advertisements
from databases.session import session
from databases.transactions.DatabaseTransactions import DatabaseTransactions
from databases.transactions.UserTransactions import UserTransactions


class AdvertisementTransactions(ABC):
    """Index of the adverts posted in the server; an advert is sent to the website when it has consent, is approved
    and is not deleted."""

    @staticmethod
    @abstractmethod
    def add(message_id: int, thread_id: int, forum_id: int, user_id: int):
        # user_id is a foreign key to users.uid, so the user has to exist first.
        UserTransactions.add_user_empty(user_id)
        advert = Advertisements(id=message_id, thread_id=thread_id, forum_id=forum_id, user_id=user_id)
        session.merge(advert)
        DatabaseTransactions.commit(session)
        return True

    @staticmethod
    @abstractmethod
    def get(message_id: int):
        advert = session.scalar(Select(Advertisements).where(Advertisements.id == message_id))
        session.close()
        return advert

    @staticmethod
    @abstractmethod
    def get_by_thread(thread_id: int):
        adverts = session.scalars(Select(Advertisements).where(Advertisements.thread_id == thread_id)).all()
        session.close()
        return adverts

    @staticmethod
    @abstractmethod
    def get_by_user(user_id: int, include_deleted=False):
        query = Select(Advertisements).where(Advertisements.user_id == user_id)
        if not include_deleted:
            query = query.where(Advertisements.deleted.is_(None))
        adverts = session.scalars(query).all()
        session.close()
        return adverts

    @staticmethod
    @abstractmethod
    def get_unpublished():
        """Adverts that can be sent to the website but haven't been received by it yet."""
        adverts = session.scalars(Select(Advertisements).where(
                Advertisements.consent_at.is_not(None),
                Advertisements.approved.is_(True),
                Advertisements.deleted.is_(None),
                Advertisements.published_at.is_(None),
        )).all()
        session.close()
        return adverts

    @staticmethod
    @abstractmethod
    def set_consent(message_id: int, consent: bool):
        advert = session.scalar(Select(Advertisements).where(Advertisements.id == message_id))
        if advert is None:
            return False
        advert.consent_at = datetime.now(tz=timezone.utc) if consent else None
        DatabaseTransactions.commit(session)
        return True

    @staticmethod
    @abstractmethod
    def set_approved(message_id: int, approved: bool):
        advert = session.scalar(Select(Advertisements).where(Advertisements.id == message_id))
        if advert is None:
            return False
        advert.approved = approved
        DatabaseTransactions.commit(session)
        return True

    @staticmethod
    @abstractmethod
    def set_published(message_id: int, published: bool = True):
        advert = session.scalar(Select(Advertisements).where(Advertisements.id == message_id))
        if advert is None:
            return False
        advert.published_at = datetime.now(tz=timezone.utc) if published else None
        DatabaseTransactions.commit(session)
        return True

    @staticmethod
    @abstractmethod
    def set_deleted(message_id: int, deleted: bool = True):
        advert = session.scalar(Select(Advertisements).where(Advertisements.id == message_id))
        if advert is None:
            return False
        advert.deleted = datetime.now(tz=timezone.utc) if deleted else None
        DatabaseTransactions.commit(session)
        return True
