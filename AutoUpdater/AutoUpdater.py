# coding: utf-8

import os
import sys
import requests
import json
import subprocess
import datetime
from itertools import groupby

def Fetch(itemType):
    r= requests.get(classes[itemType]["url"])
    return r.json()

def ParseUniques(items):
    relevantUniques = [unique for unique in items['lines'] if unique["count"] > 10 and unique['links'] < 5 and unique['itemClass'] == 3]
    relevantUniques.sort(key=lambda unique: unique['baseType'])

    groupedUniques = []
    baseTypes = []

    for baseType, uniques in groupby(relevantUniques, lambda unique: unique['baseType']):
        groupedUniques.append(list(uniques))
        baseTypes.append(baseType)

    for group in groupedUniques:
        tiers = [FindTier(item['chaosValue']) for item in group]
        PutInTier(group[0]['baseType'], ChooseTier(tiers), tierlists)

def ParseDivCards(items):
    relevantDivCards = [divCard for divCard in items['lines'] if divCard["count"] > 10]
    for item in relevantDivCards:
        PutInTier(item['name'], FindTier(item['chaosValue']), tierlists)

def Replace(itemType):
    i = 0
    data = []
    while i < len(tierlists):
        if tierlists[i]:
            data.append(classes[itemType]["tag"] + tier[i])
            data.append('    BaseType ' + ' '.join('"{0}"'.format(tier.encode('utf-8')) for tier in tierlists[i]))
        i += 1

    data = '\n'.join(data)
    data += '\n'

    with open('insertBases.tmp', "w") as tempFile:
        tempFile.write(data)

    #sed script
    subprocess.check_call(['./sedbashReplaceBases.sh', classes[itemType]["startTag"], classes[itemType]["endTag"]])
    ClearTiers()

def UpdateVersion():
    currentDatetime = datetime.datetime.now().strftime('%Y.%m.%d_%H:%M')
    subprocess.check_call(['./sedbashUpdateVersion.sh', currentDatetime, "Crymsius-filter-filterblast.filter"])
    subprocess.check_call(['./sedbashUpdateVersion.sh', currentDatetime, "filterblast.config"])

def CleanFolders():
    os.remove('Crymsius-filter-filterblast.filter-e')
    os.remove('filterblast.config-e')
    os.remove('insertBases.tmp')

def CommitPush():
    currentDatetime = datetime.datetime.now().strftime('%Y.%m.%d_%H:%M')
    subprocess.check_call(['git', 'commit', '-a', '-m', 'AutoUpdater '+currentDatetime])
    subprocess.check_call(['git', 'push'])

def ClearTiers():
    for tiers in tierlists:
        del tiers[:]

def FindTier(chaosValue):
    tiers = [T0, T1, T2, T3]
    tier = 0
    while tier < len(tiers) and chaosValue <= tiers[tier]:
        tier += 1
    return tier

def ChooseTier(tiers):
    tiersSet = set(tiers)
    if len(tiersSet) == 1:
        return tiersSet.pop()
    else:
        if 0 in tiersSet or 1 in tiersSet:
            return 5
        elif 2 in tiersSet:
            return 2
        elif 3 in tiersSet:
            return 3


def PutInTier(baseType, tier, tierlists):
    tierlists[tier].append(baseType)


if __name__ == '__main__':
    T0 = 30
    T1 = 10
    T2 = 1
    T3 = 0.4

    tier = ["T0", "T1", "T2", "T3", "T4", "TMix"]

    classes = {
        "flasks": {
            "url": "https://poe.ninja/api/data/ItemOverview?league=Delve&type=UniqueFlask"
        },
        "weapons": {
            "url": "https://poe.ninja/api/data/ItemOverview?league=Delve&type=UniqueWeapon"
        },
        "armours": {
            "url": "https://poe.ninja/api/data/ItemOverview?league=Delve&type=UniqueArmour"
        },
        "accessories": {
            "url": "https://poe.ninja/api/data/ItemOverview?league=Delve&type=UniqueAccessory"
        },
        "maps": {
            "url": "https://poe.ninja/api/data/ItemOverview?league=Delve&type=UniqueMap"
        },
        "allUniques": {
            "tag": "SetTag @Uniques_AutoUpdater_",
            "startTag": "#AutoUpdater_AllUniques_start",
            "endTag": "#AutoUpdater_AllUniques_end",
        },
        "divCards": {
            "url": "https://poe.ninja/api/data/ItemOverview?league=Delve&type=DivinationCard",
            "tag": "SetTag @DivinationCards_",
            "startTag": "#AutoUpdater_DivCards_start",
            "endTag": "#AutoUpdater_DivCards_end",
        }
    }

    tierlists = [[], [], [], [], [], []] #T0,1,2,3,4,mix

    flasks = Fetch("flasks")
    weapons = Fetch("weapons")
    armours = Fetch("armours")
    accessories = Fetch("accessories")
    maps = Fetch("maps")
    divCards = Fetch("divCards")

    ParseUniques(flasks)
    ParseUniques(weapons)
    ParseUniques(armours)
    ParseUniques(accessories)
    ParseUniques(maps)
    Replace("allUniques")

    ParseDivCards(divCards)
    Replace("divCards")

    UpdateVersion()

    CleanFolders()
    CommitPush()

    sys.exit()