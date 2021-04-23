# Predictions-Bot
  A Discord Predictions bot that is similar to twitch predictions, allowing administrators of the discord server to set up bets with fake points accrued by being active in the voice channel. The points obtained over time will be collected to a database on mongoDB. 

## How it works

### Predictions
  People's points are put into a dictionary for a temporary time until a winner is decided. After a winner is decided a function gets the loser's money and divides it up by percentages of the winner's pool. For example, the person who puts in 8000 points will get more points than someone who puts in 1000 points. If your side wins you will also get your points back + your percentage of the cut.

### Points over time
  The bot will constantly check if someone is in the voice channel and give them increment their amount with a random range of 90-125 points. Eventually I want to add a MEE6 like leveling system with messages. Unfortunately I would have to make a custom cooldown for Command Listener and I would like some assistance to that [#1 issue](https://github.com/Adgonzalez2018/Predictions-Bot/issues/1). 

# Commands = '$'
## Administrators Only
- `$Start` --> Params: "Title", "Time (s)", "believe side", "doubt side". Sets the prediction and sends a display/text to show sides and you can only bet within the given time.

![Image of Start Text](https://cdn.discordapp.com/attachments/744656857226018905/833857121305100288/Capture.PNG)

- `$refund` --> Resets the Prediction and gives back peoples points.
- `$won` --> Params: "Which side one". Sends a message with the percentages of both sides, biggest payout and amount of people on side.

![Imageo of Winner Text](https://cdn.discordapp.com/attachments/744656857226018905/833857915894628352/unknown.png)

- `$give/take` --> Param: "member.name", (amount). Allows admins to give/take points from members.  

## Regular Members
- `$believe` --> Param: (Amount). This bets on the "believe" side 
- `$doubt` --> Param: (Amount). This bets on the "doubt" side
- `$points` --> Displays your points (Automatically starts with 1000)

# Dependencies
- import time
- from discord.ext import commands
- from discord.ext.commands import has_permissions, MissingPermissions
- from threading import Timer
- from pymongo import MongoClient
- import math
- import random
- import os
