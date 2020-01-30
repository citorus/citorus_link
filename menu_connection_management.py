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

import os, sys, time
import json

import requests
from requests.auth import HTTPDigestAuth

from PyQt4 import QtGui, uic
from PyQt4.QtCore import *
from PyQt4.QtGui import *


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'menu_connection_management_base.ui'))

this_dir = os.path.dirname(__file__).decode(sys.getfilesystemencoding())


class MenuConnectionManagement (QtGui.QDialog, FORM_CLASS):

    def __init__(self, parametr_editting, parent=None):
        """Constructor."""
        super(MenuConnectionManagement, self).__init__(parent)

        self.setupUi(self)

        self.parametrEditting = parametr_editting

        # Informational text --------------------------------------------------
        self.lbConnectionTesting.setVisible(False)
        self.lbConnectionTesting_access.setVisible(False)

        # If the editing mode is filled fields --------------------------------
        self.readAuthentificationJson()
        if self.parametrEditting : 
            for item in range(len(self.dataFileJSON)):
                if self.dataFileJSON[item]["selected"] == True :
                    number = item
            self.mcUrl.setText(self.dataFileJSON[number]["url"].split('/getLayers')[0])
            self.mcName.setText(self.dataFileJSON[number]["name"])
            self.mcId = self.dataFileJSON[number]["id"]
            self.authentificationInputEnabled(True)
            if self.dataFileJSON[number]["login"] == self.dataFileJSON[number]["password"] == 'anonymous':
                self.mcAsGuest.setChecked(True)
                self.mcUser.setEnabled(False)
                self.mcPassword.setEnabled(False)
            else:
                self.mcUser.setText(self.dataFileJSON[number]["login"])
                self.mcPassword.setText(self.dataFileJSON[number]["password"])
        else:
            self.mcId = self.createIDAccount()
            self.authentificationInputEnabled(False)

        self.buttonBox.button(QDialogButtonBox.Ok).clicked.connect(self.close)
        self.buttonBox.button(QDialogButtonBox.Ok).clicked.connect(self.confirmationEnteredData)
        self.buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(self.close)

        # Set timeout to check connection server ------------------------------
        self.timerUrlChange = QTimer()
        self.timerUrlChange.setSingleShot(True)
        self.timerUrlChange.setInterval(800)
        self.timerUrlChange.timeout.connect(self.serverCheckAccess)
        self.mcUrl.textChanged.connect(self.timerUrlChange.start)

        # Set timeout to check Authentification data --------------------------
        self.timerAuthentificationDataChange = QTimer()
        self.timerAuthentificationDataChange.setSingleShot(True)
        self.timerAuthentificationDataChange.setInterval(800)
        self.timerAuthentificationDataChange.timeout.connect(self.checkAuthentificationData)
        self.mcUrl.textChanged.connect(self.timerAuthentificationDataChange.start)
        self.mcUser.textChanged.connect(self.timerAuthentificationDataChange.start)
        self.mcPassword.textChanged.connect(self.timerAuthentificationDataChange.start)

        # Set enabled for buttun Ok when input edit --------------------------
        self.mcUrl.textEdited.connect(self.btnOkSetEnabled)
        self.mcUser.textEdited.connect(self.btnOkSetEnabled)
        self.mcPassword.textEdited.connect(self.btnOkSetEnabled)

        self.mcName.textEdited.connect(self.checkFieldFill)

        # Anonymous change state ---------------------------------------------
        self.mcAsGuest.stateChanged.connect(self.checkAnonymous)
        self.mcAsGuest.stateChanged.connect(self.checkFieldFill)

        # self.mcUrl.editingFinished.connect(self.checkAuthentificationData)


    def close (self):
        super(MenuConnectionManagement, self).close()


    def authentificationInputEnabled (self, state):
        self.mcAsGuest.setEnabled(state)
        self.mcName.setEnabled(state)
        self.mcUser.setEnabled(state)
        self.mcPassword.setEnabled(state)
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(state)


    def readAuthentificationJson (self):
        with open(os.path.join(this_dir, 'authentification.json'), "r") as fileJSON:
            self.dataFileJSON = json.load(fileJSON)


    def overwriteAuthentificationJson (self):
        with open(os.path.join(this_dir, 'authentification.json'), "w") as fileJSON:
            json.dump(self.dataFileJSON, fileJSON)


    def makeValidServerUrl (self, url):
        if url is None or url.count('http://') == 0:
            return "http://" + url
        else:
            return url


    def makeValidServerUrlGetLayers (self, url):
        if url.count('/getLayers') > 0:
            return url
        elif url.split('/')[-1] == '':
            return url + 'getLayers'
        else:
            return url + '/getLayers'


    def makeCheckAccessUrl (self, url):
        hostname = url.split('http://')[1]
        if hostname.count('/') == 0:
            return url + '/checkAccess'
        else:
            return 'http://' + hostname.split('/')[0] + '/' + hostname.split('/')[1] + '/checkAccess'


    def serverCheckAccess (self):
        self.lbConnectionTesting.setVisible(True)
        self.lbConnectionTesting.setStyleSheet("color: None")
        self.lbConnectionTesting.setText("Проверка доступности сервера ...".decode('utf8'))
        
        validURL = self.makeValidServerUrl(self.mcUrl.text())
        makeCheckAccessUrl = self.makeCheckAccessUrl(validURL)
        
        try:
	        request = requests.get(makeCheckAccessUrl, timeout=3)
	        requestJSON = request.json()
	        if requestJSON['ok'] == True:
	            self.lbConnectionTesting.setStyleSheet("color: green")
	            self.lbConnectionTesting.setText("Сервер доступен".decode('utf8'))
                self.authentificationInputEnabled(True)
                self.checkAnonymous()
                self.checkFieldFill()
        except:
	        self.lbConnectionTesting.setStyleSheet("color: red")
	        self.lbConnectionTesting.setText("Сервер недоступен!!!".decode('utf8'))
	        self.authentificationInputEnabled(False)

    
    def checkAuthentificationData (self):
        if ( len(self.mcUrl.text()) > 0 and len(self.mcUser.text()) > 0 and len(self.mcPassword.text()) > 0 ):

            validURL = self.makeValidServerUrl(self.mcUrl.text())
            validURLGetLayers = self.makeValidServerUrlGetLayers(validURL)

            self.lbConnectionTesting_access.setVisible(True)
            self.lbConnectionTesting_access.setStyleSheet("color: black")
            self.lbConnectionTesting_access.setText("Проверка ...".decode('utf8')) 

            try:
                request = requests.get( validURLGetLayers , auth=HTTPDigestAuth( self.mcUser.text(), self.mcPassword.text()), timeout=3)
                if (len(request.json()) > 0 and type(request.json()) is not dict ) or (type(request.json()) is dict and not request.json().has_key(u'error')):
                    self.lbConnectionTesting_access.setVisible(False)
                    self.checkFieldFill()
                else:
                    self.lbConnectionTesting_access.setVisible(True)
                    self.lbConnectionTesting_access.setStyleSheet("color: red")
                    self.lbConnectionTesting_access.setText("Неверно введены URL, логин или пароль!!!".decode('utf8'))
                    self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
            except:
                self.lbConnectionTesting_access.setVisible(True)
                self.lbConnectionTesting_access.setStyleSheet("color: red")
                self.lbConnectionTesting_access.setText("Неверно введены URL, логин или пароль!!!".decode('utf8'))
                self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)

    
    def confirmationEnteredData (self):
        validURL = self.makeValidServerUrl(self.mcUrl.text())
        validURLGetLayers = self.makeValidServerUrlGetLayers(validURL)
        
        if self.mcAsGuest.isChecked():
            dataServerAuthentification = {
               "url" : validURLGetLayers,
               "name" : self.mcName.text(),
               "login" : "anonymous",
               "password": "anonymous",
               "selected" : True,
               "id" : self.mcId
            }
        else:
            dataServerAuthentification = {
               "url" : validURLGetLayers,
               "name" : self.mcName.text(),
               "login" : self.mcUser.text(),
               "password": self.mcPassword.text(),
               "selected" : True,
               "id" : self.mcId
            }

        # Read authentification file ------------------------------------------
        self.readAuthentificationJson()

        for item in range(len(self.dataFileJSON)):
            if self.dataFileJSON[item]["selected"] == True :
                cmbSelectedItemNumber = item

        for item in range(len(self.dataFileJSON)):
            self.dataFileJSON[item]["selected"] = False

        if self.parametrEditting :
            self.dataFileJSON[cmbSelectedItemNumber] = dataServerAuthentification
        else: 
            self.dataFileJSON.append(dataServerAuthentification)

        # Overwrite authentification file -------------------------------------
        self.overwriteAuthentificationJson()

        from CITORUS_Connect_dockwidget import MenuSettingsDialog
        MenuSettingsDialog.dialogWindowSettings()


    def checkFieldFill (self):
        if ( len(self.mcUrl.text()) > 0 and len(self.mcName.text()) > 0 and len(self.mcUser.text()) > 0 and len(self.mcPassword.text()) > 0 and self.lbConnectionTesting_access.isVisible() == False):
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)
        elif  len(self.mcUrl.text()) > 0 and len(self.mcName.text()) > 0 and self.mcAsGuest.isChecked():
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)
        else:
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)


    def btnOkSetEnabled (self):
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)


    def checkAnonymous (self):
        if self.mcAsGuest.isChecked():
            self.mcUser.setEnabled(False)
            self.mcPassword.setEnabled(False)
            self.lbConnectionTesting_access.setStyleSheet("color: grey")
            # self.lbConnectionTesting_access.setVisible(False)
        else:
            self.mcUser.setEnabled(True)
            self.mcPassword.setEnabled(True)
            self.lbConnectionTesting_access.setStyleSheet("color: red")
            # self.timerAuthentificationDataChange1.start

    
    def createIDAccount (self):
        if len(self.dataFileJSON) > 0:
            idMax = max(map(lambda x : x['id'], self.dataFileJSON))
            self.mcId = idMax + 1
        else:
            self.mcId = 0
        return self.mcId
            

