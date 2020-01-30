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


from request import Request


class RasterLayerEditing:

    def __init__(self, actLayerInfo, account):
        # Import files and block plugins

        self.account = account
        self.actLayerInfo = actLayerInfo

        # Import CITORUS_Connect_dockwidget -----------------------------------
        from ..CITORUS_Connect import dockwidget
        self.dockwidget = dockwidget
        dockwidget.spinner.setVisible(True)
        dockwidget.setEnabledWidget(False)
        while True:
            if dockwidget.spinner.isVisible(): 
                break

        try:
            if self.downloadEditObjRaster():
                # self.showInfoDialogEditingLayerBlock(self.editingLayerName)
                print ('showInfoDialogEditingLayerBlock Good!')
                self.readEditObjRaster()
                self.saveEditObjRaster()
                self.createQmlSceneStyle()
                self.importTiff()
                self.createRasterLayer()
            else:
                # self.showInfoDialogEditingLayerBlock(self.editingLayerName)
                print ('showInfoDialogEditingLayerBlock')
        except Exception as e:
            print (e)

        dockwidget.spinner.setVisible(False)
        dockwidget.setEnabledWidget(True)


    def downloadEditObjRaster (self):
        # Get request ---------------------------------------------------------
        urlServer = self.account["url"]
        url = urlServer.split('getLayers')[0] + 'blockObj?layerID=' + self.actLayerInfo['citorusID'] + '&ids=[%22' + self.actLayerInfo['rasterID'] + '%22]'
        self.requestEditObj = Request().request(url, "GET")

        if True:        # self.requestEditObj not block other users
            return True
        else:
            return False


    def readEditObjRaster (self):
        propertiesObj = self.requestEditObj["features"][0]["properties"]["object"]

        for key in propertiesObj.keys():
            if key != "type":
                self.sceneStyle = propertiesObj[key]["sceneStyle"]
                self.sceneName = propertiesObj[key]["sceneName"]
                self.sceneUrl = propertiesObj[key]["scene"]
                self.sceneNameFile = self.sceneUrl.split('/')[-1]
                self.otherFileName = self.sceneNameFile[:-(len(self.sceneNameFile.split('.')[-1])+1)]
                self.serialEditObj = self.otherFileName + '_editObj'
      

    def saveEditObjRaster (self):
        # Save data from request ----------------------------------------------
        with open(os.path.join(self.actLayerInfo['folderPath'], 'edit', self.serialEditObj), 'wb') as fileEditObj:
            fileEditObj.write(json.dumps(self.requestEditObj))


    def createQmlSceneStyle (self):
        self.sceneStyle_path = None
        import xml.etree.ElementTree as ET
        
        if isinstance(self.sceneStyle, dict) and self.sceneStyle.has_key('bands'):
            styleXml = ET.Element('qgis')
            styleXml.attrib['version'] = "2.18.28"
            styleXml.attrib['minimumScale'] = "inf"
            styleXml.attrib['maximumScale'] = "1e+08"
            styleXml.attrib['hasScaleBasedVisibilityFlag'] = "0"

            pipeXml = ET.SubElement(styleXml, 'pipe')

            for tag in self.sceneStyle.keys():
                if tag == 'rasterrenderer':
                    rrtagXml = ET.SubElement(pipeXml, tag)
                    for x in self.sceneStyle['bands'].keys():
                        rrtagXml.attrib[x] = self.sceneStyle['bands'][x]
                    ET.SubElement(rrtagXml, 'rasterTransparency')
                    for key in self.sceneStyle[tag].keys():
                        contrastXml = ET.SubElement(rrtagXml, key)
                        for k in self.sceneStyle[tag][key].keys():
                            minmaxXml = ET.SubElement(contrastXml, k)
                            minmaxXml.text = str(self.sceneStyle[tag][key][k])
                elif tag == 'brightnesscontrast' or tag == 'huesaturation' or tag == 'rasterresampler':
                    tagXml = ET.SubElement(pipeXml, tag)
                    for attr in self.sceneStyle[tag].keys():
                        tagXml.attrib[attr] = self.sceneStyle[tag][attr]

            blendModeXml = ET.SubElement(styleXml, 'blendMode')
            if self.sceneStyle.has_key('blendMode'):
                blendModeXml.text = str(self.sceneStyle['blendMode'])
            else:
                blendModeXml.text = "0"

            # File name for raster style and save data to file --------------------
            fileStyleName = self.otherFileName + '_sceneStyle.qml'
            self.sceneStyle_path = os.path.join(self.actLayerInfo['folderPath'], 'edit', fileStyleName)

            treeStyleXml = ET.ElementTree(styleXml)
            treeStyleXml.write(open(self.sceneStyle_path, 'wb'))


    def importTiff (self):
        # Get request ---------------------------------------------------------
        urlServer = self.account["url"]
        url = urlServer.split('/citorusConnect')[0] + self.sceneUrl
        requestEditObjRaster = Request().request(url, "GETRaster")

        # Save data from request ----------------------------------------------
        with open(os.path.join(self.actLayerInfo['folderPath'], 'edit', self.sceneNameFile), 'wb') as fileGetObjRaster:
            fileGetObjRaster.write(requestEditObjRaster)
        
        
    def createRasterLayer (self):
        def putBarBack():
            iface.messageBar().clearWidgets() 
            iface.messageBar().close()

        # Close yellow banner -------------------------------------------------
        iface.messageBar().widgetAdded.connect(putBarBack)

        # Remove dublicate layer ----------------------------------------------   
        originLayer = self.actLayerInfo
        QgsMapLayerRegistry.instance().removeMapLayer(iface.activeLayer().id())

        # Create raster layer and add to reestr ------------------------------- 
        layer = QgsRasterLayer(os.path.join(originLayer['folderPath'], 'edit', self.sceneNameFile), self.sceneName + ' - редактирование'.decode('utf8'))
        self.dockwidget.createIdinLayerReestr (layer.id(), self.sceneName + ' - редактирование'.decode('utf8'), originLayer['citorusID'], True, 'rasterLayer', originLayer['rasterID'], self.serialEditObj, originLayer['folderPath'], str(self.account["id"]))
        
        # Set CRS -------------------------------------------------------------
        CRS = QgsCoordinateReferenceSystem()
        CRS.createFromSrid(4326) #EPSG = 4326
        layer.setCrs(CRS)

        # Set style for raster layer ------------------------------------------
        if self.sceneStyle_path is not None:
            layer.loadNamedStyle(self.sceneStyle_path)
            layer.triggerRepaint()
            iface.layerTreeView().refreshLayerSymbology(layer.id())
            os.remove(self.sceneStyle_path) 

        QgsMapLayerRegistry.instance().addMapLayer(layer)

        # Enabled plugins and close yellow banner -----------------------------
        iface.messageBar().widgetAdded.disconnect(putBarBack)
