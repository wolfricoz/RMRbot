import logging
from datetime import timedelta

from sqlalchemy import text
from sqlalchemy.exc import InvalidRequestError, PendingRollbackError, SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import Select

import databases.current as db
from classes.singleton import Singleton
from databases.exceptions.CommitError import CommitError


class DatabaseTransactions(metaclass=Singleton):
    """Base class for all transactions; every method opens its own session through createsession()."""
    sessionmanager = sessionmaker(bind=db.engine)

    def createsession(self):
        return self.sessionmanager(expire_on_commit=False)

    def commit(self, session):
        try:
            session.commit()
        except SQLAlchemyError as e:
            logging.warning(f"DB commit failed (SQLAlchemyError), rolling back: {e}", exc_info=True)
            session.rollback()
            raise CommitError()
        finally:
            session.close()

    def ping_db(self):
        """Checks if the database is reachable, used by the /ping API route."""
        try:
            with self.createsession() as session:
                session.execute(text("SELECT 1"))
                return "alive"
        except PendingRollbackError:
            logging.warning("Pending rollback during DB ping.")
            return "error"
        except InvalidRequestError:
            logging.warning("Invalid session state during DB ping.")
            return "alive"
        except SQLAlchemyError as e:
            logging.error(f"SQLAlchemy error during DB ping: {e}", exc_info=True)
            return "error"
        except Exception as e:
            logging.error(f"Unexpected error during DB ping: {e}", exc_info=True)
            return "error"

    def get_table(self, name):
        """This function will return the table requested."""
        with self.createsession() as session:
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

    def get_all_timers(self, table_name):
        """This function will return the table requested."""
        table = self.get_table(table_name)
        print(f"table: {table}")
        warning_dict = {}
        warning_list = []
        if len(table) == 0 or table is None:
            return False
        for entry in table:
            removal_time = entry.created_at + timedelta(hours=entry.removal)
            warning_dict[entry.uid] = removal_time.strftime("%m/%d/%Y")
            warning_list.append(entry.uid)
        return warning_list, warning_dict
