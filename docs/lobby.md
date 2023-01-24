---
layout: default
title: Lobby guide
nav_order: 3
---
<h1 align="center">Lobby Commands & info </h1>
The lobby is the area where users enter our server, this area is incredibly important and to ensure the
safety of our users, we check their dobs and ages with previous entries in our database. 

### Lobby automod

The automod in the lobby does a few things, it enforces a template of age mm/dd/yyyy, and once this is filled in the automod
posts a message in the lobby moderation channel. The bot takes the information and formats it for the staff to easily 
execute the command.

If a user is underaged, the bot will automatically flag them for the ID list. **it does NOT save underaged user's data other than the uid.**
### commands
() = required, [] = optional
#### Mod: `?18a (user) (age) (mm/dd/yyyy)`, `?21a (user) (age) (mm/dd/yyyy)`, `?25a (user) (age) (mm/dd/yyyy)`
the three age commands each work the same, except for the role they give. When one of the commands is sent in 
(example: `?21a @rico stryker#6666 23 01/01/2000`) the bot will first check if the age and dob match and then it will 
check the database if there is a previous entry and check if this matches too. If no entry is found, the user is added
to the database. If the user is on the ID list, it will stop the command and inform the staff.

User's can request this data to be removed under GDPR: right to erasure.

#### Mod: `?agecheck (dob)`
this command is used to quickly check what age the user is supposed to be, it will calculate the current age using the 
date of birth. 

#### Mod: `?dblookup (user)`
This will pull up an age entry from the database, this command is used when there is a database issue or we wish to 
double check a dob.

#### Mod: `?ageadd (userid) (age) (mm/dd/yyyy)`
if a user has left the server, this command can be used to add them to the database.

#### Admin only: `agefix (user) (age) (mm/dd/yyyy)` or `agefix (userid) (age) (mm/dd/yyyy)` 
This command is intended to fix an age entry that is messed up. A replacement has been added for an age entry with an 
age/dob discrepancy 
 
#### Admin only: `?dbremove @user` or `?dbremoveid @userid`
This command is used to remove the user from the database, this currently removes the user ID and dob from the database - not warnings.
### ID commands
#### mod: `/lobby idadd (userid)`
This command is used to add a user to the ID list, which prevents users from being approved with the age commands, this also affects Age verifier.

#### admin: `/lobby idremove (userid)`
Removes the user from the ID list.
#### admin: `/lobby idverify`
Updates the user's info in the age info channel, database and clears the ID flag from the user so they can be let through with
the age commands. This command does _not_ let users through.