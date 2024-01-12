from datetime import datetime, timedelta

dcheck = datetime.now() + timedelta(hours=-70)
hours = abs(datetime.now() - dcheck).total_seconds() / 3600
timeinfo = f"last bump: {datetime.now() - dcheck}"
if datetime.now() + timedelta(hours=-69) < dcheck:
    print("72 hours has passed")
print(timeinfo)
print(round(hours, 2))