---
layout: default
title: Lobby Guide
nav_order: 3
---

<h1>Config and setup</h1>

RMRbot's setup is relatively painless, and has to only be done once when the bot joins. Since the bot is only
designed for two servers: RMR and RMN. A lot of the setup can be done through the setup command.

for all of the commands below, the permissions guild_manage required to run them.

## `/config setup`

This command will run you through the setup process of setting up the channels and roles for the bot to function
properly.
To setup setup the welcoming messages, search options and ban options will need to be done through the config command
independently.

## `/config messages key:option action:(set/remove) `

after entering the config messages command you will be prompted with a modal to input the message you wish to have
displayed for the option you have chosen. The options are as follows:

* welcomemessage
* lobbymessage
* reminder

## `/config searchcommands action:(add/remove) name:(name)`

after entering the config searchcommands command you will be prompted with a modal to input the warning you wish to have
displayed by your search warning.
The name is the name of the warning, for example: `?config searchcommands action:add name:warning1` will set the warning
to warning1.

## `/config banmessages action:(add/remove) name:(name)`

after entering the config bancommands command you will be prompted with a modal to input the message you wish to have
displayed by your ban.
The name is the name of the ban, for example: `?config banmessages action:add name:ban1` will set the ban to ban1.

## `/config welcometoggle action:(enabled/disabled)`

This command will enable or disable the welcome message.

## `/config channels key:option action:(set/remove) value:(channel)`

This command will set the channel for the option you have chosen. the value will display discord.TextChannel objects to
choose from. the channel name is the name of the channel, for
example: `/config channels key:lobby action:set value:lobby`

## `/config forums key:option action:(set/remove) value:(forum)`

This command will set the forum for the option you have chosen. the value will display the discord.ForumChannel name to
choose from.
the forum name is the name of the forum channel, for example: `/config forums key:lobby action:set value:search-channel`
will set the lobby forum to the lobby channel.

## `/config role key:option action:(set/remove) value:(role)`

This command will set the role for the option you have chosen. the value will display discord.Role objects to choose
from.

## `/config searchcommands action:(add/remove) name:(name)`
after entering the config searchcommands command you will be prompted with a modal to input the warning you wish to have
displayed by your search warning. The name is the name of the warning, for example: `/config searchcommands action:add name:warning1` will set the warning to warning1.

## `/config view`
Allows you to view the current configuration of the server. This command is not required to be run, but is useful to see 
what the current configuration is.



