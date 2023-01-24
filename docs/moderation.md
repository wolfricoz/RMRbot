---
layout: default
title: Moderation Commands
nav_order: 7
---
<h1 align="center">Moderation</h1>
The moderation commands are built to help the staff enforce the rules in the server, as well as a toolkit. 

#### mod: `/watchlist (user) (reason)`
This command adds the user to the watch list, collecting their username, userid and the reason which was given

```text
Name: @user
UID: 123445667789707
username: user#0000
reason reason here
```

#### mod: `/kick (user) [reason]`
The kick command removes an user from the server, often used as a last resort when the rules have been broken. The reason is
optional but recommended as it is logged and sent to the user.

This command logs in the shared bans channel.

#### Notify: `/kick (user) (reason)`
Notifies an user with the reason given. This command can be used for a multitude of reasons without logging an official warning

#### admin: `/ban (type) (appeal) [member] or [memberid] [reason]`
Ban is used to permanently remove users from all RMR servers, this command informs the user (if possible). If the ID version
of the command has been executed the user will be added to the ID list.

When doing the command you can choose between member and memberid or do them both. If you do member and the member is NOT
in the server, then the command will fail whereas memberid will ALWAYS work.
examples:<br>
`/ban type:ID appeal:Yes memberid:188647277181665280`<br>
`/ban type:Custom appeal:No member:@Rico Stryker#6666`

After the command is done, it will log automatically into the shared bans channel of RMR and RMN.
