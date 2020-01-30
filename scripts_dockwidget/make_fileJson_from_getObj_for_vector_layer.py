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


class MakeFileJsonFromGetObjForVectorLayer:

    def __init__(self, edit, pathFileGetObj, pathFileLayerJSON):
        """Constructor."""

        dataFileGetObj = self.readGetObj(pathFileGetObj)
        self.createLayerJson(edit, dataFileGetObj, pathFileLayerJSON)


    def readGetObj (self, path):
        with open(path, "r") as fileGetObj:
            return json.load(fileGetObj)


    def createLayerJson (self, edit, dataFileObj, exportFile):
        dataFileLayerJSON = {}

        ## example objects/getObj1
        if dataFileObj["type"] == 'FeatureCollection' and not dataFileObj["features"][0]["properties"].has_key('object'):
            dataFileLayerJSON = dataFileObj

            for f in dataFileObj["features"]:
                f["properties"]["id"] = f["_id"]
            if edit: 
                self.createReestrFields(dataFileObj["features"][0]["properties"], "type0", exportFile)
        ## example objects/getObj
        elif dataFileObj["type"] == 'FeatureCollection' and dataFileObj["features"][0]["properties"].has_key('object'):
            if type(dataFileObj["features"][0]["properties"]["object"]) is not dict:
                dataFileLayerJSON = dataFileObj
            else:
                dataFileLayerJSON["type"] = 'FeatureCollection'
                dataFileLayerJSON["features"] = map(lambda x : self.collectedJson(x), dataFileObj["features"]) 
                
                if edit:
                    self.createReestrFields(dataFileObj["features"][0]["properties"]["object"], "type1", exportFile)
        else:
            dataFileLayerJSON["type"] = 'FeatureCollection'
            dataFileLayerJSON["features"] = [self.collectedJson(dataFileObj)]
            
            if edit:
                self.createReestrFields(dataFileObj["properties"]["object"], "type1", exportFile)

        with open(exportFile, "w") as fileLayerJSON:
            json.dump(dataFileLayerJSON, fileLayerJSON)

    
    def collectedJson (self, obj):
        objectLayer = {}
        objectLayer["type"] = obj["type"]
        objectLayer["geometry"] = obj["geometry"]

        properties = {}
        objAttributes = obj["properties"]["object"]
        objAttributeID = obj["properties"]["_id"]

        for key in objAttributes.keys():
            if type(objAttributes[key]) is dict and not objAttributes[key].has_key('value'):
                for key1 in objAttributes[key].keys():
                    if type(objAttributes[key][key1]) is dict and objAttributes[key][key1].has_key('value'):
                        properties = self.collectedProperties(properties, key1, objAttributes[key][key1]["value"])
                    elif type(objAttributes[key][key1]) is not dict:        # is unicode
                        properties = self.collectedProperties(properties, key1, objAttributes[key][key1])
            elif type(objAttributes[key]) is not dict:       # is unicode
                properties = self.collectedProperties(properties, key, str(objAttributes[key]))

        properties['id'] = objAttributeID
        objectLayer["properties"] = properties

        return objectLayer


    def collectedProperties (self, dictionary, key, meaning):
        i=1
        while True:
            if not dictionary.has_key(key):
                dictionary[key] = meaning
                return dictionary
            elif not dictionary.has_key(key.split('_')[0] + '_' + str(i)):
                dictionary[key + '_' + str(i)] = meaning
                return dictionary
            else:
                i+=1


    def createReestrFields (self, obj, typeField, exportFile):
        objAttributes = obj
        dataFileReestrFields={}

        if (typeField == 'type0'):
            for key in objAttributes.keys():
                dataFileReestrFields = self.collectedProperties(dataFileReestrFields, key,["properties", key])
        else:
            for key in objAttributes.keys():
                if type(objAttributes[key]) is dict and not objAttributes[key].has_key('value'):
                    for key1 in objAttributes[key].keys():
                        if type(objAttributes[key][key1]) is dict and objAttributes[key][key1].has_key('value'):
                            dataFileReestrFields = self.collectedProperties(dataFileReestrFields, key1,["properties", "object", key, key1, "value"])
                        elif type(objAttributes[key][key1]) is not dict:        # is unicode
                            dataFileReestrFields = self.collectedProperties(dataFileReestrFields, key1,["properties", "object", key, key1])
                elif type(objAttributes[key]) is not dict:       # is unicode
                    dataFileReestrFields = self.collectedProperties(dataFileReestrFields, key,["properties", "object", str(key)])
          
        # Write fields with directory to file ---------------------------------   
        with open(os.path.join(exportFile.split('layerEdit')[0], 'reestrFields.json'), "w") as fileReestrJSON:
            json.dump(dataFileReestrFields, fileReestrJSON)

