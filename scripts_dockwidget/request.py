# -*- coding: utf-8 -*-
import json
import os, sys

from PyQt4.QtCore import *
from PyQt4.QtGui import QMessageBox
from qgis.core import *

from base64 import b64encode
from PyQt4.QtNetwork import *

this_dir = os.path.dirname(__file__).decode(sys.getfilesystemencoding())

class Request:
    def __init__(self):
        """Constructor."""

        with open(os.path.join(this_dir.split('scripts_dockwidget')[0], 'authentification.json'), "r") as fileJSON:
            dataFileJSON = json.load(fileJSON)
        # Account selection ---------------------------------------------------
        for item in range(len(dataFileJSON)):
            if dataFileJSON[item]["selected"] == True :
                self.account = dataFileJSON[item]

    def request (self, sub_url, method, params=None, files=None, timeout=None):
        json_data = None
        if params:
            json_data = json.dumps(params)
 
        url = QUrl(sub_url)
        url.setUserName(self.account["login"])
        url.setPassword(self.account["password"])
        # url.setUserName("anonymous")
        # url.setPassword("anonymous")
        req = QNetworkRequest(url)#http://91.239.142.111:8888/citorusConnect/getLayers
 
 
        # authstr = (u'%s:%s' % (self.account["login"] , self.account["password"])).encode('utf-8')        
        # authstr = (u'anonymous:anonymous').encode('utf-8')        
        # authstr = QByteArray('Basic ' +  QByteArray(authstr).toBase64())
        # req.setRawHeader("Authorization", authstr)
 
        # req.AuthenticationReuseAttribute()
 
        data = QBuffer(QByteArray())
        if json_data is not None:
            req.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
            json_data = QByteArray(json_data)
            data = QBuffer(json_data)
            
        

        # fpbytes = QByteArray()
        # if files is not None:
        #     req.setHeader(QNetworkRequest.ContentTypeHeader, 'image/tif')
        #     # fp = QFile(files)
        #     # fp.open(QIODevice.ReadOnly)
        #     # fpbytes = QByteArray(fp.readAll())
        #     # fp.close()   
        #     data = QBuffer(files)    
        #     # req.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")

        data.open(QIODevice.ReadOnly)
 
        loop = QEventLoop()
        timer = QTimer()
        # nam = QgsNetworkAccessManager.instance()
        nam = QNetworkAccessManager()
 
        if method == "GET" or method == "GETRaster":
            rep = nam.get(req)
        elif method == "POST":
            rep = nam.post(req, data)
        # elif method == "PUT":
        #     rep = nam.put(req, data)
        elif method == "DELETE":
            rep = nam.deleteResource(req)
        else:            
            rep = nam.sendCustomRequest(req, method, data)
        
        rep.finished.connect(loop.quit)
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: loop.exit(1))
        if timeout:
            timer.start(timeout * 1000) # 30 second time-out
        else:
            timer.start(60 * 1000) # 60 second time-out
        rep.finished.connect(loop.quit)
        # print('fetching request...')
        if loop.exec_() == 0:
            timer.stop()

            rep.finished.disconnect(loop.quit)
            data.close()
            data = rep.readAll()
    

            if rep.error() > 0 and rep.error() < 10:
                print( "Connection error qt code: {}".format(rep.error()) )
                # raise NGWError(NGWError.TypeRequestError, "Connection error qt code: {}".format(rep.error()), req.url().toString())
    
            status_code = rep.attribute( QNetworkRequest.HttpStatusCodeAttribute )
    
            if  status_code == 502:
                print( "Response\nerror status_code 502" )
                # raise NGWError(NGWError.TypeRequestError, "Response status code is 502", req.url().toString())
    
            if  status_code / 100 != 2:
                print("Response\nerror status_code {}\nmsg: {}".format(status_code, data))
                # raise NGWError(NGWError.TypeNGWError, data, req.url().toString())
    
            try:
                if method == "GETRaster":
                    json_response = data
                else:
                    json_response = json.loads(data.data().decode('utf8'))
                # json_response = data
            except Exception as e:
                pass
                # print e
                # print("Response\nerror response JSON parse\n%s" % data)
                # raise NGWError(NGWError.TypeNGWUnexpectedAnswer, "", req.url().toString())
            rep.deleteLater()
            del rep
            loop.deleteLater()
            # del loop
            # self.spinner.setVisible(False)
            # self.setEnabledWidget(True)

            return json_response
        else:
            self.showWarningDialogRequestTimeOut()


    def showWarningDialogRequestTimeOut (self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        
        msg.setText('Время ответа сервиса истекло'.decode('utf8'))
        msg.setWindowTitle("Предупреждение".decode('utf8'))
        msg.setStandardButtons(QMessageBox.Close)
        msg.exec_()