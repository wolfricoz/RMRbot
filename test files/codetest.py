import json
import os
from abc import ABC, abstractmethod
try:
    os.mkdir('../../bans/')
except:
    pass

class banlogger():
    def createban(userid, ):
        '''Creates the ban log, which is checked by the bot'''
        banjson = {
            "uid": userid,
            "bans": {
            },
        }
        with open(f'../bans/{userid}.json', 'w') as f:
            json.dump(banjson, f, indent=4)
    def addban(userid, guild, reason):
        ban = {"reason": reason}
        with open(f'../bans/{userid}.json', 'r+') as f:
            data = json.load(f)
            data['bans'][guild] = ban
        with open(f'../bans/{userid}.json', 'w') as f:
            json.dump(data, f, indent=4)
    def read(userid):
        with open(f'../bans/{userid}.json', 'r+') as f:
            data = json.load(f)
            for d, x in data['bans'].items():
                print(f"{d}: {x['reason']}")

    def check(userid):
        if os.path.exists(f'../bans/{userid}.json'):
            with open(f'../bans/{userid}.json', 'r+') as f:
                data = json.load(f)
                if len(data['bans'].items()) == 0:
                    print("user not banned")
                else:
                    banlogger.read(userid)
        else:
            print("user not banned")



banlogger.check(12345678910)

import datetime
from datetime import datetime, timedelta
import json
class Cooldown():
    def create(self, userid):
        '''Creates the ban log, which is checked by the bot'''
        banjson = {
            "uid": userid,
            "cooldowns": {
            },
        }
        if os.path.exists(f'{userid}.json') is True:
            print("file exists, skipping")
        else:
            with open(f'{userid}.json', 'w') as f:
                json.dump(banjson, f, indent=4)
    def add(self, userid, channel, time):

        with open(f'{userid}.json', 'r+') as f:
            data = json.load(f)
            data['cooldowns'][channel] = time.strftime('%x %X'),
            print(data)
        with open(f'{userid}.json', 'w') as f:
            json.dump(data, f, indent=4)

    def check(self, userid, channel):
        with open(f'{userid}.json', 'r+') as f:
            data = json.load(f)
            cooldown = "".join(data['cooldowns'][str(channel)])
            print(cooldown)
            return cooldown



class Datechecker:
    def datecheck(input, channel, timedelt):
        Cooldown.create(None, input)
        now = datetime.now()
        later = now + timedelta(days=timedelt)
        Cooldown.add(None, input, channel, later)
        Cooldown.check(None, input, channel)
        print(now)
        print(later)
        if now.strftime('%x %X') > str(Cooldown.check(None, input, channel)):
            print("time has passed" )
        else:
            print("on cooldown")


Datechecker.datecheck(123456789, 1025430775329464380, 3)
Datechecker.datecheck(123456789, 528743488163020840, -3)
Datechecker.datecheck(123456789, 1025430935958720522, 0)
Datechecker.datecheck(123456789, 1025430935958720523, 99)