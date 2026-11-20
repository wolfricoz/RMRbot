from datetime import datetime, timezone

from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import Select

from databases.current import PurgeDates
from databases.transactions.DatabaseTransactions import DatabaseTransactions


class PurgeTransactions(DatabaseTransactions):
    """The yearly search forum purge dates."""

    def add(self, guild_id: int, day: int, month: int) -> bool:
        """Adds a purge date; returns False when the guild already has it."""
        if self.get(guild_id, day, month) is not None:
            return False
        with self.createsession() as session:
            session.add(PurgeDates(guild=guild_id, day=day, month=month))
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                return False
        return True

    def remove(self, guild_id: int, day: int, month: int) -> bool:
        with self.createsession() as session:
            entry = session.scalar(self._select(guild_id, day, month))
            if entry is None:
                return False
            session.delete(entry)
            self.commit(session)
        return True

    def get(self, guild_id: int, day: int, month: int) -> PurgeDates | None:
        with self.createsession() as session:
            return session.scalar(self._select(guild_id, day, month))

    def get_for_guild(self, guild_id: int) -> list[PurgeDates]:
        """The guild's purge dates in calendar order."""
        with self.createsession() as session:
            return list(session.scalars(
                    Select(PurgeDates).where(PurgeDates.guild == guild_id).order_by(PurgeDates.month, PurgeDates.day)
            ).all())

    def get_all(self) -> list[PurgeDates]:
        with self.createsession() as session:
            return list(session.scalars(Select(PurgeDates)).all())

    def set_announced(self, purge_id: int):
        return self._update(purge_id, announced_at=datetime.now(tz=timezone.utc))

    def set_started(self, purge_id: int):
        """Marks the date as run for this year; set when the purge starts, so it can't start twice."""
        return self._update(purge_id, last_purged_at=datetime.now(tz=timezone.utc))

    def set_checked(self, purge_id: int) -> bool:
        """Moves the guild's check mark to this purge date."""
        with self.createsession() as session:
            entry = session.get(PurgeDates, purge_id)
            if entry is None:
                return False
            session.execute(
                    update(PurgeDates).where(PurgeDates.guild == entry.guild, PurgeDates.id != entry.id).values(checked=False)
            )
            entry.checked = True
            self.commit(session)
        return True

    @staticmethod
    def _select(guild_id: int, day: int, month: int):
        return Select(PurgeDates).where(PurgeDates.guild == guild_id, PurgeDates.day == day, PurgeDates.month == month)

    def _update(self, purge_id: int, **values) -> bool:
        with self.createsession() as session:
            entry = session.get(PurgeDates, purge_id)
            if entry is None:
                return False
            for key, value in values.items():
                setattr(entry, key, value)
            self.commit(session)
        return True
