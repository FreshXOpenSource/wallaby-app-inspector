# Copyright (c) by it's authors. 
# Some rights reserved. See LICENSE, AUTHORS.

import wallaby.backends.couchdb as couch
import wallaby.backends.elasticsearch as es

from wallaby.frontends.qt.baseWindow import *

from wallaby.pf.peer.searchDocument import *

import wallaby.frontends.qt.resource_rc as resource_rc
from UI_mainWindow import *

import app_rc

class MainWindow(BaseWindow, Ui_MainWindow):
    def __init__(self, quitCB, options, embedded=False):
        if options.db != None:
            db = options.db
        else:
            db = "bootstrap"

        BaseWindow.__init__(self, "wallaby", "inspector", options, quitCB, dbName=db, embedded=embedded)

        # set up User Interface (widgets, layout...)
        self.setupUi(self)

        self.scrollArea.setWidgetResizable(True)

    def setConnectionSettings(self, options):
        if options and options.fx:
            options.server = "https://relax.freshx.de"
            options.couchPort = "443"
            options.esPort = "443/es"

        couch.Database.setURLForDatabase(self.dbName(), options.server + ":" + options.couchPort)
        es.Connection.setURLForIndex(None, options.server + ':' + options.esPort)

        if options and options.username != None and options.password != None:
            es.Connection.setLoginForIndex(None, options.username, options.password)

    def _credentialsArrived(self, pillow, feathers):
        pass
