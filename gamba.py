import time
import discord
import os
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions
import Functions
from threading import Timer
import random
from pymongo import MongoClient
import math
import datetime
# global vars
intents = discord.Intents.all()
believePool, doubtPool, globalDict, guildMember = {}, {}, {}, {}
global posts, cluster
startComDescription = "If the title/blv/dbt is more than one word use \"\". t is the time and is in seconds i.e. t = 120 = 2 minutes (Only admins can use)"
giveComDescription = "Gives points to specific member, you have to type their discord NAME (Only admins can use)."
refundComDescription = "Refunds points and stops prediction (Only admins can use)."
wonComDescription = "Sets win after a prediction has started, side = \"blv\" or \"dbt\" (Only admins can use)."
TOKEN, GUILD, CHANNEL1, CHANNEL2, CHANNEL3 = os.getenv("Token"), os.getenv("Guild"), os.getenv("Channel1"), os.getenv("Channel2"), os.getenv("Channel3")
CLUSTER_LINK, CLUSTER_ELEMENT, DB_ELEMENT = os.getenv("ClusterLink"), os.getenv("PointsData"), os.getenv("UserPoints")
cluster = MongoClient(CLUSTER_LINK)

####################################
# Functions that can't be exported #
####################################
'''
lists all the guilds that the bot is in and then checks to see if the guild is a database
if it isn't it gets all members using get_members(new Guild, new collection for new Guild)
only reason why it isn't just one DB is because I was getting dup errors for it but I actually fixed that bug
'''


def addGuild():
    global posts
    guilds = bot.guilds
    dbList = cluster.list_database_names()
    for guild in guilds:
        thisGuild = Functions.removeSpace(guild.name)
        posts = []
        if thisGuild not in dbList:
            collectionName = f"{thisGuild} Points"
            var = cluster[thisGuild]
            var.create_collection(collectionName)
            this = var[collectionName]
            get_members(guild, this)
        else:
            pass


'''
Whenever a command that uses points is called it has to find the specific user's guild and returns the db and collection
I'm not sure if I need to return the database though.
'''


def findTheirGuild(guildName):
    newGuildNameStr = Functions.removeSpace(guildName)
    if newGuildNameStr in bot.dbList:
        db = cluster[newGuildNameStr]
        collection = db[f"{newGuildNameStr} Points"]
        return db, collection
    else:
        pass


# this just gets a list of all the guilds but actually makes it usable to find it in mongoDB
def listGuild():
    guilds = bot.guilds
    for guild in guilds:
        guildCutSpace = Functions.removeSpace(str(guild.name))
        bot.dbList.append(guildCutSpace)
    return bot.dbList


'''
this function is threaded and runs ever 30 minutes, you can change the interval to whatever you want
has to be in seconds though. I haven't fixed it yet to do it for all guids, it currently only does it for one guild
with the given channels. You could copy/paste per channel for each server but that's lame :/
'''


# FIXED, now checks thru every guild and vc and if someone is in there they get a random int between 90-125 you can change if you want
def voiceChannelCheck():
    vcList = []
    for guild in bot.guilds:
        notNeeded, collection = findTheirGuild(guild.name)
        for channel in guild.voice_channels:
            vcList.append(channel)
        for vc in vcList:
            if len(vc.members) > 0:
                for person in vc.members:
                    points = random.randint(90, 125)
                    userPoints = Functions.showPoints(collection.find({"name": person.name})) + points
                    collection.update_one({"name": person.name}, {"$set": {"points": userPoints}})
            else:
                pass




'''
These functions below are used only for refunding, 
just takes back the points from the dict and adds them back to DB
and then resetAllDicts() calls the latter function and clears all dicts afterwards
'''


def resetAllDicts():
    globalDict.clear()
    refund_dicts()
    believePool.clear()
    doubtPool.clear()


def refund_dicts():
    for k, v in believePool.items():
        userPoints = Functions.showPoints(bot.betCollection.find({"name": k}))
        bot.betCollection.update_one({"name": k}, {"$set": {"points": userPoints + v}})

    for k, v in doubtPool.items():
        userPoints = Functions.showPoints(bot.betCollection.find({"name": k}))
        bot.betCollection.update_one({"name": k}, {"$set": {"points": userPoints + v}})


''' 
Used for mongoDB which assigns their id name and gives them at least 1000 points, this can be changed
if you want to only assign them their name and increase the amount of points.
'''


def get_members(guild, guildCollection):
    for person in guild.members:
        posts.append({"_id": person.id, "name": person.name, "points": 1000})
    for person in posts:
        guildCollection.insert_one(person)


# basically whenever tries to place a bet it first checks if its past the timer or not, if not then their bets are placed
def timeCheck():
    now = datetime.datetime.now()
    print(bot.endTime)
    if now < bot.endTime:
        return True
    else:
        return bot.endTime

'''
After every win it calls the bot collection that was set during $start command and gives the user's percentage of the pool + their own amount that they put in.
Note: I believe that there is some point loss overall since their points are truncated, you don't have to use math.
If you want you can just give them any decimal/leftover points, 
but if you want displays to look nice you should format strings involving nums. Do whatever you want with that though I just think its easier this way.
and take into consideration the percentages too if you do.
'''


def giveAmountWon(loserPool, winnerPool):
    loserSum = sum(loserPool.values())
    winnerSum = sum(winnerPool.values())
    for k, v in winnerPool.items():
        userPoints = Functions.showPoints(bot.betCollection.find({"name": k}))
        x = v / winnerSum
        amount = x * loserSum + v
        amount = math.trunc(amount)
        bot.betCollection.update_one({"name": k}, {"$set": {"points": userPoints + amount}})
        winnerPool[k] = amount


class Bot(commands.Bot):
    def __init__(self):
        super(Bot, self).__init__(command_prefix=['$'], intents=intents, case_insensitive=True)
        self.endTime = None
        self.blvPercent, self.dbtPercent, self._last_member = None, None, None
        self.predictionDB, self.betCollection = None, None
        self.dbList = []
        self.add_cog(Predictions(self))
        self.add_cog(Points(self))

    async def on_ready(self):
        print(f'Bot has logged in as {bot.user}')
        addGuild()
        this = Timer(1800, voiceChannelCheck)
        this.start()
        bot.dbList = listGuild()

    @commands.Cog.listener()
    async def on_guild_join(self):
        addGuild()
        pass


# ALL THE COMMANDS THAT ARE USED FOR PREDICTIONS LIKE STARTING THE BET, BETTING, AND REFUNDING
class Predictions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message = None

    @commands.command(aliases=['set'], description=startComDescription)
    @has_permissions(manage_roles=True, ban_members=True)
    async def start(self, ctx, title, t: int, blv, dbt):
        bot.predictionDB, bot.betCollection = findTheirGuild(ctx.author.guild.name)
        globalDict['blv'], globalDict['dbt'] = blv, dbt
        globalDict['title'], globalDict['Total'], globalDict['Time'] = title, 0, t
        bot.endTime = datetime.datetime.now() + datetime.timedelta(seconds=t)
        minutes, secs = divmod(t, 60)
        timer = '{:02d}:{:02d}'.format(minutes, secs)
        text = Functions.startText(title, blv, dbt, timer)
        message = await ctx.send(text)

        while t >= 0:
            minutes, secs = divmod(t, 60)
            timer = '{:02d}:{:02d}'.format(minutes, secs)
            time.sleep(1)
            t -= 1
            await message.edit(content=Functions.startText(title, blv, dbt, timer))
        await ctx.send("Submissions have closed")

    @start.error
    async def start_error(self, ctx, error):
        if isinstance(error, MissingPermissions):
            text = f"Sorry {ctx.message.author.mention}, you do not have permissions to do that! <:davidCD:805202027848007770>"
            await ctx.send(ctx.message.channel, text)

    # bets on believe
    # another thing to note is that if you bet on dbt, you can't bet blv or if you have no points you aren't allowed to bet
    # it also adds to your previous amount if you have previously bet on this side
    @commands.command(aliases=['believe', 'blv'])
    async def betBelieve(self, ctx, amount: int):
        user, userMention, thisTime = ctx.message.author.name, ctx.message.author.mention, timeCheck()
        if isinstance(thisTime, bool):
            userDB = bot.betCollection.find({"name": user})
            userPoints = Functions.showPoints(userDB)
            userPoints -= amount
            if user in doubtPool:
                text = f"You've chosen your side already {userMention} <:PogO:738917913670582323>"
                await ctx.send(text)
                pass
            elif userPoints < 0:
                userPoints += amount
                fail_amount_text = f"{userMention} you don't have that many points... <:flor:689313613994786821> \n" \
                                   f"You have {userPoints} points "
                await ctx.send(fail_amount_text)
                pass
            elif user in believePool and userPoints > 0:
                believePool[user] += amount
                globalDict['Total'] += amount
                blvPercent, dbtPercent = Functions.percentage(believePool, doubtPool, globalDict)
                text = Functions.userInputPts(userMention, amount, blvPercent, dbtPercent, 'blv', globalDict,
                                              believePool, doubtPool)
                bot.betCollection.update_one({"name": user}, {"$set": {"points": userPoints}})
                await ctx.send(text)
                pass
            else:
                globalDict['Total'] += amount
                believePool[user] = amount
                blvPercent, dbtPercent = Functions.percentage(believePool, doubtPool, globalDict)
                text = Functions.userInputPts(userMention, amount, blvPercent, dbtPercent, 'blv', globalDict,
                                              believePool, doubtPool)
                bot.betCollection.update_one({"name": user}, {"$set": {"points": userPoints}})
                await ctx.send(text)
                pass
            pass
        else:
            text = f"{userMention} Submissions have closed! <:ohwow:602690781224108052>"
            await ctx.send(text)
            pass

    # bets on doubt side
    # another thing to note is that if you bet on blv you can't bet dbt or if you have no points you aren't allowed to bet
    # it also adds to your previous amount if you have previously bet on this side
    @commands.command(aliases=['doubt', 'dbt'])
    async def betDoubt(self, ctx, amount: int):
        user, userMention, thisTime = ctx.message.author.name, ctx.message.author.mention, timeCheck()
        print(thisTime)
        if isinstance(thisTime, bool):
            userDB = bot.betCollection.find({"name": user})
            userPoints = Functions.showPoints(userDB)
            userPoints -= amount
            if user in believePool:
                text = f"You've chosen your side already {userMention} <:PogO:738917913670582323>"
                await ctx.send(text)
                pass
            elif userPoints < 0:
                userPoints += amount
                fail_amount_text = f"{userMention} you don't have that many points... <:flor:689313613994786821> \n" \
                                   f"You have {userPoints} points "
                await ctx.send(fail_amount_text)
                pass
            elif user in doubtPool and userPoints > 0:
                doubtPool[user] += amount
                globalDict['Total'] += amount
                blvPercent, dbtPercent = Functions.percentage(believePool, doubtPool, globalDict)
                text = Functions.userInputPts(userMention, amount, blvPercent, dbtPercent, 'dbt', globalDict,
                                              believePool, doubtPool)
                bot.betCollection.update_one({"name": user}, {"$set": {"points": userPoints}})
                await ctx.send(text)
                pass
            else:
                globalDict['Total'] += amount
                doubtPool[user] = amount
                blvPercent, dbtPercent = Functions.percentage(believePool, doubtPool, globalDict)
                text = Functions.userInputPts(userMention, amount, blvPercent, dbtPercent, 'dbt', globalDict,
                                              believePool, doubtPool)
                bot.betCollection.update_one({"name": user}, {"$set": {"points": userPoints}})
                await ctx.send(text)
                pass
            pass
        else:
            text = f"{userMention} Submissions have closed! <:ohwow:602690781224108052>"
            await ctx.send(text)
            pass

    # set winner command
    @commands.command(name='won', description=wonComDescription)
    @has_permissions(manage_roles=True, ban_members=True)
    async def winner(self, ctx, side: str):
        pool, title, blv, dbt, blvSum, dbtSum = Functions.returnValues(globalDict, believePool, doubtPool)
        blvPercent, dbtPercent = Functions.percentage(believePool, doubtPool, globalDict)
        if side == "blv" or "believe":
            giveAmountWon(doubtPool, believePool)
            winnerBlvText = Functions.returnWinText(title, blv, blvPercent, dbtPercent, 'blv', believePool, doubtPool)
            bot.blvPercent, bot.dbtPercent = None, None
            Functions.resetAfterWin(globalDict, believePool, doubtPool)
            await ctx.send(winnerBlvText)
            pass
        elif side == "dbt" or "doubt":
            giveAmountWon(believePool, doubtPool)
            winnerDbtText = Functions.returnWinText(title, dbt, blvPercent, dbtPercent, 'dbt', believePool, doubtPool)
            bot.blvPercent, bot.dbtPercent = None, None
            Functions.resetAfterWin(globalDict, believePool, doubtPool)
            await ctx.send(winnerDbtText)
            pass

    @winner.error
    async def winner_error(self, ctx, error):
        if isinstance(error, MissingPermissions):
            text = f"Sorry {ctx.message.author.mention}, you do not have permissions to do that! <:davidCD:805202027848007770>"
            await ctx.send(text)
            pass

    @commands.command(aliases=['reset'], description=refundComDescription)
    @has_permissions(manage_roles=True, ban_members=True)
    async def refund(self, ctx):
        resetAllDicts()
        bot.blvPercent, bot.dbtPercent = None, None
        refund_text = "The prediction has ended early, refunding your points <:FeelsBadMan:692245421170622496>"
        await ctx.send(refund_text)

    @refund.error
    async def refund_error(self, ctx, error):
        if isinstance(error, MissingPermissions):
            text = f"Sorry {ctx.message.author.mention}, you do not have permissions to do that! <:davidCD:805202027848007770>"
            await ctx.send(ctx.message.channel, text)


# this cog basically displays points, takes and gives
class Points(commands.Cog):
    def __init__(self, bot):
        self.message = None
        self.bot = bot
        self.userCollection = None
        self.userDB = None

    @commands.command(name='give', description=giveComDescription)
    @has_permissions(manage_roles=True, ban_members=True)
    async def givePts(self, ctx, give_Member: str, amount: int):
        bot.userDB, bot.userCollection = findTheirGuild(ctx.author.guild.name)
        thisMember = bot.userCollection.find({"name": give_Member})
        userPoints = Functions.showPoints(thisMember) + amount
        bot.userCollection.update_one({"name": give_Member}, {"$set": {"points": userPoints}})
        text = f"{give_Member} you have {userPoints} points <:money:689308022660399117> <:Pog:602691798498017302>"
        await ctx.send(text)

    @givePts.error
    async def give_error(self, ctx, error):
        if isinstance(error, MissingPermissions):
            text = f"Sorry {ctx.message.author.mention}, you do not have permissions to do that! <:davidCD:805202027848007770>"
            await ctx.send(text)
            pass

    # I haven't actually considered if they take more than what they have so be aware of that not that important to me at the moment
    @commands.command(name='take', description="Takes points from specific member, you have to type their discord NAME (Only admins can use).")
    @has_permissions(manage_roles=True, ban_members=True)
    async def takePts(self, ctx, take_Member: str, amount: int):
        bot.userDB, bot.userCollection = findTheirGuild(ctx.author.guild.name)
        thisMember = bot.userCollection.find({"name": take_Member})
        userPoints = Functions.showPoints(thisMember) - amount
        bot.userCollection.update_one({"name": take_Member}, {"$set": {"points": userPoints}})
        text = f"{take_Member} you have {userPoints} points <:money:689308022660399117> <:FeelsBadMan:692245421170622496>"
        await ctx.send(text)

    @takePts.error
    async def give_error(self, ctx, error):
        if isinstance(error, MissingPermissions):
            text = f"Sorry {ctx.message.author.mention}, you do not have permissions to do that! <:davidCD:805202027848007770>"
            await ctx.send(text)
            pass

    @commands.command(aliases=['points', 'pts'], description="Shows your points")
    async def askPts(self, ctx):
        user, userMention = ctx.message.author.name, ctx.message.author.mention
        bot.userDB, bot.userCollection = findTheirGuild(ctx.author.guild.name)
        thisMember = bot.userCollection.find({"name": user})
        userPoints = Functions.showPoints(thisMember)
        text = f"{userMention} you have {userPoints} points <:money:689308022660399117>"
        await ctx.send(text)


bot = Bot()
bot.run(TOKEN)

#############################
# UNUSED FUNCTIONS/COMMANDS #
#############################

""" @commands.Cog.listener()
    @commands.has_any_role(['Lettuce', 'Top Dogs'])
    @commands.cooldown(1, 120, commands.BucketType.user)
    async def on_message(self, message):
        user = message.author.name
        if user in memberDict.keys():
            memberDict[user] += random.randint(25, 50)
        print(memberDict)
"""
