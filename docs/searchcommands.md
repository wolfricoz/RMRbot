---
layout: default
title: Search commands Guide
nav_order: 5
---

[//]: # (write down all commands from forum.py)

<h1 align="center">Search commands</h1>

RMRbot has a few commands which are used to search for things, these commands are mostly used by the staff team to
modalate the search section.

### automod:

* on_thread_create: When a user creates a thread, the bot will automatically check if the user has other adverts up, how
  similar they are, if it is within three days, it will automatically check if the age disclaimer has been given. If it
  is all correct it will automatically add the right tags to the post.
* on_message: When a user posts a message, check if the user wants to bump the post, if so, bump it. If the user is on
  cooldown, inform them of this.
* on_message_delete: When a user deletes their message, check if it was the main post, if so, remove the thread from the
  channel and inform the user.

### all: `/forum bump`

This command is used to bump the thread, it will automatically check if the user is on cooldown. if the user hasn't
edited or commented in 3 days, it will automatically approve the thread.

### all: `/forum close`

Close the thread, this will remove the thread from the channel and send the user their advert.

### mod: `/forum warn warning_type:option thread:optional`

This command is used to warn the user with the warning_type, if the command is performed inside of a thread it will
automatically grab the information from the thread. If outside of a thread, the thread argument is required.

In the future, the giving a warning may be optional allowing staff to redirect adverts to the correct channel.
More warning types can be added with the `/config searchcommands action:(add/remove) name:(name)` command. More info in the
config section.

### mod: `/forum history user:required`

Shows the history of the user's search warnings and allows admins to remove warnings.

### mod: `approve applet`

To approve an advert, right click the message of the advert and go to the apps section, hover over it and select '
approve'

### mod: `custom warning`

To send a custom warning, right click the message of the advert and go to the apps section, hover over it and select '
custom warning'
