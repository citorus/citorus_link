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

from PyQt4 import uic, Qt
from qgis.core import *
from qgis.utils import *
from PyQt4.QtGui import *

from request import Request

this_dir = os.path.dirname(__file__)

class RasterLayerImport:

    def __init__(self, objId, account):
        # Import files and block plugins

        self.account = account
        self.objId = objId
        
        # Folder path ---------------------------------------------------------
        self.main_path = this_dir.split('scripts_dockwidget')[0]
        self.objects_path = os.path.join(self.main_path, 'objects')
        self.obj_path = os.path.join(self.objects_path, str(account['id']), objId)

        # Import CITORUS_Connect_dockwidget -----------------------------------
        from ..CITORUS_Connect import dockwidget
        self.dockwidget = dockwidget
        dockwidget.spinner.setVisible(True)
        dockwidget.setEnabledWidget(False)
        while True:
            if dockwidget.spinner.isVisible(): 
                break
        try:
            self.downloadGetObj(objId)
            self.removeDuplicateRasters()
            self.readGetObjectRaster()
        except Exception as e:
            print (e)

        dockwidget.spinner.setVisible(False)
        dockwidget.setEnabledWidget(True)

    
    def downloadGetObj (self, objId):
        # Create new folder ---------------------------------------------------
        if not os.path.isdir(self.obj_path):
            os.mkdir(self.obj_path)
            os.mkdir(os.path.join(self.obj_path, 'edit'))

        # Get request ---------------------------------------------------------
        urlServer = self.account["url"]
        url = urlServer.split('getLayers')[0] + 'getObj?id=' + objId
        requestGetObj = Request().request(url, "GET")
        
        # Save data from request ----------------------------------------------
        with open(os.path.join(self.obj_path, 'getObj'), 'wb') as fileGetObj:
            fileGetObj.write(json.dumps(requestGetObj))


    def removeDuplicateRasters (self):
        # Read authentification Json ------------------------------------------    
        with open(os.path.join(self.main_path, 'authentification.json'), "r") as fileJSON:
            dataFileAuthentificationJSON = json.load(fileJSON)

        # Get list account with the same url ----------------------------------   
        listAccount = [str(x['id']) for x in dataFileAuthentificationJSON if x['url'] == self.account['url']]
        
        # Read file layers reestr ---------------------------------------------    
        with open(os.path.join(self.main_path, 'layersReestr.json'), "r") as fileJSON:
            dateFileLayersReestr = json.load(fileJSON)

        # Remove dublicate layer ----------------------------------------------   
        myLayers = QgsMapLayerRegistry.instance().mapLayers()
        for lyrId in myLayers.keys():
            if dateFileLayersReestr.has_key(lyrId):
                if self.objId == dateFileLayersReestr[lyrId]['citorusID'] and (not dateFileLayersReestr[lyrId]['editable']) and dateFileLayersReestr[lyrId]['number_account'] in listAccount:
                    QgsMapLayerRegistry.instance().removeMapLayer(myLayers[lyrId])


    def getCoordinatesFromRastrPng (self, d): 
        if "type" in d.keys(): 
            if d["type"] != "Polygon": 
                if "geometry" in d.keys(): 
                    self.getCoordinatesFromRastrPng(d["geometry"]) 
                elif "features" in d.keys(): 
                    self.getCoordinatesFromRastrPng(d["features"][0]) 
                else: 
                    return Exception("Недопустимый формат файла".decode('utf8')) 
            else: 
                self.rasterCoords = d["coordinates"][0]

    
    def readGetObjectRaster (self):
        with open(os.path.join(self.obj_path, 'getObj'), "r") as fileGetObjRaster:
            dataFileGetObjRaster = json.load(fileGetObjRaster)

        def putBarBack():
            iface.messageBar().clearWidgets() 
            iface.messageBar().close()

        # Close yellow banner -------------------------------------------------
        iface.messageBar().widgetAdded.connect(putBarBack)

        # For each png create lyr with georeferencing -------------------------
        numberGeoref = 0
        numberUngeoref = 0
        for feat in dataFileGetObjRaster["features"]:
            self.getCoordinatesFromRastrPng(feat)
            featCoords = self.rasterCoords 
            if len(featCoords) > 0:     # Show info about the number of georeferenced objs
                numberGeoref +=1
            else: 
                numberUngeoref +=1
            featId = feat["properties"]["_id"]
            for key in feat["properties"]["object"].keys():
                if key != "type":
                    sceneName = feat["properties"]["object"][key]["sceneName"]
                    sceneQuickLook = feat["properties"]["object"][key]["sceneQuickLook"]
                    pngName = sceneQuickLook.split('/')[-1]
            self.createPNG(sceneQuickLook, pngName)
            self.createWLDFile(featCoords, pngName)  # georeferencing file for png
            self.createRasterLayer(pngName, sceneName, featId)

        # Enabled plugins and close yellow banner -----------------------------
        iface.messageBar().widgetAdded.disconnect(putBarBack)
        
        # Show info about the number of georeferenced objs --------------------
        self.showInfoDialogImportRasterLayer(numberGeoref,numberUngeoref)
        # print ('showInfoDialogImportRasterLayer',numberGeoref,numberUngeoref)


    def createPNG (self, urlPng, pngName):
        # Get request ---------------------------------------------------------
        urlServer = self.account["url"]
        url = urlServer.split('/citorusConnect')[0] + urlPng
        requestGetPng = Request().request(url, "GETRaster")

        # Save data from request ----------------------------------------------
        with open(os.path.join(self.obj_path, pngName), 'wb') as fileGetPng:
            fileGetPng.write(requestGetPng)
    

    def createWLDFile (self, coords, pngName):
        fileName = pngName[:-(len(pngName.split('.')[-1])+1)]

        # Get png size from QgsRasterLayer ------------------------------------
        rasterLayerWLD = QgsRasterLayer(os.path.join(self.obj_path, pngName))
        pngHeight = rasterLayerWLD.height()
        pngWidth = rasterLayerWLD.width()
        QgsMapLayerRegistry.instance().addMapLayer(rasterLayerWLD, False)
        QgsMapLayerRegistry.instance().removeMapLayer(rasterLayerWLD)

        # Calculate wld file parameters by coords -----------------------------
        wld1 = (coords[1][0] - coords[0][0])/pngWidth       # pixel size in the x-direction in map units/pixel
        wld2 = 0                                            # rotation about y-axis
        wld3 = 0                                            # rotation about x-axis
        wld4 = -(coords[3][1] - coords[0][1])/pngHeight     # pixel size in the y-direction in map units, almost always negative
        wld5 = coords[3][0]                                 # x-coordinate of the center of the upper left pixel
        wld6 = coords[3][1]                                 # y-coordinate of the center of the upper left pixel

        wld = str(wld1) + '\n' + str(wld2) + '\n' + str(wld3) + '\n' + str(wld4) + '\n' + str(wld5) + '\n' + str(wld6)
            
        # Save data in wld file -----------------------------------------------
        with open(os.path.join(self.obj_path, fileName + '.wld'), 'wb') as fileGetObjRasterWLD:
            fileGetObjRasterWLD.write(wld)


    def createRasterLayer (self, pngName, sceneName, rasterId):
        # Create raster layer and add to reestr ------------------------------- 
        layer = QgsRasterLayer(os.path.join(self.obj_path, pngName), sceneName + ' - предпросмотр'.decode('utf8'))
        self.dockwidget.createIdinLayerReestr (layer.id(), sceneName + ' - предпросмотр'.decode('utf8'), self.objId, False, 'rasterLayer', rasterId, None, self.obj_path, str(self.account['id']))

        # Set CRS -------------------------------------------------------------
        CRS = QgsCoordinateReferenceSystem()
        CRS.createFromSrid(4326) #EPSG = 4326
        layer.setCrs(CRS)

        # Add layer to QGIS --------------------------------------------------- 
        QgsMapLayerRegistry.instance().addMapLayer(layer)



    def showInfoDialogImportRasterLayer (self, georef, ungeoref):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        
        # msg.setText("Кол-во геопривязанных изображений: ".decode('utf8') + str(georef) + " .\nКол-во негеопривязанных изображений: ".decode('utf8') + str(ungeoref) + " .")
        msg.setText("Кол-во импортированных изображений: ".decode('utf8') + str(georef + ungeoref) + ".")
        msg.setWindowTitle("Импорт растрового слоя".decode('utf8'))
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()