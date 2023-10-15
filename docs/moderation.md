---
layout: default
title: Moderation Guide
nav_order: 5
---

<h1 align="center">Moderation commands</h1>
The moderation commands are built to help the staff enforce the rules in the server, as well as a toolkit. This includes
commands to kick, ban and warn users. The commands are split into two categories, mod and admin. Mod commands are commands
which are used by moderators and admins, admin commands are commands which are used by admins only.

Warnings have been completely overhauled, the new system is much more flexible and allows for easier navigation and
management.

### mod: `/watchlist user:required reason:required`

Adds the user to the watchlist, this command is used to keep track of users who haven't broken the rules yet but are
close or suspected of breaking the rules. The command will automatically log the user's name, id and the reason given
both in a channel and in the database.

### mod: `/watchhistory user:required`

Shows a fancy paginated embed with all the warnings the user has received, this command is used to quickly check if a
user has been watchlisted before and manage the watchlist.

### mod: `/kick user:required reason:optional`

Kicks the user from the server, this command is used to remove users who have broken the rules with an invite link to
rejoin. The reason is optional
but recommended as it is logged and sent to the user.

the default reason is: "breaking the server rules"

user receives:
```text
you've been kicked from <servername> for <reason>
 
You may rejoin once your behavior improves.
<insert invite link here>
```

### mod: `/notify user:required reason:required`

Notifies the user with the reason given. This command can be used for a multitude of reasons without logging an official
warning.

user receives:
```text
<servername> **__Notification__**: <reason>
```

### mod: `/warn user:required notify:(Yes/No)`
Warns a user for breaking our rules, it is however **not** used for search warnings. If a search warning has to be sent
out, please use `/forum warn` to achieve this. The command saves the warning which was given.

### mod: `/warnhistory user:required`
Shows a fancy paginated embed with all the warnings the user has received, this command is used to quickly check if a
user has been warned before and manage the warnings. Only shows warnings given with the `/warn` command.

Only admins can remove warnings.

### admin: `/ban bantype:required appeal:required member:optional memberid:optional reason:optional`

Ban is used to permanently remove users from all RMR servers, this command informs the user (if possible). If the ID
version
of the command has been executed the user will be added to the ID list.

When doing the command you can choose between member and memberid or do them both. If you do member and the member is
NOT
in the server, then the command will fail whereas memberid will ALWAYS work.

examples:<br>
`/ban bantype:ID appeal:Yes memberid:188647277181665280`<br>
`/ban bantype:Custom appeal:No member:@Rico Stryker#6666`

user receives:
```text
You've been banned from <servername> with reason: 
<reason>

<if appeal is yes>
To appeal this ban, you can send an email to roleplaymeetsappeals@gmail.com
 ```

After the command is done, it will log automatically into the shared bans channel of RMR and RMN.

You can add ban types with the `/config banmessages action:(add/remove) name:(name)` command. More info in the config
section.

### admin: `/searchban member:required days:required`

This command is used to ban a user from the search section, this command will automatically give the user the timeout
role
and add the user to the search ban database. When the timestamp has been reached, the user will automatically be removed
from
the database and the timeout role will be removed.