# Copyright (c) by it's authors. 
# Some rights reserved. See LICENSE, AUTHORS.

from wallaby.pf.room import *

from wallaby.pf.peer.viewer import Viewer
from wallaby.pf.peer.tab import Tab

from wallaby.pf.peer.multiViewQuery import MultiViewQuery
from wallaby.pf.peer.documentListQuery import DocumentListQuery

class __config__(Room):
    def __init__(self, name):
        Room.__init__(self, name)

        self._widgetViewer = None
        self._roomViewer = None
        self._allRooms = None
        self._multiQuery = None
        self._docList = None

        self._initialized = False
        self._state = None
        self._lastSel = None

    def customPeers(self):
        if self._widgetViewer is not None: self._widgetViewer.destroy()
        if self._roomViewer is not None: self._roomViewer.destroy()
        if self._allRooms is not None: self._allRooms.destroy()
        if self._multiQuery is not None: self._multiQuery.destroy()
        if self._docList is not None: self._docList.destroy()

        self._multiQuery = MultiViewQuery("__CONFIG__", pillow=None)
        self._docList = DocumentListQuery("__CONFIG__")

        self._allRoom = Viewer("__CONFIG__", self._roomsChanged, "rooms", raw=True)

        self._widgetViewer = Viewer("__CONFIG__", self._widgetSelected, "widgets.*", raw=True, exact=True)
        self._roomViewer = Viewer("__CONFIG__", self._roomSelected, "rooms.*", raw=True, exact=True)

        if not self._initialized:
            self.catch("Inspector.In.AddPeer", self._addPeer)
            self.catch("Inspector.In.RemovePeer", self._removePeer)
            self.catch("Inspector.In.Suggest", self._doSuggest)
            self.catch("Inspector.In.InitializeRoom", self._initRoom)
            self.catch("MultiViewer.Out.Select", self._multiViewerChanged)

            from wallaby.pf.peer.editDocument import EditDocument
            self.catch(EditDocument.Out.State, self._newState)

            from wallaby.common.document import Document
            from wallaby.pf.peer.credentials import Credentials
            House.get("__DOC__").throw(Credentials.Out.Credential, Document())
            House.get("__FILTERS__").throw(Credentials.Out.Credential, Document())

        self._initialized = True
        self._lastSelection = None
        self._lastRoom = None
        self._suggests = None

    def _multiViewerChanged(self, pillow, sel):
        if sel is None or len(sel) < 1: return

        if self._lastSel != sel:
            self._lastSel = sel
            self.throw("DocumentChanger.In.Select", ("widgets", sel[0]))

    def _roomsChanged(self, rooms):
        if rooms is None: return

        import wallaby.FXUI as FXUI
        if FXUI.mainWindow.options().app != "inspector":
            filters = {
                "filters": [
                    ["All", [{"__key__": "!inspector-"}, {"__key__": "!itest-"}]]
                ]
            }
            for room in sorted(rooms.keys()):
                if not room.startswith('__'):
                    filters["filters"].append([room, [{"room": "^" + room}]])
        else:
            filters = {
                "filters": [
                    ["All", []],
                    ["Inspector", [{"__key__": "^inspector-"}]],
                    ["Inspector-Test", [{"__key__": "^itest-"}]]
                ]
            }

        from wallaby.common.document import Document
        House.get("__FILTERS__").throw(Viewer.In.Document, Document(data=filters))

    def _newState(self, pillow, state):
        self._state = state

    def _doSuggest(self, *args):
        room = self._roomViewer.selection()
        if room is not None and "." in room:
            _, room = room.split(".")
            House.get(room).throw(Room.In.Suggest, None)

    def _initRoom(self, *args):
        room = self._roomViewer.selection()
        if room is not None and "." in room:
            _, room = room.split(".")
            House.get(room).throw(Room.In.Initialize, True)

    def _roomSelected(self, value):
        room = self._roomViewer.selection()
        if room is not None and "." in room:
            _, room = room.split(".")

            if room != self._lastRoom:
                if self._lastRoom is not None:
                    House.get(self._lastRoom).uncatch(Viewer.In.Document, self._roomDoc)
                    House.get(self._lastRoom).uncatch(Room.Out.Suggests, self._newSuggest)

                House.get("__DOC__").throw(Viewer.In.Document, None)
   
                if room != "__DOC__": 
                    House.get(room).catch(Viewer.In.Document, self._roomDoc)
                    House.get(room).catch(Room.Out.Suggests, self._newSuggest)
                    self._lastRoom = room
                else:
                    self._lastRoom = None

    def _roomDoc(self, pillow, doc):
        if doc == None: return
        from wallaby.common.document import Document
        House.get("__DOC__").throw(Viewer.In.Document, Document(data=doc._data))

    def _removePeer(self, pillow, idx):
       from wallaby.pf.peer.documentChanger import DocumentChanger
       self.throw(DocumentChanger.In.RemoveRow, "rooms.*.Peers")

    def _addPeer(self, pillow, idx):
        room = self._roomViewer.selection()
        if room is not None and "." in room:
            _, room = room.split(".")

        if self._suggests:
            suggest = self._suggests.get("peers." + str(idx))
            if suggest is not None:
                config = suggest["config"]
                if config != None:
                    try:
                        import json
                        config = json.loads(config)
                    except Exception as e:
                        print "Error while parsing JSON", config, e
                        config = {}

                self.__addPeer(room, suggest["peer"], config)

    def __addPeer(self, room, name, config):
        if self._state not in ("Edit", "New", "Dirty"):
            from wallaby.qt_combat import QtGui
            import wallaby.FX as FX
            reply = QtGui.QMessageBox.question(FX.mainWindow, 'Edit configuration',
                "You must edit the configuration to add peers. Do you want to edit?", QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

            if reply == QtGui.QMessageBox.Yes:
                from wallaby.pf.peer.editDocument import EditDocument
                self.throw(EditDocument.In.Edit, None)
            else:
                return

        from wallaby.pf.peer.documentChanger import DocumentChanger
        self.throw(DocumentChanger.In.InsertRow, ("rooms.*.Peers", {"name": name, "config": config}))

        from wallaby.pf.room import House

        observer = House.observer()
        cls = observer.peerClass(name)

        try:
            for dep in cls.Dependencies:
                observer = House.observer()
                cls2 = observer.peerClass(dep)

                config = {}
                try:
                    description = cls2.Description
                    if isinstance(description, (list, tuple)):
                        description, config = description
                except: pass

                print "Looking for", dep, "in", House.get(room).allPeers()
                if dep in House.get(room).allPeers():
                    continue

                found = False

                for peer in House.get(room).allPeers():
                    if dep == peer.__class__.__name__: 
                        found = True
                        break

                if found: continue

                self.__addPeer(room, dep, config)
        except: pass

    def _newSuggest(self, pillow, doc):
        self._suggests = doc
        House.get("__SUGGEST__").throw(Viewer.In.Document, doc)

    def _widgetSelected(self, value):
        if value != None and "wallabyType" in value:
            selection = "i" + value["wallabyType"]
        else:
            selection = "iDefault"

        if value != None and "room" in value:
            from wallaby.pf.peer.documentChanger import DocumentChanger
            self.throw(DocumentChanger.In.Select, ("rooms", value['room']))

        if selection == self._lastSelection: return
        self._lastSelection = selection

        self.throw(Tab.In.SelectByName, "widgetConfigs." + selection)
        self.throw(Tab.In.SelectByName, "configTab." + selection)

