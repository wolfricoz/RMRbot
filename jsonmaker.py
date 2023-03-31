import json
import os
from abc import ABC, abstractmethod
import datetime
from datetime import datetime, timedelta
import pytz
#makes dir for ban logging
try:
    os.mkdir('../bans/')
except:
    pass

# Data to be written


class Configer(ABC):
    @abstractmethod
    async def create(userid, member):
        """Creates the user data"""
        dictionary = {
            "Name": member.name,
            "warnings": [],
            "cooldowns": {
            },
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
            await Configer.create(user.id, user)
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
            await Configer.create(user.id, user)
            print(f"config created for {user.id}")


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

class guildconfiger(ABC):
    @abstractmethod
    async def create(guildid, guildname):
        try:
            os.mkdir("jsons")
        except:
            pass
        "Creates the config"
        dictionary = {
            "Name": guildname,
            "addrole": [],
            "remrole": [],
            "welcomeusers": True,
            "welcome": "This can be changed with /config welcome",
            "waitingrole": [],
        }
        json_object = json.dumps(dictionary, indent=4)
        if os.path.exists(f"jsons/{guildid}.json"):
            print(f"{guildid} already has a config")
            with open(f"jsons/template.json", "w") as outfile:
                outfile.write(json_object)
        else:
            with open(f"jsons/{guildid}.json", "w") as outfile:
                outfile.write(json_object)
                print(f"config created for {guildid}")
    @abstractmethod
    async def addrole(guildid, interaction, roleid, key):
        if os.path.exists(f"jsons/{guildid}.json"):
            with open(f"jsons/{guildid}.json") as f:
                data = json.load(f)
                for x in data[key]:
                    if x == roleid:
                        await interaction.followup.send("Failed to add role! Role already in config")
                        break
                else:
                    data[key].append(roleid)
                    await interaction.followup.send(f"Role added to {key}")
            with open(f"jsons/{guildid}.json", 'w') as f:
                json.dump(data, f, indent=4)
    @abstractmethod
    async def remrole(guildid, roleid, key):
        if os.path.exists(f"jsons/{guildid}.json"):
            with open(f"jsons/{guildid}.json") as f:
                data = json.load(f)
                data[key].remove(roleid)
            with open(f"jsons/{guildid}.json", 'w') as f:
                json.dump(data, f, indent=4)
    @abstractmethod
    async def welcome(guildid, interaction,key, welcome):
        if os.path.exists(f"jsons/{guildid}.json"):
            with open(f"jsons/{guildid}.json") as f:
                data = json.load(f)
                data[key] = welcome
            with open(f"jsons/{guildid}.json", 'w') as f:
                json.dump(data, f, indent=4)
            await interaction.followup.send(f"welcome updated to '{welcome}'")
    @abstractmethod
    async def updateconfig(guildid):
        with open(f'jsons/{guildid}.json', 'r+') as file:
            data = json.load(file)
            newdictionary = {
                "Name": data['Name'],
                "addrole": data['addrole'],
                "remrole": data['remrole'],
                "welcomeusers": True,
                "welcome": data['welcome'],
                "waitingrole": ['waitingrole'],
            }
            print(newdictionary)

        with open(f'jsons/{guildid}.json', 'w') as f:
            json.dump(newdictionary, f, indent=4)
    @abstractmethod
    async def viewconfig(interaction, guildid):
        if os.path.exists(f"jsons/{guildid}.json"):
            with open(f"jsons/{guildid}.json") as f:
                data = json.load(f)
                vdict = f"""
Name: {data['Name']}
addrole: {data['addrole']}
remrole: {data['remrole']}
welcomeusers: {data['welcomeusers']},
welcome: {data['welcome']}
waitingrole: {data['waitingrole']}
                """
                return vdict