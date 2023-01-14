import json
import os
from abc import ABC, abstractmethod
# Data to be written
class configer(ABC):
    @abstractmethod
    async def create(userid, member):
        "Creates the user data"
        dictionary = {
            "Name": member.name,
            "warnings": [],
        }
        json_object = json.dumps(dictionary, indent=4)
        if os.path.exists(f"users/{userid}.json"):
            print(f"{userid} already has a config")
        else:
            with open(f"users/{userid}.json", "w") as outfile:
                outfile.write(json_object)
                print(f"config created for {userid}")


    async def addwarning(self, user, interaction, warning):
        if os.path.exists(f"users/{user.id}.json"):
            with open(f"users/{user.id}.json") as f:
                data = json.load(f)
                data['warnings'].append(warning)
            with open(f"users/{user.id}.json", 'w') as f:
                json.dump(data, f, indent=4)
        else:
            configer.create(user.id, user)
            print(f"config created for {user.id}")
            if os.path.exists(f"users/{user.id}.json"):
                with open(f"users/{user.id}.json") as f:
                    data = json.load(f)
                    data['warnings'].append(warning)
                with open(f"users/{user.id}.json", 'w') as f:
                    json.dump(data, f, indent=4)
    async def getwarnings(self, user, interaction):
        if os.path.exists(f"users/{user.id}.json"):
            with open(f"users/{user.id}.json") as f:
                data = json.load(f)
                warnmess = "\n".join(data['warnings'])
                print(len(warnmess))
                if len(warnmess) < 2000:
                    await interaction.channel.send(f"`Warnings:` \n{warnmess}")
                elif len(warnmess) > 2000:
                    await interaction.channel.send(f"`Warnings:` \n{warnmess[0:2000]}")
                    await interaction.channel.send(warnmess[2000:4000])
                elif len(warnmess) > 2000:
                    await interaction.channel.send(f"`Warnings:` \n{warnmess[0:2000]}")
                    await interaction.channel.send(warnmess[2000:4000])
                    await interaction.channel.send(warnmess[4000:6000])
        else:
            configer.create(user.id, user)
            print(f"config created for {user.id}")
<<<<<<< Updated upstream
=======


class BanLogger:
    def create(userid):
        """Creates the ban log, which is checked by the bot"""
        banjson = {
            "uid": userid,
            "bans": {
            },
        }
        with open(f'../bans/{userid}.json', 'w') as f:
            json.dump(banjson, f, indent=4)

    def add(userid, guild, reason):
        ban = {"reason": reason}
        with open(f'../bans/{userid}.json', 'r+') as f:
            data = json.load(f)
            data['bans'][guild] = ban
            print(data)
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
                    BanLogger.read(userid)
        else:
            print("user not banned")

class Cooldown():
    def add(self, userid, channel, time):

        with open(f'./users/{userid}.json', 'r+') as f:
            data = json.load(f)
            data['cooldowns'][channel] = time.strftime('%x %X')
        with open(f'./users/{userid}.json', 'w') as f:
            json.dump(data, f, indent=4)

    def check(self, userid, channel, time):
        with open(f'./users/{userid}.json', 'r+') as f:
            tz = pytz.timezone('US/Eastern')
            data = json.load(f)
            now = datetime.now(tz)

            if str(channel) in data['cooldowns']:
                print("cooldown found")
                print(data['cooldowns'][str(channel)])
                cooldown = "".join(data['cooldowns'][str(channel)])
                if now.strftime('%x %X') > cooldown:
                    print("Can post")
                    return True
                else:
                    print("Can't post")
                    return False
            else:
                Cooldown.add(self, userid, channel, time)
                return True

    async def notify(self,  userid, channel, modchannel, message):
        with open(f'./users/{userid}.json', 'r+') as f:
            tz = pytz.timezone('US/Eastern')
            data = json.load(f)
            now = datetime.now(tz)

            if str(channel) in data['cooldowns']:
                cooldown = "".join(data['cooldowns'][str(channel)])

                await modchannel.send(f"{message.author.mention} has posted too early in {message.channel.mention}. \n"
                                      f"Last post: {cooldown} in <#{str(channel)}>")




class Updater:
    async def update(self):
        count = 0
        for x in os.listdir('./users'):
            print(x)
            with open(f'./users/{x}', 'r+') as f:
                data = json.load(f)
                dictionary = {
                    "Name": data['Name'],
                    "warnings": data['warnings'],
                    "cooldowns": {
                    },
                }
            with open(f'./users/{x}', 'w') as f:
                json.dump(dictionary, f, indent=4)
            count += 1
        print(f"updated: {count}")


class Datechecker:
    def datecheck(input, channel, timedelt):
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
>>>>>>> Stashed changes
