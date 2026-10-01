from abc import ABC, abstractmethod
from datetime import timedelta

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import Select

import databases.current as db
from databases.exceptions.CommitError import CommitError
from databases.session import session


class DatabaseTransactions(ABC):

    @staticmethod
    @abstractmethod
    def commit(session):
        try:
            session.commit()
        except SQLAlchemyError as e:
            print(e)
            session.rollback()
            raise CommitError()
        finally:
            session.close()

    @staticmethod
    @abstractmethod
    def get_table(name):
        """This function will return the table requested."""
        match name.lower():
            case "config":
                return session.scalars(Select(db.Config)).all()
            case "users":
                return session.scalars(Select(db.Users)).all()
            case "warnings":
                return session.scalars(Select(db.Warnings)).all()
            case "servers":
                return session.scalars(Select(db.Servers)).all()
            case "timers":
                return session.scalars(Select(db.Timers).order_by(db.Timers.uid)).all()
            case "idverification":
                return session.scalars(Select(db.IdVerification)).all()

    @staticmethod
    @abstractmethod
    def get_all_timers(table_name):
        """This function will return the table requested."""
        table = DatabaseTransactions.get_table(table_name)
        print(f"table: {table}")
        warning_dict = {}
        warning_list = []
        session.close()
        if len(table) == 0 or table is None:
            return False
        for entry in table:
            removal_time = entry.created_at + timedelta(hours=entry.removal)
            warning_dict[entry.uid] = removal_time.strftime("%m/%d/%Y")
            warning_list.append(entry.uid)
        return warning_list, warning_dict
