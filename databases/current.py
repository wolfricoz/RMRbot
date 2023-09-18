from datetime import datetime
from typing import List, Optional

import pymysql
from sqlalchemy import create_engine, DateTime, ForeignKey, String, BigInteger
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy_utils import database_exists, create_database

pymysql.install_as_MySQLdb()

engine = create_engine("mariadb://root:@127.0.0.1:3306/rmrbotnew")
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


class Config(Base):
    __tablename__ = "config"
    guild: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    admin: Mapped[int] = mapped_column(BigInteger)
    mod: Mapped[int] = mapped_column(BigInteger)
    trial: Mapped[int] = mapped_column(BigInteger)
    lobbystaff: Mapped[int] = mapped_column(BigInteger)


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
    idcheck: Mapped[bool] = mapped_column(default=False)
    idverified: Mapped[bool] = mapped_column(default=False)
    verifieddob: Mapped[Optional[datetime]]
    user: Mapped["Users"] = relationship(back_populates="id")


class database:
    def create(self):
        Base.metadata.create_all(engine)
        print("Database built")

# session = Session(engine)
# birth = datetime.strptime('06/18/1997', '%m/%d/%Y')
# rico = Users(uid=188647277181665280, dob=birth)
# ricowarn = Warnings(uid=188647277181665280, reason="Broke a search rule", type="WARNING")
# ricoswarn = Warnings(uid=188647277181665280, reason="Broke a search rule", type="SEARCH")
# ricowatch = Watchlist(uid=188647277181665280, reason="Being a sussy baka")
# ricoid = IdVerification(uid=188647277181665280)
#
#
# # session.add(rico)
# session.commit()
# # session.add_all([ricowarn, ricoswarn, ricowatch])
# # session.add(ricoid)
# session.commit()
#
# a = session.scalar(select(Users).where(Users.uid == 188647277181665280))
# for x in a.warnings:
#     print(x.reason)
#     print(x.type)
# for x in a.watchlist:
#     print(x.reason)
#
# print(a.id.idverified)
# print(f"user has: {len(a.warnings)} warnings")
