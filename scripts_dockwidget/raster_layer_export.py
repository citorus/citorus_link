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

from ..requests import api
from ..requests.auth import HTTPDigestAuth

from request import Request

from raster_layer_import import RasterLayerImport

this_dir = os.path.dirname(__file__)

class RasterLayerExport:

    def __init__(self, actLayerInfo, account):
        # Import files and block plugins

        self.account = account
        self.actLayerInfo = actLayerInfo

        self.actLayer = iface.activeLayer()

        objId = actLayerInfo['citorusID']
        layerName = actLayerInfo['qgisName'][:-17]
        
        # Folder path ---------------------------------------------------------
        self.main_path = this_dir.split('scripts_dockwidget')[0]
        self.objects_path = os.path.join(self.main_path, 'objects')
        self.obj_path = os.path.join(self.objects_path, str(account['id']), objId)

        # Files path ----------------------------------------------------------
        self.pathFileLayerExport = os.path.join(self.actLayerInfo['folderPath'], 'edit', 'layerEportRaster.json')
        self.pathFileLayerStyle = os.path.join(self.actLayerInfo['folderPath'], 'edit', 'sceneStyle.json')

        # Import CITORUS_Connect_dockwidget -----------------------------------
        from ..CITORUS_Connect import dockwidget

        dockwidget.spinner.setVisible(True)
        dockwidget.setEnabledWidget(False)
        while True:
            if dockwidget.spinner.isVisible(): 
                break
        try:
            self.saveStyleToQML()
            self.createJsonSceneStyle()
            self.checkGeoreferencing()
            self.putRequest()
            self.postRequestStyle()
            self.unblockExportLayer()
            self.deleteExportRasterFiles()
            RasterLayerImport(objId, account)
        except Exception as e:
            print (e)
            # self.showErrorDialogExport()

        dockwidget.spinner.setVisible(False)
        dockwidget.setEnabledWidget(True)

    
    def saveStyleToQML (self):
        layerPath = self.actLayer.dataProvider().dataSourceUri()
        if '\\' in layerPath: 
            resourseFile = layerPath.split('\\')[-1]
        else:
            resourseFile = layerPath.split('/')[-1]
        self.rasterName  = resourseFile[:-(len(resourseFile.split('.')[-1]) + 1)]
        self.actLayer.saveNamedStyle(os.path.join(self.actLayerInfo['folderPath'], 'edit', self.rasterName + '.qml'))
        

    def createJsonSceneStyle (self):
        import xml.etree.ElementTree as ET
        root = ET.parse(os.path.join(self.actLayerInfo['folderPath'], 'edit', self.rasterName + '.qml')).getroot()

        jsonRasterStyle = {}
        typeStyle = root.findall('pipe/rasterrenderer')[0].get('type')
        if typeStyle == "multibandcolor" or typeStyle == "singlebandgray":
            jsonRasterStyle['bands'] = root.find('pipe/rasterrenderer').attrib
            jsonRasterStyle['rasterrenderer'] = {}
            for child in root.find('pipe').getchildren():
                if child.tag != "rasterrenderer":
                    jsonRasterStyle[child.tag] = child.attrib
                else:
                    for band in root.find('pipe/rasterrenderer').getchildren():
                        if band.tag != "rasterTransparency":
                            jsonRasterStyle['rasterrenderer'][band.tag] = {}
                            for value in band.getchildren():
                                jsonRasterStyle['rasterrenderer'][band.tag][value.tag] = value.text

            jsonRasterStyle['blendMode'] = root.find('blendMode').text
        else:
            print ('Style not defined')
        
        self.dataFileRasterStyle = jsonRasterStyle
        
        # Write file for editing ----------------------------------------------
        with open(self.pathFileLayerStyle, "w") as fileLayerJSON:
            json.dump(jsonRasterStyle, fileLayerJSON)

        with open(os.path.join(self.actLayerInfo['folderPath'], 'getObj'), "r") as fileGetObjRaster:
            dataFileGetObjRaster = json.load(fileGetObjRaster)

        dataFileGetObjRaster = dataFileGetObjRaster['features'][0]
        dataFileGetObjRaster['properties']['layerID'] = self.actLayerInfo['citorusID']
        dataFileGetObjRaster['properties']['object']['aa57fc9b9c865a232a23f8877b3aa1352']['sceneStyle'] = jsonRasterStyle
        
        # Write file for editing ----------------------------------------------
        with open(self.pathFileLayerExport, "w") as fileLayerJSON:
            json.dump([dataFileGetObjRaster], fileLayerJSON)


    def checkGeoreferencing (self):
        from osgeo import gdal

        # rasterPath = None
        # if self.dateFileLayersReestr.has_key(self.actLayer.id()):
        #     myLayers = QgsMapLayerRegistry.instance().mapLayers()
        #     for key in myLayers.keys(): 
        #         if self.actLayer.name() == myLayers[key].name() and self.actLayer.id() != myLayers[key].id():
        #             rasterPath = myLayers[key].dataProvider().dataSourceUri()
        # else:
        #     rasterPath = self.actLayer.dataProvider().dataSourceUri()
            
        # if rasterPath is not None:
        #     rasterName = '.'.join(rasterPath.split('/')[-1].split('.')[:-1])
        #     rasterFolder = rasterPath.split('/' + rasterPath.split('/')[-1])[0]
        #     wldPath = os.path.join(rasterFolder, rasterName + '.wld')
        rasterPath = self.actLayer.dataProvider().dataSourceUri()
        if '\\' in rasterPath: 
			rasterNameFull = rasterPath.split('\\')[-1]
        else:
			rasterNameFull = rasterPath.split('/')[-1]
        rasterFolder = rasterPath.split(rasterNameFull)[0]

        # rasterFolder = rasterPath.split('/' + rasterPath.split('/')[-1])[0]
        # rasterNameFull = rasterPath.split('/')[-1]
        rasterName = rasterNameFull[:-(len(rasterNameFull.split('.')[-1])+1)]
        wldPath = os.path.join(rasterFolder, rasterName + '.wld')
        if os.path.isfile(wldPath):
            with open(wldPath, "r") as fileRasterGeoref:
                content = [x.strip() for x in fileRasterGeoref.readlines()]
                wld1 = float(content[0])  # pixel size in the x-direction in map units/pixel
                wld4 = float(content[3])  # pixel size in the y-direction in map units, almost always negative
                wld5 = float(content[4])  # x-coordinate of the center of the upper left pixel
                wld6 = float(content[5])  # y-coordinate of the center of the upper left pixel
                tiffHeight = self.actLayer.height()
                tiffWidth = self.actLayer.width()
                bboxBLy = wld6 + wld4 * tiffHeight
                bboxTRx = wld5 + wld1 * tiffWidth
                bbox = [wld5, bboxBLy, bboxTRx, wld6]
                print (bbox)
                new_file = os.path.join(self.actLayerInfo['folderPath'], 'edit', 'export.tif')
                self.exportRasterFile = new_file
                previous_file = self.actLayer.dataProvider().dataSourceUri()
                gdal.Translate( new_file, previous_file, format = 'GTiff', outputSRS = 'EPSG:4326', outputBounds = bbox)
        else:
            self.exportRasterFile = rasterPath
            
        # else:
        #     self.exportRasterFile = os.path.join(self.actLayerInfo['folderPath'], 'edit', self.actLayerInfo['qgisName'].split('.')[0] + '.tif')


    def putRequest (self):
        urlServer = self.account["url"]
        url = urlServer.split('getLayers')[0] + 'putObj/' + self.actLayerInfo['rasterID']
        with open(self.exportRasterFile,'rb') as data:
            files = {'data': data}
            req = api.put(url,  auth=HTTPDigestAuth(self.account["login"], self.account["password"]), files = files)
            # req = Request().request(url, 'PUT', files=files) 
            # req = Request().request(url, 'POST', params=files) 
            json_response = json.loads(req.content)
        if json_response['ok']:
            self.showInfoDialogExportRaster()
        else:
            print ('Error')
            self.showErrorDialogExport()


    def postRequestStyle (self):
        # Read export file ----------------------------------------------------
        with open(self.pathFileLayerExport, "r") as fileGetObj:
            dataFileExport = json.dumps(json.load(fileGetObj))

        # Post reqest ---------------------------------------------------------
        urlServer = self.account["url"]
        url = urlServer.split('getLayers')[0] + 'saveObj'
        jsonData={"data": dataFileExport }
        requestExport = Request().request(url, 'POST', params=jsonData) 
        print (requestExport)


    def unblockExportLayer (self):
        # Get request ---------------------------------------------------------
        urlServer = self.account["url"]
        url = urlServer.split('getLayers')[0] + 'unblockObj?layerID=' + self.actLayerInfo['citorusID'] + '&ids=[%22' + self.actLayerInfo['rasterID'] + '%22]'
        requestEditObj = Request().request(url, "GET")
        

    def deleteExportRasterFiles (self):
        # Remove raster layer from plugins ------------------------------------
        checkname = self.actLayer.name()
        myLayers = QgsMapLayerRegistry.instance().mapLayers()
        for key in myLayers.keys(): 
            if checkname == myLayers[key].name():
                QgsMapLayerRegistry.instance().removeMapLayer(myLayers[key])

        # Delete temp files for editing layer ---------------------------------
        try:
            dir_edit_path = os.path.join(self.actLayerInfo['folderPath'], 'edit')
            qml_file = self.actLayerInfo['number_editObj'].split('_editObj')[0] + '.qml'
            os.remove(self.pathFileLayerExport)                 # remove export file data
            os.remove(self.pathFileLayerStyle)                  # remove export file style
            os.remove(os.path.join(dir_edit_path, self.actLayerInfo['number_editObj']))     # remove editing file editObj
            os.remove(os.path.join(dir_edit_path, qml_file))    # remove export file qml
        except:
            pass

    
    def showInfoDialogExportRaster (self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)

        msg.setText("Данные отправлены на сервер.".decode('utf8')) #str(self.requestExport.text.count("true"))
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
        # self.btnbarExport.setEnabled(False)
        # self.btnbarEditing.setEnabled(False)
        # self.btnbarExport.setCursor(QCursor(QtCore.Qt.ArrowCursor))
        # self.btnbarEditing.setCursor(QCursor(QtCore.Qt.ArrowCursor))