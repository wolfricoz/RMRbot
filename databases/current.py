import os
from datetime import datetime
from typing import List, Optional

import pymysql
from dotenv import load_dotenv
from sqlalchemy import create_engine, DateTime, ForeignKey, String, BigInteger, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import func
from sqlalchemy_utils import database_exists, create_database

pymysql.install_as_MySQLdb()
load_dotenv('.env')
DB = os.getenv('DB')

engine = create_engine(f"{DB}/rmrbotnew", poolclass=NullPool, echo=False)
if not database_exists(engine.url):
    create_database(engine.url)

conn = engine.connect()


class Base(DeclarativeBase):
    pass


class Users(Base):
    __tablename__ = "users"
    uid: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    dob: Mapped[Optional[datetime]]
    entry: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    warnings: Mapped[List["Warnings"]] = relationship()
    watchlist: Mapped[List["Watchlist"]] = relationship()
    id: Mapped["IdVerification"] = relationship(back_populates="user")


class Warnings(Base):
    __tablename__ = "warnings"
    id: Mapped[int] = mapped_column(primary_key=True)
    uid: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.uid", ondelete="CASCADE"))
    reason: Mapped[str] = mapped_column(String(1024))
    type: Mapped[str] = mapped_column(String(20))
    entry: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Servers(Base):
    __tablename__ = "servers"
    guild: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)


class Config(Base):
    __tablename__ = "config"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    guild: Mapped[int] = mapped_column(BigInteger, ForeignKey("servers.guild", ondelete="CASCADE"))
    key: Mapped[str] = mapped_column(String(512), primary_key=True)
    value: Mapped[str] = mapped_column(String(1980))


class Search(Base):
    __tablename__ = "search"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    guild: Mapped[int] = mapped_column(BigInteger, ForeignKey("servers.guild", ondelete="CASCADE"))
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(String(1980))


class Watchlist(Base):
    __tablename__ = "watchlist"
    id: Mapped[int] = mapped_column(primary_key=True)
    uid: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.uid", ondelete="CASCADE"))
    reason: Mapped[str] = mapped_column(String(1024))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class IdVerification(Base):
    __tablename__ = "verification"
    uid: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.uid", ondelete="CASCADE"), primary_key=True,
                                     autoincrement=False)
    reason: Mapped[Optional[str]] = mapped_column(String(1024))
    idcheck: Mapped[bool] = mapped_column(Boolean,default=False)
    idverified: Mapped[bool] = mapped_column(Boolean, default=False)
    verifieddob: Mapped[Optional[datetime]]
    user: Mapped["Users"] = relationship(back_populates="id")


class database:
    def create(self):
        Base.metadata.create_all(engine)
        print("Database built")
