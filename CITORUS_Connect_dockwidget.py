# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CITORUSConnectDockWidget
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
from osgeo import ogr
from functools import partial
import datetime

# import requests
# from requests.auth import HTTPDigestAuth
from scripts_dockwidget.request import Request

# from base64 import b64encode
# from PyQt4.QtNetwork import *

from PyQt4 import QtGui, uic, QtCore, Qt
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.gui import *
from qgis.core import *
from qgis.utils import *

from menu_settings import MenuSettings
from scripts_dockwidget.vector_layer_import import VectorLayerImport
from scripts_dockwidget.vector_layer_editing import VectorLayerEditing
from scripts_dockwidget.vector_layer_export import VectorLayerExport
from scripts_dockwidget.raster_layer_import import RasterLayerImport
from scripts_dockwidget.raster_layer_editing import RasterLayerEditing
from scripts_dockwidget.raster_layer_export import RasterLayerExport


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'CITORUS_Connect_dockwidget_base.ui'))

# this_dir = os.path.dirname(os.path.realpath(__file__))
this_dir = os.path.dirname(__file__).decode(sys.getfilesystemencoding())
ICONS_PATH = os.path.join(this_dir, 'icons/')
OBJECTS_PATH = os.path.join(this_dir, 'objects/')
DATA_PATH = os.path.join(this_dir, 'data/')


class PreviewCanvas(QMainWindow):
    def __init__(self, layers, backLayer, projectName, layerName):
        QMainWindow.__init__(self)

        QMainWindow.setWindowTitle(self, projectName + u'@' + layerName)

        self.canvas = QgsMapCanvas()
        # self.canvas.setCanvasColor(Qt.white)

        

        self.canvas.resize(QSize(300,300))
        # self.canvas.setWindowTitle(u'Предварительный просмотр')

        self.canvas.setExtent(layers[-1].extent())
        listLayers = [QgsMapCanvasLayer(x) for x in layers] 
        listLayers.append(QgsMapCanvasLayer(backLayer))
        # listLayers = [QgsMapCanvasLayer(layer), QgsMapCanvasLayer(backLayer)]
        self.canvas.setLayerSet(listLayers)

        self.setCentralWidget(self.canvas)

        self.actionZoomIn = QAction("", self)
        self.actionZoomIn.setIcon(QIcon(os.path.join(ICONS_PATH, 'preview/zoomin.svg')))
        self.actionZoomOut = QAction("", self)
        self.actionZoomOut.setIcon(QIcon(os.path.join(ICONS_PATH, 'preview/zoomout.svg')))
        self.actionZoomFullExtent = QAction("", self)
        self.actionZoomFullExtent.setIcon(QIcon(os.path.join(ICONS_PATH, 'preview/fullextent.svg')))
        self.actionPan = QAction("Pan", self)
        self.actionPan.setIcon(QIcon(os.path.join(ICONS_PATH, 'preview/pan.svg')))

        self.actionZoomIn.setCheckable(True)
        self.actionZoomOut.setCheckable(True)
        self.actionZoomFullExtent.setCheckable(False)
        self.actionPan.setCheckable(True)

        self.actionZoomIn.triggered.connect(self.zoomIn)
        self.actionZoomOut.triggered.connect(self.zoomOut)

        
        self.actionZoomFullExtent.triggered.connect(partial(self.zoomFullExtent, layers[-1]))
        self.actionPan.triggered.connect(self.pan)

        self.toolbar = self.addToolBar("Canvas actions")
        self.toolbar.addAction(self.actionZoomIn)
        self.toolbar.addAction(self.actionZoomOut)
        self.toolbar.addAction(self.actionZoomFullExtent)
        self.toolbar.addAction(self.actionPan)

        # create the map tools
        self.toolPan = QgsMapToolPan(self.canvas)
        self.toolPan.setAction(self.actionPan)
        self.toolZoomIn = QgsMapToolZoom(self.canvas, False) # false = in
        self.toolZoomIn.setAction(self.actionZoomIn)
        self.toolZoomOut = QgsMapToolZoom(self.canvas, True) # true = out
        self.toolZoomOut.setAction(self.actionZoomOut)
        # self.toolZoomFullExtent = QgsMapTool(self.canvas)
        # self.toolZoomFullExtent.setAction(self.actionZoomFullExtent)

        self.pan()

        self.show()

        ####breakpoint
        # import pdb
        # pyqtRemoveInputHook()
        # pdb.set_trace()
        

    def zoomIn(self):
        self.canvas.setMapTool(self.toolZoomIn)

    def zoomOut(self):
        self.canvas.setMapTool(self.toolZoomOut)

    def zoomFullExtent(self, layer):
        #self.canvas.setMapTool(self.toolZoomFullExtent)
        self.canvas.setExtent(layer.extent())
        layer.triggerRepaint()

    def pan(self):
        self.canvas.setMapTool(self.toolPan)


class CITORUSConnectDockWidget (QtGui.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(CITORUSConnectDockWidget, self).__init__(parent)

        self.setupUi(self)

        # Add Icons for buttons in button-bar
        # Import to QGIS ------------------------------------------------------
        icon_buttonImport = QIcon()
        icon_buttonImport.addPixmap(QPixmap(os.path.join(ICONS_PATH, 'iButtonImport.png')), QIcon.Normal, QIcon.Off)
        self.btnbarImport.setIcon(icon_buttonImport)
        self.btnbarImport.setToolTip('Импортировать в QGIS'.decode('utf8'))

        # Export to CITORUS ---------------------------------------------------
        icon_buttonExport = QIcon()
        icon_buttonExport.addPixmap(QPixmap(os.path.join(ICONS_PATH, 'iButtonExport.png')), QIcon.Normal, QIcon.Off)
        self.btnbarExport.setIcon(icon_buttonExport)
        self.btnbarExport.setToolTip("Экспортировать в CITORUS".decode('utf8'))

        # Refresh -------------------------------------------------------------
        icon_buttonRefresh = QIcon()
        icon_buttonRefresh.addPixmap(QPixmap(os.path.join(ICONS_PATH, 'iButtonRefresh.png')), QIcon.Normal, QIcon.Off)
        self.btnbarRefresh.setIcon(icon_buttonRefresh)
        self.btnbarRefresh.setToolTip("Обновить".decode('utf8'))

        # Settings ------------------------------------------------------------
        icon_buttonSettings = QIcon()
        icon_buttonSettings.addPixmap(QPixmap(os.path.join(ICONS_PATH, 'iButtonSettings.png')), QIcon.Normal, QIcon.Off)
        self.btnbarSettings.setIcon(icon_buttonSettings)
        self.btnbarSettings.setToolTip('Настройки'.decode('utf8'))

        # Editing ------------------------------------------------------------
        icon_buttonEditing = QIcon()
        icon_buttonEditing.addPixmap(QPixmap(os.path.join(ICONS_PATH, 'iButtonEditing.png')).scaledToWidth(22), QIcon.Normal, QIcon.Off)
        self.btnbarEditing.setIcon(icon_buttonEditing)
        self.btnbarEditing.setToolTip('Редактирование'.decode('utf8'))

        # Help message label -------------------------------------------------
        # url = "http://%s/docs_ngcom/source/ngqgis_connect.html" % self.tr("docs.nextgis.com")
        url = "https://yandex.ru/"
        self.helpMessageLabel.setText(
            ' <span style="font-weight:bold;font-size:12px;color:blue;">?    </span><a href="%s">%s</a>' % (
                url,
                self.tr("Help")
            )
        )

        # Loading ------------------------------------------------------------
        movie = QtGui.QMovie(os.path.join(ICONS_PATH, "ajax-loader.gif"))
        self.spinner.setMovie(movie)
        movie.start()

        # Function on buttons in top bar -------------------------------------
        self.btnbarImport.clicked.connect(self.importLayer)
        self.btnbarExport.clicked.connect(self.showInfoDialogExportLayer)
        self.btnbarEditing.clicked.connect(self.showInfoDialogEditingLayer)
        self.btnbarRefresh.clicked.connect(self.clickRefresh)
        self.btnbarSettings.clicked.connect(self.openSettingDialog)

        self.readAuthentificationJson()
        self.checkFolderAccount()

        # Selected Item tree in window plugin --------------------------------
        self.treeWidget.itemSelectionChanged.connect(self.treeItemSelected)

        # Change legend interface --------------------------------------------
        # iface.legendInterface().currentLayerChanged.connect(self.legendLayerChanged)

        # QgsMapLayerRegistry.instance().legendLayersAdded.connect(self.legendLayerChanged)
        QgsMapLayerRegistry.instance().layersRemoved.connect(self.legendLayerRemovedItem)

        # self.treeWidget.itemExpanded.connect(self.treeItemSelected)
        # self.treeWidget.itemClicked.connect(self.treeItemSelected)
        # self.treeWidget.mousePressEvent = self.mymouseDoubleClickEvent

        # Open information windows for layers ---------------------------------
        self.treeWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.treeWidget.customContextMenuRequested.connect(self.openInfoPopup)


        self.selectedItemsDesc = []
        self.selectedItemsFolderLayer = 0
        self.serialEditObj = 'wew'

        crsEPSG = 'EPSG:4326' # Change accordingly
        QSettings().setValue('/Projections/defaultBehaviour', 'useProject')
        QSettings().setValue('/Projections/layerDefaultCrs', crsEPSG)
        
        self.spinner.setVisible(False)


    def closeEvent (self, event):
        # self.btnbarRefresh.clicked.disconnect(self.clickRefresh)
        # self.btnbarSettings.clicked.disconnect(self.openSettingDialog)
        # self.treeWidget.itemSelectionChanged.disconnect(self.treeItemSelected)
        # self.treeWidget.customContextMenuRequested.disconnect(self.openInfoPopup)
        self.closingPlugin.emit()
        event.accept()


    # def spinnerLoading (self):
    #     while True:
    #         if self.treeWidget.topLevelItemCount() == 0:
    #             break
    #     self.spinner.setVisible(True)

    
    def legendLayerChanged (self):
        try:
            for lyr in iface.legendInterface().layers():
                lyr.selectionChanged.disconnect(self.selectedFeaturesLayer)
        except:
            pass

        # Get active layer ----------------------------------------------------
        self.actLayer = iface.activeLayer()

        if self.actLayer and self.dateFileLayersReestr.has_key(self.actLayer.id()):
            self.actLayerInfo = self.dateFileLayersReestr[self.actLayer.id()]

            # Set enabled for Export button -----------------------------------
            if self.actLayerInfo['editable']:
                self.btnbarExport.setEnabled(True)
                self.btnbarExport.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
            else:
                self.btnbarExport.setEnabled(False)
                self.btnbarExport.setCursor(QCursor(QtCore.Qt.ArrowCursor))

            # Set enabled for Editing button ----------------------------------
            if self.actLayerInfo['type'] == 'vectorLayer' and len(self.actLayer.selectedFeatures()) > 0 and not self.actLayerInfo['editable'] :
                self.btnbarEditing.setEnabled(True)
                self.btnbarEditing.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
            elif self.actLayerInfo['type'] == 'rasterLayer' and not self.actLayerInfo['editable'] :
                self.btnbarEditing.setEnabled(True)
                self.btnbarEditing.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
            else:
                self.btnbarEditing.setEnabled(False)
                self.btnbarEditing.setCursor(QCursor(QtCore.Qt.ArrowCursor))

            if self.actLayerInfo['type'] == 'vectorLayer' and not self.actLayerInfo['editable']:
                self.actLayer.selectionChanged.connect(self.selectedFeaturesLayer)
        elif self.actLayer and self.actLayer.type() == 1:
            for key in self.dateFileLayersReestr.keys(): 
                if self.dateFileLayersReestr[key]['qgisName'] == self.actLayer.name() and self.dateFileLayersReestr[key]['editable']:
                    self.actLayerInfo = self.dateFileLayersReestr[key]
                    self.btnbarExport.setEnabled(True)
                    self.btnbarExport.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
                    break
                else:
                    self.btnbarExport.setEnabled(False)
                    self.btnbarEditing.setEnabled(False)
                    self.btnbarExport.setCursor(QCursor(QtCore.Qt.ArrowCursor))
                    self.btnbarEditing.setCursor(QCursor(QtCore.Qt.ArrowCursor))
        else:
            self.actLayerInfo = None
            self.btnbarEditing.setEnabled(False)
            self.btnbarExport.setEnabled(False)
            self.btnbarExport.setCursor(QCursor(QtCore.Qt.ArrowCursor))
            self.btnbarEditing.setCursor(QCursor(QtCore.Qt.ArrowCursor))
    

    def legendLayerRemovedItem (self, layerId):
        if self.dateFileLayersReestr.has_key(layerId[0]):
            self.dateFileLayersReestr.pop(layerId[0], None)

        # Overwrite authentification file -------------------------------------
        with open(os.path.join(this_dir, 'layersReestr.json'), "w") as fileJSON:
            json.dump(self.dateFileLayersReestr, fileJSON)


    def selectedFeaturesLayer (self, features): 
        if len(self.actLayer.selectedFeatures()) > 0 and not self.actLayerInfo['editable']:
            self.btnbarEditing.setEnabled(True)
            self.btnbarEditing.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        else:
            self.btnbarEditing.setEnabled(False)
            self.btnbarEditing.setCursor(QCursor(QtCore.Qt.ArrowCursor))
        
    
    def openSettingDialog (self):
        self.menuset = MenuSettings()
        global MenuSettingsDialog
        MenuSettingsDialog = self.menuset
        self.menuset.show()
        # self.sd.exec_()


    def checkFolderAccount (self):
        listIdAccount = map(lambda x : x['id'], self.dataFileJSON)
        listExistFoldersU = [filename for filename in os.listdir(OBJECTS_PATH) if os.path.isdir(os.path.join(OBJECTS_PATH,filename))]
        listExistFolders = map(lambda x : int(x), listExistFoldersU)

        listDifference = list(set(listIdAccount)-set(listExistFolders))
        if len(listDifference) > 0:
            map(lambda x : os.mkdir(os.path.join(OBJECTS_PATH, str(x))), listDifference)


    def readAuthentificationJson (self):
        with open(os.path.join(this_dir, 'authentification.json'), "r") as fileJSON:
            self.dataFileJSON = json.load(fileJSON)

        if len(self.dataFileJSON) > 0 and self.treeWidget.topLevelItemCount() == 0:
            self.createTree()
        elif len(self.dataFileJSON) > 0:
            self.createTree()
        elif len(self.dataFileJSON) == 0:
            self.removeTree()
        self.btnbarImport.setEnabled(False)
        self.btnbarImport.setCursor(QCursor(QtCore.Qt.ArrowCursor))

    
    def readLayerReestrJson (self):
        with open(os.path.join(this_dir, 'layersReestr.json'), "r") as fileJSON:
            self.dateFileLayersReestr = json.load(fileJSON)
        
        self.actLayer = iface.activeLayer()

        if self.actLayer and self.dateFileLayersReestr.has_key(self.actLayer.id()):
            self.actLayerInfo = self.dateFileLayersReestr[self.actLayer.id()]


    def setEnabledWidget (self, enabled):
        # print(self.btnbarImport.enabled)
        # self.btnbarExport.setEnabled(enabled)
        self.btnbarImport.setEnabled(enabled)
        self.btnbarSettings.setEnabled(enabled)
        self.btnbarRefresh.setEnabled(enabled)

        # self.btnbarEditing.setEnabled(enabled)
        self.treeWidget.setEnabled(enabled)
        
        if enabled:
            self.btnbarImport.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
            self.btnbarSettings.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
            self.btnbarRefresh.setCursor(QCursor(QtCore.Qt.PointingHandCursor))

            iface.legendInterface().currentLayerChanged.connect(self.legendLayerChanged)
            self.legendLayerChanged()
        else:
            self.btnbarExport.setEnabled(enabled)
            self.btnbarEditing.setEnabled(enabled)
            self.btnbarImport.setCursor(QCursor(QtCore.Qt.ArrowCursor))
            self.btnbarExport.setCursor(QCursor(QtCore.Qt.ArrowCursor))
            self.btnbarSettings.setCursor(QCursor(QtCore.Qt.ArrowCursor))
            self.btnbarRefresh.setCursor(QCursor(QtCore.Qt.ArrowCursor))
            self.btnbarEditing.setCursor(QCursor(QtCore.Qt.ArrowCursor))
            try:
                iface.legendInterface().currentLayerChanged.disconnect(self.legendLayerChanged)
            except:
                pass


    def createIdinLayerReestr (self, layerID, qgisName, citorusID, editable, typeLayer, rasterID, number_editObj, folderPath, number_account):
        with open(os.path.join(this_dir, 'layersReestr.json'), "r") as fileLayerReestr:
            fileReestr = json.load(fileLayerReestr)

        fileReestr[layerID] = {}
        fileReestr[layerID]['qgisName'] = qgisName
        fileReestr[layerID]['citorusID'] = citorusID
        fileReestr[layerID]['editable'] = editable
        fileReestr[layerID]['type'] = typeLayer
        fileReestr[layerID]['rasterID'] = rasterID
        fileReestr[layerID]['number_editObj'] = number_editObj
        fileReestr[layerID]['folderPath'] = folderPath
        fileReestr[layerID]['number_account'] = number_account
        
        with open(os.path.join(this_dir, 'layersReestr.json'), "w") as fileLayerReestr:
            json.dump(fileReestr, fileLayerReestr)

        self.dateFileLayersReestr = fileReestr



    ################ Modal window ######################
    def showInfoDialogPopup (self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        
        infoText = ''
        for info in range(len(self.selectedItemsDesc)):
            infoText+=self.selectedItemsDesc[info]+'\n'
        msg.setText(infoText)
        msg.setWindowTitle("Информация".decode('utf8'))
        msg.setStandardButtons(QMessageBox.Close)
        msg.exec_()

    
    def showWarningDialogHttpConnection (self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        
        msg.setText('Сервис недоступен'.decode('utf8'))
        msg.setWindowTitle("Предупреждение".decode('utf8'))
        msg.setStandardButtons(QMessageBox.Close)
        msg.exec_()


    def showInfoDialogImportRasterLayer (self, georef, ungeoref):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        
        msg.setText("Кол-во геопривязанных изображений: ".decode('utf8') + str(georef) + " .\nКол-во негеопривязанных изображений: ".decode('utf8') + str(ungeoref) + " .")
        msg.setWindowTitle("Импорт растрового слоя".decode('utf8'))
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()


    def showInfoDialogEditingLayer (self):
        if iface.activeLayer().type() == 1:
            self.showInfoDialogEditingRasterLayer()
        else:
            msg = QMessageBox.question(iface.mainWindow(), 'Информационное окно'.decode('utf8'), 
                     'Взять объекты на редактирование?'.decode('utf8'), QMessageBox.Yes, QMessageBox.No)
            if msg == QtGui.QMessageBox.Yes:
                VectorLayerEditing(self.actLayerInfo, self.account)


    def showInfoDialogEditingLayerBlock (self, layer):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        
        msg.setText("Объект доступен для редактирования на слое «CITORUS – ".decode('utf8') + self.editingLayerName + "» ".decode('utf8') )
        msg.setWindowTitle("Блокирование объектов".decode('utf8'))
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()


    def showInfoDialogEditingRasterLayer(self):
        msg = QMessageBox.question(iface.mainWindow(), 'Информационное окно'.decode('utf8'), 
                 'Разрешить вносить изменения в растровый слой?'.decode('utf8'), QMessageBox.Yes, QMessageBox.No)
        if msg == QtGui.QMessageBox.Yes:
            RasterLayerEditing(self.actLayerInfo, self.account)
        else:
            pass


    def showInfoDialogExportLayer (self):
        msg = QMessageBox.question(iface.mainWindow(), 'Информационное окно'.decode('utf8'), 
                'Вы желаете экспортировать отредактированные Объекты ('.decode('utf8') + self.actLayerInfo['qgisName'] + ') в CITORUS?'.decode('utf8'), 
                QMessageBox.Yes, QMessageBox.No)
        if self.actLayerInfo['type'] == 'vectorLayer' and msg == QtGui.QMessageBox.Yes:
            VectorLayerExport(self.actLayerInfo, self.account)
        elif self.actLayerInfo['type'] == 'rasterLayer' and msg == QtGui.QMessageBox.Yes:
            # self.exportRasterLayer()
            RasterLayerExport(self.actLayerInfo, self.account)


    def showInfoDialogExport (self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        
        msg.setText("Данные отправлены на сервер.\nКол-во отправленных объектов: ".decode('utf8') + str(len(self.requestExport)) + ".") #str(self.requestExport.text.count("true"))
        # msg.setText("Данные отправлены на сервер.\nКол-во отправленных объектов: ".decode('utf8') + str(self.requestExport.text.count("true")) + ".\nКол-во неотправленных объектов: ".decode('utf8') + str(self.requestExport.text.count("false")) + ".")
        msg.setWindowTitle("Экспорт".decode('utf8'))
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()


    def showInfoDialogExportRaster (self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        
        msg.setText("Данные отправлены на сервер.".decode('utf8')) #str(self.requestExport.text.count("true"))
        # msg.setText("Данные отправлены на сервер.\nКол-во отправленных объектов: ".decode('utf8') + str(self.requestExport.text.count("true")) + ".\nКол-во неотправленных объектов: ".decode('utf8') + str(self.requestExport.text.count("false")) + ".")
        msg.setWindowTitle("Экспорт".decode('utf8'))
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()


    def showErrorDialogExport (self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        
        msg.setText("Произошла ошибка".decode('utf8'))
        msg.setWindowTitle("Экспорт".decode('utf8'))
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        self.btnbarExport.setEnabled(False)
        self.btnbarEditing.setEnabled(False)
        self.btnbarExport.setCursor(QCursor(QtCore.Qt.ArrowCursor))
        self.btnbarEditing.setCursor(QCursor(QtCore.Qt.ArrowCursor))



    ################ Create tree #######################
    def getRequests (self):
        # Account selection ---------------------------------------------------
        for item in range(len(self.dataFileJSON)):
            if self.dataFileJSON[item]["selected"] == True :
                self.account = self.dataFileJSON[item]
        self.readLayerReestrJson()       

        # Get request ---------------------------------------------------------
        
        # self.request = requests.get( self.account["url"] , auth=HTTPDigestAuth( self.account["login"] , self.account["password"]))
        # self.request = self.__request( self.account["url"] , 'GET')
        self.request = Request().request(self.account["url"] , "GET", timeout = 30)
        
        self.requestJSON = self.request#.json()
        # self.requestJSON = [{"id":"fcec5dd740bf0feeb59b3b28e37e01e41","name":"Карта рельефа (2)","parent":""},{"id":"a023e898eb8f8823d36031b738d01e969","name":"SRTM","parent":""},{"id":"ff299c8bbd9ae05e5f723682747646172","name":"Данные об арендаторах","parent":"c03e99ecb58fbb6c556f8d0d28285da26"},{"id":"a880394d022bb1069d98fea7058ae4e98","name":"Договора аренды","parent":"c03e99ecb58fbb6c556f8d0d28285da26"},{"id":"d64a895dade4990fd86cf6769f7e07768","name":"Борис Р.","parent":""},{"id":"b5ab8c398d8ac149f16ea19e24cd7700c","name":"БорисТ","parent":""},{"id":"b79ce845f248d3e38cfc07c733d070295","name":"Выделы","parent":"d26e7a17b5d96a9b0608043130ccadcc2"},{"id":"d26e7a17b5d96a9b0608043130ccadcc2","name":"Лесоустроительные данные","parent":""},{"id":"c03e99ecb58fbb6c556f8d0d28285da26","name":"Данные лесопользования","parent":""},{"id":"cbab76267735f88f45def38f3bcbf8aac","name":"Природные ресурсы ДВ","parent":""},{"id":"f48a8ed54dc72ceb98393a25f87160adc","name":"Лесные декларации","parent":"c03e99ecb58fbb6c556f8d0d28285da26"},{"id":"f17d3d5d57f7709a864a8b81c58713bea","name":"Лесохозяйственные дороги (ХК)","parent":"e1b4842eff61194222504f21a29ec7d5c"},{"id":"e1b4842eff61194222504f21a29ec7d5c","name":"Лесовозные дороги","parent":""},{"id":"c30f1bcca2ff2a2c40f9fa8612383ff55","name":"Лесохозяйственные дороги (ПК)","parent":"e1b4842eff61194222504f21a29ec7d5c"},{"id":"a8adcaffe150977e244f3d9beacf2c0ec","name":"Объекты инфраструктуры","parent":"c03e99ecb58fbb6c556f8d0d28285da26"},{"id":"f29120b9934a738479762767f19bbe8b0","name":"Отчеты об использовании лесов","parent":"c03e99ecb58fbb6c556f8d0d28285da26"},{"id":"bbe8095127c526512cdb24d2947d64d8e","name":"Кварталы","parent":"d26e7a17b5d96a9b0608043130ccadcc2"},{"id":"e252fa80cd41a1732317b602338b225b2","name":"Участковые лесничества","parent":"d26e7a17b5d96a9b0608043130ccadcc2"},{"id":"cb230acdd28b078f71e980cbafa8ce6e1","name":"Лесничества","parent":"d26e7a17b5d96a9b0608043130ccadcc2"},{"id":"dee2d74aabbe7e59326618a00cec01171","name":"Таксационные описания","parent":""}]
        

    def listParentsChildren (self):
        # List with parent elements 0 order -----------------------------------
        self.listParentElements = []

        # Dictionary with parents and their children --------------------------
        self.dictChildrenByParentsID = {}

        for element in range(len(self.requestJSON)):
		    if self.requestJSON[element]['parent'] == '':
				self.listParentElements.append(self.requestJSON[element])
		    else:
				if not self.dictChildrenByParentsID.has_key(self.requestJSON[element]['parent']):
				    self.dictChildrenByParentsID[self.requestJSON[element]['parent']] = []
				self.dictChildrenByParentsID[self.requestJSON[element]['parent']].append(self.requestJSON[element])

    
    def createTreeWidgetItem (self, item):
        treeItem = QTreeWidgetItem()
        # treeItem.setFlags(Qt.NoItemFlags)
        treeItem.setText(0, item['name'])
        treeItem.setData(1, 1, item['id'])         # field objectId
        if item.has_key('desc'):
            treeItem.setData(1, 4, [u'Описание: ' + item['desc'], u'Автор: ' + item['owner'], u'Дата создания: ' + item['dateCreate']])       # field description
        else:
            treeItem.setData(1, 4, ['         Нет информации'.decode('utf8')])                       # field description

        # Set icon for layers or folders --------------------------------------
        if item.has_key('layerType') and item['layerType'] == 'raster':
            treeItem.setIcon(0,QIcon(os.path.join(ICONS_PATH, "raster_layer.svg")))
            treeItem.setData(1, 2, 'rasterlayer')
        elif not item.has_key('geometry'):
            treeItem.setIcon(0,QIcon(os.path.join(ICONS_PATH, "group.png")))
            treeItem.setData(1, 2, 'folder')
        elif item['geometry']['features'] == []:
            treeItem.setIcon(0,QIcon(os.path.join(ICONS_PATH, "vector_layer_not_found.svg")))
            treeItem.setData(1, 2, 'layernotfound')
        else:
            treeItem.setData(1, 2, 'layer')
            if item['geometry']['features'][0]['geometry']['type'] == 'Point':
                treeItem.setIcon(0,QIcon(os.path.join(ICONS_PATH, "vector_layer_point.svg")))
            elif item['geometry']['features'][0]['geometry']['type'] == 'Polygon' or item['geometry']['features'][0]['geometry']['type'] == 'MultiPolygon':
                treeItem.setIcon(0,QIcon(os.path.join(ICONS_PATH, "vector_layer_polygon.svg")))
            else:
                treeItem.setIcon(0,QIcon(os.path.join(ICONS_PATH, "vector_layer_line.svg")))     

        # Create children for the tree item -----------------------------------
        if self.dictChildrenByParentsID.has_key(item['id']):
            for obj in range(len(self.dictChildrenByParentsID[item['id']])):
                element = self.dictChildrenByParentsID[item['id']][obj]
                child = self.createTreeWidgetItem(element)
                treeItem.addChild(child)
            return treeItem
        else: 
            return treeItem

    
    def treeItemSelected(self):
        # print self.treeWidget.selectedItems()[0].text(0)
        # print self.treeWidget.selectedItems()[0].data(1,1)
        # print self.treeWidget.selectedItems()[0].childCount()
        if len(self.treeWidget.selectedItems()) > 0:
            self.selectedItemsName = self.treeWidget.selectedItems()[0].text(0)
            self.selectedItemsId = self.treeWidget.selectedItems()[0].data(1,1)
            self.selectedItemsFolderLayer = self.treeWidget.selectedItems()[0].data(1,2)         
            self.selectedItemsDesc = self.treeWidget.selectedItems()[0].data(1,4)

        if len(self.treeWidget.selectedItems()) > 0 and (self.selectedItemsFolderLayer == 'layer' or self.selectedItemsFolderLayer == 'rasterlayer'):
            self.btnbarImport.setEnabled(True)
            self.btnbarImport.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        else:
            self.btnbarImport.setEnabled(False)
            self.btnbarImport.setCursor(QCursor(QtCore.Qt.ArrowCursor))


    def addChildLoading (self):
        self.locked_item = QTreeWidgetItem(["loading..."])
        self.treeWidget.addTopLevelItem(self.locked_item)
    
    def createTree (self):
        self.setEnabledWidget(False)
        self.spinner.setVisible(True)
        try:
		    self.getRequests()
		    self.listParentsChildren()
		    self.removeTree()

		    for element in range(len(self.listParentElements)):
		    	parent = self.createTreeWidgetItem(self.listParentElements[element])	
		    	self.treeWidget.addTopLevelItem(parent)
        except Exception as e:
            print (e)
            self.showWarningDialogHttpConnection()
        
        self.spinner.setVisible(False)
        self.setEnabledWidget(True)


    def removeTree (self):
        self.treeWidget.clear()
    


    ################ Refresh #######################
    def clickRefresh (self):
        self.removeTree()

        with open(os.path.join(this_dir, 'authentification.json'), "r") as fileJSON:
            self.dataFileJSON = json.load(fileJSON)
        if len(self.dataFileJSON) > 0:
            self.createTree()
        self.btnbarImport.setEnabled(False)



    ################ Popup window ##################
    def openInfoPopup (self, position):
        popupMenu = QMenu()

        if self.selectedItemsFolderLayer == 'layer' or self.selectedItemsFolderLayer == 'rasterlayer':
            popupInfo = QAction(self)
            popupInfo.setText("Информация".decode('utf8'))
            popupInfo.setIcon(QIcon(os.path.join(ICONS_PATH, 'info.svg')))
            
            popupMenu.addAction(popupInfo)
            popupInfo.triggered.connect(self.showInfoDialogPopup)

        if self.selectedItemsFolderLayer == 'layer':
            popupPreview = QAction(self)
            popupPreview.setText("Предварительный просмотр".decode('utf8'))
            popupPreview.setIcon(QIcon(os.path.join(ICONS_PATH, 'preview.svg')))

            popupMenu.addAction(popupPreview)
            popupPreview.triggered.connect(self.openPreview)
            
        
        popupMenu.exec_(self.treeWidget.viewport().mapToGlobal(position))

    

    ################ Preview window ################
    def downloadPreview (self, objId):
        # Get request ---------------------------------------------------------
        urlServer = self.account["url"]
        url = urlServer.split('getLayers')[0] + 'getPreview?id=' + objId
        requestPreview = requests.get(url, auth=HTTPDigestAuth( self.account["login"] , self.account["password"]), stream=True)

        # Save data from request ----------------------------------------------
        with open(os.path.join(OBJECTS_PATH, 'getPreview'), 'wb') as filePreview:
            filePreview.write(requestPreview.content)
    

    def clearMapLayerRegistry (self):
        myLayers = QgsMapLayerRegistry.instance().mapLayers()
        for elem in myLayers.keys():
            if elem.count('Preview') > 0:
                QgsMapLayerRegistry.instance().removeMapLayer(myLayers[elem])

    
    def readFilePreview (self):
        with open(os.path.join(OBJECTS_PATH, 'getPreview'), "r") as filePreview:
            self.dataFilePreview = json.load(filePreview)
        
        previewListFeaturesAll = self.dataFilePreview["features"]

        self.previewListLayer = []
        listTypesGeometry = list(set(map(lambda x : x['geometry']['type'], self.dataFilePreview["features"])))
        for typeGeom in listTypesGeometry:
            previewListFeatures = [x for x in previewListFeaturesAll if x["geometry"]["type"] == typeGeom]
            self.previewListLayer.append(self.createLayerPreview(previewListFeatures))


    def createLayerPreview (self, listFeatures):
        featureType = listFeatures[0]["geometry"]["type"]
        previewLayer = QgsVectorLayer('%s?crs=EPSG:%s' % (featureType, str(4326)),
            "Preview", 
            "memory")

        pr = previewLayer.dataProvider()
        # Add fields to vector layer ------------------------------------------
        pr.addAttributes( [QgsField("name", QVariant.String)])
        previewLayer.updateFields()

        for elem in listFeatures:
            feature = QgsFeature()
            feature.setGeometry(
                QgsGeometry.fromWkt(
                    ogr.CreateGeometryFromJson(
                        json.dumps(elem["geometry"])
                    ).ExportToWkt()
                )
            )
            if elem["properties"].has_key("name"):
                feature.setAttributes([elem["properties"]["name"]])
            pr.addFeatures([feature])
        previewLayer.updateExtents()
        pLExtent = previewLayer.extent()
        nExt = QgsRectangle(pLExtent.xMinimum() - 0.01, pLExtent.yMinimum() - 0.01, pLExtent.xMaximum() + 0.01, pLExtent.yMaximum() + 0.01)
        previewLayer.setExtent(nExt)

        previewLayer.setCustomProperty("labeling", "pal")
        previewLayer.setCustomProperty("labeling/enabled", "true")
        previewLayer.setCustomProperty("labeling/fontFamily", "Arial")
        previewLayer.setCustomProperty("labeling/fontSize", "14")
        previewLayer.setCustomProperty("labeling/fieldName", "name")
        return previewLayer

    
    def addLayersToPreview (self):
        ####adm1 layer added
        self.adm1 = QgsVectorLayer(os.path.join(DATA_PATH, 'states/states.shp'), 'States_Preview', 'ogr')
        symbols = self.adm1.rendererV2().symbols()
        symbol = symbols[0]
        symbol.setColor(QColor.fromRgb(255,255,255))

        self.adm1.setCustomProperty("labeling", "pal")
        self.adm1.setCustomProperty("labeling/enabled", "true")
        self.adm1.setCustomProperty("labeling/fontFamily", "Arial")
        self.adm1.setCustomProperty("labeling/fontSize", "16")
        self.adm1.setCustomProperty("labeling/fieldName", "GN_NAME")
        self.adm1.setProviderEncoding(u'UTF-8')     # show cyrillic symbols
        # self.adm1.setCustomProperty("labeling/placement", "2")

        QgsMapLayerRegistry.instance().addMapLayers(self.previewListLayer, False)
        QgsMapLayerRegistry.instance().addMapLayers([self.adm1], False)

        try:
            self.myPreview.hide()
        except:
            pass

        serviceName = self.account["url"].split('/getLayers')[0].split('/')[-1]
        self.myPreview = PreviewCanvas(self.previewListLayer, self.adm1, serviceName, self.selectedItemsName)
        

    def openPreview (self):
        try:
            self.downloadPreview(self.selectedItemsId)
            self.clearMapLayerRegistry()    
            self.readFilePreview()    
            self.addLayersToPreview()
        except:
            self.showWarningDialogHttpConnection()


    def showInfoDialog (self, title):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        infoText = ''
        for info in range(len(self.selectedItemsDesc)):
            infoText+=self.selectedItemsDesc[info]+'\n'
        msg.setText(infoText)
        msg.setWindowTitle(title)
        msg.setStandardButtons(QMessageBox.Close)
        msg.exec_()
        


    ################ Import Layer ##################
    def importLayer (self):
        if self.selectedItemsFolderLayer == 'rasterlayer':
            RasterLayerImport(self.selectedItemsId, self.account)
        else:
            VectorLayerImport(self.selectedItemsId, self.account, self.treeWidget.selectedItems()[0].text(0))


    ################ Import Raster Layer ##################

    ################ Editing Raster Layer ##################
    
    ################ Editing Layer ################## 
    
    ################ Export Layer ##################

    ################ Export Raster Layer ##################
    
    # def changedSelectedItemQTreeWidget (self):
    #     root = self.treeWidget.topLevelItemCount()
    #     for item in range(root):
    #         self.treeWidget.topLevelItem(item).setSelected(False)
    #         if self.treeWidget.topLevelItem(item).data(1,1) == self.actLayerInfo['citorusID']:
    #             self.treeWidget.topLevelItem(item).setSelected(True)
    #         if self.treeWidget.topLevelItem(item).childCount() > 0:
    #             def recurseChild (parent):
    #                 if parent.childCount() > 0:
    #                     for child in range(parent.childCount()):
    #                         recurseChild (parent.child(child))
    #                 else:
    #                     parent.setSelected(False)
    #                     if parent.data(1,1) == self.actLayerInfo['citorusID']:
    #                         parent.setSelected(True)
    #             recurseChild (self.treeWidget.topLevelItem(item))




    # def mymouseDoubleClickEvent (self, event):
    #     print event
    #     if event.button() == QtCore.Qt.RightButton:
    #         print("right click !")

    # dict_a = [{'name': 'python', 'points': 10}, {'name': 'java', 'points': 8}]
    # map(lambda x : x['name'], dict_a) # Output: ['python', 'java']
