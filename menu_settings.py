# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CITORUSConnect
                                 A QGIS plugin
 Plugin
                             -------------------
        begin                : 2018-11-13
        copyright            : (C) 2018 by author
        email                : author@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""

import os, sys
import json

from PyQt4 import QtGui, uic, QtCore, Qt
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import *
from qgis.gui import *
from qgis.core import *

from menu_connection_management import MenuConnectionManagement


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'menu_settings_base.ui'))

this_dir = os.path.dirname(__file__).decode(sys.getfilesystemencoding())
OBJECTS_PATH = os.path.join(this_dir, 'objects/')


class MenuSettings (QtGui.QDialog, FORM_CLASS):

    def __init__(self, parent=None):
        """Constructor."""
        super(MenuSettings, self).__init__(parent)

        self.setupUi(self)

        # Copying the original window settings --------------------------------
        self.getOriginalWindowSettings()
        
        # Set saved window settings -------------------------------------------
        self.dialogWindowSettings()

        # Button functions ----------------------------------------------------
        self.btnNew.clicked.connect(self.openMenuConnectionManagementNew)
        self.btnEdit.clicked.connect(self.openMenuConnectionManagementEdit)
        self.btnDelete.clicked.connect(self.deleteAccount)

        # self.buttonBox.button(QDialogButtonBox.Ok).clicked.connect(self.confirmationEnteredData)
        self.buttonBox.button(QDialogButtonBox.Ok).clicked.connect(self.close)
        self.buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(self.cancelEnteredData)
        self.buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(self.close)

        self.cmbConnections.activated.connect(self.comboboxSelectItem)


    def close (self):
        super(MenuSettings, self).close()
        self.readAuthentificationJson()

        self.checkFolderAccount()
        from CITORUS_Connect import dockwidget
        dockwidget.removeTree()
        # dockwidget.spinnerLoading()
        dockwidget.spinner.setVisible(True)
        # dockwidget.addChildLoading()
        while True:
            if dockwidget.spinner.isVisible(): 
                break
        dockwidget.readAuthentificationJson()
        dockwidget.spinner.setVisible(False)
        

    # def closeEvent(self, event):
    #     # Read authentification file ------------------------------------------
    #     self.readAuthentificationJson()

    #     self.checkFolderAccount()
    #     from CITORUS_Connect import dockwidget
    #     dockwidget.addChildLoading()
    #     dockwidget.readAuthentificationJson()
    #     # event.accept()


    def getOriginalWindowSettings (self):
        with open(os.path.join(this_dir, 'authentification.json'), "r") as fileJSON:
            self.originalSettings = json.load(fileJSON)

    
    def readAuthentificationJson (self):
        with open(os.path.join(this_dir, 'authentification.json'), "r") as fileJSON:
            self.dataFileJSON = json.load(fileJSON)


    def overwriteAuthentificationJson (self):
        with open(os.path.join(this_dir, 'authentification.json'), "w") as fileJSON:
            json.dump(self.dataFileJSON, fileJSON)


    def dialogWindowSettings (self):
        # Read authentification file ------------------------------------------
        self.readAuthentificationJson()

        # Clear list of objects in ComboBox -----------------------------------
        self.cmbConnections.clear()

        # Set saved window settings -------------------------------------------
        if len(self.dataFileJSON) > 0:
            self.btnEdit.setEnabled(True)
            self.btnDelete.setEnabled(True)
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)
            for item in range(len(self.dataFileJSON)):
                self.cmbConnections.addItems([self.dataFileJSON[item]["name"]])
                if self.dataFileJSON[item]["selected"] == True :
                    self.cmbConnections.setCurrentIndex(item)
        else: 
            self.btnEdit.setEnabled(False)
            self.btnDelete.setEnabled(False)
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)


    def comboboxSelectItem (self) :
        for item in range(len(self.dataFileJSON)):
            self.dataFileJSON[item]["selected"] = False
        self.dataFileJSON[self.cmbConnections.currentIndex()]["selected"] = True 

        # Overwrite authentification file -------------------------------------
        self.overwriteAuthentificationJson()


    def openMenuConnectionManagementNew (self) :
        self.menuconnection = MenuConnectionManagement ( parametr_editting = False )
        self.menuconnection.show()


    def openMenuConnectionManagementEdit (self) :
        self.menuconnection = MenuConnectionManagement ( parametr_editting = True )
        self.menuconnection.show()

    
    # def confirmationEnteredData (self) :
    #     # self.checkFolderAccount()
    #     from CITORUS_Connect import dockwidget
    #     dockwidget.readAuthentificationJson()

        
    def cancelEnteredData (self) :
        with open(os.path.join(this_dir, 'authentification.json'), "w") as fileJSON:
            json.dump(self.originalSettings, fileJSON)


    def deleteAccount (self) :
        for item in range(len(self.dataFileJSON)):
            if self.dataFileJSON[item]["selected"] == True :
                cmbSelectedItemNumber = item
        
        # Remove account from the list ----------------------------------------
        del self.dataFileJSON[cmbSelectedItemNumber]

        if len(self.dataFileJSON) > 0:
            self.dataFileJSON[0]["selected"] = True

        # Overwrite authentification file -------------------------------------
        self.overwriteAuthentificationJson()
        
        # Set saved window settings -------------------------------------------
        self.dialogWindowSettings()
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)


    def checkFolderAccount (self):
        listIdAccount = map(lambda x : x['id'], self.dataFileJSON)
        listExistFolders = [int(foldername) for foldername in os.listdir(OBJECTS_PATH) if os.path.isdir(os.path.join(OBJECTS_PATH,foldername))]

        listDifference = list(set(listIdAccount)-set(listExistFolders))
        if len(listDifference) > 0:
            map(lambda x : self.createFolderAccount(x), listDifference)
        
        listDifferenceExist = list(set(listExistFolders)-set(listIdAccount))
        if len(listDifferenceExist) > 0:
            map(lambda x : self.deleteFolderAccount(x), listDifferenceExist)


    def createFolderAccount (self, accountId):
        os.mkdir(os.path.join(OBJECTS_PATH, str(accountId)))

        # fileLyaersReestr = {}
        # with open(os.path.join(OBJECTS_PATH, str(accountId), 'layersReestr.json'), "w") as fileJSON:
        #     json.dump(fileLyaersReestr, fileJSON)

    
    def deleteFolderAccount (self, accountId):
        listExistLayers = [str(foldername) for foldername in os.listdir(os.path.join(OBJECTS_PATH, str(accountId))) if os.path.isdir(os.path.join(OBJECTS_PATH, str(accountId),foldername))]
        # Remove layers from map ----------------------------------------------     
        myLayers = QgsMapLayerRegistry.instance().mapLayers()
        # with open(os.path.join(OBJECTS_PATH, str(accountId), 'layersReestr.json'), "r") as fileLayerReestr:
        with open(os.path.join(this_dir, 'layersReestr.json'), "r") as fileLayerReestr:
            fileReestr = json.load(fileLayerReestr)
        for key in myLayers.keys():
            if fileReestr.has_key(key):
            # if listExistLayers.count(QgsExpressionContextUtils.layerScope(myLayers[x]).variable('id')) > 0:
                QgsMapLayerRegistry.instance().removeMapLayer(myLayers[key])

        # Remove folders with cash by ID Account ------------------------------
        for layerId in listExistLayers:
            dir_obj_path = os.path.join(OBJECTS_PATH, str(accountId), layerId)
            for elem in os.listdir(os.path.join(dir_obj_path, 'edit')):
                os.remove(os.path.join(dir_obj_path, 'edit', elem))
            os.rmdir(os.path.join(dir_obj_path, 'edit'))

            for elfile in os.listdir(dir_obj_path):
                os.remove(os.path.join(dir_obj_path, elfile))
            os.rmdir(dir_obj_path)

        # os.remove(os.path.join(OBJECTS_PATH, str(accountId), 'layersReestr.json'))

        os.rmdir(os.path.join(OBJECTS_PATH, str(accountId)))
