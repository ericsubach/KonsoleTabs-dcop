#!/usr/bin/env python

################################################################################
# Set up Konsole prepopulated with named tabs, commands already executed on
# those tabs, and commands in the history -- all of this is on a per-tab basis.
#
# NOTE: This script only works with older Konsole versions using DCOP, not the 
#       newer ones using D-Bus.
#
# The primary advantage to using this as opposed to using Konsole's profile
# capabilities is the ability to set up per-tab history, so invoking
# frequently used commands is easy. It is currently limited to just one 
# 'profile.'
#
# Author: Eric Subach (2012)
# Copyright 2013 In-Depth Engineering. All Rights Reserved.
#
################################################################################

################################################################################
# Config File Location: ~/.konsoleTabs
#
# File Format Example:
#
#_tabs = [
#         ("compile",  [],              ["make -j8"]),
#         ("System", ["stopSystem.sh"], ["startSystem.sh"]),
#         ("other",    [],              [])
#        ]
#_commonCommands = ["source commonStartup.sh"]
#
# The tuple format is: (tab name, commands to run on tab, commands to have in history)
# The common commands format is: (command, command, ...)
################################################################################

import os
import os.path
import re
import subprocess
import sys
import tempfile
from sets import Set
from time import sleep

_programName = "konsole"
_configFilename = "~/.konsoleTabs"
_startShellCommand = "kstart konsole --script"
_newTabTemplate           = "dcop konsole-%s konsole newSession"
_closeTabTemplate         = "dcop konsole-%s session-%s closeSession"
_renameTabTemplate        = "dcop konsole-%s session-%s renameSession %s"
_commandToTabTemplate     = "dcop konsole-%s session-%s sendSession '%s'"
_commandToAllTabsTemplate = "dcop konsole-%s konsole sendAllSessions '%s'"
_historyFilename     = ".history"
_historyFilenameTemp = _historyFilename + ".tempbackup"

# Read file that contains the tabs and common commands definition.
tConfigFilePath = os.path.expanduser(_configFilenamee)
config = {}

try:
   namespace = {}
   #exec open(tConfigFilePath).read() in namespace
   execfile(tConfigFilePath, config)
#except IOError:
except:
   print "Error reading %s; either file doesn't exist or there was an error reading it. Make sure it is executable." %(tConfigFilePath)
   sys.exit(0)

try:
   _tabs = config["_tabs"]
   _commonCommands = config["_commonCommands"]
except:
   print "Required data is not defined -- read the source file for an example."
   sys.exit(0)

################################################################################

# Get all PIDs of a given process name as a set.
def getAllPids(aProgramName):
   tPIDSet = Set([])
   
   try:
      #tPIDSetString = subprocess.check_output(["/sbin/pidof", aProgramName])
      tProcess = subprocess.Popen(["/sbin/pidof", aProgramName], stdout=subprocess.PIPE)
      tProcess.wait()
      tPIDSetString = tProcess.communicate()[0]
      tPIDSetString = tPIDSetString.strip()
      tPIDSet       = Set(tPIDSetString.split())
   except: #subprocess.CalledProcessError:
      pass
      
   return tPIDSet

################################################################################

# Get PID list of all instances of program
tPIDSetBefore = getAllPids(_programName)
print "tpidsetbefore = "
print tPIDSetBefore

# Open a special shell with DCOP enabled.
#subprocess.check_call(["kstart", "konsole --script"])
subprocess.call(_startShellCommand, shell=True)

sleep(1)

# Get all process IDs again.
tPIDSetAfter = getAllPids(_progamName)
print "tpidsetafter = "
print tPIDSetAfter

# Calculate the difference between when invoked before and now. The new id
# should be the only one in the set.
tDifference = tPIDSetAfter - tPIDSetBefore

if len(tDifference) == 1:
   tNewPID = tDifference.pop()
else:
   print "Error: couldn't get PID of the new shell."
   sys.exit()
   
################################################################################

os.chdir(os.environ["HOME"])

tHistoryFilePath = os.path.join(os.getcwd(), _historyFilename)

# Create history file if it doesn't exist.
if not os.path.exists(tHistoryFilePath):
   tHistoryFileTemp = open(tHistoryFilePath)
   tHistoryFileTemp.close()
   
# Move history file to backup location.
os.rename(_historyFilename, _historyFilenameTemp)

# Create tabs (with modified history for that tab).
# for tIdx in range(0, len(_tabs)):
for tData in _tabs:
   tHistoryFileNew = open(_historyFilename, "w+")
   
   tCommands = tData[2]
   
   # Get the modified history list and write it to history file.
   for tCommand in tCommands:
      print tCommand
      tHistoryFileNew.write(tCommand + os.linesep)
   tHistoryFileNew.close()
   
   tNewTabShellCommand = _newTabTemplate % (tNewPID)
   subprocess.call(tNewTabShellCommand, shell=True)
   sleep(0.5)
   
   os.remove(_historyFilename)
   
   
# Restore history file.
os.rename(_historyFilenameTemp, _historyFilename)



# Rename tabs.
for tIdx, tData in enumerate(_tabs):
   tTabName, tTabCommands, tTabHistory = tData
   
   tRenameTabShellCommand = _renameTabTemplate % (tNewPID, tIdx+2, tTabName)
   subprocess.call(tRenameTabShellCommand, shell=True)
   
# Run common commands on each tab.
for tCommonCommand in _commonCommands:
   tShellCommand = _commandToAllTabsTemplate % (tNewPID, tCommonCommand)
   subprocess.call(tShellCommand, shell=True)
   
sleep(1)

# Run unique command for each tab.
for tIdx, tData in enumerate(_tabs):
   tTabName, tTabCommands, tTabHistory = tData
   
   for tTabCommand in tTabCommands:
      tShellCommand = _commandToTabTemplate % (tNewPID, tIdx+2, tTabCommand)
      subprocess.call(tShellCommand, shell=True)
   #if len(tTabCommands) > 0:
   #   sleep(1)

tCloseTabShellCommand = _closeTabTemplate % (tNewPID, 1)
subprocess.call(tCloseTabShellCommand, shell=True)
