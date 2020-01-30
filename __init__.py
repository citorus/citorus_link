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


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load CITORUSConnect class from file CITORUSConnect.

    :param iface: A QGIS interface instance.
    :type iface: QgisInterface
    """
    #
    from .CITORUS_Connect import CITORUSConnect
    return CITORUSConnect(iface)
