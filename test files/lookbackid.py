import json
import re
user = 451308005657542668
print("checking")
verification = re.compile(r"\*\*USER ID VERIFICATION\*\*", flags=re.IGNORECASE)
uuid = re.compile(r"\b451308005657542668\b", flags=re.MULTILINE)
with open('../config/history.json', 'r') as f:
    history = json.load(f)
for a in history:
    if history[a]['author'] == 987662623187288094:
        vmatch = verification.search(history[a]['content'])
        umatch = uuid.search(history[a]['content'])
        if vmatch is not None:
            if umatch is not None:
                print(f"[USER ID CHECK]{user} `{history[a]['created']}`\n"
                               f"{history[a]['content']}")
            else:
                print("umatch fail")