---
layout: default
title: Lobby Guide
nav_order: 4
---

<h1>Lobby Information</h1>
The lobby's main function is to verify the user based on their age and date of birth. This is done by the bot automatically
when the user joins the server. When the user inputs their date of birth, the bot will send a message to the lobby moderation
where the staff can easily approve the user. The bot will automatically check the user's age and date of birth against the
database and if the user is on the ID list. If the user is on the ID list, the bot will automatically flag the user and
inform the staff.

### Lobby automod:

* Invite info: When a user joins the server, the bot will automatically send a message with the invite info.
* on join send button: When a user joins the server, the bot will automatically send a message with a button to verify
  their age.
* Check age: When a user verifies their age, the bot will automatically check if the user is on the ID list, if their
  age and dob match and if there is a previous entry in the database. If one of the mentioned checks fails, the bot will
  notifiy the staff.
* clean up: When a user is approved by staff, the bot will automatically remove the message with the button and the
  user's
  message.
* welcome message: When a user is approved by staff, the bot will automatically send a welcome message in the general
  chat.

### mod: `?18a, ?21a, ?25a user age mm/dd/yyyy`

this is automatically done by clicking the allow button in the lobby moderation channel

The three age commands each work the same, except for the role they give.
(example: `?21a @rico stryker#6666 23 01/01/2000`)

### mod: `/Lobby return user`

This command is used to return a user to the lobby, this is used when a user has been approved but needs to be returned
to the lobby for whatever reason. This will automatically remove the roles from the user specified in the config.
it is affected by the options: 18+ role, 21+, 25+ role, add, rem, return to lobby. Rem will be added to the user.

### mod: `/lobby agecheck dob:mm/dd/yyyy`

this command is used to quickly check what age the user is supposed to be, it will calculate the current age using the
date of birth.

## mod: `/verification idcheck operation:(add, update, get) toggle:(True, False) userid:required reason:optional`

This command is used to add, update or get an entry in the ID list. The ID list is used to prevent users from being
approved with the age commands.

### admin: `/Lobby button text:string`

This will create a button with the text given, this is used to create the age verification button, the age verification
button
is also automatically created when a user joins the server.

### admin: `/Lobby database operation:option userid:required dob:optional`

This command is used to add, remove or edit an entry in the database. The database is used to check if a user has been
verified before and to add date of births to the database. This command does not affect the ID list.

### admin: `/Lobby idverify process:option user dob:mm/dd/yyyy`

This command is used to verify a user's age, this command is used when the user is on the ID list. This command will
update
the user's info in the age info channel, database and clears the ID flag from the user so they can be let through with
the age commands. This command does _not_ let users through unless process:True is used.

## NSFW age gate
just like the lobby, the NSFW age gate is used to verify the user's age. This is done by the bot automatically when the
user clicks the button. The bot will automatically check the user's age and date of birth against the database and if
the user is on the ID list. If the user is on the ID list, the bot will automatically flag the user and inform the
staff.