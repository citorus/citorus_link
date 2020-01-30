# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CITORUSConnect
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

from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt
from PyQt4.QtGui import QAction, QIcon

from qgis.core import QgsMapLayer, QgsMessageLog

# Initialize Qt resources from file resources.py
import resources


# Import the code for the DockWidget
from CITORUS_Connect_dockwidget import CITORUSConnectDockWidget
import os.path, sys, json
this_dir = os.path.dirname(__file__).decode(sys.getfilesystemencoding())


class CITORUSConnect:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgisInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'CITORUSConnect_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&CITORUS.Link')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'CITORUSConnect')
        self.toolbar.setObjectName(u'CITORUSConnect')

        #print "** INITIALIZING CITORUSConnect"

        self.pluginIsActive = False
        self.dockwidget = None


    # noinspection PyMethodMayBeStatic
    def tr(self, message, russian=False):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        if russian:
            return message.decode("utf8")
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('CITORUSConnect', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action


    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/CITORUSConnect/icon.png'
        self.add_action(
            icon_path,
            text=self.tr('Развернуть/свернуть CITORUS.Link', True),
            callback=self.run,
            parent=self.iface.mainWindow())


    #--------------------------------------------------------------------------

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        #print "** CLOSING CITORUSConnect"

        # disconnects
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)

        # remove this statement if dockwidget is to remain
        # for reuse if plugin is reopened
        # Commented next statement since it causes QGIS crashe
        # when closing the docked window:
        # self.dockwidget = None

        self.pluginIsActive = False


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        #print "** UNLOAD CITORUSConnect"

        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&CITORUS.Link'),
                action)
            self.iface.removeToolBarIcon(action)

        # delete all data from file layer reestr
        with open(os.path.join(this_dir, 'layersReestr.json'), "w") as fileJSON:
            json.dump({}, fileJSON)

        # Remove folders with cash by ID Account ------------------------------
        OBJECTS_PATH = os.path.join(self.plugin_dir, 'objects/')
        listExistAccount = [str(foldername) for foldername in os.listdir(OBJECTS_PATH) if os.path.isdir(os.path.join(OBJECTS_PATH, foldername))]
        for accountId in listExistAccount:
            dir_id_path = os.path.join(OBJECTS_PATH, accountId)
            listExistLayers = [str(foldername) for foldername in os.listdir(dir_id_path) if os.path.isdir(os.path.join(dir_id_path, foldername))]
            for layerId in listExistLayers:
                # Remove the content of a folder EDIT
                dir_obj_path = os.path.join(dir_id_path, layerId)
                for elem in os.listdir(os.path.join(dir_obj_path, 'edit')):
                    os.remove(os.path.join(dir_obj_path, 'edit', elem))
                os.rmdir(os.path.join(dir_obj_path, 'edit'))
                # Remove the content of a folder LAYERID
                for elfile in os.listdir(dir_obj_path):
                    os.remove(os.path.join(dir_obj_path, elfile))
                os.rmdir(dir_obj_path)
        
        # remove the toolbar
        del self.toolbar

    #--------------------------------------------------------------------------

    def run(self):
        """Run method that loads and starts the plugin"""

        if not self.pluginIsActive:
            self.pluginIsActive = True

            #print "** STARTING CITORUSConnect"

            # dockwidget may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)
            if self.dockwidget == None:
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = CITORUSConnectDockWidget()
                global dockwidget
                dockwidget = self.dockwidget
                dockwidget.setStyleSheet(open(os.path.join(this_dir, "style.qss"), "r").read())

            # connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)

            # show the dockwidget
            # TODO: fix to allow choice of dock location
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)
            self.dockwidget.show()

