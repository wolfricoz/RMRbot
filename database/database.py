"""Database connection and every table the bot uses.

The connection is built from the DB_* environment variables (see .env.example). The old single DB url is still
read when DB_HOST isn't set, so a server that hasn't moved its .env over yet keeps working.
"""
import logging
import os
from datetime import datetime
from typing import List, Optional

import pymysql
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, Text, URL, create_engine, make_url
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import func
from sqlalchemy_utils import create_database, database_exists

from data.env.loader import env, load_environment

load_environment()

# DB_TYPE -> (SQLAlchemy driver name, the port that server listens on by default). Anything else is used as given.
_DIALECTS = {
    "mysql"     : ("mysql", 3306),
    "mariadb"   : ("mysql", 3306),
    "postgresql": ("postgresql", 5432),
    "postgres"  : ("postgresql", 5432),
}


def build_database_url() -> URL:
    """The database url from the DB_* variables. Pure string building, so it can be checked without a connection."""
    # `or` instead of env()'s default, because .env.example leaves unused values as empty strings.
    database_name = env('DB_NAME') or 'rmrbotnew'
    legacy_url = env('DB')
    if not env('DB_HOST') and legacy_url:
        logging.warning("DB is deprecated: set DB_TYPE, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT and DB_NAME instead.")
        return make_url(f"{legacy_url.rstrip('/')}/{database_name}")

    db_type = env('DB_TYPE') or 'mysql'
    drivername, default_port = _DIALECTS.get(db_type.lower(), (db_type, 3306))
    # URL.create escapes special characters in the password, which an f-string url would not.
    return URL.create(
        drivername=drivername,
        username=env('DB_USER') or None,
        password=env('DB_PASSWORD') or None,
        host=env('DB_HOST') or '127.0.0.1',
        port=int(env('DB_PORT') or default_port),
        database=database_name,
    )


db_url = build_database_url()
connect_args = {}
if db_url.get_backend_name() == "postgresql":
    # Timestamps are stored and read as UTC, which the rest of the bot assumes (e.g. the searchban timers).
    connect_args["options"] = "-c timezone=utc"
else:
    # mysql:// urls without a driver load MySQLdb, which pymysql stands in for.
    pymysql.install_as_MySQLdb()

# NullPool opens a fresh connection per session, so the bot never holds on to a stale one.
engine = create_engine(db_url, poolclass=NullPool, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)


def ensure_database_exists():
    """Creates the database itself when it's missing; called by database.create() so importing this file opens no
    connection."""
    if not database_exists(engine.url):
        create_database(engine.url)


class Base(DeclarativeBase):
    pass


# noinspection PyTypeChecker, PydanticTypeChecker
class Users(Base):
    __tablename__ = "users"
    uid: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    entry: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    date_of_birth: Mapped[Optional[str]] = mapped_column(String(4096))
    server: Mapped[Optional[str]] = mapped_column(String(4096))
    warnings: Mapped[List["Warnings"]] = relationship(cascade="save-update, merge, delete, delete-orphan")
    id: Mapped["IdVerification"] = relationship(back_populates="user", cascade="save-update, merge, delete, delete-orphan")


# noinspection PyTypeChecker, PydanticTypeChecker
class Warnings(Base):
    __tablename__ = "warnings"
    id: Mapped[int] = mapped_column(primary_key=True)
    uid: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.uid", ondelete="CASCADE"))
    reason: Mapped[str] = mapped_column(String(1024))
    type: Mapped[str] = mapped_column(String(20))
    entry: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# noinspection PyTypeChecker, PydanticTypeChecker

class Servers(Base):
    __tablename__ = "servers"
    guild: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)


# noinspection PyTypeChecker, PydanticTypeChecker

class Config(Base):
    # Reminder to self you can add multiple keys in this database
    __tablename__ = "config"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    guild: Mapped[int] = mapped_column(BigInteger, ForeignKey("servers.guild", ondelete="CASCADE"))
    key: Mapped[str] = mapped_column(String(512), primary_key=True)
    value: Mapped[str] = mapped_column(String(1980))


# noinspection PyTypeChecker, PydanticTypeChecker

class IdVerification(Base):
    __tablename__ = "verification"
    uid: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.uid", ondelete="CASCADE"), primary_key=True,
                                     autoincrement=False)
    reason: Mapped[Optional[str]] = mapped_column(String(1024))
    idcheck: Mapped[bool] = mapped_column(Boolean, default=False)
    idverified: Mapped[bool] = mapped_column(Boolean, default=False)
    verifieddob: Mapped[Optional[datetime]]
    user: Mapped["Users"] = relationship(back_populates="id")


class Timers(Base):
    __tablename__ = "timers"
    id: Mapped[int] = mapped_column(primary_key=True)
    uid: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.uid", ondelete="CASCADE"))
    guild: Mapped[int] = mapped_column(BigInteger, ForeignKey("servers.guild", ondelete="CASCADE"))
    role: Mapped[Optional[int]] = mapped_column(BigInteger)
    reason: Mapped[Optional[str]] = mapped_column(String(1024))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # in hours
    removal: Mapped[int]

class Approvals(Base):
    __tablename__ = "approvals"
    id: Mapped[int] = mapped_column(primary_key=True)
    uid: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.uid", ondelete="CASCADE"))
    guild: Mapped[int] = mapped_column(BigInteger, ForeignKey("servers.guild", ondelete="CASCADE"))
    thread: Mapped[int] = mapped_column(BigInteger)
    # The advert's text as it was approved: edits are diffed against the latest one.
    content: Mapped[Optional[str]] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Advertisements(Base):
    __tablename__ = "advertisements"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    thread_id: Mapped[int] = mapped_column(BigInteger, index=True)
    forum_id: Mapped[int] = mapped_column(BigInteger, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.uid", ondelete="CASCADE"), index=True)
    consent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=None)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=None)
    # The post's page on the website, returned when it was published.
    url: Mapped[Optional[str]] = mapped_column(String(255), default=None)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=None)


class AdvertisementHolds(Base):
    """Why an advert isn't on the website yet."""
    # A table of its own because database.create() adds new tables, but no columns to existing ones.
    __tablename__ = "advertisement_holds"
    advert_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("advertisements.id", ondelete="CASCADE"), primary_key=True, autoincrement=False)
    # What the author was told, so the same reason isn't sent twice.
    reason: Mapped[str] = mapped_column(Text)
    # publish_pending leaves the advert alone until then; without one it checks the advert on every run.
    retry_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=None)


class Interests(Base):
    """The "I'm interested" messages sent to advert authors, for statistics."""
    # The text isn't kept: reports send it to the advert moderators.
    __tablename__ = "interests"
    id: Mapped[int] = mapped_column(primary_key=True)
    guild: Mapped[int] = mapped_column(BigInteger, ForeignKey("servers.guild", ondelete="CASCADE"), index=True)
    thread_id: Mapped[int] = mapped_column(BigInteger, index=True)
    author_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.uid", ondelete="CASCADE"), index=True)
    sender_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.uid", ondelete="CASCADE"), index=True)
    # False when the author doesn't accept direct messages.
    delivered: Mapped[bool] = mapped_column(Boolean, default=False)
    reported_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class database:
    @staticmethod
    def create():
        ensure_database_exists()
        Base.metadata.create_all(engine)
        print("Database built")


def create_bot_database():
    ensure_database_exists()
    Base.metadata.create_all(engine)


def drop_bot_database():
    """Drops every table; for throwaway test databases only."""
    if os.getenv('DISCORD_TOKEN'):
        raise Exception("You cannot drop the database while the bot is in production")
    if not engine.url.database.endswith("_test"):
        raise Exception(f"drop_bot_database() only drops test databases; DB_NAME '{engine.url.database}' doesn't end "
                        f"in '_test'.")
    Base.metadata.drop_all(engine)
