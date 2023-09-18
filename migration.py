from datetime import datetime

import sqlalchemy.exc
from sqlalchemy import select
from sqlalchemy.orm import Session

import databases.old as olddb
import databases.current as sqlalchemytest

sqlalchemytest.database().create()
olddb.database().create()

oldsession = Session(bind=olddb.engine)
newsession = Session(bind=sqlalchemytest.engine)
users = oldsession.query(olddb.user).all()
for u in users:
    try:
        user = sqlalchemytest.Users(uid=u.uid, dob=datetime.strptime(u.dob, "%m/%d/%Y"))
        newsession.add(user)
        newsession.commit()
    except sqlalchemy.exc.PendingRollbackError:
        newsession.rollback()

    except:
        pass

idcheck = oldsession.query(olddb.idcheck).all()

for i in idcheck:
    nuser = newsession.scalar(select(sqlalchemytest.Users).where(sqlalchemytest.Users.uid == i.uid))
    if nuser is None:
        user = sqlalchemytest.Users(uid=i.uid)
        newsession.add(user)
        idc = sqlalchemytest.IdVerification(uid=i.uid, reason="Underaged user from old database", idcheck=i.check)
        newsession.add(idc)
        newsession.commit()
        continue
    if i.uid == nuser.uid:
        idc = sqlalchemytest.IdVerification(uid=i.uid, reason="Migrated from old database", idcheck=i.check)
        newsession.add(idc)
        newsession.commit()
    else:
        print(f"{i.uid} not in users table")
