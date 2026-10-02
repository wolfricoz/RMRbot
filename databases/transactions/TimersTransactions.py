from sqlalchemy.sql import Select

from databases.current import Timers
from databases.transactions.DatabaseTransactions import DatabaseTransactions


class TimersTransactions(DatabaseTransactions):

    def add_timer(self, userid, guildid, time_in_hours, roleid=None, reason=None):
        """Adds timer to the database"""
        with self.createsession() as session:
            session.add(Timers(uid=userid, guild=guildid, removal=time_in_hours, role=roleid, reason=reason))
            self.commit(session)

    def get_timer_with_role(self, userid, guildid, roleid):
        """Gets the timer from the database with userid, guild and roleid"""
        with self.createsession() as session:
            return session.scalar(Select(Timers).where(Timers.uid == userid, Timers.guild == guildid, Timers.role == roleid))

    def remove_timer(self, timer):
        # The timer was loaded by another (now closed) session, so it is looked up again by id in this one.
        with self.createsession() as session:
            entry = session.get(Timers, timer.id)
            if entry is None:
                return
            session.delete(entry)
            self.commit(session)
