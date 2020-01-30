def getRequests (self):
        # Account selection ---------------------------------------------------
        for item in range(len(self.dataFileJSON)):
            if self.dataFileJSON[item]["selected"] == True :
                self.account = self.dataFileJSON[item]
        self.readLayerReestrJson()       

        # Get request ---------------------------------------------------------
        
        # self.request = requests.get( self.account["url"] , auth=HTTPDigestAuth( self.account["login"] , self.account["password"]))
        self.request = self.__request( self.account["url"] , 'GET')
        
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
    