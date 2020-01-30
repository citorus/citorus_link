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
import json, datetime
from osgeo import ogr

from PyQt4 import uic, Qt
from PyQt4.QtCore import *
from qgis.core import *
from qgis.utils import *


from request import Request

from make_fileJson_from_getObj_for_vector_layer import MakeFileJsonFromGetObjForVectorLayer


class VectorLayerEditing:

    def __init__(self, actLayerInfo, account):
        """Constructor."""

        self.account = account
        self.actLayerInfo = actLayerInfo
        
        serialEditObj = self.createSerialNumberEditObj()
        serialLayerEdit = 'layerEdit{}.json'.format(serialEditObj.split('editObj')[1])
        
        # Files path ----------------------------------------------------------
        pathFileGetObj = os.path.join(actLayerInfo['folderPath'], 'edit', serialEditObj)
        pathFileLayerJson = os.path.join(actLayerInfo['folderPath'], 'edit', serialLayerEdit)

        # Get current time (minutes) for editing layer name -------------------
        currentTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        editingLayerName = self.actLayerInfo['qgisName'] + ' ' + currentTime

        # Import CITORUS_Connect_dockwidget -----------------------------------
        from ..CITORUS_Connect import dockwidget
        self.dockwidget = dockwidget
        dockwidget.spinner.setVisible(True)
        dockwidget.setEnabledWidget(False)
        while True:
            if dockwidget.spinner.isVisible(): 
                break
        try:
            if self.downloadEditObj():
                # self.showInfoDialogEditingLayerBlock(self.editingLayerName)
                print ('showInfoDialogEditingLayerBlock Goood!')
                self.saveEditObj(pathFileGetObj)
                MakeFileJsonFromGetObjForVectorLayer(True, pathFileGetObj, pathFileLayerJson)
                self.createVectorLayer(pathFileLayerJson, editingLayerName, serialEditObj)
            else:
                # self.showInfoDialogEditingLayerBlock(self.editingLayerName)
                print ('showInfoDialogEditingLayerBlock')
        except Exception as e:
            print (e)

        dockwidget.spinner.setVisible(False)
        dockwidget.setEnabledWidget(True)

    
    def createSerialNumberEditObj (self):
        listExistFiles = [filename for filename in os.listdir(os.path.join(self.actLayerInfo['folderPath'], 'edit'))]

        i=0
        while True:
            if listExistFiles.count('editObj' + str(i)) == 0:
                return 'editObj{}'.format(i)
            else:
                i+=1


    def downloadEditObj (self):
        # Get request ---------------------------------------------------------
        urlServer = self.account["url"]
        listIdSelectedFeatures = map(lambda x : str(x["id"]), iface.activeLayer().selectedFeatures()) 
        url = urlServer.split('getLayers')[0] + 'blockObj?layerID=' + self.actLayerInfo['citorusID'] + '&ids=' + str(listIdSelectedFeatures).replace("'", '%22')
        self.requestEditObj = Request().request(url, "GET")

        if True:        # self.requestEditObj not block other users
            return True
        else:
            return False


    def saveEditObj (self, pathFileGetObj):
        # Save data from request ----------------------------------------------
        with open(pathFileGetObj, 'wb') as fileEditObj:
            fileEditObj.write(json.dumps(self.requestEditObj))


    def createVectorLayer (self, fileJsonName, editingLayerName, serialEditObj):  
        # Read file layer JSON and get features -------------------------------          
        with open(fileJsonName, "r") as fileLayerJson:
            dataFileLayerJSON = json.load(fileLayerJson)
        listFeatures = dataFileLayerJSON["features"] 

        # Create vertor layer and add to reestr -------------------------------    
        featureType = listFeatures[0]["geometry"]["type"]
        vectorLayer = QgsVectorLayer('%s?crs=EPSG:%s' % (featureType, str(4326)), editingLayerName, "memory")
  
        originLayer = self.actLayerInfo
        self.dockwidget.createIdinLayerReestr(vectorLayer.id(), editingLayerName, originLayer['citorusID'], True, 'vectorLayer', None, serialEditObj, originLayer['folderPath'], str(self.account["id"]))                               

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

        # Field "ID" block editing --------------------------------------------
        editFormConf = vectorLayer.editFormConfig()
        idx = vectorLayer.fields().indexFromName('id')
        editFormConf.setReadOnly(idx)

        # Add vector layer to the map -----------------------------------------
        QgsMapLayerRegistry.instance().addMapLayer(vectorLayer)

        # Block or start editing layer ----------------------------------------
        vectorLayer.startEditing()

        # Remove layer.json ---------------------------------------------------  
        os.remove(fileJsonName)
