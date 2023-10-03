import json
import os
from datetime import datetime

import sqlalchemy.exc
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

import databases.current as currentDB
import databases.old as olddb
import time

currentDB.database.create()
olddb.database().create()

oldsession = Session(bind=olddb.engine)
newsession = Session(bind=currentDB.engine)
users = oldsession.query(olddb.user).all()
start = time.perf_counter()
for u in users:
    try:
        user = currentDB.Users(uid=u.uid, dob=datetime.strptime(u.dob, "%m/%d/%Y"))
        newsession.merge(user)
        newsession.commit()
    except sqlalchemy.exc.PendingRollbackError:
        newsession.rollback()

    except:
        pass
print("users done")
newsession.close()
idcheck = oldsession.query(olddb.idcheck).all()
wuser = newsession.query(currentDB.Users).all()
userids = [x.uid for x in wuser]
print(len(userids))
for i in idcheck:
    if i.uid not in userids:
        user = currentDB.Users(uid=i.uid)
        newsession.merge(user)
    idc = currentDB.IdVerification(uid=i.uid, reason="Migrated from old database", idcheck=i.check)
    newsession.add(idc)
    newsession.commit()

print("IDcheck done")
newsession.close()
warnings = oldsession.query(olddb.warnings)
for w in warnings:
    count = w.swarnings
    if w.uid not in userids:
        user = currentDB.Users(uid=w.uid)
        newsession.merge(user)
    while count > 0:
        warn = currentDB.Warnings(uid=w.uid, reason="Search warning migrated from old db", type="SEARCH")
        count -= 1
        newsession.add(warn)
        newsession.commit()
print("warnings done")
for file in os.listdir('users'):
    with open(f'users/{file[:-5]}.json', 'r') as f:
        try:
            data = json.load(f)
        except:
            print(f"{file} failed")

        if len(data['warnings']) > 0:
            count = len(data['warnings'])
            pos = len(data['warnings']) - 1
            if file[:-5] not in userids:
                user = currentDB.Users(uid=file[:-5])
                newsession.merge(user)
            while count > 0:
                warn = currentDB.Warnings(uid=file[:-5], reason=data['warnings'][pos], type="WARN")
                count -= 1
                pos -= 1
                newsession.add(warn)
                newsession.commit()

#Adding default configs
server = currentDB.Servers(guild=395614061393477632)
newsession.add(server)
newsession.commit()
devchannel = currentDB.Config(guild=395614061393477632, type="DEV", value="987679198560796713")
newsession.add(devchannel)
welcome = currentDB.Config(guild=395614061393477632, type="WELCOME", value="Welcome to roleplay meets reborn")
newsession.add(welcome)
lobby = currentDB.Config(guild=395614061393477632, type="LOBBY", value="973355021137752114")
newsession.add(lobby)
newsession.commit()

confrequest = newsession.scalars(Select(currentDB.Config).where(currentDB.Config.guild == 395614061393477632))
for x in confrequest:
    value = x.value
    if value.isdigit():
        print("this is an int")
        continue
    print("this is a string")
end = time.perf_counter()
print(f"Migration finished in {end - start:0.4f} seconds")