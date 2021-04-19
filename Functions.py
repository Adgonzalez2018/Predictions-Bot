import math
import datetime


def userInputPts(user, amount, blvPercent, dbtPercent, side, globalDict, believePool, doubtPool):
    text = f"{user} has entered the pool with **{amount} points! on \"{globalDict[side]}\"** <:Pog:602691798498017302> \n" \
           f"```autohotkey\n" \
           f"Total Pool: {globalDict['Total']} points\n" \
           f"Blv Percent/People/Amount: {blvPercent}%, {len(believePool)}, {sum(believePool.values())}\n" \
           f"Dbt Percent/People/Amount: {dbtPercent}%, {len(doubtPool)}, {sum(doubtPool.values())} ```"
    return text


def startText(title, blv, dbt, timer):
    text = f"> Prediction Started: **{title}?** Time Left: **{timer}**\n" \
           f"```bash\n" \
           f"Type $believe (amount) to bet on \"{blv}\"\n" \
           f"Type $doubt (amount) to bet on \"{dbt}\"\n" \
           f"Type $points to check how many points you have```"
    return text


def returnValues(globalDict, believePool, doubtPool):
    pool, title = globalDict['Total'], globalDict['title']
    blv, dbt = globalDict['blv'], globalDict['dbt']
    blvSum, dbtSum = sum(believePool.values()), sum(doubtPool.values())
    return pool, title, blv, dbt, blvSum, dbtSum


def percentage(believePool, doubtPool, globalDict):
    blv = sum(believePool.values())
    dbt = sum(doubtPool.values())
    poolSize = globalDict['Total']
    blv = (blv / poolSize) * 100
    dbt = (dbt / poolSize) * 100
    dbtPercent = math.trunc(dbt)
    blvPercent = math.trunc(blv)
    return blvPercent, dbtPercent


def resetAfterWin(globalDict, believePool, doubtPool):
    globalDict.clear()
    believePool.clear()
    doubtPool.clear()


def returnWinText(title, Result, blvPercent, dbtPercent, side, believePool, doubtPool):
    global winner, maxVal, biggestWinner
    if side == 'blv':
        maxVal = max(believePool.values())
        biggestWinner = max(believePool, key=believePool.get)
        winner = "Believers"
    elif side == 'dbt':
        maxVal = max(doubtPool.values())
        biggestWinner = max(doubtPool, key=doubtPool.get)
        winner = "Doubters"

    winnerText = f"```autohotkey\n" \
                 f"Prediction Results: {winner} Won!\n" \
                 f"Title: \"{title}?\"\n" \
                 f"Result: \"{Result}\"\n" \
                 f"Biggest Pay out: {biggestWinner} with +{maxVal} points\n" \
                 f"Blv Percent/People/Amount: {blvPercent}%, {len(believePool)}, {sum(believePool.values())} points\n" \
                 f"Dbt Percent/People/Amount: {dbtPercent}%, {len(doubtPool)}, {sum(doubtPool.values())} points ```"
    return winnerText


def giveEndTime(globalDict):
    addTime = globalDict['Time']
    now = datetime.datetime.now()
    endTime = now + datetime.timedelta(seconds=addTime)
    return endTime


def timeCheck(globalDict):
    now = datetime.datetime.now()
    endTime = giveEndTime(globalDict)
    if now < endTime:
        return True
    else:
        return endTime


def endText(globalDict, believePool, doubtPool):
    blvPercent, dbtPercent = percentage(globalDict, believePool, doubtPool)
    text = f"> Submissions Closed!: **{globalDict['title']}?**" \
           f"```autohotkey\n" \
           f"Total Pool: {globalDict['Total']} points\n" \
           f"Blv Percent/People/Amount: {blvPercent}%, {len(believePool)}, {sum(believePool.values())}\n" \
           f"Dbt Percent/People/Amount: {dbtPercent}%, {len(doubtPool)}, {sum(doubtPool.values())} ```"
    return text


def showPoints(post):
    for i in post:
        return i["points"]

'''
    async def closeSubmissions(self):
        now = datetime.datetime.now()
        endTime = now + datetime.timedelta(seconds=globalDict['Time'])
        while datetime.datetime.now() < endTime:
            pass
        blvPercent, dbtPercent = Functions.percentage(believePool, doubtPool, globalDict)
        endText = Functions.endText(globalDict, believePool, doubtPool, blvPercent, dbtPercent)
        await bot.process_commands()'''

"""if after is None:
    members = voiceChannel1.members
    print(members)
    print(after)
else:
    pass"""
