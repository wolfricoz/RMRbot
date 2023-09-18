import os

import pymysql
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, Boolean, BigInteger
from sqlalchemy.ext.declarative import declarative_base

pymysql.install_as_MySQLdb()
load_dotenv('config.env')
DBTOKEN = os.getenv("DB")

# sqlalchemy
# "mysql://bot:nKUZCzcm$LK!nffvpCEu8@162.248.101.136/rmrbot", echo=False
engine = create_engine("sqlite:///bot.sqlite", echo=False)  # connects to the database

base = declarative_base()


# class creates table
class user(base):
    __tablename__ = 'user'

    uid = Column(BigInteger, primary_key=True)
    dob = Column(String(10))

    def __init__(self, uid, dob):
        self.uid = uid
        self.dob = dob


class config(base):
    __tablename__ = 'config'

    guild = Column(BigInteger, primary_key=True)
    lobby = Column(BigInteger)
    agelog = Column(BigInteger)
    modlobby = Column(BigInteger)
    general = Column(BigInteger)

    def __init__(self, guild, lobby, agelog, modlobby, general):
        self.guild = guild
        self.lobby = lobby
        self.agelog = agelog
        self.modlobby = modlobby
        self.general = general


# commits it to the databse
class permissions(base):
    __tablename__ = 'permissions'

    guild = Column(BigInteger, primary_key=True)
    admin = Column(BigInteger, default=None)
    mod = Column(BigInteger, default=None)
    trial = Column(BigInteger, default=None)
    lobbystaff = Column(BigInteger, default=None)

    def __init__(self, guild, admin, mod, trial, lobbystaff):
        self.guild = guild
        self.admin = admin
        self.mod = mod
        self.trial = trial
        self.lobbystaff = lobbystaff


class warnings(base):
    __tablename__ = 'warnings'

    uid = Column(BigInteger, primary_key=True)
    swarnings = Column(BigInteger)

    def __init__(self, uid, swarnings):
        self.uid = uid
        self.swarnings = swarnings


class idcheck(base):
    __tablename__ = 'idcheck'

    uid = Column(BigInteger, primary_key=True)
    check = Column(Boolean, default=False)

    def __init__(self, uid, check):
        self.uid = uid
        self.check = check


class database():
    def create(self):
        base.metadata.create_all(engine)


def func1(file):
    os.system(f"python3.10 {file} 1")

# os.remove("bot.sqlite")
# Thread(target=func1, args=("permissionsbackup.py",)).start()
# Thread(target=func1, args=("configbackup.py",)).start()
# Thread(target=func1, args=("userbackup.py",)).start()
# Thread(target=func1, args=("warningsbackup.py",)).start()
# Thread(target=func1, args=("bansbackup.py",)).start()
# # os.system("permissionsbackup.py 1")
# # os.system("configbackup.py 1")
# # os.system("userbackup.py 1")
# # os.system("warningsbackup.py 1")
# # os.system("bansbackup.py 1")
# import datetime
# with open('lastbackup.txt', 'w') as f:
#     f.write(f"Last backup made at: {datetime.datetime.now()}")
