#! /usr/bin/env python
# -*- coding: utf8 -*-
#
# Copyright (C) 2014  Evol Online
# Author: Andrei Karas (4144)

import array
import base64
import gzip
import os
import re
import datetime
import xml
import csv
import ogg.vorbis
import StringIO
import sys
import zlib
import struct
import shutil
from sets import Set
from xml.dom import minidom

def detectCommand():
    if sys.argv[0][-12:] == "/listmaps.py":
        return "listmaps"
    elif sys.argv[0][-15:] == "/extractmaps.py":
        return "extractmaps"
    elif sys.argv[0][-13:] == "/mapstotmx.py":
        return "mapstotmx"
    elif sys.argv[0][-15:] == "/queststoxml.py":
        return "queststoxml"
    elif sys.argv[0][-14:] == "/itemstoxml.py":
        return "itemstoxml"
    elif sys.argv[0][-17:] == "/monsterstoxml.py":
        return "monsterstoxml"
    elif sys.argv[0][-20:] == "/mercenariestoxml.py":
        return "mercenariestoxml"
    elif sys.argv[0][-13:] == "/petstoxml.py":
        return "petstoxml"
    elif sys.argv[0][-21:] == "/homunculusestoxml.py":
        return "homunculusestoxml"
    elif sys.argv[0][-15:] == "/skillstoxml.py":
        return "skillstoxml"
    elif sys.argv[0][-14:] == "/tmxtocache.py":
        return "tmxtocache"
    return "help"

def makeDir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def readInt32(f):
    data = f.read(4)
    arr = array.array("I")
    arr.fromstring(data)
    return arr[0]

def readInt16(f):
    data = f.read(2)
    arr = array.array("H")
    arr.fromstring(data)
    return arr[0]

def readMapName(f):
    data = f.read(12)
    data = str(data)
    while data[-1] == '\x00':
        data = data[:-1]
    return data

def readData(f, sz):
    return f.read(sz)

def readFile(path):
    with open(path, "r") as f:
        return f.read()

def writeInt32(f, i):
    f.write(struct.pack("I", i))

def writeInt16(f, i):
    f.write(struct.pack("H", i))

def writeMapName(f, name):
    if len(name) > 12:
        name = name[:12]
    while len(name) < 12:
        name = name + '\x00'
    f.write(struct.pack("12s", name))

def writeData(f, data):
    f.write(data)

def getTileData(mapData, x, y, sx):
    data = mapData[y * sx + x]
    arr = array.array("B")
    arr.fromstring(data)
    data = arr[0]
    return data

def getTile(data):
    normal = 0
    collison = 0
    if data == 0:    # 000 normal walkable
        normal = 1
        collision = 5
    elif data == 1:  # 001 non walkable
        normal = 2
        collision = 6
    elif data == 2:  # 010 same with 0
        normal = 1
        collision = 5
    elif data == 3:  # 011 same with 0, but water
        normal = 3
        collision = 5
    elif data == 4:  # 100 same with 0
        normal = 1
        collision = 5
    elif data == 5:  # 101 same with 1, but shootable (for now not supported!!!)
        normal = 4
        collision = 6
    elif data == 6:  # 110 same with 0
        normal = 1
        collision = 5
    return (str(normal), str(collision))

def getGroundTile(flag):
    return str(flag + 1)

def getCollisionTile(flag):
    if flag == 0:
        return "0"
    return "4"

def copyFile(src, dst, name):
    shutil.copyfile(src + name, dst + name)

def saveFile(fileName, data):
    with open(fileName, "w") as w:
        w.write(data)

def stripQuotes(data):
    if len(data) == 0:
        return data
    if data[-1] == "\"":
        data = data[:-1]
    if data[0] == "\"":
        data = data[1:]
    if data[-1] == "'":
        data = data[:-1]
    if data[0] == "'":
        data = data[1:]
    return data

def stripQuotes2(data):
    for idx in xrange(0, len(data)):
        data[idx] = stripQuotes(data[idx])
    return data

def strToXml(data):
    data = data.replace("&", "&amp;");
    data = data.replace("<", "&lt;");
    data = data.replace(">", "&gt;");
    return data

def printHelp():
    print "Unknown options selected."
    print ""
    print "Use list.py for list maps in cache"
    print "Use extract.py to extract maps from cache"
    exit(0)

def listMapCache(f, mapsCount):
    print "Known maps:"
    print "{0:12} {1:<4}x {2:<4} {3:<10}".format("Map name", "sx", "sy", "compressed size")
    for i in xrange(0, mapsCount):
        name = readMapName(f)
        sx = readInt16(f)
        sy = readInt16(f)
        sz = readInt32(f)
        print "{0:12} {1:<4}x {2:<4} {3:<10}".format(name, sx, sy, sz)
        f.seek(sz, 1)

def extractMaps(f, mapsCount):
    destDir = "maps/"
    makeDir(destDir)
    for i in xrange(0, mapsCount):
        name = readMapName(f)
        sx = readInt16(f)
        sy = readInt16(f)
        sz = readInt32(f)
        data = readData(f, sz)
        dc = zlib.decompressobj()
        data = dc.decompress(data)
        with open(destDir + name, "wb") as w:
            w.write(struct.pack("H", sx))
            w.write(struct.pack("H", sy))
            w.write(data)

def covertToTmx(f, mapsCount):
    destDir = "clientdata/"
    mapsDir = destDir + "maps/"
    tilesetsDir = destDir + "graphics/tilesets/"
    templatesDir = "templates/"
    makeDir(mapsDir)
    makeDir(tilesetsDir)
    copyFile(templatesDir, tilesetsDir, "collision.png")
    copyFile(templatesDir, tilesetsDir, "tileset.png")
    tmx = readFile("templates/template.tmx")
    for i in xrange(0, mapsCount):
        name = readMapName(f)
        print "converting map [{0:4}/{1:4}]: {2}".format(i, mapsCount + 1, name)
        sx = readInt16(f)
        sy = readInt16(f)
        sz = readInt32(f)
        mapData = readData(f, sz)
        dc = zlib.decompressobj()
        mapData = dc.decompress(mapData)
        ground = ""
        collision = ""
        fringe = ""
        for y in xrange(0, sy):
            for x in xrange(0, sx):
                tileData = getTileData(mapData, x, y, sx)
                tile = getTile(tileData)
                if x + 1 == sx and y + 1 == sy:
                    ground = ground + tile[0]
                    collision = collision + tile[1]
                    fringe = fringe + "0";
                else:
                    ground = ground + tile[0] + ","
                    collision = collision + tile[1] + ","
                    fringe = fringe + "0,";
            ground = ground + "\n"
            collision = collision + "\n"
            fringe = fringe + "\n"
        saveFile(mapsDir + name + ".tmx", tmx.format(sx, sy, ground, collision, fringe))

def covertQuests():
    destDir = "clientdata/"
    templatesDir = "templates/"
    questsDbFile = "serverdata/db/quest_db.txt"
    fieldsSplit = re.compile(",")
    makeDir(destDir)
    tpl = readFile(templatesDir + "quest.tpl")
    quests = readFile(templatesDir + "quests.xml")
    data = ""
    with open(questsDbFile, "r") as f:
        for line in f:
            if line == "" or line[0:2] == "//":
                continue
            rows = fieldsSplit.split(line)
            if len(rows) < 9:
                continue
            questId = rows[0]
            text = rows[8]
            if text[-1] == "\n":
                text = text[:-1]
            text = strToXml(stripQuotes(text))
            name = text
            if len(name) > 20:
                name = name[:19]

            data = data + tpl.format(questId, name, text + ": " + str(questId))
    saveFile(destDir + "quests.xml", quests.format(data))

def prepStat(val, text):
    if val != "0" and val != "":
        return "        {0}=\"{1}\"\n".format(text, val)
    return ""

def convertItems():
    destDir = "clientdata/"
    templatesDir = "templates/"
    itemsDbFile = "serverdata/sql-files/item_db_re.sql"
    fieldsSplit = re.compile(",")
    bracketsSplit = re.compile("[(]|[)]")
    makeDir(destDir)
    tpl = readFile(templatesDir + "item.tpl")
    items = readFile(templatesDir + "items.xml")
    data = ""
    ids = Set()
    with open(itemsDbFile, "r") as f:
        for line in f:
            if len(line) < 10 or line[0:2] == "//" or line[0:12] != "REPLACE INTO":
                continue
            rows = bracketsSplit.split(line)
            if len(rows) < 2:
                continue
            rows = fieldsSplit.split(rows[1])
            if len(rows) < 31:
                continue
            rows = stripQuotes2(rows)
            itemId = rows[0]
            name = rows[1]
            name2 = rows[2]
            itemType = rows[3]
            priceBuy = rows[4]
            priceSell = rows[5]
            weight = rows[6]
            atk = rows[7]
            matk = rows[8]
            defence = rows[9]
            attackRange = rows[10]
            slots = rows[11]
            equipJobs = rows[12]
            equipUpper = rows[12]
            equipGender = rows[14]
            equipLocations = rows[15]
            weaponLevel = rows[16]
            equipLevelMin = rows[17]
            equipLevelMax = rows[18]
            refinable = rows[19]
            view = rows[20]
            bindOnEquip = rows[21]
            buyInStore = rows[22]
            delay = rows[23]
            tradeFlag = rows[24]
            tradeGroup = rows[25]
            nouseFlag = rows[26]
            nouseGroup = rows[27]
            stackAmount = rows[28]
            stackFlag = rows[29]
            sprite = rows[30]

            name = name.replace("\\'", "'")
            image = ""

            statStr = prepStat(atk, "attack")
            statStr = statStr + prepStat(matk, "mattack")
            statStr = statStr + prepStat(defence, "defence")
            statStr = statStr + prepStat(weight, "weight")
            statStr = statStr + prepStat(attackRange, "range")
            statStr = statStr + prepStat(delay, "speed")
#            print itemId + "," + equipLocations
#            typeStr = "other"
            typeStr = "equip-legs"
            spriteStr = "equipment/legs/trousers-male.xml"
            image = "generic/box-fish.png"
            if itemType == 0 or itemType == 2 or itemType == 18: # usable
                image = "usable/bread.png"
                typeStr = "usable"
                spriteStr = "";
            elif equipLocations == "0":
                image = "usable/bread.png"
                typeStr = "usable"
                spriteStr = "";
            elif equipLocations == "1":
                image = "equipment/legs/shorts.png|S:#4d4d4d,514d47,686868,706662,919191,99917b,b6b6b6,c0b698,dfdfdf,e4dfca"
                typeStr = "equip-legs"
                spriteStr = "equipment/legs/shorts-male.xml|#4d4d4d,514d47,686868,706662,919191,99917b,b6b6b6,c0b698,dfdfdf,e0d5bf";
            elif equipLocations == "2":
                image = "equipment/weapons/knife.png"
                typeStr = "equip-1hand"
                spriteStr = "equipment/weapons/knife.xml";
            elif equipLocations == "4":
                image = "equipment/hands/armbands.png"
                typeStr = "equip-arms"
                spriteStr = "equipment/hands/armbands-male.xml";
            elif equipLocations == "16":
                image = "equipment/chest/cottonshirt.png|S:#3c3c3c,3e3c38,4d4d4d,514d47,686868,706662,919191,99917b,b6b6b6,c0b698,dfdfdf,e4dfca"
                typeStr = "equip-torso"
                spriteStr = "equipment/chest/cottonshirt-male.xml|#43413d,59544f,7a706c,8a8176,a69e88,d1c7a7,e0d5bf";
            elif equipLocations == "64":
                image = "equipment/feet/boots.png|S:#3c3c3c,40332d,4d4d4d,5e4a3d,686868,705740,919191,a1825d,b6b6b6,b59767,dfdfdf,dbbf88"
                typeStr = "equip-feet"
                spriteStr = "equipment/feet/boots-male.xml|#40332d,5e4a3d,705740,a1825d,b59767,dbbf88";
            elif equipLocations == "136":
                image = "equipment/chest/cottonshirt.png|S:#3c3c3c,3e3c38,4d4d4d,514d47,686868,706662,919191,99917b,b6b6b6,c0b698,dfdfdf,e4dfca"
                typeStr = "equip-torso"
                spriteStr = "equipment/chest/cottonshirt-male.xml|#43413d,59544f,7a706c,8a8176,a69e88,d1c7a7,e0d5bf";
            elif equipLocations == "256":
                image = "equipment/head/bandana.png"
                typeStr = "equip-head"
                spriteStr = "equipment/head/bandana-male.xml";
            elif equipLocations == "512":
                # no sprites in evol
                image = "equipment/chest/sailorshirt.png"
                typeStr = "equip-torso"
                spriteStr = "equipment/chest/shirt-male.xml|#131913,1b231d,233129,35433e,4e6059,6c8279;#72571e,836737,a5854d,b18f45";

            name = strToXml(name);

            if itemId not in ids:
                ids.add(itemId)
                data = data + tpl.format(itemId, name, 0,
                    statStr, image, typeStr, spriteStr)
            if view != "0" and view not in ids:
                ids.add(view)
                data = data + tpl.format(view, name, 0,
                    statStr, image, typeStr, spriteStr)

    saveFile(destDir + "items.xml", items.format(data))

def convertMonsters():
    destDir = "clientdata/"
    templatesDir = "templates/"
    monstersDbFile = "serverdata/sql-files/mob_db_re.sql"
    fieldsSplit = re.compile(",")
    bracketsSplit = re.compile("[(]|[)]")
    makeDir(destDir)
    tpl = readFile(templatesDir + "monster.tpl")
    monsters = readFile(templatesDir + "monsters.xml")
    data = ""
    ids = Set()
    monsterSprite = """<sprite>monsters/blub.xml</sprite>
        <sprite>accessories/blub-tentacle.xml|#3e4164,3a3968,544a82,64437a,7d6db4,a26392,8f99c4,d294ab,b3cdcd,e7b8b8,d9ecd1,f0e8c5</sprite>""";
    with open(monstersDbFile, "r") as f:
        for line in f:
            if len(line) < 10 or line[0:2] == "//" or line[0:12] != "REPLACE INTO":
                continue
            rows = bracketsSplit.split(line)
            if len(rows) < 2:
                continue
            rows = fieldsSplit.split(rows[1])
            if len(rows) < 5:
                continue
            monsterId = rows[0]
            name = strToXml(stripQuotes(rows[2]))
            data = data + tpl.format(monsterId, name, monsterSprite)

    saveFile(destDir + "monsters.xml", monsters.format(data))

def convertMercenaries():
    destDir = "clientdata/"
    templatesDir = "templates/"
    mercenariesDbFile = "serverdata/db/mercenary_db.txt"
    fieldsSplit = re.compile(",")
    makeDir(destDir)
    tpl = readFile(templatesDir + "mercenary.tpl")
    mercenaries = readFile(templatesDir + "mercenaries.xml")
    data = ""
    mercenarySprite = "<sprite>monsters/croc.xml</sprite>";
    with open(mercenariesDbFile, "r") as f:
        for line in f:
            if line == "" or line[0:2] == "//":
                continue
            rows = fieldsSplit.split(line)
            if len(rows) < 9:
                continue
            mercenaryId = rows[0]
            data = data + tpl.format(mercenaryId, mercenarySprite)
    saveFile(destDir + "mercenaries.xml", mercenaries.format(data))

def convertPets():
    destDir = "clientdata/"
    templatesDir = "templates/"
    petsDbFile = "serverdata/db/pet_db.txt"
    fieldsSplit = re.compile(",")
    makeDir(destDir)
    tpl = readFile(templatesDir + "pet.tpl")
    pets = readFile(templatesDir + "pets.xml")
    data = ""
    petSprite = "<sprite>monsters/tortuga.xml</sprite>";
    with open(petsDbFile, "r") as f:
        for line in f:
            if line == "" or line[0:2] == "//":
                continue
            rows = fieldsSplit.split(line)
            if len(rows) < 9:
                continue
            petId = rows[0]
            data = data + tpl.format(petId, petSprite)
    saveFile(destDir + "pets.xml", pets.format(data))

def convertHomunculuses():
    destDir = "clientdata/"
    templatesDir = "templates/"
    homunculusesDbFile = "serverdata/db/re/homunculus_db.txt"
    fieldsSplit = re.compile(",")
    makeDir(destDir)
    tpl = readFile(templatesDir + "homunculus.tpl")
    homunculuses = readFile(templatesDir + "homunculuses.xml")
    data = ""
    homunculusSprite = "<sprite>monsters/tortuga.xml</sprite>";
    with open(homunculusesDbFile, "r") as f:
        for line in f:
            if line == "" or line[0:2] == "//":
                continue
            rows = fieldsSplit.split(line)
            if len(rows) < 9:
                continue
            homunculusId = rows[0]
            data = data + tpl.format(homunculusId, homunculusSprite)
    saveFile(destDir + "homunculuses.xml", homunculuses.format(data))

def convertSkillsToXml():
    destDir = "clientdata/"
    templatesDir = "templates/"
    skillsDbFile = "serverdata/db/re/skill_db.txt"
    fieldsSplit = re.compile(",")
    makeDir(destDir)
    tpl = readFile(templatesDir + "skill.tpl")
    skills = readFile(templatesDir + "skills.xml")
    data = ""
    with open(skillsDbFile, "r") as f:
        for line in f:
            if line == "" or line[0:2] == "//":
                continue
            rows = fieldsSplit.split(line)
            if len(rows) < 9:
                continue
            skillId = rows[0]
            name = rows[15].strip()
            description = rows[16].strip()
            idx = description.find ("//")
            if idx > 1:
                description = description[:idx]
            data = data + tpl.format(skillId, name, description)
    saveFile(destDir + "skills.xml", skills.format(data))

def getTmxFiles(srcDir):
    for name in os.listdir(srcDir):
        fileName = srcDir + name
        if os.path.isfile(fileName) == False:
            continue
        if name.endswith(".tmx") == False:
            continue
        yield fileName

def recreateMapCache():
    destDir = "mapcache/"
    srcDir = "clientdata/maps/"
    makeDir(destDir)
    sz = 0L
    mapsCount = 0
    with open(destDir + "map_cache.dat", "wb") as w:
        writeInt32(w, 0)  # file size
        writeInt16(w, 0)  # maps count
        writeInt16(w, 0)  # padding
        sz = sz + 8
        for fileName in getTmxFiles(srcDir):
            dom = minidom.parse(fileName)
            root = dom.documentElement
            firstgid = 0
            for tileset in root.getElementsByTagName("tileset"):
                try:
                    name = tileset.attributes["name"].value
                except:
                    name = ""
                if name == "Collision":
                    firstgid = int(tileset.attributes["firstgid"].value)
                    break

            for layer in root.getElementsByTagName("layer"):
                if layer.attributes["name"].value == "Collision":
                    data = layer.getElementsByTagName("data")
                    if data is None or len(data) != 1:
                        continue
                    data = data[0]
                    width = int(layer.attributes["width"].value)
                    height = int(layer.attributes["height"].value)
                    encoding = data.attributes["encoding"].value
                    compression = data.attributes["compression"].value
                    if encoding == "base64":
                        binData = data.childNodes[0].data.strip()
                        binData = binData.decode('base64')
                        if compression == "gzip":
                            dc = zlib.decompressobj(16 + zlib.MAX_WBITS)
                        else:
                            dc = zlib.decompressobj()
                        layerData = dc.decompress(binData)
                        arr = array.array("I")
                        arr.fromstring(layerData)
                    else:
                        print "map format not supported: " + fileName
                        continue
                    tiles = []
                    for tile in arr:
                        if tile == 0:
                            tileType = 0
                        else:
                            tileType = tile - firstgid;
                        if tileType == 0 or tileType == 4:
                            tiles.append(0)
                        else:
                            tiles.append(1)
                    comp = zlib.compressobj()
                    binData = struct.pack(str(len(tiles))+"B", *tiles)
                    binData = zlib.compress(binData)
                    idx = fileName.rfind("/") + 1
                    mapName = fileName[idx:-4]
                    writeMapName(w, mapName)
                    writeInt16(w, width)
                    writeInt16(w, height)
                    writeInt32(w, len(binData))
                    writeData(w, binData)
                    print fileName
                    mapsCount = mapsCount + 1
                    sz = sz + 12 + 8 + len(binData)
                    break
        w.seek(0);
        writeInt32(w, sz)
        writeInt16(w, mapsCount)

def readMapCache(path, cmd):
    if cmd == "help":
        printHelp()
    if cmd == "queststoxml":
        covertQuests()
        return
    elif cmd == "itemstoxml":
        convertItems()
        return
    elif cmd == "monsterstoxml":
        convertMonsters();
        return
    elif cmd == "mercenariestoxml":
        convertMercenaries();
        return
    elif cmd == "petstoxml":
        convertPets();
        return
    elif cmd == "homunculusestoxml":
        convertHomunculuses();
        return
    elif cmd == "skillstoxml":
        convertSkillsToXml();
        return
    elif cmd == "tmxtocache":
        recreateMapCache();
        return

    with open(path, "rb") as f:
        size = readInt32(f)
        if os.path.getsize(path) != size:
            print "Map cache corrupted, wrong file size."
            exit(1)
        mapsCount = readInt16(f)
        print "Maps count: " + str(mapsCount)
        readInt16(f) # padding
        if cmd == "listmaps":
            listMapCache(f, mapsCount)
        elif cmd == "extractmaps":
            extractMaps(f, mapsCount)
        elif cmd == "mapstotmx":
            covertToTmx(f, mapsCount)


readMapCache("serverdata/db/re/map_cache.dat", detectCommand())
