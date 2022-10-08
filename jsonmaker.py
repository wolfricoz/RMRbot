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
            with open(f"users/template.json", "w") as outfile:
                outfile.write(json_object)
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
            self.create(user.id, user)
            print(f"config created for {user.id}")
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
            self.create(user.id, user)
            print(f"config created for {user.id}")
