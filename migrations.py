from sqlalchemy import create_engine, MetaData
from sqlalchemy import Column, String, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from migrate.versioning.schema import Table, Column
from dotenv import load_dotenv
import sqlite3
import os
import db
load_dotenv('main.env')
DBTOKEN = os.getenv("DB")

#sqlalchemy
engine = create_engine(DBTOKEN, echo=True) #connects to the database
db_meta = MetaData(bind=engine)
engine.echo = False

class idcheck (base):

   __tablename__ = 'idcheck'

   uid = Column(BIGINT, primary_key=True)
   check = Column(Boolean, default=False)


   def __init__(self, uid, check):
       self.uid = uid
       self.check = check

idcheck.__table__.create(db.session.bind)
#Gets table
#table = Table('permissions', db_meta)
#adds column to the table
#try:
#    col = Column('lobbystaff', Integer, default=None)
#    col.create(table)
#    print("Column 'lobbystaff' added to table")
#except:
#    print("Column 'lobbystaff already exists")


