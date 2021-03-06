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
    try:
        r= requests.get(classes["poeninja"]["url"] + classes[itemType]["overview"] + "?"+ "league=" + classes["poeninja"]["league"] + "&type=" + classes[itemType]["type"])
        r.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        print ("Http Error:",errh)
        return False, {}
    except requests.exceptions.ConnectionError as errc:
        print ("Error Connecting:",errc)
        return False, {}
    except requests.exceptions.Timeout as errt:
        print ("Timeout Error:",errt)
        return False, {}
    except requests.exceptions.RequestException as err:
        print ("OOps: Something Else",err)
        return False, {}
    else:
        return True, r.json()

def defineTiers(currencies):
    '''
        Use an array of currency and modify the limits between tiers 0 and 1 and between 1 and 2
        limit0-1 = 0.5*value0 + value1 / 1.5
        limit1-2 = value1 + value2 / 2
    '''
    if requestStatus:
        exaltValue = 90
        divineValue = 10

        exaltValueArray = [currency['chaosEquivalent'] for  currency in currencies['lines'] if currency['currencyTypeName'] == "Exalted Orb"]
        if exaltValueArray :
            exaltValue = exaltValueArray[0]

        divineValueArray = [currency['chaosEquivalent'] for  currency in currencies['lines'] if currency['currencyTypeName'] == "Divine Orb"]
        if divineValueArray :
            divineValue = divineValueArray[0]

        tiers[0] = min((0.5*exaltValue + divineValue) / 1.5, 60) # Exalt tier is no more than 60c
        tiers[1] = max(tiers[1],(divineValue + 1) * 0.5)

        print(tiers)


def ParseUniques(items):
    '''
        Function that will parse unique items for the given category, keeping only relevent items.
        Relevant items are items with high confidence

        It will then find tier for each unique and put them in their matching tier.
    '''

    if requestStatus:
        relevantUniques = [unique for unique in items['lines'] if unique["count"] > 10 and unique['links'] < 5 and unique['itemClass'] == 3]
        # hot fix for synthesised unique items not having the correct base type
        for unique in relevantUniques:
            if 'Synthesised' in unique['baseType']:
                unique['baseType'] = unique['baseType'][12:]
        # end hotfix
        relevantUniques.sort(key=lambda unique: unique['baseType'])

        groupedUniques = []
        baseTypes = []

        for baseType, uniques in groupby(relevantUniques, lambda unique: unique['baseType']):
            groupedUniques.append(list(uniques))
            baseTypes.append(preventWrongBaseType(baseType))

        for group in groupedUniques:
            tiers = [FindTier(item['chaosValue']) for item in group]
            PutInTier(preventWrongBaseType(group[0]['baseType']), ChooseTier(tiers), tierlists)

def preventWrongBaseType(baseType):
    '''
        Function to prevent poe.ninja wrong basetypes.
    '''
    if baseType == "Torture Chamber Map":
        baseType = "Underground Sea Map"
    return baseType

def ParseDivCards(items):
    if requestStatus :
        relevantDivCards = [divCard for divCard in items['lines'] if divCard["count"] > 10]
        for item in relevantDivCards:
            PutInTier(item['name'], FindTier(item['chaosValue']), tierlists)

def ParseFossils(items):
    if requestStatus :
        relevantFossils = [fossil for fossil in items['lines'] if fossil["count"] > 3]
        for item in relevantFossils:
            PutInTier(item['name'], FindTier(item['chaosValue']), tierlists)

def ParseEssences(items):
    if requestStatus :
        relevantEssences = [essence for essence in items['lines'] if essence["count"] > 3]
        for item in relevantEssences:
            PutInTier(item['name'], FindTier(item['chaosValue']), tierlists)

def ParseIncubators(items):
    if requestStatus :
        relevantIncubators = [incubator for incubator in items['lines'] if incubator["count"] > 3]
        for item in relevantIncubators:
            PutInTier(item['name'], FindTier(item['chaosValue']), tierlists)

def ParseOils(items):
    if requestStatus :
        relevantOils = [oil for oil in items['lines'] if oil["count"] > 3]
        for item in relevantOils:
            PutInTier(item['name'], FindTier(item['chaosValue']), tierlists)

def ParseProphecies(items):
    if requestStatus :
        relevantProphecies = [prophecy for prophecy in items['lines'] if prophecy["count"] > 3]
        for item in relevantProphecies:
            if item['name'] != "A Gracious Master":
                PutInTier(item['name'], FindTier(item['chaosValue']), tierlists)

def ParseBaseTypes(items):
    if requestStatus :
        relevantItems = [baseItem for baseItem in items['lines'] if baseItem["count"] > 10 and baseItem["chaosValue"] > tiers[1]]
        for item in relevantItems:
            baseType = {
                "baseType": item['name'],
                "ilvl": item['levelRequired'],
                "variant": item['variant']
            }
            PutInTier(baseType, FindTier(item['chaosValue']), tierlists)

def Replace(itemType):
    if requestStatus:
        i = 0
        with open('insertBases.tmp', "w") as tempFileTags:
            with open('insertSections.tmp', "w") as tempFileSections:
                while i < len(tierlists):
                    if tierlists[i]:
                        #first : updating tags
                        tempFileTags.write(classes[itemType]["tag"] + tier[i] + '\n')

                        tempFileTags.write('    BaseType == ' + ' '.join('"{0}"'.format(tier) for tier in tierlists[i]) + '\n')

                        #second : updating filter section relative to the tier
                        tempFileSections.write(classes[itemType]["section"][i] + '\n')
                    i += 1

        #sed script
        subprocess.check_call(['./sedbashReplaceBases.sh', classes[itemType]["startTag"], classes[itemType]["endTag"]])
        subprocess.check_call(['./sedbashReplaceSections.sh', classes[itemType]["startSection"], classes[itemType]["endSection"]])
        ClearTiers()

def ReplaceProphecy(itemType):
    if requestStatus:
        i = 0
        with open('insertBases.tmp', "w") as tempFileTags:
            with open('insertSections.tmp', "w") as tempFileSections:
                while i < len(tierlists):
                    if tierlists[i]:
                        #first : updating tags
                        tempFileTags.write(classes[itemType]["tag"] + tier[i] + '\n')

                        tempFileTags.write('    Prophecy ' + ' '.join('"{0}"'.format(tier) for tier in tierlists[i]) + '\n')

                        #second : updating filter section relative to the tier
                        tempFileSections.write(classes[itemType]["section"][i] + '\n')
                    i += 1

        #sed script
        subprocess.check_call(['./sedbashReplaceBases.sh', classes[itemType]["startTag"], classes[itemType]["endTag"]])
        subprocess.check_call(['./sedbashReplaceSections.sh', classes[itemType]["startSection"], classes[itemType]["endSection"]])
        ClearTiers()

def ReplaceBaseType(baseType):
    i = 0
    with open('insertSections.tmp', "w") as tempFileSections:
        while i < len(tierlists):
            if tierlists[i]:
                #Variant separation
                itemsShaper = [item for item in tierlists[i] if item["variant"] == "Shaper"]
                itemsElder = [item for item in tierlists[i] if item["variant"] == "Elder"]
                itemsCrusader = [item for item in tierlists[i] if item["variant"] == "Crusader"]
                itemsRedeemer = [item for item in tierlists[i] if item["variant"] == "Redeemer"]
                itemsHunter = [item for item in tierlists[i] if item["variant"] == "Hunter"]
                itemsWarlord = [item for item in tierlists[i] if item["variant"] == "Warlord"]
                itemsOther = [item for item in tierlists[i] if not item["variant"]]

                itemsShaperIlvl = {}
                itemsElderIlvl = {}
                itemsCrusaderIlvl = {}
                itemsRedeemerIlvl = {}
                itemsHunterIlvl = {}
                itemsWarlordIlvl = {}
                itemsOtherIlvl = {}

                for item in itemsShaper:
                    if item["ilvl"] in itemsShaperIlvl:
                        itemsShaperIlvl[item["ilvl"]].append(item["baseType"])
                    else:
                        itemsShaperIlvl[item["ilvl"]] = [item["baseType"]]
                for item in itemsElder:
                    if item["ilvl"] in itemsElderIlvl:
                        itemsElderIlvl[item["ilvl"]].append(item["baseType"])
                    else:
                        itemsElderIlvl[item["ilvl"]] = [item["baseType"]]
                for item in itemsCrusader:
                    if item["ilvl"] in itemsCrusaderIlvl:
                        itemsCrusaderIlvl[item["ilvl"]].append(item["baseType"])
                    else:
                        itemsCrusaderIlvl[item["ilvl"]] = [item["baseType"]]
                for item in itemsRedeemer:
                    if item["ilvl"] in itemsRedeemerIlvl:
                        itemsRedeemerIlvl[item["ilvl"]].append(item["baseType"])
                    else:
                        itemsRedeemerIlvl[item["ilvl"]] = [item["baseType"]]
                for item in itemsHunter:
                    if item["ilvl"] in itemsHunterIlvl:
                        itemsHunterIlvl[item["ilvl"]].append(item["baseType"])
                    else:
                        itemsHunterIlvl[item["ilvl"]] = [item["baseType"]]
                for item in itemsWarlord:
                    if item["ilvl"] in itemsWarlordIlvl:
                        itemsWarlordIlvl[item["ilvl"]].append(item["baseType"])
                    else:
                        itemsWarlordIlvl[item["ilvl"]] = [item["baseType"]]
                for item in itemsOther:
                    if item["ilvl"] in itemsOtherIlvl:
                        itemsOtherIlvl[item["ilvl"]].append(item["baseType"])
                    else:
                        itemsOtherIlvl[item["ilvl"]] = [item["baseType"]]

                #Shaper
                if itemsShaper :
                    tempFileSections.write(classes[baseType]["section"][i] + '\n')
                    tempFileSections.write('    HasInfluence Shaper\n')
                    for ilvl in itemsShaperIlvl:
                        tempFileSections.write('    Branch\n')
                        tempFileSections.write('        ItemLevel >= ' + str(ilvl) + '\n')
                        tempFileSections.write('        BaseType ' + ' '.join('"{0}"'.format(item) for item in itemsShaperIlvl[ilvl]) + '\n')

                #Elder
                if itemsElder :
                    tempFileSections.write(classes[baseType]["section"][i] + '\n')
                    tempFileSections.write('    HasInfluence Elder\n')
                    for ilvl in itemsElderIlvl:
                        tempFileSections.write('    Branch\n')
                        tempFileSections.write('        ItemLevel >= ' + str(ilvl) + '\n')
                        tempFileSections.write('        BaseType ' + ' '.join('"{0}"'.format(item) for item in itemsElderIlvl[ilvl]) + '\n')

                #Crusader
                if itemsCrusader :
                    tempFileSections.write(classes[baseType]["section"][i] + '\n')
                    tempFileSections.write('    HasInfluence Crusader\n')
                    for ilvl in itemsCrusaderIlvl:
                        tempFileSections.write('    Branch\n')
                        tempFileSections.write('        ItemLevel >= ' + str(ilvl) + '\n')
                        tempFileSections.write('        BaseType ' + ' '.join('"{0}"'.format(item) for item in itemsCrusaderIlvl[ilvl]) + '\n')

                #Redeemer
                if itemsRedeemer :
                    tempFileSections.write(classes[baseType]["section"][i] + '\n')
                    tempFileSections.write('    HasInfluence Redeemer\n')
                    for ilvl in itemsRedeemerIlvl:
                        tempFileSections.write('    Branch\n')
                        tempFileSections.write('        ItemLevel >= ' + str(ilvl) + '\n')
                        tempFileSections.write('        BaseType ' + ' '.join('"{0}"'.format(item) for item in itemsRedeemerIlvl[ilvl]) + '\n')

                #Hunter
                if itemsHunter :
                    tempFileSections.write(classes[baseType]["section"][i] + '\n')
                    tempFileSections.write('    HasInfluence Hunter\n')
                    for ilvl in itemsHunterIlvl:
                        tempFileSections.write('    Branch\n')
                        tempFileSections.write('        ItemLevel >= ' + str(ilvl) + '\n')
                        tempFileSections.write('        BaseType ' + ' '.join('"{0}"'.format(item) for item in itemsHunterIlvl[ilvl]) + '\n')

                #Warlord
                if itemsWarlord :
                    tempFileSections.write(classes[baseType]["section"][i] + '\n')
                    tempFileSections.write('    HasInfluence Warlord\n')
                    for ilvl in itemsWarlordIlvl:
                        tempFileSections.write('    Branch\n')
                        tempFileSections.write('        ItemLevel >= ' + str(ilvl) + '\n')
                        tempFileSections.write('        BaseType ' + ' '.join('"{0}"'.format(item) for item in itemsWarlordIlvl[ilvl]) + '\n')

                #Other
                if itemsOther :
                    tempFileSections.write(classes[baseType]["section"][i] + '\n')
                    tempFileSections.write('    HasInfluence None\n')
                    for ilvl in itemsOtherIlvl:
                        tempFileSections.write('    Branch\n')
                        tempFileSections.write('        ItemLevel >= ' + str(ilvl) + '\n')
                        tempFileSections.write('        BaseType ' + ' '.join('"{0}"'.format(item) for item in itemsOtherIlvl[ilvl]) + '\n')

            i += 1

    #sed script
    subprocess.check_call(['./sedbashReplaceSections.sh', classes[baseType]["startSection"], classes[baseType]["endSection"]])
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
    if os.path.exists('insertSections.tmp'):
        os.remove('insertSections.tmp')

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
    tiers = [55, 9.9, 0.9, 0.4] #borders between T0 and T1, T1 and T2, and T2 and T3
    tier = ["T0", "T1", "T2", "T3", "T4", "TMix"]

    classes = {
        "poeninja" : {
            "league": "Harvest",
            "url": "https://poe.ninja/api/data/"
        },
        "currency": {
            "overview": "CurrencyOverview",
            "type": "Currency"
        },
        "flasks": {
            "overview": "itemoverview",
            "type": "UniqueFlask"
        },
        "weapons": {
            "overview": "itemoverview",
            "type": "UniqueWeapon"
        },
        "armours": {
            "overview": "itemoverview",
            "type": "UniqueArmour"
        },
        "accessories": {
            "overview": "itemoverview",
            "type": "UniqueAccessory"
        },
        "maps": {
            "overview": "itemoverview",
            "type": "UniqueMap"
        },
        "jewels": {
            "overview": "itemoverview",
            "type": "UniqueJewel"
        },
        "allUniques": {
            "tag": "SetTag @Uniques_AutoUpdater_",
            "startTag": "#AutoUpdater_AllUniques_start",
            "endTag": "#AutoUpdater_AllUniques_end",
            "startSection": "#AutoUpdater_AllUniques_section_start",
            "endSection": "#AutoUpdater_AllUniques_section_end",
            "section": [
'''    Branch #Uniques - T0
        Tags @Uniques_AutoUpdater_T0
        SetFontSize 45
        SetBackgroundColor 255 255 255
        SetBorderColor 175 96 37
        Tags $soundT0
        MinimapIcon 0 Blue Star
        PlayEffect Blue''',
'''    Branch #Uniques - T1
        Tags @Uniques_AutoUpdater_T1
        SetFontSize 45
        SetBackgroundColor 70 20 0
        SetTextColor 255 255 255
        SetBorderColor 175 96 37
        Tags $soundT1
        MinimapIcon 0 Brown Star
        PlayEffect Brown''',
'''    Branch #Uniques - T2
        Tags @Uniques_AutoUpdater_T2
        SetFontSize 45
        SetBackgroundColor 70 20 0
        SetBorderColor 255 255 255
        Tags $soundT2
        MinimapIcon 1 Yellow Star
        PlayEffect Yellow Temp''',
'''    Branch #Uniques - T3
        Tags @Uniques_AutoUpdater_T3
        SetFontSize 40
        SetBackgroundColor 70 20 0
        SetBorderColor 175 96 37
        Tags $soundT3
        MinimapIcon 2 White Star
        PlayEffect White Temp''',
'''    Branch #Uniques - T4
        Tags @Uniques_AutoUpdater_T4
        SetFontSize 30
        SetBackgroundColor 70 20 0 200''',
'''    Branch #Uniques - TMix (same BaseType used for T0 or T1 and Tless)
        Tags @Uniques_AutoUpdater_TMix
        SetFontSize 50
        SetBackgroundColor 175 96 37
        SetTextColor 70 20 0
        SetBorderColor 255 255 255
        MinimapIcon 0 Red Star
        PlayEffect Red
        Tags $soundTMix'''
            ]
        },
        "divCards": {
            "overview": "itemoverview",
            "type": "DivinationCard",
            "tag": "SetTag @DivinationCards_",
            "startTag": "#AutoUpdater_DivCards_start",
            "endTag": "#AutoUpdater_DivCards_end",
            "startSection" : "#AutoUpdater_DivCards_section_start",
            "endSection" : "#AutoUpdater_DivCards_section_end",
            "section": [
'''    Branch Inherit # Divination Cards - T0
        Tags @DivinationCards_T0
        SetFontSize 45
        SetBackgroundColor 255 255 255
        SetTextColor 255 165 0
        SetBorderColor 255 165 0
        Tags $soundT0
        MinimapIcon 0 Blue Square
        PlayEffect Blue''',
'''    Branch Inherit # Divination Cards - T1
        Tags @DivinationCards_T1
        SetFontSize 44
        SetBackgroundColor 255 165 0 245
        SetTextColor 255 255 255
        SetBorderColor 255 255 255
        Tags $soundT1
        MinimapIcon 0 Brown Square
        PlayEffect Brown''',
'''    Branch Inherit # Divination Cards - T2
        Tags @DivinationCards_T2
        SetFontSize 40
        SetBackgroundColor 255 165 0 235
        SetTextColor 0 0 0
        SetBorderColor 255 255 255
        Tags $soundT2
        MinimapIcon 1 Yellow Square
        PlayEffect Yellow Temp''',
'''    Branch Show # Divination Cards - T3
        Tags @DivinationCards_T3
        SetFontSize 38
        SetBackgroundColor 255 165 0 210
        SetTextColor 0 0 0
        SetBorderColor 255 165 0
        MinimapIcon 2 White Square
        PlayEffect White Temp''',
'''    Branch Hide # Divination Cards - T4
        Tags @DivinationCards_T4
        SetFontSize 32
        SetBackgroundColor 255 165 0 180
        SetTextColor 0 0 0
        SetBorderColor 0 0 0'''
            ]
        },
        "fossils": {
            "overview": "itemoverview",
            "type": "Fossil",
            "tag": "SetTag @Fossils_",
            "startTag": "#AutoUpdater_Fossils_start",
            "endTag": "#AutoUpdater_Fossils_end",
            "startSection": "#AutoUpdater_Fossils_section_start",
            "endSection": "#AutoUpdater_Fossils_section_end",
            "section": [
'''    Branch # Leagues - Delve - Fossils - T0
        Tags @Fossils_T0
        SetFontSize 45
        SetBackgroundColor 255 255 255
        SetTextColor 255 178 57
        SetBorderColor 255 178 57
        Tags $soundT0
        MinimapIcon 0 Blue Hexagon
        PlayEffect Blue''',
'''    Branch # Leagues - Delve - Fossils - T1
        Tags @Fossils_T1
        SetFontSize 44
        SetBackgroundColor 255 178 57
        SetTextColor 255 255 255
        SetBorderColor 255 255 255
        Tags $soundT1
        MinimapIcon 0 Brown Hexagon
        PlayEffect Brown''',
'''    Branch # Leagues - Delve - Fossils - T2
        Tags @Fossils_T2
        SetFontSize 40
        SetBackgroundColor 255 178 57
        SetTextColor 175 57 18
        SetBorderColor 255 255 255
        Tags $soundT2
        MinimapIcon 1 Yellow Hexagon
        PlayEffect Yellow Temp''',
'''    Branch # Leagues - Delve - Fossils - T3
        Tags @Fossils_T3
        SetFontSize 38
        SetBackgroundColor 255 178 57 210
        SetTextColor 175 57 18
        SetBorderColor 175 57 18
        Tags $soundT3
        MinimapIcon 2 White Hexagon
        PlayEffect White Temp''',
'''    Branch # Leagues - Delve - Fossils - T4
        Tags @Fossils_T4
        SetFontSize 32
        SetBackgroundColor 255 178 57 180
        SetTextColor 175 57 18
        SetBorderColor 0 0 0'''
            ]
        },
        "baseTypes": {
            "overview": "itemoverview",
            "type": "BaseType",
            "startSection" : "#AutoUpdater_BaseTypes_section_start",
            "endSection" : "#AutoUpdater_BaseTypes_section_end",
            "section": [
'''Show #Atlas and special bases - Autotiered T0
    Rarity <= Rare
    SetFontSize 45
    SetBackgroundColor 255 255 255
    SetTextColor 0 180 0
    SetBorderColor 0 180 0
    Tags $soundT0
    MinimapIcon 0 Blue Triangle
    PlayEffect Blue''',
'''Show #Atlas and special bases - Autotiered T1
    Rarity <= Rare
    SetFontSize 42
    SetBackgroundColor 0 180 0
    SetTextColor 255 255 255
    SetBorderColor 255 255 255
    Tags $soundT1
    MinimapIcon 0 Brown Triangle
    PlayEffect Brown''',
'''Show # Atlas and special bases - T2
    Rarity <= Rare
    SetFontSize 37
    SetBackgroundColor 0 180 0
    SetTextColor 0 0 0
    SetBorderColor 0 0 0
    Tags $soundT2
    MinimapIcon 1 Yellow Triangle
    PlayEffect Yellow Temp'''
            ]
        },
         "prophecies": {
            "overview": "itemoverview",
            "type": "Prophecy",
            "tag": "SetTag @Prophecies_",
            "startTag": "#AutoUpdater_Prophecies_names_start",
            "endTag": "#AutoUpdater_Prophecies_names_end",
            "startSection" : "#AutoUpdater_Prophecies_section_start",
            "endSection" : "#AutoUpdater_Prophecies_section_end",
            "section": [
'''    Branch # Leagues - Prophecy - Prophecies - T0
        Tags @Prophecies_T0
        SetFontSize 45
        SetBackgroundColor 255 255 255
        SetTextColor 128 0 200
        SetBorderColor 128 0 200
        Tags $soundT0
        MinimapIcon 0 Blue Moon
        PlayEffect Blue''',
'''    Branch # Leagues - Prophecy - Prophecies - T1
        Tags @Prophecies_T1
        SetBackgroundColor 128 0 200
        SetTextColor 255 255 255
        SetBorderColor 255 255 255
        SetFontSize 43
        Tags $soundT1
        MinimapIcon 0 Brown Moon
        PlayEffect Brown''',
'''    Branch # Leagues - Prophecy - Prophecies - T2
        Tags @Prophecies_T2
        SetBackgroundColor 128 0 200 230
        SetFontSize 40
        Tags $soundT2
        MinimapIcon 1 Yellow Moon
        PlayEffect Yellow Temp''',
'''    Branch # Leagues - Prophecy - Prophecies - T3
        Tags @Prophecies_T3
        SetBackgroundColor 128 0 200 200
        SetFontSize 36
        Tags $soundT3
        MinimapIcon 2 White Moon
        PlayEffect White Temp''',
'''    Branch # Leagues - Prophecy - Prophecies - T4
        Tags @Prophecies_T4
        SetFontSize 33
        SetBackgroundColor 128 0 200 170'''
            ]
        },
        "essences": {
            "overview": "itemoverview",
            "type": "Essence",
            "tag": "SetTag @Essences_",
            "startTag": "#AutoUpdater_Essences_start",
            "endTag": "#AutoUpdater_Essences_end",
            "startSection" : "#AutoUpdater_Essences_section_start",
            "endSection" : "#AutoUpdater_Essences_section_end",
            "section" : [
'''    Branch # Leagues - Essence - Essences - T0
        Tags @Essences_T0
        SetFontSize 50
        SetBackgroundColor 255 255 255
        Tags $soundT0
        PlayEffect Blue
        MinimapIcon 0 Blue Kite''',
'''    Branch # Leagues - Essence - Essences - T1
        Tags @Essences_T1
        SetFontSize 50
        SetBackgroundColor 10 25 90
        SetTextColor 255 255 255
        SetBorderColor 255 255 255
        Tags $soundT1
        PlayEffect Brown
        MinimapIcon 0 Brown Kite''',
'''    Branch # Leagues - Essence - Essences - T2
        Tags @Essences_T2
        SetFontSize 40
        SetBackgroundColor 180 195 245
        SetTextColor 10 25 90
        SetBorderColor 10 25 90
        Tags $soundT2
        PlayEffect Yellow Temp
        MinimapIcon 1 Yellow Kite''',
'''    Branch # Leagues - Essence - Essences - T3
        Tags @Essences_T3
        SetFontSize 36
        Tags $soundT3
        SetBackgroundColor 180 195 245 200
        MinimapIcon 2 White Kite''',
'''    Branch # Leagues - Essence - Essences - T4
        Tags @Essences_T4
        SetFontSize 33
        SetBackgroundColor 180 195 245 170'''
            ]
        },
        "incubators": {
            "overview": "itemoverview",
            "type": "Incubator",
            "tag": "SetTag @Incubators_",
            "startTag": "#AutoUpdater_Incubators_start",
            "endTag": "#AutoUpdater_Incubators_end",
            "startSection" : "#AutoUpdater_Incubators_section_start",
            "endSection" : "#AutoUpdater_Incubators_section_end",
            "section" : [
'''    Branch # Leagues - Legion - Incubators - T0
        Tags @Incubators_T0
        SetFontSize 50
        SetBackgroundColor 255 255 255
        SetTextColor 244 74 204 255
        SetBorderColor 244 74 204 255
        Tags $soundT0
        MinimapIcon 0 Blue Cross''',
'''    Branch # Leagues - Legion - Incubators - T1
        Tags @Incubators_T1
        SetFontSize 45
        SetBackgroundColor 244 74 204 255
        SetBorderColor 62 18 52 255
        SetTextColor 62 18 52 255
        Tags $soundT1
        MinimapIcon 0 Brown Cross''',
'''    Branch # Leagues - Legion - Incubators - T2
        Tags @Incubators_T2
        SetFontSize 42
        SetBackgroundColor 62 18 52 255
        SetTextColor 244 74 204 255
        SetBorderColor 244 74 204 255
        Tags $soundT2
        MinimapIcon 1 Yellow Cross''',
'''    Branch # Leagues - Legion - Incubators - T3
        Tags @Incubators_T3
        SetFontSize 38
        SetBackgroundColor 62 18 52 200
        SetTextColor 244 74 204 255
        SetBorderColor 244 74 204 255
        Tags $soundT3
        MinimapIcon 2 White Cross''',
'''    Branch # Leagues - Legion - Incubators - T4
        Tags @Incubators_T4
        SetFontSize 35
        SetBackgroundColor 62 18 52 180
        SetTextColor 244 74 204 255
        SetBorderColor 244 74 204 255'''
            ]
        },
        "oils": {
            "overview": "itemoverview",
            "type": "Oil",
            "tag": "SetTag @Oils_",
            "startTag": "#AutoUpdater_Oils_start",
            "endTag": "#AutoUpdater_Oils_end",
            "startSection" : "#AutoUpdater_Oils_section_start",
            "endSection" : "#AutoUpdater_Oils_section_end",
            "section" : [
'''    Branch # Leagues - Blight - Oils - T0
        Tags @Oils_T0
        SetBackgroundColor 255 255 255
        SetTextColor 8 82 70 255
        SetBorderColor 8 82 70 255
        SetFontSize 50
        Tags $soundT0
        MinimapIcon 0 Blue Cross
        PlayEffect Blue''',
'''    Branch # Leagues - Blight - Oils - T1
        Tags @Oils_T1
        SetBackgroundColor 241 232 200 255
        SetTextColor 8 82 70 255
        SetBorderColor 8 82 70 255
        SetFontSize 48
        Tags $soundT1
        MinimapIcon 0 Brown Cross
        PlayEffect Brown''',
'''    Branch # Leagues - Blight - Oils - T2
        Tags @Oils_T2
        SetBackgroundColor 8 82 70 255
        SetTextColor 241 232 200 255
        SetBorderColor 241 232 200 255
        SetFontSize 42
        Tags $soundT2
        MinimapIcon 1 Yellow Cross
        PlayEffect Yellow''',
'''    Branch # Leagues - Blight - Oils - T3
        Tags @Oils_T3
        SetBackgroundColor 8 82 70 230
        SetTextColor 241 232 200 255
        SetBorderColor 241 232 200 255
        SetFontSize 38
        Tags $soundT3
        MinimapIcon 2 White Cross
        PlayEffect White''',
'''    Branch # Leagues - Blight - Oils - T4
        Tags @Oils_T4
        SetBackgroundColor 8 82 70 200
        SetTextColor 241 232 200 255
        SetBorderColor 241 232 200 255
        SetFontSize 38'''
            ]
        }
    }

    requestStatus, currency = Fetch("currency")
    defineTiers(currency)


    tierlists = [[], [], [], [], [], []] #T0,1,2,3,4,mix

    requestStatus, flasks = Fetch("flasks")
    ParseUniques(flasks)
    requestStatus, weapons = Fetch("weapons")
    ParseUniques(weapons)
    requestStatus, armours = Fetch("armours")
    ParseUniques(armours)
    requestStatus, accessories = Fetch("accessories")
    ParseUniques(accessories)
    requestStatus, jewels = Fetch("jewels")
    ParseUniques(jewels)
    requestStatus, maps = Fetch("maps")
    ParseUniques(maps)
    Replace("allUniques")

    requestStatus, divCards = Fetch("divCards")
    ParseDivCards(divCards)
    Replace("divCards")

    requestStatus, fossils = Fetch("fossils")
    ParseFossils(fossils)
    Replace("fossils")

    requestStatus, essences = Fetch("essences")
    ParseEssences(essences)
    Replace("essences")

    requestStatus, incubators = Fetch("incubators")
    ParseIncubators(incubators)
    Replace("incubators")

    requestStatus, oils = Fetch("oils")
    ParseOils(oils)
    Replace("oils")

    requestStatus, prophecies = Fetch("prophecies")
    ParseProphecies(prophecies)
    ReplaceProphecy("prophecies")

    requestStatus, baseTypes = Fetch("baseTypes")
    ParseBaseTypes(baseTypes)
    ReplaceBaseType("baseTypes")

    UpdateVersion()

    CleanFolders()
    CommitPush()

    sys.exit()