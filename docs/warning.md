---
layout: default
title: Warning commands
nav_order: 6
---
<h1 align="center">Warning commands</h1>
The warning commands are the commands which allow staff to warn users, edit search warnings and view warnings. The warning
system is scheduled to be overhauled in the future, but for now we will start with the old system!

#### mod: `/warn (user) (reason)`
This command warns a user for breaking our rules, it is however **not** used for search warnings. If a search warning has to be 
sent out, please use `/ad custom` to achieve this. The command saves the warning which was given.

This command also logs it in the warnings channel

#### mod: `/warnings (user)`
This command looks up all the warnings an user has received. it looks into both search warnings and normal warnings.
A current limitation of this command is that it can only show up to 2000 characterd of the warnings.

#### admin: `/ad warnremove (user) [amount]`
This removes a search warning from the user, if amount is not filled in then the command will remove 1 warning.

This command is often used when a search warning was given wrongfully, mistakes happen!
#### admin: `/ad warnadd (user) [amount]`
This adds a search warning from the user, if amount is not filled in then the command will remove 1 warning.

this command is mostly used if the database connection has been messed up and a warning needs to be added to compensate.
#### admin: `/ad warnset (user) (amount)`
This sets the amount of warnings a user has to the amount. The amount is required to be filled in, as there is no default.

