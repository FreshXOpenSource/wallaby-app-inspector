# Copyright (c) by it's authors. 
# Some rights reserved. See LICENSE, AUTHORS.

from wallaby.pf.room import *

from wallaby.pf.peer.multiViewer import MultiViewer
from wallaby.pf.peer.multiViewEditor import MultiViewEditor

class __widgetquery__(Room):
    def __init__(self, name):
        Room.__init__(self, name)

        self._queryEditor = None

    def customPeers(self):
        if self._queryEditor is not None: self._queryEditor.destroy()
        self._queryEditor = MultiViewEditor(self._name, dstRoom="__CONFIG__", pillow=MultiViewer.In.Refresh)
