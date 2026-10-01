from abc import ABC, abstractmethod

from sqlalchemy.sql import Select

from databases.current import Timers
from databases.session import session
from databases.transactions.DatabaseTransactions import DatabaseTransactions


class TimersTransactions(ABC):
    @staticmethod
    @abstractmethod
    def add_timer(userid, guildid, time_in_hours, roleid=None, reason=None):
        """Adds timer to the database"""
        entry = Timers(uid=userid, guild=guildid, removal=time_in_hours, role=roleid, reason=reason)
        session.add(entry)
        DatabaseTransactions.commit(session)

    @staticmethod
    @abstractmethod
    def get_timer_with_role(userid, guildid, roleid):
        """Gets the timer from the database with userid, guild and roleid"""
        timer = session.scalar(Select(Timers).where(Timers.uid == userid, Timers.guild == guildid, Timers.role == roleid))
        session.close()
        return timer

    @staticmethod
    @abstractmethod
    def remove_timer(timer):
        session.delete(timer)
        session.commit()
