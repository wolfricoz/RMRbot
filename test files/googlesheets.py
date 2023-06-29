import json
import os
from abc import ABC, abstractmethod
from random import shuffle
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from timer import timer
# from ducks import Dex
# Authorize the API
scope = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.file'
]

no = ["I want my partner to play as", "Other information", "Timestamp", "Email address", "Uid", "Feedback", "Participate?", "age", "Rematch"]


class RoomMate(ABC):
    @abstractmethod
    def pairing(p, u1, u2):
        """Checks if the pairings match, if they do not match then will return a -1 to signal the loop to stop"""
        user1pref = str(u1.get("I want my partner to play as")).replace(" ", "").split(',')
        user1 = str(u1.get(p)).replace(" ", "").split(',')
        user2pref = str(u2.get("I want my partner to play as")).replace(" ", "").split(',')
        user2 = str(u2.get(p)).replace(" ", "").split(',')
        sc = 0
        psc = 0
        for up in user1pref:
            for u in user2:
                if up == "" or u == "":
                    pass
                elif up.lower() in u.lower():
                    # print(up)
                    # print(u)
                    sc += 1
                elif u.lower() == "any" or up.lower() == "any":
                    sc += 1
        for up in user2pref:
            for u in user1:
                if up == "" or u == "":
                    pass
                elif up.lower() in u.lower():
                    # print(up)
                    # print(u)
                    psc += 1
                elif up.lower() == "any":
                    psc += 1
                elif u.lower() == "any" or up.lower() == "any":
                    psc += 1
        if sc == 0:
            print(f"{u2['Username']} was not a match for {u1['Username']}(pairing)")
            sc = -1
            psc = 0

        if psc == 0:
            print(f"{u2['Username']} was not a match for {u1['Username']}(pairing)")
            sc = -1
            psc = 0
        return sc + psc

    @abstractmethod
    def nsfw(p, u1, u2):
        """Checks if the NSFW preferences match, if they do not match then will return a -1 to signal the loop to stop.
        If they semi-match they get a +1, if its a direct match its a +2"""
        sc = 0
        if u1.get(p) == "SFW" and u2.get(p) == "NSFW" or u1.get(p) == "NSFW" and u2.get(p) == "SFW":
            sc = -1
            print(f"{u2['Username']} was not a match for {u1['Username']}(nsfw)")
        elif u1.get(p) == u2.get(p):
            sc += 2
        else:
            sc += 1
        return sc

    @abstractmethod
    def genres(p, u1, u2):
        """Checks the genre preferences, if user2 has preferences which are in user1's then it will deduct a point"""
        user1 = str(u1.get(p)).replace(" ", "").split(',')
        userex1 = str(u1.get("Excluded Genres")).replace(" ", "").split(',')
        user2 = str(u2.get(p)).replace(" ", "").split(',')
        sc = 0
        for up in user1:
            for u in user2:
                if up == "" or u == "":
                    pass
                elif up.lower() in u.lower():
                    sc += 1
        for up in userex1:
            for u in user2:
                if up == "" or u == "":
                    pass
                elif up.lower() in u.lower():
                    sc -= 1
        return sc

    @abstractmethod
    def other(p, u1, u2):
        """checks if the values match, if they match then adds +1 to score"""
        user1 = str(u1.get(p)).replace(" ", "").split(',')
        user2 = str(u2.get(p)).replace(" ", "").split(',')
        sc = 0
        for up in user1:
            for u in user2:
                if up == "" or u == "":
                    pass
                elif up.lower() == u.lower():

                    sc += 1
        return sc

    @abstractmethod
    def api():
        # Authorize the API
        scope = [
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/drive.file'
        ]
        file_name = 'client_key.json'
        creds = ServiceAccountCredentials.from_json_keyfile_name(file_name, scope)
        client = gspread.authorize(creds)
        sheet = client.open('RR TEST SHEET 11423').sheet1
        python_sheet = sheet.get_all_records()
        shuffle(python_sheet)
        with open('roulette.json', 'w') as f:
            json.dump(python_sheet, f, indent=4)

        return python_sheet, sheet

    @abstractmethod
    def agecheck(p, u1, u2):
        if isinstance(u1['Age'], int):
            age1 = u1['Age']
        else:
            age1 = int(re.sub(r'\D', '', u1['Age']))
        if isinstance(u2['Age'], int):
            age2 = u2['Age']
        else:
            age2 = int(re.sub(r'\D', '', u2['Age']))




        u1pref = int(u1['Minimal partner age'])
        u2pref = int(u2['Minimal partner age'])
        sc = 0
        if age2 >= u1pref:
            sc += 1
        else:
            sc = -1
        if age1 >= u2pref:
            sc += 1
        else:
            sc = -1
        return sc

with timer() as t:
    python_sheet, sheet = RoomMate.api()
    try:
        os.remove("rr.txt")
    except FileNotFoundError:
        pass
    matched = {}
    matchcounter = {}
    matchresult = {}
    for mc in python_sheet:
        matchcounter[mc.get('Username')] = 0
    for u1 in python_sheet:
        print(u1['Username'], " being matched")
        userchecked = {}
        gcount = 0
        oldcount = 0

        if matchcounter[u1.get('Username')] >= 3:
            print(f"{u2.get('Username')} already has the max amount of matches")
            continue
        for p in u1.keys():
            sk = ['Username']

            if p in no or p in sk:
                pass
            else:
                user1 = str(u1.get(p)).replace(" ", "").split(',')
                for _ in user1:
                    gcount += 1
        for u2 in python_sheet:
            count = 0
            if u1['Participate?'] == "No" or u2['Participate?'] == "No":
                count = -1
                break
            if matchcounter[u2.get('Username')] >= 3 :
                print(f"{u2.get('Username')} is already matched")
                continue
            for p in u2.keys():
                if p == "Username" and u1.get(p) == u2.get(p):
                    count = -1
                    break
                elif p == "I want to play as":
                    pc = RoomMate.pairing(p, u1, u2)
                    if pc == -1:
                        count = -1
                        break
                    else:
                        oldcount = count
                        count += pc
                elif p == "NSFW":
                    pc = RoomMate.nsfw(p, u1, u2)
                    if pc == -1:
                        count = -1
                        break
                    else:
                        oldcount = count
                        count += pc

                elif p == "Genres":
                    pc = RoomMate.genres(p, u1, u2)
                    oldcount = count
                    count += pc
                elif p == "Minimal partner age":
                    pc = RoomMate.agecheck(p, u1, u2)
                    oldcount = count
                    count += pc

                elif p in no:
                    continue
                else:
                    pc = RoomMate.other(p, u1, u2)
                    oldcount = count
                    count += pc
                print(f"{u1['Username']} + {u2['Username']}: {p}: {count}/{gcount} ({count - oldcount})")
            # Final count checker, if -1, its skipped. otherwise its converted to percentages.
            if count == -1:
                pass
            else:
                percent = 100 / gcount * count

                userchecked[u2.get('Username')] = round(percent, 2)
        delete = [key for key in userchecked if userchecked.get(key) == -1]
        for w in delete:
            userchecked.pop(w)

        if len(userchecked) == 0:
            winner = "No partner matched their preferences"
            matchresult[u1.get('Username')] = None
        else:
            winner = max(userchecked, key=userchecked.get)
            matchcounter[winner] += 1
            matchcounter[u1.get('Username')] += 1
            matchresult[u1.get('Username')] = max(userchecked.values())
            print(matchcounter)

            # done.append(u1.get('Username'))
        print(f"<----\ndone with {u1.get('Username')}\n"
              f"Recommended partner: {winner}\n"
              f"---->")
        if len(winner) == 0:
            winner = "No partner matched their preferences"
        with open('rr.txt', 'a', encoding='utf-16') as f:
            f.write(f"\nUsername: {u1.get('Username')} ({u1.get('Uid')})\n"
                    f"Recommended partner(s): {winner}\n"
                    f"Extra info from user: {u1.get('Other information')}\n"
                    f"\ndebug: {userchecked}\n")
        # print(done)
        matched[u1.get('Username')] = winner
        print(userchecked)
    print(t.elapse)
    print(matched)

    print(f"R")
    print("Match results: ",matchresult)
    for m, ma in matched.items():
        print(f"{m} and {ma}. match rating: {matchresult[m]}")
    matchedid = []
    for i in python_sheet:
        if i.get('Username') == winner:
            winnerid = i.get('Uid')
    matchedid[u1.get('Uid')] = winnerid
    # test = next(item for item in python_sheet if item["Username"] == "Rico Stryker#6666")
    cell = sheet.find(f"{m}")
    sheet.update_cell(cell.row, 22, value=f"{ma},{cell.value}")
