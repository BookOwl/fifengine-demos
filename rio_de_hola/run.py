#!/usr/bin/env python

# -*- coding: utf-8 -*-

# ####################################################################
#  Copyright (C) 2005-2013 by the FIFE team
#  http://www.fifengine.net
#  This file is part of FIFE.
#
#  FIFE is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2.1 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the
#  Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
# ####################################################################
# This is the rio de hola client for FIFE.

import sys, os, re, math, random, shutil

fife_path = os.path.join('..','..','engine','python')
if os.path.isdir(fife_path) and fife_path not in sys.path:
	sys.path.insert(0,fife_path)

from fife import fife
print "Using the FIFE python module found here: ", os.path.dirname(fife.__file__)

from fife.extensions import *
from scripts import world
from scripts.common import eventlistenerbase
from fife.extensions import pychan
from fife.extensions.pychan.pychanbasicapplication import PychanApplicationBase
from fife.extensions.pychan.fife_pychansettings import FifePychanSettings
from fife.extensions.pychan import widgets
from fife.extensions.pychan.internal import get_manager
from fife.extensions.fife_settings import Setting
from fife.extensions.fife_utils import getUserDataDirectory

TDS = FifePychanSettings(app_name="rio_de_hola")

class KeyFilter(fife.IKeyFilter):
	"""
	This is the implementation of the fife.IKeyFilter class.

	Prevents any filtered keys from being consumed by fifechan.
	"""
	def __init__(self, keys):
		fife.IKeyFilter.__init__(self)
		self._keys = keys

	def isFiltered(self, event):
		return event.getKey().getValue() in self._keys

class ApplicationListener(eventlistenerbase.EventListenerBase):
	def __init__(self, engine, world):
		super(ApplicationListener, self).__init__(engine,regKeys=True,regCmd=True, regMouse=False, regConsole=True, regWidget=True)
		self.engine = engine
		self.world = world

		keyfilter = KeyFilter([fife.Key.ESCAPE, fife.Key.F10])
		keyfilter.__disown__()
		engine.getEventManager().setKeyFilter(keyfilter)

		self.quit = False
		self.aboutWindow = None

		self.rootpanel = pychan.loadXML('gui/rootpanel.xml')
		self.rootpanel.mapEvents({ 
			'quitButton' : self.onQuitButtonPress,
			'aboutButton' : self.onAboutButtonPress,
			'optionsButton' : TDS.showSettingsDialog
		})
		self.rootpanel.show()

	def keyPressed(self, evt):
		print evt
		keyval = evt.getKey().getValue()
		keystr = evt.getKey().getAsString().lower()
		consumed = False
		if keyval == fife.Key.ESCAPE:
			self.quit = True
			evt.consume()
		elif keyval == fife.Key.F10:
			get_manager().getConsole().toggleShowHide()
			evt.consume()
		elif keystr == 'p':
			self.engine.getRenderBackend().captureScreen('screenshot.png')
			evt.consume()

	def onCommand(self, command):
		if command.getCommandType() == fife.CMD_QUIT_GAME:
			self.quit = True
			command.consume()

	def onConsoleCommand(self, command):
		result = ''
		if command.lower() in ('quit', 'exit'):
			self.quit = True
			result = 'quitting'
		elif command.lower() in ( 'help', 'help()' ):
			get_manager().getConsole().println( open( 'misc/infotext.txt', 'r' ).read() )
			result = "-- End of help --"
		else:
			result = self.world.onConsoleCommand(command)
		if not result:
			try:
				result = str(eval(command))
			except:
				pass
		if not result:
			result = 'no result'
		return result

	def onQuitButtonPress(self):
		cmd = fife.Command()
		cmd.setSource(None)
		cmd.setCommandType(fife.CMD_QUIT_GAME)
		self.engine.getEventManager().dispatchCommand(cmd)

	def onAboutButtonPress(self):
		if not self.aboutWindow:
			self.aboutWindow = pychan.loadXML('gui/help.xml')
			self.aboutWindow.mapEvents({ 'closeButton' : self.aboutWindow.hide })
			self.aboutWindow.distributeData({ 'helpText' : open("misc/infotext.txt").read() })
		self.aboutWindow.show()

class IslandDemo(PychanApplicationBase):
	def __init__(self):
		super(IslandDemo,self).__init__(TDS)
		self.world = world.World(self.engine)
		self.listener = ApplicationListener(self.engine, self.world)
		self.world.load(str(TDS.get("rio", "MapFile")))

	def createListener(self):
		pass # already created in constructor

	def _pump(self):
		if self.listener.quit:
			self.breakRequested = True
			
			# get the correct directory to save the map file to
			mapSaveDir = getUserDataDirectory("fife", "rio_de_hola") + "/maps"
			
			# create the directory structure if it does not exist
			if not os.path.isdir(mapSaveDir):
				os.makedirs(mapSaveDir)
			
			# save map file to directory
			self.world.save(mapSaveDir + "/savefile.xml")
		else:
			self.world.pump()

def main():
	app = IslandDemo()
	app.run()


if __name__ == '__main__':
	if TDS.get("FIFE", "ProfilingOn"):
		import hotshot, hotshot.stats
		print "Starting profiler"
		prof = hotshot.Profile("fife.prof")
		prof.runcall(main)
		prof.close()
		print "analysing profiling results"
		stats = hotshot.stats.load("fife.prof")
		stats.strip_dirs()
		stats.sort_stats('time', 'calls')
		stats.print_stats(20)
	else:		
		main()
