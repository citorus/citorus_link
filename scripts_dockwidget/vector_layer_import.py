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

from PyQt4 import uic, Qt
from PyQt4.QtCore import *
from qgis.core import *
from qgis.utils import *


from request import Request

from make_fileJson_from_getObj_for_vector_layer import MakeFileJsonFromGetObjForVectorLayer

this_dir = os.path.dirname(__file__)

class VectorLayerImport:

    def __init__(self, objId, account, layerName):
        # Import files and block plugins

        self.account = account
        self.objId = objId
        self.layerName = layerName
        
        # Folder path ---------------------------------------------------------
        self.main_path = this_dir.split('scripts_dockwidget')[0]
        objects_path = os.path.join(self.main_path, 'objects')
        self.obj_path = os.path.join(objects_path, str(account['id']), objId)
        
        # Files path ----------------------------------------------------------
        pathFileGetObj = os.path.join(self.obj_path, 'getObj')
        pathFileLayerJson = os.path.join(self.obj_path, 'layer.json')

        # Import CITORUS_Connect_dockwidget -----------------------------------
        from ..CITORUS_Connect import dockwidget
        self.dockwidget = dockwidget
        dockwidget.spinner.setVisible(True)
        dockwidget.setEnabledWidget(False)
        while True:
            if dockwidget.spinner.isVisible(): 
                break
        try:
            self.downloadGetObj(pathFileGetObj)
            MakeFileJsonFromGetObjForVectorLayer(False, pathFileGetObj, pathFileLayerJson)
            self.readLayerJSON(pathFileLayerJson)
        except Exception as e:
            print (e)

        dockwidget.spinner.setVisible(False)
        dockwidget.setEnabledWidget(True)

    
    def downloadGetObj (self, pathFileGetObj):
        # Create new folder ---------------------------------------------------
        if not os.path.isdir(self.obj_path):
            os.mkdir(self.obj_path)
            os.mkdir(os.path.join(self.obj_path, 'edit'))

        # Get request ---------------------------------------------------------
        urlServer = self.account["url"]
        url = urlServer.split('getLayers')[0] + 'getObj?id=' + self.objId
        requestGetObj = Request().request(url, "GET")
        
        # Save data from request ----------------------------------------------
        with open(pathFileGetObj, 'wb') as fileGetObj:
            fileGetObj.write(json.dumps(requestGetObj))


    def readLayerJSON (self, fileJsonName):
        # Read file layer JSON ------------------------------------------------      
        with open(fileJsonName, "r") as fileLayerJson:
            dataFileLayerJSON = json.load(fileLayerJson)

        # Read file layers reestr ---------------------------------------------    
        with open(os.path.join(self.main_path, 'layersReestr.json'), "r") as fileJSON:
            dateFileLayersReestr = json.load(fileJSON)
        
        # Remove dublicate layer ----------------------------------------------   
        myLayers = QgsMapLayerRegistry.instance().mapLayers()
        for lyrId in myLayers.keys():
            if dateFileLayersReestr.has_key(lyrId):
                if self.objId == dateFileLayersReestr[lyrId]['citorusID'] and not dateFileLayersReestr[lyrId]['editable']:
                    QgsMapLayerRegistry.instance().removeMapLayer(myLayers[lyrId])
        
        # Get all objects and types of geometry from dataFileLayerJSON --------
        listFeaturesAll = dataFileLayerJSON["features"]
        listTypesGeometry = list(set(map(lambda x : x['geometry']['type'], dataFileLayerJSON["features"])))
   
        # Create layer for each types of geometry in a primitive --------------     
        for typeGeom in listTypesGeometry:
            layerListFeatures = [x for x in listFeaturesAll if x["geometry"]["type"] == typeGeom]
            self.createVectorLayer(layerListFeatures)

        # Remove layer json ---------------------------------------------------  
        os.remove(fileJsonName)


    def createVectorLayer (self, listFeatures):    
        # Create vertor layer and add to reestr -------------------------------    
        featureType = listFeatures[0]["geometry"]["type"]
        vectorLayer = QgsVectorLayer('%s?crs=EPSG:%s' % (featureType, str(4326)), self.layerName, "memory") 
        self.dockwidget.createIdinLayerReestr(vectorLayer.id(), self.layerName, self.objId, False, 'vectorLayer', None, False, self.obj_path, str(self.account["id"]))

        # It's need. But i don't know why? ------------------------------------
        pr = vectorLayer.dataProvider()

        # Add fields to vector layer ------------------------------------------
        fields = map(lambda x : QgsField(x, QVariant.String), listFeatures[0]["properties"])
        pr.addAttributes(fields)
        vectorLayer.updateFields()

        # Add feture (with geometry and attributes) to vector layer -----------
        for elem in listFeatures:
            feature = QgsFeature()
            feature.setGeometry(
                QgsGeometry.fromWkt(
                    ogr.CreateGeometryFromJson(
                        json.dumps(elem["geometry"])
                    ).ExportToWkt()
                )
            )
            attributes = []
            for x in listFeatures[0]["properties"]:
                if elem["properties"].has_key(x):
                    attributes.append(elem["properties"][x])
                else:
                    attributes.append("")
            feature.setAttributes(attributes)
            pr.addFeatures([feature])
            
        vectorLayer.updateExtents()

        # Add vector layer to the map -----------------------------------------
        QgsMapLayerRegistry.instance().addMapLayer(vectorLayer)

        # Block editing layer -------------------------------------------------
        vectorLayer.setReadOnly()

