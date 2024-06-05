"""Test file for debugging purposes"""
import os
from datetime import datetime, timedelta
from databases import current as db
from dotenv import load_dotenv

# dcheck = datetime.now() + timedelta(hours=-70)
# hours = abs(datetime.now() - dcheck).total_seconds() / 3600
# timeinfo = f"last bump: {datetime.now() - dcheck}"
# if datetime.now() + timedelta(hours=-69) < dcheck:
#     print("72 hours has passed")
# print(timeinfo)
# print(round(hours, 2))

from classes.databaseController import SearchWarningTransactions

load_dotenv('.env')
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = os.getenv("PREFIX")
DBTOKEN = os.getenv("DB")
version = os.getenv('VERSION')
db.database.create()
var1, var2 = SearchWarningTransactions.get_total_warnings(188647277181665280)

print(var1)
print(var2)

