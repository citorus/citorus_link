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
from PyQt4.QtCore import *
from qgis.core import *
from qgis.utils import *


from request import Request

from vector_layer_import import VectorLayerImport


class VectorLayerExport:

    def __init__(self, actLayerInfo, account):
        # Import files and block plugins

        self.account = account
        self.actLayerInfo = actLayerInfo

        objId = actLayerInfo['citorusID']
        layerName = actLayerInfo['qgisName'][:-17]

        # Files path ----------------------------------------------------------
        self.pathFileEditObj = os.path.join(actLayerInfo['folderPath'], 'edit', actLayerInfo['number_editObj'])
        self.pathFileReestrFields = os.path.join(actLayerInfo['folderPath'], 'edit', 'reestrFields.json')
        self.pathFileLayerExport = os.path.join(actLayerInfo['folderPath'], 'edit', 'layerEport.json')

        # Import CITORUS_Connect_dockwidget -----------------------------------
        from ..CITORUS_Connect import dockwidget

        dockwidget.spinner.setVisible(True)
        dockwidget.setEnabledWidget(False)
        while True:
            if dockwidget.spinner.isVisible(): 
                break
        try:
            self.changedExistingFile()
            self.postRequests()
            self.unblockExportLayer()
            self.deleteEditingFiles()
            VectorLayerImport(objId, account, layerName)
        except Exception as e:
            print (e)

        dockwidget.spinner.setVisible(False)
        dockwidget.setEnabledWidget(True)


    def changedExistingFile (self):  
        # Read GetObj for editing file ----------------------------------------
        with open(self.pathFileEditObj, "r") as fileEditObj:
            dataFileGetObjExport = json.load(fileEditObj)

        # Read reest fieds file -----------------------------------------------    
        with open(self.pathFileReestrFields, "r") as fileReestrFields:
            dataFileReestrFieldsExport = json.load(fileReestrFields)

        # Get fields from active layer ----------------------------------------
        exportLyr = iface.activeLayer()
        features = exportLyr.getFeatures()
        fields = exportLyr.pendingFields()
        fieldsList = [x.name() for x in fields]
        indexFieldId = fieldsList.index('id')

        # Change export file --------------------------------------------------
        dataFileGetObjExportEditing = dataFileGetObjExport['features']
        for f in features:
            attrs = f.attributes()
            geom = f.geometry()
            feat = {}
            for el in dataFileGetObjExportEditing:
                if el.has_key('_id'):
                    if el['_id'] == attrs[indexFieldId]:
                        el['properties']['_id'] = attrs[indexFieldId]
                        el['properties']['layerID'] = self.actLayerInfo['citorusID']
                        if geom != None:
                            el['geometry'] = json.loads(geom.exportToGeoJSON())
                        else:
                            el['geometry'] = None
                        for attr in range(len(attrs)):
                            if attr != indexFieldId:
                                dirField = dataFileReestrFieldsExport[fields[attr].name()]
                                self.changedEditedFile(el, dirField, attrs[attr])
                else:
                    if el['properties']['_id'] == attrs[indexFieldId]:
                        el['properties']['layerID'] = self.actLayerInfo['citorusID']
                        if geom != None:
                            el['geometry'] = json.loads(geom.exportToGeoJSON())
                        else:
                            el['geometry'] = None
                        for attr in range(len(attrs)):
                            if attr != indexFieldId:
                                dirField = dataFileReestrFieldsExport[fields[attr].name()]
                                self.changedEditedFile(el, dirField, attrs[attr])

        # Save export file (json) ---------------------------------------------
        with open(self.pathFileLayerExport, "w") as fileLayerJSON:
            json.dump(dataFileGetObjExportEditing, fileLayerJSON)


    def changedEditedFile (self, dic, keys, value):
        if value == NULL:
            value = None
        for key in keys[:-1]:
            dic = dic.setdefault(key, {})
        dic[keys[-1]] = value
    

    def postRequests (self):
        # Read export file ----------------------------------------------------
        with open(self.pathFileLayerExport, "r") as fileGetObj:
            dataFileExport = json.dumps(json.load(fileGetObj))

        # Post reqest ---------------------------------------------------------
        urlServer = self.account["url"]
        url = urlServer.split('getLayers')[0] + 'saveObj'
        jsonData={"data": dataFileExport }
        requestExport = Request().request(url, 'POST', params=jsonData) 
        print (requestExport)
        # print ("Кол-во отправленных объектов: ".decode('utf8') + str(requestExport.text.count("true")))
        # self.showInfoDialogExport()

    
    def unblockExportLayer (self):
        # Get request ---------------------------------------------------------
        urlServer = self.account["url"]
        listId = map(lambda x : str(x["id"]), iface.activeLayer().getFeatures()) 
        url = urlServer.split('getLayers')[0] + 'unblockObj?layerID=' + self.actLayerInfo['citorusID'] + '&ids=' + str(listId).replace("'", '%22')
        requestEditObj = Request().request(url, "GET")
                
    
    def deleteEditingFiles (self):
        # Save Layaer Edits ---------------------------------------------------
        iface.activeLayer().commitChanges()

        # Delete temp files for editing layer ---------------------------------
        os.remove(self.pathFileEditObj)
        os.remove(self.pathFileLayerExport)
        
        # Remove editing layer ------------------------------------------------
        QgsMapLayerRegistry.instance().removeMapLayer(iface.activeLayer())


