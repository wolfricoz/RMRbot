from sqlalchemy import create_engine
from sqlalchemy import Column, String, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
load_dotenv('main.env')
DBTOKEN = os.getenv("DB")

#sqlalchemy
engine = create_engine(DBTOKEN, echo=True) #connects to the database
base = declarative_base()
engine.echo = False
#class creates table
class user (base):

   __tablename__ = 'user'

   uid = Column(Integer, primary_key=True)
   dob = Column(String(10))

   def __init__(self, uid, dob):
       self.uid = uid
       self.dob = dob


class config(base):

    __tablename__ = 'config'

    guild = Column(Integer, primary_key=True)
    lobby = Column(Integer)
    agelog = Column(Integer)
    modlobby = Column(Integer)
    general = Column(Integer)

    def __init__(self, guild, lobby, agelog, modlobby, general):
        self.guild = guild
        self.lobby = lobby
        self.agelog = agelog
        self.modlobby = modlobby
        self.general = general
#commits it to the databse
class permissions (base):

   __tablename__ = 'permissions'

   guild = Column(Integer, primary_key=True)
   admin = Column(Integer)
   mod = Column(Integer)
   trial = Column(Integer)

   def __init__(self,guild, admin, mod, trial):
       self.guild = guild
       self.admin = admin
       self.mod = mod
       self.trial = trial

class warnings (base):

   __tablename__ = 'warnings'

   uid = Column(Integer, primary_key=True)
   swarnings = Column(Integer)


   def __init__(self, uid, swarnings):
       self.uid = uid
       self.swarnings = swarnings

base.metadata.create_all(engine)


