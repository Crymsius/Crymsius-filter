# coding: utf-8

import os
import sys
import requests
import json
import subprocess
import datetime
from itertools import groupby

def Fetch(itemType):
    '''
        Used to make requests and fetch json data
    '''
    r= requests.get(classes[itemType]["url"])
    return r.json()

def defineTiers(currencies):
    '''
        Use an array of currency and modify the limits between tiers 0 and 1 and between 1 and 2
        limit0-1 = 0.5*value0 + value1 / 1.5
        limit1-2 = value1 + value2 / 2
    '''
    exaltValue = 90
    divineValue = 10

    exaltValueArray = [currency['chaosEquivalent'] for  currency in currencies['lines'] if currency['currencyTypeName'] == "Exalted Orb"]
    if exaltValueArray :
        exaltValue = exaltValueArray[0]

    divineValueArray = [currency['chaosEquivalent'] for  currency in currencies['lines'] if currency['currencyTypeName'] == "Divine Orb"]
    if divineValueArray :
        divineValue = divineValueArray[0]

    tiers[0] = (0.5*exaltValue + divineValue) / 1.5
    tiers[1] = (divineValue + 1) * 0.5


def ParseUniques(items):
    '''
        Function that will parse unique items for the given category, keeping only relevent items.
        Relevant items are items with high confidence

        It will then find tier for each unique and put them in their matching tier.
    '''
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
    if os.path.exists('Crymsius-filter-filterblast.filter-e'):
        os.remove('Crymsius-filter-filterblast.filter-e')
    if os.path.exists('filterblast.config-e'):
        os.remove('filterblast.config-e')
    if os.path.exists('insertBases.tmp'):
        os.remove('insertBases.tmp')

def CommitPush():
    currentDatetime = datetime.datetime.now().strftime('%Y.%m.%d_%H:%M')
    subprocess.check_call(['git', 'commit', '-a', '-m', 'AutoUpdater '+currentDatetime])
    subprocess.check_call(['git', 'push'])

def ClearTiers():
    for tiers in tierlists:
        del tiers[:]

def FindTier(chaosValue):
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
    tiers = [30, 10, 0.9, 0.4] #borders between T0 and T1, T1 and T2, and T2 and T3
    tier = ["T0", "T1", "T2", "T3", "T4", "TMix"]

    classes = {
        "currency": {
            "url": "https://poe.ninja/api/data/CurrencyOverview?league=Delve&type=Currency"
        },
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

    currency = Fetch("currency")
    defineTiers(currency)


    tierlists = [[], [], [], [], [], []] #T0,1,2,3,4,mix

    print tiers[0]
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