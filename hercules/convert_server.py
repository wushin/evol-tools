#! /usr/bin/env python
# -*- coding: utf8 -*-
#
# Copyright (C) 2014  Evol Online
# Author: Andrei Karas (4144)

from code.server.consts import *
from code.server.itemdb import *
from code.server.mobdb import *
from code.server.npcs import *
from code.server.utils import *

cleanServerData()
createMainScript()
convertNpcs()
convertMobDb()
convertItemDb()
convertConsts()
