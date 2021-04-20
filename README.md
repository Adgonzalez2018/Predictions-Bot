# Predictions-Bot
A Discord Predictions bot that is similar to twitch predictions, allowing administrators of the discord server to set up bets with fake points accrued by being active in the voice channel. The points obtained over time will be collected to a database on mongoDB. 

## How it works
# Predictions
People's points are put into a dictionary for a temporary time until a winner is decided. After a winner is decided a function gets the loser's money and divides it up by percentages of the winner's pool. For example, the person who puts in 8000 poitns will get more points than someone who puts in 1000 points. If your side wins you will also get your points back + your percentage of the cut.
## Points over time
The bot will constantly check if someone is in the voice channel and give them increment their amount with a random range of 90-125 points. Eventually I want to add a MEE6 like leveling system with messages. Unfortunately I would have to make a custom cooldown for Command Listener. 

# Commands = '$'
## Administrators Only
-$start --> Params: "Title", "Time (s)", "believe side", "doubt side". Sets the prediction and sends a display/text to show sides and you can only bet within the given time.
-$refund --> Resets the Prediction and gives back peoples points.
-$won --> Params: "Which side one". Sends a message with the percentages of both sides, biggest payout and amount of people on side.
-$give/take --> Param: "member.name", (amount). Allows admins to give/take points from members.  
## Regular Members
-$beleive --> Param: (Amount). This bets on the "believe" side 
-$doubt --> Param: (Amount). This bets on the "doubt" side
-$points --> Displays your points (Automatically starts with 1000)

# Dependencies
-import time
- from discord.ext import commands
- from discord.ext.commands import has_permissions, MissingPermissions
- from threading import Timer
- from pymongo import MongoClient
- import math
- import random
- import os
