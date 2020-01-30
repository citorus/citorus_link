from PyQt4.QtGui import *
from PyQt4.QtCore import *

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