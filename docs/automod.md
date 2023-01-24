<h1 align="center">Auto Moderation</h1>
Auto moderation is currently a beta feature which is still being refined. Auto moderation was created to lessen the burden
on the staff, by having the bot flag rule breakers and sometimes outright taking action.

### Lobby automod

The automod in the lobby does a few things, it enforces a template of age mm/dd/yyyy, and once this is filled in the automod
posts a message in the lobby moderation channel. The bot takes the information and formats it for the staff to easily 
execute the command.

### Search Automod

The search channels have a lot of rules which can be hard to keep track of; this is where automod came in originally to
reduce the stress of the advert team. The following rules are being moderated:

#### List checking
The bot checks if the advert is under 10 list items by looking for messages shorter than 50, with -, *, •, • >, ★, ☆, ♡ (More to be added when needed!).
When an user does post a list over 10 items, the advert team is notified.

#### List checking
The bot checks for more than 2 spaces in a row, if such an instance is found the advert is removed and the user is notified.

#### Length checking
The bot checks if the advert is under 650 characters for quick-search and if the advert is over 600 characters for general search channels. Special channels are excempt!
If the advert breaks this rule, it automatically removes this and notifies the user without recording an official warning.

#### Age checking (beta)
The bot is using regex to look through adverts to see if the user has included the following 3 lines:<br>
`r"\b(all character(s|'s) ([2-9][0-9]|18|19)|all character(s|'s) are ([2-9][0-9]|18|19)|([2-9][0-9]|18|19)\+ character(s|'s))\b"`
* all characters 18+
* all character's are 18+
* 18+ character's 
note: the age checker will look for any age over 18, so it could be 27+ and still work!

#### cooldown (final testing phase)
The cooldown checker checks the date of the previous message sent in the channel, this however can be circumvented if the user
removes their previous message. If a previous message was in the time period set for the channel (70 for normal search, 22 for quick)

The bot currently informs the staff but the goal is to implement this to automatically remove the post and inform the user.
