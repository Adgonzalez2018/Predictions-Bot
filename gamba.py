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


# Functions that can't be exported
def AddGuild():
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


def findTheirGuild(guildName):
    newGuildNameStr = Functions.removeSpace(guildName)
    if newGuildNameStr in bot.dbList:
        db = cluster[newGuildNameStr]
        collection = db[f"{newGuildNameStr} Points"]
        return db, collection
    else:
        pass


def listGuild():
    guilds = bot.guilds
    for guild in guilds:
        guildCutSpace = Functions.removeSpace(str(guild.name))
        bot.dbList.append(guildCutSpace)
    return bot.dbList

# STILL NEED TO FIX THIS FUNCTION
def addPts():
    vc1, vc2 = bot.get_channel(id=CHANNEL1), bot.get_channel(id=CHANNEL2)
    if len(vc1.members) > 0:
        for person in vc1.members:
            points = random.randint(90, 125)
            userPoints = Functions.showPoints(bot.Collection.find({"name": person.name}))
            bot.Collection.update_one({"name": person.name}, {"$set": {"points": userPoints + points}})
    else:
        pass
    if len(vc2.members) > 0:
        for person in vc2.members:
            points = random.randint(90, 125)
            userPoints = Functions.showPoints(bot.Collection.find({"name": person.name}))
            bot.Collection.update_one({"name": person.name}, {"$set": {"points": userPoints + points}})
    else:
        pass


def resetAllDicts():
    globalDict.clear()
    refund_dicts()
    believePool.clear()
    doubtPool.clear()


def refund_dicts():
    for k, v in believePool.items():
        userPoints = Functions.showPoints(bot.Collection.find({"name": k}))
        bot.Collection.update_one({"name": k}, {"$set": {"points": userPoints + v}})

    for k, v in doubtPool.items():
        userPoints = Functions.showPoints(bot.Collection.find({"name": k}))
        bot.Collection.update_one({"name": k}, {"$set": {"points": userPoints + v}})


def get_members(guild, guildCollection):
    for person in guild.members:
        posts.append({"_id": person.id, "name": person.name, "points": 1000})
    for person in posts:
        guildCollection.insert_one(person)


def giveAmountWon(loserPool, winnerPool):
    loserSum = sum(loserPool.values())
    winnerSum = sum(winnerPool.values())
    for k, v in winnerPool.items():
        userPoints = Functions.showPoints(bot.Collection.find({"name": k}))
        x = v / winnerSum
        amount = x * loserSum + v
        amount = math.trunc(amount)
        bot.Collection.update_one({"name": k}, {"$set": {"points": userPoints + amount}})
        winnerPool[k] = amount


class Bot(commands.Bot):
    def __init__(self):
        super(Bot, self).__init__(command_prefix=['$'], intents=intents, case_insensitive=True)
        self.blvPercent, self.dbtPercent, self._last_member = None, None, None
        self.predictionDB, self.Collection = None, None
        self.dbList = []
        self.add_cog(Predictions(self))
        self.add_cog(Points(self))

    async def on_ready(self):
        print(f'Bot has logged in as {bot.user}')
        AddGuild()
        this = Timer(1800, addPts)
        this.start()
        bot.dbList = listGuild()


class Predictions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message = None

    @commands.command(aliases=['set'], description=startComDescription)
    @has_permissions(manage_roles=True, ban_members=True)
    async def start(self, ctx, title, t: int, blv, dbt):
        bot.predictionDB, bot.Collection = findTheirGuild(ctx.author.guild.name)
        globalDict['blv'], globalDict['dbt'] = blv, dbt
        globalDict['title'], globalDict['Total'], globalDict['Time'] = title, 0, t
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

    @commands.command(aliases=['believe', 'blv'])
    async def betBelieve(self, ctx, amount: int):
        user, userMention = ctx.message.author.name, ctx.message.author.mention
        userDB = bot.Collection.find({"name": user})
        userPoints = Functions.showPoints(userDB)
        if isinstance(Functions.timeCheck(globalDict), bool):
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
                bot.Collection.update_one({"name": user}, {"$set": {"points": userPoints}})
                await ctx.send(text)
                pass
            else:
                globalDict['Total'] += amount
                believePool[user] = amount
                blvPercent, dbtPercent = Functions.percentage(believePool, doubtPool, globalDict)
                text = Functions.userInputPts(userMention, amount, blvPercent, dbtPercent, 'blv', globalDict,
                                              believePool, doubtPool)
                bot.Collection.update_one({"name": user}, {"$set": {"points": userPoints}})
                await ctx.send(text)
                pass
            pass
        else:
            text = f"{userMention} Submissions have closed! <:ohwow:602690781224108052>"
            await ctx.send(text)
            pass

    @commands.command(aliases=['doubt', 'dbt'])
    async def betDoubt(self, ctx, amount: int):
        user, userMention = ctx.message.author.name, ctx.message.author.mention
        userDB = bot.Collection.find({"name": user})
        userPoints = Functions.showPoints(userDB)
        if isinstance(Functions.timeCheck(globalDict), bool):
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
                bot.Collection.update_one({"name": user}, {"$set": {"points": userPoints}})
                await ctx.send(text)
                pass
            else:
                globalDict['Total'] += amount
                doubtPool[user] = amount
                blvPercent, dbtPercent = Functions.percentage(believePool, doubtPool, globalDict)
                text = Functions.userInputPts(userMention, amount, blvPercent, dbtPercent, 'dbt', globalDict,
                                              believePool, doubtPool)
                bot.Collection.update_one({"name": user}, {"$set": {"points": userPoints}})
                await ctx.send(text)
                pass
            pass
        else:
            text = f"{userMention} Submissions have closed! <:ohwow:602690781224108052>"
            await ctx.send(text)
            pass

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
        bot.Collection.update_one({"name": give_Member}, {"$set": {"points": userPoints}})
        text = f"{give_Member} you have {userPoints} points <:money:689308022660399117> <:Pog:602691798498017302>"
        bot.userCollection, bot.userDB = None, None
        await ctx.send(text)

    @givePts.error
    async def give_error(self, ctx, error):
        if isinstance(error, MissingPermissions):
            text = f"Sorry {ctx.message.author.mention}, you do not have permissions to do that! <:davidCD:805202027848007770>"
            await ctx.send(text)
            pass

    @commands.command(name='take',
                      description="Takes points from specific member, you have to type their discord NAME (Only admins can use).")
    @has_permissions(manage_roles=True, ban_members=True)
    async def takePts(self, ctx, take_Member: str, amount: int):
        bot.userDB, bot.userCollection = findTheirGuild(ctx.author.guild.name)
        thisMember = bot.userCollection.find({"name": take_Member})
        userPoints = Functions.showPoints(thisMember) - amount
        bot.userCollection.update_one({"name": take_Member}, {"$set": {"points": userPoints}})
        text = f"{take_Member} you have {userPoints} points <:money:689308022660399117> <:FeelsBadMan:692245421170622496>"
        bot.userCollection, bot.userDB = None, None
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
        bot.userDb, bot.userCollection = None, None
        await ctx.send(text)


bot = Bot()
bot.run(TOKEN)


""" if guild.name in collectionList:
            db.create_collection(f"{guild.name}")
            thisGuild = db[guild.name]
            print(thisGuild)
            for person in guild.members:
                posts.append({"_id": person.id, "name": person.name, "points": 1000})
            for person in posts:
                thisGuild.insert_one(person)
            print(db.collection_names())
        else:
            print(guild.name)
            print(db.list_collection_names())
            pass
    print(db.list_collection_names())
"""

""" @commands.Cog.listener()
    @commands.has_any_role(['Lettuce', 'Top Dogs'])
    @commands.cooldown(1, 120, commands.BucketType.user)
    async def on_message(self, message):
        user = message.author.name
        if user in memberDict.keys():
            memberDict[user] += random.randint(25, 50)
        print(memberDict)
"""