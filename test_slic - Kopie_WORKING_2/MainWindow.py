# -*- coding: utf-8 -*-
"""
/***************************************************************************
 MainWindow
                                 A QGIS plugin
 A QGIS plugin for superpixel computation using superpixel algorithms.
 The plugin structure was generated using Plugin Builder:
 http://g-sherman.github.io/Qgis-Plugin-Builder/
 and later reworked into a full MainWindow plugin.

 Code snippets, citations or inspirations are credited by including
 the url in the comments.
                              -------------------
        begin                : 2021-04-12
        git sha              : $Format:%H$
        copyright            : (C) 2021 by ososcody
        email                : TODO
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon

from qgis.PyQt.QtWidgets import QWidget, QAction, QFileDialog

# Import to open weblinks
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl

from PyQt5.QtWidgets import QMainWindow

import sys

from qgis.core import *  #

from qgis.core import (
    QgsProject,
    QgsMapLayerProxyModel)

# https://qgis.org/pyqgis/master/gui/QgsFileWidget.html
from qgis.gui import QgsFileWidget

# Initialize Qt resources from file resources.py
# Import the code for the dialog (UI)
from .Ui_MainWindow import Ui_MainWindow

# to use my QGIS processing algorithms, see: https://docs.qgis.org/3.16/en/docs/pyqgis_developer_cookbook/cheat_sheet.html#processing-algorithms
from qgis.core import QgsApplication
# TODO: Imports and enables the processing plugins:
#from my_plugin_provider import MyProcessingProvider  # which is itself importing all processing plugins


import os.path

import numpy as np  # eventuell rasterio nehmen?
from osgeo import gdal
from skimage import exposure
from skimage.segmentation import slic  # import slic
from skimage.color import label2rgb  # Import the label2rgb function from the scikit-image color module


#### END of imports #####

class MainWindow:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
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
            'TestSLIC_{}.qm'.format(locale)) # TODO
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # FRESHLY WRITTEN************************************
        self.main_win = QMainWindow()
        # Create the dialog (after translation) and keep reference
        self.ui = Ui_MainWindow()
        # FERTIG

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr('Superpixelplugin') #u'&Test SLIC')#'Superpixelplugin')#u'&Superpixelplugin')#&Test SLIC')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

        # necessary for the processing plugin
        #self.provider = None  # introduce empty provider variable
        #######
        ######
        #####
        ####
        ###
        ##
        # ! immer die connecteten functions ohne () schreiben!

        # set tabWidget to first show the welcome tab @ index 0
        # Example: https://stackoverflow.com/questions/46399319/how-can-we-open-a-tab-specific-tab-in-pyqt-on-button-click
        self.ui.tabWidget.setCurrentIndex(0)  # show the tab_welcome at start of the plugin

        # connect the help button
        # https://stackoverflow.com/questions/45090982/passing-extra-arguments-through-connect?noredirect=1&lq=1
        #self.ui.pb_help.clicked.connect(self.openWebsite)  # on click open website url
        ##### WORKING with injected parameterized argument #####
        # https://stackoverflow.com/questions/53041540/passing-default-argument-and-custom-argument-to-slot-function?noredirect=1&lq=1
        my_url = "http://www.readthedocs.org"
        self.ui.pb_help.clicked.connect(
            lambda default, my_url=my_url: self.openWebsite(my_url))  # click opens website with parameterized url
        #############


        ############## TODO BAUSTELLE#############################
        ####### Raster data input ################################
        from qgis.core import QgsProviderRegistry # see: https://qgis.org/pyqgis/3.2/core/Provider/QgsProviderRegistry.html
        # !!!! CURRENTLY THERE IS A BUG, see: https://github.com/qgis/QGIS/issues/38472
        # GET INPUT
        # code snippet from: https://create-qgis-plugin.readthedocs.io/en/latest/step2a_gui.html
        # prepare the range of supported providers for file drivers
        excluded_prov = [p for p in QgsProviderRegistry.instance().providerList() if p not in ['gdal']]
        self.ui.cb_inRaster.setExcludedProviders(excluded_prov)            # set the excluded providers
        self.ui.cb_inRaster.setFilters(QgsMapLayerProxyModel.RasterLayer)  # show only valid raster files to choose from
        #self.ui.cb_inRaster.layerChanged.connect(self._choose_image)      # if the selection changes, run function
        self.ui.cb_inRaster.layerChanged.connect(self.loadRasters)         # if the selection changes, run function
        #self.imageAction.triggered.connect(self._browse_for_image)
        self.ui.imageAction.triggered.connect(self.openRaster)      # image toolButton connected to openRaster function
        #self.imageButton.setDefaultAction(self.imageAction)
        self.ui.tb_inRaster.setDefaultAction(self.ui.imageAction)   # sets the default behaviour
        ##################

        # Create a date and time for the filename, see: https://stackoverflow.com/questions/10607688/how-to-create-a-file-name-with-the-current-date-time-in-python
        from datetime import datetime
        dateandtime = datetime.now().strftime("%Y-%m-%d_%H-%m-%d")  # %Y%m%d-%H%M")  # %S")

        self.currentAlgorithmName = ""  # variable will be set after algorithm was chosen

        # import os
        from os.path import join as pjoin

        # get the path to the users documents folder
        path_to_folder = os.path.expanduser('~\\Documents')
        # >>OR<< use the current working directory
        # import os
        #path_to_folder = os.getcwd()

        # TODO:
        # create new folder "SuperpixelpluginOutput" if it does not exist yet
        if os.path.exists(pjoin(path_to_folder, "SuperpixelpluginOutput")) == False:
            #create new folder:
            os.mkdir(pjoin(path_to_folder, "SuperpixelpluginOutput"))
        else:
            pass

        ####### Data IO via FileWidgets ################################
        # AVG segments Raster output
        # code snippet from: https://create-qgis-plugin.readthedocs.io/en/latest/step2a_gui.html
        self.ui.fw_outRasterSegmentsAvgColor.lineEdit().setReadOnly(False)  # True)

        #path_and_filename = pjoin("C:", "foo", "bar", "baz" + self.currentAlgorithmName + "_avg_" + str(dateandtime) + ".tif")
        path_and_filename = pjoin(path_to_folder, "SuperpixelpluginOutput", self.currentAlgorithmName + "_avg_" + str(dateandtime) + ".tif")
        #self.ui.fw_outRasterSegmentsAvgColor.lineEdit().setPlaceholderText(path_and_filename)
        self.ui.fw_outRasterSegmentsAvgColor.lineEdit().setText(path_and_filename)
        self.ui.fw_outRasterSegmentsAvgColor.setStorageMode(QgsFileWidget.SaveFile)
        self.ui.fw_outRasterSegmentsAvgColor.setFilter("Tiff (*.tif);;All (*.*)")
        self.ui.fw_outRasterSegmentsAvgColor.confirmOverwrite()  # True)


        # For the Vector segments output
        # code snippet from: https://create-qgis-plugin.readthedocs.io/en/latest/step2a_gui.html
        self.ui.fw_outVector.lineEdit().setReadOnly(False)  # True)
        #self.ui.fw_outVector.lineEdit().setPlaceholderText('[Create temporary layer]')
        #self.ui.fw_outVector.lineEdit().setPlaceholderText(self.currentAlgorithmName + "_poly_" + str(dateandtime) + ".shp")
        path_and_filename = pjoin(path_to_folder, "SuperpixelpluginOutput", self.currentAlgorithmName + "_poly_" + str(dateandtime) + ".shp")
        #self.ui.fw_outVector.lineEdit().setPlaceholderText(path_and_filename)
        self.ui.fw_outVector.lineEdit().setText(path_and_filename)
        self.ui.fw_outVector.setStorageMode(QgsFileWidget.SaveFile)
        self.ui.fw_outVector.setFilter("Shapefile (*.shp);;All (*.*)")
        self.ui.fw_outVector.confirmOverwrite()  # True)

        # For the Vector statistics segments output
        # code snippet from: https://create-qgis-plugin.readthedocs.io/en/latest/step2a_gui.html
        self.ui.fw_outVectorStats.lineEdit().setReadOnly(False)  # True)
        #self.ui.fw_outVector.lineEdit().setPlaceholderText('[Create temporary layer]')
        #self.ui.fw_outVectorStats.lineEdit().setPlaceholderText(self.currentAlgorithmName + "_poly_stats_" + str(dateandtime) + ".shp")
        path_and_filename = pjoin(path_to_folder, "SuperpixelpluginOutput", self.currentAlgorithmName + "_poly_stats_" + str(dateandtime) + ".shp")
        #self.ui.fw_outVectorStats.lineEdit().setPlaceholderText(path_and_filename)
        self.ui.fw_outVectorStats.lineEdit().setText(path_and_filename)
        self.ui.fw_outVectorStats.setStorageMode(QgsFileWidget.SaveFile)
        self.ui.fw_outVectorStats.setFilter("Shapefile (*.shp);;All (*.*)")
        self.ui.fw_outVectorStats.confirmOverwrite()  # True)

        # And the raster segments output
        # code snippet from: https://create-qgis-plugin.readthedocs.io/en/latest/step2a_gui.html
        self.ui.fw_outRaster.lineEdit().setReadOnly(False)  # True)
        #self.ui.fw_outRaster.lineEdit().setPlaceholderText('[Create temporary layer]')
        path_and_filename = pjoin(path_to_folder, "SuperpixelpluginOutput", self.currentAlgorithmName + "_raster_segments_" + str(dateandtime) + ".tif")
        #self.ui.fw_outRaster.lineEdit().setPlaceholderText(path_and_filename)
        self.ui.fw_outRaster.lineEdit().setText(path_and_filename)
        self.ui.fw_outRaster.setStorageMode(QgsFileWidget.SaveFile)
        self.ui.fw_outRaster.setFilter("Tiff (*.tif);;All (*.*)")
        self.ui.fw_outRaster.confirmOverwrite()  # True)

        ################

        # GUI eingegebene parameter einlesen
        self.ui.pb_run.clicked.connect(self.setVariables)

        ###############
        # When the tab is changed... # see API: https://doc.qt.io/qt-5/qtabwidget.html#currentChanged
        self.ui.tabWidget.currentChanged.connect(self.setupRunButton)  # THIS IS WORKING!!!!
        ###############


        #############
        # EXPERIMENT
        # TODO: MUSS DAS HIER SEIN? MAL AUSGEKLAMMERT
        self.ui.pb_run.clicked.connect(self.loadRasters)


        # Open up the output directory containing the results
        os.startfile(pjoin(path_to_folder, "SuperpixelpluginOutput"))  # TODO: Open at click run


    # TODO OPTIONAL SAVE SETTINGS
    def getSettingValues(self): # to save the plugin settings as a file, function from: https://www.youtube.com/watch?v=f6jGVlTqGSI
        self.setting_window = QSettings("Superpixelplugin")  # TODO



    # TODO DODOOOOO
    # TODO
    # TODO
    # TODO
    # For the processing plugins to work
    #def initProcessing(self):
    #    self.provider = MyProcessingProvider()
    #    QgsApplication.processingRegistry().addProvider(self.provider)



    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('MainWindow', message)

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
        parent=None
    ):
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
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            #self.iface.addPluginToMenu(
            self.iface.addPluginToRasterMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        # initializes the processing plugins
        # TODO HEUTE self.initProcessing()  ****************************

        # Setup the GUI plugin all OSes compatible
        icon_path = os.path.join(self.plugin_dir, "icon.png")
        self.add_action(
            icon_path,
            text=self.tr('Superpixelplugin'),#u'Test SLIC'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # Add the provider to the processing registry to put the processingplugins in the toolbox
        # self.provider = MyProcessingProvider()
        # QgsApplication.processingRegistry().addProvider(self.provider)



        # GESCHRIEBEN
        # self.ui.tb_inVector.clicked.connect(self.openVector)
        # Was ist mit cb_inRaster?
        # self.ui.cb_inRaster.clicked.connect(self.openRaster)

        # TODO woanders jetzt geregelt
        #self.ui.tb_inRaster.clicked.connect(self.openRaster) # Das selbe, wie die imageAction
        # self.ui.fw_inRaster.clicked.connect(self.openRaster)

        # TODO: MUSS DAS HIER REIN??
        #self.ui.cb_inRaster

        # Hier die Werte auslesen der DoubleSpinBoxen etc.
        self.setVariables()  # siehe def setVariables <-------------------------


        # get the inRaster properties / metadata to show them in the TextBrowser
        self.tb = self.ui.QTextBrowser

        self.tbAlgo = self.ui.QTextBrowser_2  # For debugging purposes to display selected algorithm

        self.logBrowser = self.ui.logBrowser

        self.progressBar = self.ui.progressBar

        # Set a shortcut to the run button
        self.ui.pb_run.setShortcut("Return")  #"Ctrl+Return")

        # SETZE HIER MAL ALLE ALS CHECKED per default:
        # set check box states to checked as default
        self.ui.checkBox_openAsLayerInQGIS.setChecked(True)
        self.ui.checkBox_createVectorSegments.setChecked(True)
        self.ui.checkBox_calculateOutRasterSegmentsAvgColor.setChecked(True)
        self.ui.checkBox_createVectorStatistics.setChecked(True)


        # Connects the QToolButton "tb_outRaster" with the saveRaster function
        #TODO Deprecated othe file out
        # self.ui.tb_outRaster.clicked.connect(self.saveRaster)  # ## SAVE RASTER!!

        """
        HIER DIE SAVE WIDGET EINBAUEN???
        # -> https://gis.stackexchange.com/questions/278828/how-to-use-qgsfilewidget-to-save-file
        # -> https://webgeodatavore.github.io/pyqgis-samples/gui-group/QgsRasterLayerSaveAsDialog.html <---
        """

        ############## START MENU BAR ACTIONS ###########
        # Examples, see: https://www.geeksforgeeks.org/pyqt5-qaction/
        # Add a triggered action to the actions in the menu bar
        # >>>> https://stackoverflow.com/questions/46399319/how-can-we-open-a-tab-specific-tab-in-pyqt-on-button-click

        # MenuBar > FILE ##
        # Exit action ist in .ui festgelegt worden.

        # MenuBar > ALGORITHMS #######
        # MenuBar > ALGORITHMS >> SLIC
        self.ui.actionSLIC.triggered.connect(lambda: self.ui.tabWidget.setCurrentIndex(1))
        # MenuBar > ALGORITHMS >> Watershed
        self.ui.actionWatershed.triggered.connect(lambda: self.ui.tabWidget.setCurrentIndex(2))
        # MenuBar > ALGORITHMS >> Quickshift
        self.ui.actionQuickShift.triggered.connect(lambda: self.ui.tabWidget.setCurrentIndex(3))
        # MenuBar > ALGORITHMS >> Felzenszwalb
        self.ui.actionFelzenszwalb.triggered.connect(lambda: self.ui.tabWidget.setCurrentIndex(4))
        # MenuBar > ALGORITHMS >> Next Algo
        #self.ui.actionSLIC.triggered.connect(lambda: self.ui.tabWidget.setCurrentIndex(1))

        # MenuBar > HELP ##########
        # Example: https://subscription.packtpub.com/book/application_development/
        # 9781788831000/7/ch07lvl1sec58/creating-a-custom-menu-bar?query=menu

        # MenuBar > HELP >> Documentation
        my_url = "http://www.readthedocs.org/ososcody/superpixelplugin"  # TODO: Change urls to my specific addresses
        self.ui.actionHelp.triggered.connect(
            lambda default, my_url=my_url: self.openWebsite(my_url))  # click opens website with parameterized url

        # MenuBar > HELP >> Repository
        my_url = "http://www.github.com/ososcody/superpixelplugin"
        self.ui.actionGitHub.triggered.connect(
            lambda default, my_url=my_url: self.openWebsite(my_url))  # click opens website with parameterized url

        # MenuBar > HELP >> Feedback
        my_url = "http://www.github.com/ososcody/superpixelplugin"
        self.ui.actionFeedback.triggered.connect(
            lambda default, my_url=my_url: self.openWebsite(my_url))  # click opens website with parameterized url

        # MenuBar > HELP >> About
        self.ui.actionAbout.triggered.connect(lambda: self.ui.tabWidget.setCurrentIndex(8))

        # MenuBar > VIEW LOG
        self.ui.actionGo_to_Log.triggered.connect(lambda: self.ui.tabWidget.setCurrentIndex(9))
        ############### END MENU BAR ACTIONS ############

        self.loadRasters()

        self.clearText()  # clear the text browser on init

        # TODO +++++++++++++++++++++
        ## HIER RICHTIG?
        self.ui.pb_run.clicked.connect(self.checkCheckBoxStatus)


    def setupRunButton(self):
        """Receives the index of the open tab and assigns the suitable algorithm to the run button,
        additionally prints the tabs name in a text browser for debugging purposes"""

        if self.ui.tabWidget.currentIndex() == 1:

            #self.tbAlgo.clear()
            self.ui.QTextBrowser_2.clear()
            text = "SLIC"
            #self.tbAlgo.append(text)
            self.ui.QTextBrowser_2.append(text)

            self.ui.pb_run.clicked.connect(self.slic)  # << WORKS

            # set current algorithm name:
            self.currentAlgorithmName = "SLIC"

        elif self.ui.tabWidget.currentIndex() == 2:

            #self.tbAlgo.clear()
            self.ui.QTextBrowser_2.clear()
            text = "Watershed"
            self.ui.QTextBrowser_2.append(text)

            self.ui.pb_run.clicked.connect(self.watershed)  # << WORKS

            # set current algorithm name:
            self.currentAlgorithmName = "Watershed"

        elif self.ui.tabWidget.currentIndex() == 3:

            self.ui.QTextBrowser_2.clear()
            text = "QuickShift"
            self.ui.QTextBrowser_2.append(text)

            self.ui.pb_run.clicked.connect(self.quickshift)  # << WORKS

            # set current algorithm name:
            self.currentAlgorithmName = "QuickShift"

        elif self.ui.tabWidget.currentIndex() == 4:

            self.ui.QTextBrowser_2.clear()
            text = "Felzenszwalb"
            self.ui.QTextBrowser_2.append(text)

            self.ui.pb_run.clicked.connect(self.felzenszwalb)  # << WORKS

            # set current algorithm name:
            self.currentAlgorithmName = "Felzenszwalb"

        else:
            pass

        #####
        #self.ui.label.setText(np.max(self.segments_slic))  # show num of super pix in label



    # function from: https://create-qgis-plugin.readthedocs.io/en/latest/step2a_gui.html
    def log(self, text: str):
        # append text to log window
        self.logBrowser.append(str(text) + '\n')
        # open the widget on the log screen
        # TODO optional: self.ui.tabWidget.setCurrentIndex(self.ui.tabWidget.indexOf(self.tab_log))
        #self.ui.tabWidget.setCurrentIndex(self.ui.tabWidget.indexOf(self.tab_log))
        # Should do the same
        self.ui.tabWidget.setCurrentIndex(9)  # Direct approach


    def appendText(self):

        verticalScrollBar = self.ui.QTextBrowser.verticalScrollBar()  # create a vertical scrollbar for the QTextBrowser

        #layer = self.iface.activeLayer()        # assign the active layer in the QGIS Project as variable layer #### Done: Besser DEN AKTIVEN AUS DEM DROP DOWN MENU NEHMEN!!!!
        layer = self.ui.cb_inRaster.currentLayer()  # selects the currentLayer from the dropdown menu
        # QgsRasterLayer https://qgis.org/pyqgis/master/core/QgsRasterLayer.html

        if layer is None:                         # If no raster layer is loaded yet, pass
            pass
        else:          # else, clear textBrowser, load raster layer metadata and show it in the textBrowser:
            self.clearText()                   # clear the textBrowser first
            
            text = str("The chosen input rasters metadata and properties are: {}".format(
                        layer.htmlMetadata()))  # get the chosen raster layers metadata

            self.tb.append(text)                # appends the text to the textBrowser

            verticalScrollBar.setValue(verticalScrollBar.minimum()) # Scroll to the top of the text by setting the scrollbar to the minimum value
            # example scrolling to the bottom: https://stackoverflow.com/questions/54875284/scrollbar-to-always-show-the-bottom-of-a-qtextbrowser-streamed-text

    def clearText(self):
        """ Clear the textBrowser text """
        self.tb.clear()
        verticalScrollBar = self.ui.QTextBrowser.verticalScrollBar()  # create a vertical scrollbar for the QTextBrowser
        verticalScrollBar.setValue(verticalScrollBar.minimum())



    def segments2Vector(self):
        """Calculates vector polygons from raster superpixel segments"""
        # from qgis.core import QgsApplication # better organize imports at the top of the script
        # to use QGIS processing algorithms, see: https://docs.qgis.org/3.16/en/docs/pyqgis_developer_cookbook/cheat_sheet.html#processing-algorithms
        # from qgis import processing  # https://docs.qgis.org/3.16/en/docs/pyqgis_developer_cookbook/processing.html

        # use the GDAl polygonize function included in QGIS to calculate vector polygons
        # nice example, see: https://gis.stackexchange.com/questions/300615/running-qgis-processing-algorithm-in-qgis-plugin

        from qgis import processing # https://qgis.org/pyqgis/3.16/core/QgsProcessing.html?highlight=processing#module-QgsProcessing

        #if self.ui.checkBox_createVectorSegments.isChecked:
        #if self.ui.checkBox_createVectorSegments.isChecked == True:


        #segmentedRaster = self.outRaster #self.ui.fw_outRaster.FilePath()

        params = {'INPUT': self.outRaster, #segmentedRaster,  # outRasterFile,  # takes the path to the computed superpixel raster segments file as input
                  'BAND':1,
                  'FIELD':'DN',
                  'EIGHT_CONNECTEDNESS':False,
                  'EXTRA':'',
                  #'OUTPUT':'TEMPORARY_OUTPUT'} # creates a temporary output
                  'OUTPUT': self.outVector,  # self.ui.fw_outVector.getSaveFileName()  # creates a temporary output
                  #'OUTPUT':'TEMPORARY_OUTPUT' # creates a temporary output
                  }

        # result = processing.run("gdal:polygonize", params)
        # or with own gui dialog: https://docs.qgis.org/3.16/en/docs/user_manual/processing/console.html

        result = processing.run("gdal:polygonize", params)

        # Add the result to QGIS project
        # TODO hier wieder checkBox einbauen !!!!!!!!!!!!!!!!!
        # https://docs.qgis.org/3.16/en/docs/pyqgis_developer_cookbook/loadlayer.html
        # add/load the resulting Vector layer to the QGIS project canvas
        segment2vectorLayer = self.iface.addVectorLayer(         # add the layer to the QGIS project
            result['OUTPUT'],                                    # data to use as new layer
            str.split(os.path.basename(self.outVector), ".")[0], # name for layer in QGIS, generated from outVector path in GUI
            #filter=QgsProviderRegistry.instance().fileVectorFilters())[0])
            "ogr")                                              # driver, ogr, since it is a vector layer

        # TODO: Style the Vector layer!
        # For help see (styling Points): https://anitagraser.com/pyqgis-101-introduction-to-qgis-python-programming-for-non-programmers/pyqgis-101-styling-vector-layers/
        # and in general: https://opensourceoptions.com/blog/loading-and-symbolizing-vector-layers/
        # and: https://gis.stackexchange.com/questions/331408/change-vector-layer-symbology-pyqgis-3
        # and: https://gis.stackexchange.com/questions/255320/increasing-size-and-changing-color-in-centroids-lines-and-polygons

        # create a style
        symbol = QgsFillSymbol.createSimple(                                # QgsFillSymbol for polygons
                                            {#'draw_inside_polygon': '0',   # styling of the inside
                                             'color': 'transparent',
                                             'color_border':'red',          # styling of the outer line
                                             'line_style': 'solid',
                                             'width_border':'0.25'
                                             })
        """ # another way to set styling properties:
        # Set fill colour
        symbol.setColor(QColor.(QColor("transparent"))) #"blue"))) #fromRgb(255, 128, 0)) 

        symbol.setStrokeColor(QColor("blue"))
        # symbol.setColor(QColor.fromRgb(255,128,0))
        symbol.setStrokeWidth(0.5)
        """
        # add the styling to the layers renderer
        segment2vectorLayer.renderer().setSymbol(symbol)

        # repaint/update the view of the layer with the new style
        segment2vectorLayer.triggerRepaint()


        # TODO: REMAINS
        """ ### GERADE DEAKTIVIERT------------
        # run or cancel
        self.ui.button_box.button(QDialogButtonBox.Ok).setText("Run")
        self.ui.button_box.clicked.connect(self.run)
        #self.ui.button_box.rejected.connect(self.close)
        """
        # Die run Funktion verknüpfen
        # GUI eingegebene parameter einlesen
        #self.ui.pb_run.clicked.connect(self.run)

    def vectorSegments2stats(self):
        """Calculates vector polygons from raster superpixel segments"""
        # from qgis.core import QgsApplication # better organize imports at the top of the script
        # to use QGIS processing algorithms, see: https://docs.qgis.org/3.16/en/docs/pyqgis_developer_cookbook/cheat_sheet.html#processing-algorithms
        # from qgis import processing  # https://docs.qgis.org/3.16/en/docs/pyqgis_developer_cookbook/processing.html

        # use the GDAl polygonize function included in QGIS to calculate vector polygons
        # nice example, see: https://gis.stackexchange.com/questions/300615/running-qgis-processing-algorithm-in-qgis-plugin

        from qgis import processing  # https://qgis.org/pyqgis/3.16/core/QgsProcessing.html?highlight=processing#module-QgsProcessing

        # if self.ui.checkBox_createVectorSegments.isChecked:
        # if self.ui.checkBox_createVectorSegments.isChecked == True:

        # segmentedRaster = self.outRaster #self.ui.fw_outRaster.FilePath()

        # THIS WAS WORKING PERFECTLY for 1 band:
        """
        processing.run("native:zonalstatisticsfb",
                       {'INPUT': 'C:\\Users\\username\\Desktop\\MASTERARBEIT\\CODE\\Rasters\\testHill\\av.shp',
                        'INPUT_RASTER': 'C:/Users/username/Desktop/MASTERARBEIT/CODE/Rasters/testsubASTER.tif',
                        'RASTER_BAND': 1, 'COLUMN_PREFIX': '_', 'STATISTICS': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
                        'OUTPUT': 'TEMPORARY_OUTPUT'})
        """

        # TODO hier eine for schleife, für die range(1 to len(bands)): alle ergebnisse zu liste [] hinzufügen und am ende alle ergebnisse stacken.

        params = {'INPUT': self.outVector,
                  # segmentedRaster,  # outRasterFile,  # takes the path to the computed superpixel raster segments file as input
                  'INPUT_RASTER': self.inRaster, #'C:/Users/username/Desktop/MASTERARBEIT/CODE/Rasters/testsubASTER.tif',
                  'RASTER_BAND': 1,  # TODO: hier eine variable i für die bands einführen
                  'COLUMN_PREFIX': '_',
                  'STATISTICS': [0,1,2,3,4,5,6,7,8,9,10,11],  # TODO AVG, etc., (gewünschte Statistiken)
                  #'OUTPUT':'TEMPORARY_OUTPUT'} # creates a temporary output
                  'OUTPUT': self.outVectorStats}  # creates a temporary output
                  #'OUTPUT': self.outVector  # self.ui.fw_outVector.getSaveFileName()  # creates a temporary output
                  # 'OUTPUT':'TEMPORARY_OUTPUT' # creates a temporary output
                  #}

        # result = processing.run("gdal:polygonize", params)
        # or with own gui dialog: https://docs.qgis.org/3.16/en/docs/user_manual/processing/console.html

        result = processing.run("native:zonalstatisticsfb", params)     # run the algorithm: native:zonalstatisticsfb

        # Add the result to QGIS project
        # TODO hier wieder checkBox einbauen !!!!!!!!!!!!!!!!!
        # https://docs.qgis.org/3.16/en/docs/pyqgis_developer_cookbook/loadlayer.html
        # WORKING: self.iface.addVectorLayer(result['OUTPUT'], "VectorSegments", "ogr")#str.split(os.path.basename(inRasterFile), ".")[0])  # adds/loads the resulting Vector layer to the QGIS project canvas
        vectorSegments2statsLayer = self.iface.addVectorLayer(  # adds resulting Vector layer to the QGIS project canvas
            result['OUTPUT'],
            str.split(os.path.basename(self.outVectorStats), ".")[0],
            #filter=QgsProviderRegistry.instance().fileVectorFilters()[0])
            "ogr")  # str.split(os.path.basename(inRasterFile), ".")[0])

        # TODO: Style the Vector layer!
        # For help see (styling Points): https://anitagraser.com/pyqgis-101-introduction-to-qgis-python-programming-for-non-programmers/pyqgis-101-styling-vector-layers/
        # and in general: https://opensourceoptions.com/blog/loading-and-symbolizing-vector-layers/
        # and: https://gis.stackexchange.com/questions/331408/change-vector-layer-symbology-pyqgis-3
        # and: https://gis.stackexchange.com/questions/255320/increasing-size-and-changing-color-in-centroids-lines-and-polygons

        # create a style
        symbol = QgsFillSymbol.createSimple(  # QgsFillSymbol for polygons
            {  # 'draw_inside_polygon': '0',    # styling of the inside
                'color': 'transparent',
                'color_border': 'green',  # styling of the outer line
                'line_style': 'solid',
                'width_border': '0.25'
            })

        """ # another way of setting properties:
        # Set fill colour
        symbol.setColor(QColor.(QColor("transparent"))) #"blue"))) #fromRgb(255, 128, 0)) 

        symbol.setStrokeColor(QColor("blue"))
        # symbol.setColor(QColor.fromRgb(255,128,0))
        symbol.setStrokeWidth(0.5)
        """

        # add the styling to the layers renderer
        vectorSegments2statsLayer.renderer().setSymbol(symbol)

        # repaint/update the view of the layer with the new style
        vectorSegments2statsLayer.triggerRepaint()


    # def rasterSegmentsAvgColor(self):
    #
    #     """
    #     # Nachfolgender code ist angepasst aus dem tutorial von:
    #     # https://opensourceoptions.com/blog/python-geographic-object-based-image-analysis-geobia/
    #     driverTiff = gdal.GetDriverByName('GTiff')  # GDAL assign GTiff file driver (besser rasterio nehmen?)
    #     # global raster_dataset # set as a global variable
    #
    #     raster_dataset = gdal.Open(
    #         self.inRaster.dataProvider().dataSourceUri())  # use GDAL to open file from inRaster path
    #     self.nbands = raster_dataset.RasterCount  # get number of raster bands
    #     band_data = []  # create a list for the raster bands
    #     for i in range(1, self.nbands + 1):  # starting with band as 1
    #         band = raster_dataset.GetRasterBand(i).ReadAsArray()  # reads each band as ---> np array <---
    #         band_data.append(band)  # append the band as a np array to the band_data list
    #     band_data = np.dstack(band_data)  # put all in a single variable as a ---> stack of the bands <---
    #
    #     # normalize the raster band values
    #     # scale image values from 0.0 - 1.0
    #     self.img_normalized = exposure.rescale_intensity(band_data)
    #
    #     # ---> jetzt kommt SLIC <---
    #     # self.img_normalized ist jetzt normalized (values from 0.0 - 1.0)
    #     """
    #
    #
    #
    #     import rasterio as rio
    #     #import rioxarray
    #     # code snipped from: https://gis.stackexchange.com/questions/37238/writing-numpy-array-to-raster-file?rq=1
    #     #with rio.open('other_file.tif') as src:
    #
    #     #TODO DAS EINE ODER DAS ANDERE*******************
    #     with rio.open(self.inRaster.source()) as src:  # .source() gets the file path
    #     #with rio.open(self.inRaster) as src:  # .source() gets the file path
    #         ras_data = src.read()
    #         ras_meta = src.profile  # <- useful metadata of the input raster
    #         # will be necessary for the new image
    #
    #         # make changes to the raster properties
    #         ras_meta['dtype'] = "int32"
    #         ras_meta['nodata'] = -999
    #
    #
    #         # Label output zuweisen # TODO könnte so noch probleme geben, wenn mehrere Algos hintereinander berechnet werden.
    #         # TODO braucht eventuell noch sowas wie when changed?
    #         if self.ui.tabWidget.currentIndex() == 1:
    #             self.label = self.segments_slic
    #         # if self.segments_watershed is not None:
    #         if self.ui.tabWidget.currentIndex() == 2:
    #             self.label = self.segments_watershed
    #         # if self.segments_quickshift is not None:
    #         if self.ui.tabWidget.currentIndex() == 3:
    #             self.label = self.segments_quickshift
    #         # if self.segments_felzenszwalb is not None:
    #         if self.ui.tabWidget.currentIndex() == 4:
    #             self.label = self.segments_felzenszwalb
    #         else:
    #             print("NO VALID LABEL (SEGMENTS) FOUND")
    #
    #
    #
    #         # Put segments on top of original image to compare# TODO: ACHTUNG nur SLIC!!!
    #         #ras_data = label2rgb(self.label, #self.label, #self.segments_slic,  #label,  #self.ui.le_outRaster.text(), #self.outRaster.source(), #label,  # label TODO hier richtigen input nehmen von jeweiligem Algo den output...
    #         resultAVG = label2rgb(self.label, #self.label, #self.segments_slic,  #label,  #self.ui.le_outRaster.text(), #self.outRaster.source(), #label,  # label TODO hier richtigen input nehmen von jeweiligem Algo den output...
    #         #rasterSegmentsAvgColor = label2rgb(self.segments_slic,  #label,  #self.ui.le_outRaster.text(), #self.outRaster.source(), #label,  # label TODO hier richtigen input nehmen von jeweiligem Algo den output...
    #                                            self.img_normalized,  # normalized_img_rgb,  #TODO: Original input aber normalisiert einbauen!!!
    #                                            kind='avg',
    #                                            bg_label=0)  # img muss 3 channels haben...
    #     # Save the array using rasterio
    #     #with rio.open('outname.tif', 'w', **ras_meta) as dst:
    #     #with rio.open("C:/Users/username/Desktop/rasterSegmentsAvgColor.tif", 'w', **ras_meta) as dst:
    #
    #     #with rio.open(self.ui.fw_outRasterSegmentsAvgColor().filePath(), 'w', **ras_meta) as dst:
    #     with rio.open(self.outRasterSegmentsAvgColor, 'w', **ras_meta) as dst:
    #
    #     #with rio.open(self.ui.fw_outRasterSegmentsAvgColor().filePath(), 'w', **ras_meta) as dst:
    #         #dst.write(numpy_array, 1)
    #         #dst.write(rasterSegmentsAvgColor, 1)  # war 1
    #         #dst.write(ras_data, 1)  # war 1
    #
    #         #dst.write(resultAVG)#, 1)  # war 1
    #
    #         dst.write(resultAVG)#, 1)  # war 1
    #         # see: https://gis.stackexchange.com/questions/329925/rasterio-save-multiband-raster-to-tiff-file
    #
    #     #outRasterFile = str(QFileDialog.getSaveFileName(caption="Save clipped raster as",
    #                                                     #filter="GeoTiff (*.tif)")[0])
    #
    #     # rasterSegmentsAvgColor.rio.to_raster("C:/Users/username/Desktop/rasterSegmentsAvgColor.tif")#self.ui.fw_outRasterSegmentsAvgColor().filePath())
    #
    #     # ---> save segments to raster <----
    #
    #     """
    #     segments_fn = self.ui.fw_outRasterSegmentsAvgColor.filePath()  # get the name from the input field / picker
    #     segments_ds = driverTiff.Create(segments_fn,                   # create empty array recycle properties
    #                                     raster_dataset.RasterXSize,    # of raster_dataset
    #                                     raster_dataset.RasterYSize,
    #                                     1,                             # 1 band
    #                                     gdal.GDT_Float32)              # save as Float 32 values
    #     segments_ds.SetGeoTransform(raster_dataset.GetGeoTransform())  # transform
    #     segments_ds.SetProjection(raster_dataset.GetProjectionRef())   # assign the CRS
    #
    #     segments_ds.GetRasterBand(1).WriteArray(rasterSegmentsAvgColor)  # hier wird segments geschrieben
    #
    #     segments_ds = None
    #     """
    #     # Funktion noch aufrufen per button!
    #
    #     # Adds the output to QGIS as a new layer # TODO vermutlich so noch nicht richtig
    #     #    iface.addRasterLayer(path_to_tif, "layer name that you like")
    #     self.iface.addRasterLayer(self.ui.fw_outRasterSegmentsAvgColor().filePath(), # the file path, # TODO: Test it!!!!!!!!!!!
    #                               str.split(os.path.basename(outRasterFile), ".")[0])


    def rasterSegmentsAvgColor(self):


        # Nachfolgender code ist angepasst aus dem tutorial von:
        # https://opensourceoptions.com/blog/python-geographic-object-based-image-analysis-geobia/
        # Setup the GeoTiff driver of GDAL
        driverTiff = gdal.GetDriverByName('GTiff')  # get the GDAL GeoTiff file driver
        # get the raster file path and open it as raster_dataset in gdal
        raster_dataset = gdal.Open(self.inRaster.dataProvider().dataSourceUri()
                                   # self.inRaster.source() # wäre bei rasterio gegangen
                                   )                # use GDAL to open file from inRaster path

        self.nbands = raster_dataset.RasterCount    # get the number of raster bands
        band_data = []                              # create a list for the raster bands

        # Read in all bands of the raster dataset
        for i in range(1, self.nbands + 1):         # start with band as 1 up to the number of bands

            #band = raster_dataset.GetRasterBand(i).ReadAsArray()  # reads each band as ---> np array <---

            band = np.array(raster_dataset.GetRasterBand(i).ReadAsArray())  # reads each band as ---> np array <---

            #band = raster_dataset.GetRasterBand(1).ReadAsArray()  # reads each band as ---> np array <---
            # !!!! ACHTUNG TODO HIER BAND PICKER EINBAUEN, hab es manuell auf das 1. band gestelt: .GetRasterBand(1) # starts with 1

            band_data.append(band)  # append the band as a np array to the band_data list
        band_data_stack = np.dstack(band_data)  # put all in a single variable as a ---> stack of the bands <---

        # normalize the raster band values
        # scale image values from 0.0 - 1.0

        self.img_normalized = exposure.rescale_intensity(band_data_stack)
        # self.img_normalized ist jetzt normalized (values from 0.0 - 1.0)

        """
        import rasterio as rio
        #import rioxarray
        # code snipped from: https://gis.stackexchange.com/questions/37238/writing-numpy-array-to-raster-file?rq=1
        #with rio.open('other_file.tif') as src:

        #TODO DAS EINE ODER DAS ANDERE*******************
        with rio.open(self.inRaster.source()) as src:  # .source() gets the file path
        #with rio.open(self.inRaster) as src:  # .source() gets the file path
            ras_data = src.read()
            ras_meta = src.profile  # <- useful metadata of the input raster
            # will be necessary for the new image

            # make changes to the raster properties
            ras_meta['dtype'] = "int32"
            ras_meta['nodata'] = -999
        """

        # Label output zuweisen # TODO könnte so noch probleme geben, wenn mehrere Algos hintereinander berechnet werden.
        # TODO braucht eventuell noch sowas wie when changed?
        if self.ui.tabWidget.currentIndex() == 1:
            self.label = self.segments_slic
        # if self.segments_watershed is not None:
        if self.ui.tabWidget.currentIndex() == 2:
            self.label = self.segments_watershed
        # if self.segments_quickshift is not None:
        if self.ui.tabWidget.currentIndex() == 3:
            self.label = self.segments_quickshift
        # if self.segments_felzenszwalb is not None:
        if self.ui.tabWidget.currentIndex() == 4:
            self.label = self.segments_felzenszwalb
        else:
            print("NO VALID LABEL (SEGMENTS) FOUND")



        # Put segments on top of original image to compare# TODO: ACHTUNG nur SLIC!!!
        #ras_data = label2rgb(self.label, #self.label, #self.segments_slic,  #label,  #self.ui.le_outRaster.text(), #self.outRaster.source(), #label,  # label TODO hier richtigen input nehmen von jeweiligem Algo den output...
        rasterSegmentsAvgColor = label2rgb(self.label, #self.label, #self.segments_slic,  #label,  #self.ui.le_outRaster.text(), #self.outRaster.source(), #label,  # label TODO hier richtigen input nehmen von jeweiligem Algo den output...
        #rasterSegmentsAvgColor = label2rgb(self.segments_slic,  #label,  #self.ui.le_outRaster.text(), #self.outRaster.source(), #label,  # label TODO hier richtigen input nehmen von jeweiligem Algo den output...
                                           self.img_normalized,  # normalized_img_rgb,  #TODO: Original input aber normalisiert einbauen!!!
                                           kind='avg',
                                           bg_label=0)  # img muss 3 channels haben...
        """
        # Save the array using rasterio
        #with rio.open('outname.tif', 'w', **ras_meta) as dst:
        #with rio.open("C:/Users/username/Desktop/rasterSegmentsAvgColor.tif", 'w', **ras_meta) as dst:

        #with rio.open(self.ui.fw_outRasterSegmentsAvgColor().filePath(), 'w', **ras_meta) as dst:
        with rio.open(self.outRasterSegmentsAvgColor, 'w', **ras_meta) as dst:

        #with rio.open(self.ui.fw_outRasterSegmentsAvgColor().filePath(), 'w', **ras_meta) as dst:
            #dst.write(numpy_array, 1)
            #dst.write(rasterSegmentsAvgColor, 1)  # war 1
            #dst.write(ras_data, 1)  # war 1

            #dst.write(resultAVG)#, 1)  # war 1

            dst.write(resultAVG)#, 1)  # war 1
            # see: https://gis.stackexchange.com/questions/329925/rasterio-save-multiband-raster-to-tiff-file

        #outRasterFile = str(QFileDialog.getSaveFileName(caption="Save clipped raster as",
                                                        #filter="GeoTiff (*.tif)")[0])

        # rasterSegmentsAvgColor.rio.to_raster("C:/Users/username/Desktop/rasterSegmentsAvgColor.tif")#self.ui.fw_outRasterSegmentsAvgColor().filePath())
        """



        """ # Another try
        # ---> save segments to raster <----
        segments_fn = self.ui.fw_outRasterSegmentsAvgColor.filePath()  # get the name from the input field / picker

        # https://gis.stackexchange.com/questions/213937/in-gdal-how-to-save-3-dimensional-array-as-stacked-raster-image
        #DataSet = driver.Create(Name, Array.shape[2], Array.shape[1], Array.shape[0], DataType)

        #noDataValue = band_data[np.isnan(band_data)] # TODO Funktioniert noDataValue???
        segments_ds = driverTiff.Create(segments_fn,                   # create empty array recycle properties
                                        raster_dataset.RasterXSize,    # of raster_dataset
                                        raster_dataset.RasterYSize,
                                        #1,                             # 1 band
                                        #rasterSegmentsAvgColor.shape[-1], # if channels last
                                        band_data_stack.shape[-1], # if channels last
                                        #3, #muss noch dynamisch # TODO
                                        gdal.GDT_Float32)              # save as Float 32 values

        segments_ds.SetGeoTransform(raster_dataset.GetGeoTransform())  # transform
        segments_ds.SetProjection(raster_dataset.GetProjectionRef())   # assign the CRS

        #segments_ds.GetRasterBand(1).WriteArray(rasterSegmentsAvgColor)  # hier wird segments geschrieben

        #for i, image in enumerate(Array, 1):
        #for i, rasterSegmentsAvgColor in enumerate(band_data, 1):
        for i, rasterSegmentsAvgColor in enumerate(band_data_stack, 1):
            #DataSet.GetRasterBand(i).WriteArray(image)
            segments_ds.GetRasterBand(i).WriteArray(rasterSegmentsAvgColor)  # hier wird segments geschrieben
            #DataSet.GetRasterBand(i).SetNoDataValue(NDV)
            #segments_ds.GetRasterBand(i).SetNoDataValue(noDataValue)  # hier wird segments geschrieben

        #segments_ds.FlushCache()
        segments_ds = None # clear ram
        """


        # ---> save segments to raster <----
        segments_fn = self.ui.fw_outRasterSegmentsAvgColor.filePath()  # get the name from the input field / picker

        rasterSegmentsAvgColor() # TODO  ()









        # Funktion noch aufrufen per button!

        # Adds the output to QGIS as a new layer # TODO vermutlich so noch nicht richtig
        #    iface.addRasterLayer(path_to_tif, "layer name that you like")
        self.iface.addRasterLayer(self.ui.fw_outRasterSegmentsAvgColor().filePath(), # the file path, # TODO: Test it!!!!!!!!!!!
                                  #str.split(os.path.basename(self.outRasterSegmentsAvgColor), ".")[0])
                                  str.split(os.path.basename(self.outRasterSegmentsAvgColor), ".")[0], "gdal") # TODO : GDAL hinzugefügt


    def stylizeRasterSegments(self): # TODO noch nicht fertig
        """Changes the style of the visual appearance of the output raster"""
        # https://opensourceoptions.com/blog/loading-and-symbolizing-raster-layers/
        print("Hello Style!")

    # genial: https://create-qgis-plugin.readthedocs.io/en/latest/step2a_gui.html

    # TODO equivalent zu choose_image
    def loadRasters(self):  # looks through all rasters in the QGIS project // >> dropdown menu <<
        """Load all raster layers found in QGIS into a list "raster_layers" and add them in the combo box dropdown menu"""

        # TODO Deprecated war für altes öffnen
        firstStart=0
        if firstStart==0:
            self.appendText() # Todo ___________

            pass
        else:
            #self.ui.cb_inRaster.clear()  # clears the combo box beginning with the 2nd call of the loadRasters function
            pass
        firstStart+=1


        layers = [layer for layer in QgsProject.instance().mapLayers().values()]  # loop through all qgis layers
        raster_layers = []
        for layer in layers:
            if layer.type() == QgsMapLayer.RasterLayer:
                raster_layers.append(layer.name())   # append all found raster layers to the list
        self.ui.cb_inRaster.addItems(raster_layers)  # add the list of raster layers found in qgis to the combo box dopdown menu


        layer = self.ui.cb_inRaster.currentLayer()  # selects the currentLayer from the dropdown menu

        # TODO: Experiment** warscheinlich die falsche stelle, muss erst berechnet werden, wenn raster gewählt ist *****
        # If no raster was chosen, pass, else show rasters metadata
        #if raster_layers == 0:  # TODO eigentlich active layer == 0
        if layer is None:  # TODO eigentlich active layer == 0
            pass
        else:
            self.appendText()
            #self.ui.cb_inRaster.currentIndexChanged.connect(self.appendText)  # TODO aufruf anpassen

    # TODO equivalent zu browse_for_image
    def openRaster(self):
        """Open raster from file dialog"""

        global inRasterFile # expose inRasterFile as a global variable

        #inRasterFile = str(QFileDialog.getOpenFileName(caption="Open raster",
        #                                               filter="GeoTiff (*.tif, *.png *.jpeg *.jpg *.bmp)")[0])

        #path = QFileDialog.getOpenFileName(filter=QgsProviderRegistry.instance().fileRasterFilters())[0]
        inRasterFile = QFileDialog.getOpenFileName(caption="Open raster",
                                                   filter=QgsProviderRegistry.instance().fileRasterFilters())[0]

        # if a path to a raster file was chosen (not none),
        if inRasterFile is not None:
            # add this raster to QGIS as a layer with its basename as the layer name
            layer = self.iface.addRasterLayer(inRasterFile, str.split(os.path.basename(inRasterFile), ".")[0])

            # TODO: set this picked file on top of the list of the comboBox that gets filled with available raster layers in self.loadRasters()
            self.ui.cb_inRaster.setLayer(layer)
            ### TODO gerade auskommentiert abends
            #self.loadRasters()




            # Show a success message to the user:
            # see: https://docs.qgis.org/3.16/en/docs/pyqgis_developer_cookbook/communicating.html#showing-messages-the-qgsmessagebar-class
            self.iface.messageBar().pushMessage("Yeah!", "File was successfully opened!",
                                            level=Qgis.Success,
                                            duration=3)



    def saveRaster(self):
        """Get the save file name for the processed raster from a file dialog"""

        global outRasterFile  # expose outRasterFile as a global variable

        #outRasterFile = str(QFileDialog.getSaveFileName(caption="Save raster as",
        outRasterFile = str(self.ui.fw_outRaster.getSaveFileName(          # gets the file path
            caption="Save raster as",                                      # caption
            filter=QgsProviderRegistry.instance().fileRasterFilters())[0]  # file type filter
            # filter="GeoTiff (*.tif)")[0]
            )

        #self.setRasterLine(outRasterFile)

        # Show a success message to the user:
        # see: https://docs.qgis.org/3.16/en/docs/pyqgis_developer_cookbook/communicating.html#showing-messages-the-qgsmessagebar-class
        self.iface.messageBar().pushMessage("Yeah!", "File was successfully saved!",
                                            level=Qgis.Success,
                                            duration=3)
    # BACKUP VON VORHER
    #def saveRaster(self):
        """Get the save file name for the processed raster from a file dialog"""
        """
        global outRasterFile  # expose outRasterFile as a global variable

        #outRasterFile = str(QFileDialog.getSaveFileName(caption="Save raster as",
        outRasterFile = str(self.ui.fw_outRaster.getSaveFileName(caption="Save raster as",
                                                        filter="GeoTiff (*.tif)")[0])
        self.setRasterLine(outRasterFile)

        # Show a success message to the user:
        # see: https://docs.qgis.org/3.16/en/docs/pyqgis_developer_cookbook/communicating.html#showing-messages-the-qgsmessagebar-class
        self.iface.messageBar().pushMessage("Yeah!", "File was successfully saved!",
                                            level=Qgis.Success,
                                            duration=3)
    """

    def saveVector(self): # TODO: DEPRECATED not in use currently
        """Get the save file name for a computed vector file from a file dialog"""

        global outVectorFile

        #outVectorFile = str(QFileDialog.getSaveFileName(caption="Save vector as",
        outVectorFile = str(self.ui.fw_outRaster.getSaveFileName(
            caption="Save vector as",
            filter=QgsProviderRegistry.instance().fileVectorFilters()[0]))
            #filter="Shapefile (*.shp)")[0])

        # Show a success message to the user:
        # see: https://docs.qgis.org/3.16/en/docs/pyqgis_developer_cookbook/communicating.html#showing-messages-the-qgsmessagebar-class
        self.iface.messageBar().pushMessage("Yeah!", "File was successfully saved!",
                                            level=Qgis.Success,
                                            duration=3)

        # TODO deprecated self.setVectorLine(outVectorFile)


    # https://qgis.org/pyqgis/master/gui/QgsFileWidget.html


    def setRasterLine(self, text):
        """Set the chosen name of the output raster "outRaster" in the GUI element "le_outRaster" """
        self.ui.le_outRaster.setText(text)

        # self.ui.fw_outRaster.lineEdit.setText(text)
        #self.ui.fw_outRaster.lineEdit(text)

        # self.ui.fw_outRasterSegmentsAvgColor.lineEdit.setText(text)
        #self.ui.fw_outRasterSegmentsAvgColor.lineEdit(text)


    def setVectorLine(self, text):
        """Set the chosen name of the output vector "outVector" in the GUI element "le_outVector" """
        #self.ui.le_outVector.setText(text)


    def getRasterLayer(self):
        """Gets the in the combo box selected raster layer"""
        global layer  # expose variable layer as a global variable
        global layername  # expose variable layer as a global variable

        # WAR FRÜHER SO TODO layer = None
        layer = self.ui.cb_inRaster.currentLayer()
        layername = self.ui.cb_inRaster.currentText()  # assigns the chosen filename with the variable layername
        for lyr in QgsProject.instance().mapLayers().values():
            if lyr.name() == layername:
                layer = lyr
                break
        return layer



    def setVariables(self):
        #  -----> Get and set all variables from UI <-----

        # Algorithm chooser combobox: (entfernt)
        # self.ui.cb_algorithm.addItem("SLIC")
        # self.ui.cb_algorithm.addItem("A second Superpixel Algorithm")
        # index = self.ui.cb_algorithm.findText("SLIC", QtCore.Qt.MatchFixedString)  # um default item zu setzten
        # self.ui.cb_algorithm.setCurrentIndex(index)
        # um den Auswahlwert zu nutzen:
        # self.getAlgoChoice = self.ui.cb_algorithm.currentText()  # returns a string



        self.inRaster = self.getRasterLayer()  # path to the currently selected input raster file # TODO stimmt das? so?

        # VORHER OWN SAVE FIILE self.outRaster = self.ui.le_outRaster.text()  # path to the output segments raster file
        self.outRaster = self.ui.fw_outRaster.filePath()  # path to the output segments raster file
        #self.ui.fw_outRaster.fileChanged(self.saveRaster)

        self.outVector = self.ui.fw_outVector.filePath()  # TODO: ausprobieren
        #self.ui.fw_outVector.fileChanged.connect(self.saveVector)

        self.outVectorStats = self.ui.fw_outVectorStats.filePath()  # TODO: ausprobieren

        self.outRasterSegmentsAvgColor = self.ui.fw_outRasterSegmentsAvgColor.filePath()
        #self.ui.fw_outRasterSegmentsAvgColor.fileChanged(self.saveRaster)


        # TODO:::::::::::::::::::::::::::::
        #self.mQgsFileWidget.fileChanged.connect(self.getFileName) # see example: https://www.youtube.com/watch?v=AAYQz_2rrTo
        """
        # ist ja eine comboBox self.cb_inRaster.fileChanged.connect(self.getFileName)
        self.ui.cb_inRaster.fileChanged.connect(self.getFileName)
        # self.ui.fw_inRaster.connect(self.getFileName)
        self.ui.fw_outRasterSegmentsAvgColor.fileChanged.connect(self.getFileName)
        self.ui.fw_outVector.fileChanged.connect(self.getFileName)
        self.ui.fw_outRaster.fileChanged.connect(self.getFileName)
        """



        # VARIABLES
        
        # Variables of Algorithm > SLIC
        self.nSegments_slic = self.ui.spin_nSegments_slic.value()  #
        self.compactness_slic = self.ui.spin_compactness_slic.value()
        self.sigma_slic = self.ui.spin_sigma_slic.value()
        self.startLabel_slic = self.ui.spin_startLabel_slic.value()
        # Variables of Algorithm > Watershed
        self.markers_watershed = self.ui.spin_markers_watershed.value()  #
        self.compactness_watershed = self.ui.spin_compactness_watershed.value()
        # Variables of Algorithm > QuickShift
        self.kernelSize_quickshift = self.ui.spin_kernelSize_quickshift.value()
        self.maxDist_quickshift = self.ui.spin_maxDist_quickshift.value()
        self.ratio_quickshift = self.ui.spin_ratio_quickshift.value()
        # Variables of Algorithm > Felzenszwalb
        self.scale_felzenszwalb = self.ui.spin_scale_felzenszwalb.value()
        self.sigma_felzenszwalb = self.ui.spin_sigma_felzenszwalb.value()
        self.minSize_felzenszwalb = self.ui.spin_minSize_felzenszwalb.value()

        # ############# END SET VARIABLES ######################################







    def slic(self):
        """Compute the SLIC superpixel algorithm using the slic function of the scikit-image python library"""
        # See https://scikit-image.org/docs/dev/api/skimage.segmentation.html#skimage.segmentation.slic
        # from skimage.segmentation import slic # organize imports at the beginning / top

        self.progressBar.setValue(0)


        """ Dann doch einfach direkt eingebunden
        # prepare necessary vaiables
        img = self.inRaster.dataProvider().dataSourceUri()  # sollte der Pfad sein, oder # self.inRaster
        n_segments = self.nSegments
        compactness = self.compactness
        sigma = self.sigma
        startlabel = self.startLabel
        """
        """
        # Alternativ mit rasterio
        # https://rasterio.readthedocs.io/en/latest/quickstart.html#saving-raster-data
        # A dataset for storing the example grid is opened like so
        new_dataset = rasterio.open(
            '/tmp/new.tif',
            'w',
            driver = 'GTiff',
            height = Z.shape[0],
            width = Z.shape[1],
            count = 1,
            dtype = Z.dtype,
            crs = '+proj=latlong',
            transform = transform,)
        # Values for the height, width, and dtype keyword arguments are taken directly from attrib. of the 2-D array, Z.
        # Not all raster formats can support the 64-bit float values in Z, but the GeoTIFF format can.

        # Saving raster data
        new_dataset.write(Z, 1)
        new_dataset.close()
        """
        # ---> https://rasterio.readthedocs.io/en/latest/topics/writing.html <----
        # An array is written to a new single band TIFF.
        # For rasterio, see: https://rasterio.readthedocs.io/en/latest/quickstart.html

        # Nachfolgender code ist angepasst aus dem tutorial von:
        # https://opensourceoptions.com/blog/python-geographic-object-based-image-analysis-geobia/
        driverTiff = gdal.GetDriverByName('GTiff')  # GDAL assign GTiff file driver (besser rasterio nehmen?)
        #global raster_dataset # set as a global variable

        raster_dataset = gdal.Open(self.inRaster.dataProvider().dataSourceUri())  # use GDAL to open file from inRaster path

        self.nbands = raster_dataset.RasterCount  # get number of raster bands
        band_data = []  # create a list for the raster bands
        for i in range(1, self.nbands + 1):  # starting with band as 1
            band = raster_dataset.GetRasterBand(i).ReadAsArray()  # reads each band as ---> np array <---
            band_data.append(band)  # append the band as a np array to the band_data list
        band_data = np.dstack(band_data)  # put all in a single variable as a ---> stack of the bands <---

        self.progressBar.setValue(10)

        # Check if multiband data:
        # TODO HIER WENN MEHR BÄNDER; DANN
        # (height, width, channels) = img.shape[:3]
        if band_data.shape[-1] > 1:  # if more than 1 channel is present in image, than compute gradient image, else pass
            self.multichannel=True
        else:
            self.multichannel=False
        ##

        # normalize the raster band values
        # scale image values from 0.0 - 1.0
        self.img_normalized = exposure.rescale_intensity(band_data)

        self.progressBar.setValue(20)

        # ---> jetzt kommt SLIC <---
        # self.img_normalized ist jetzt normalized (values from 0.0 - 1.0)

        # TODO: update variables???
        self.setVariables()
        ########NEW################

        self.progressBar.setValue(30)

        self.segments_slic = slic(self.img_normalized,
                        n_segments=self.nSegments_slic,
                        compactness=self.compactness_slic,
                        sigma=self.sigma_slic,
                        # startlabel_slic=self.startLabel,
                        multichannel = self.multichannel)#=True  # TODO: eventuell noch checkbox einbauen?, siehe oben, oder besser als lambda function hier
                        #)  # max_iter = 10 standard # argument multichannel = true standard!!!

        self.progressBar.setValue(80)

        # ---> save segments to raster <----
        #segments_fn = self.outRaster  # to get the name from the input field or picker#

        segments_ds = driverTiff.Create(self.outRaster, #segments_fn,
                                        raster_dataset.RasterXSize,
                                        raster_dataset.RasterYSize,
                                        1,
                                        gdal.GDT_Float32)
        segments_ds.SetGeoTransform(raster_dataset.GetGeoTransform())  # transform
        segments_ds.SetProjection(raster_dataset.GetProjectionRef())  # assign the CRS
        segments_ds.GetRasterBand(1).WriteArray(self.segments_slic)  # hier wird segments geschrieben # hier oft Fehler mit Dimensions
        segments_ds = None
        # Funktion noch in der run function aufrufen!

        # Hardcoded aufruf des Ergebnis layers in QGIS
        #self.addLayers() # WORKING

        self.progressBar.setValue(100)

        # TODO' TEMPORARILY DISABLED ************ ~~~~~~~~~~~~~~~~~
        #self.checkCheckBoxStatus()

        ###############################
        # TESTWEISE TODO REMOVE??######## ()?
        self.addLayers()  # adds the last raster output to the QGIS Project


        # TODO: Vielleicht nur als temp zwischendatei, um dann die statistik zu berechnen?
        # Muss ja auch garnicht als Layer geladen werden.
        self.segments2Vector()  # REIHENFOLGE GETAUSCHT
        # Ist in def enthalten: self.iface.addVectorLayer(result['OUTPUT'], str.split(os.path.basename(self.outVector), ".")[0], "ogr")#str.split(os.path.basename(inRasterFile), ".")[0])  # adds/loads the resulting Vector layer to the QGIS project canvas

        self.vectorSegments2stats()
        # self.statistics()
        # self.addLayers()

        self.rasterSegmentsAvgColor()  # TODO WORKING ####### Reihenfolge geändert
        self.addLayers()

        ##############################

    def checkCheckBoxStatus(self):

        # Open output as new layer in QGIS, if checkBox isChecked
        if self.ui.checkBox_openAsLayerInQGIS.isChecked():
            self.addLayers()

            # self.ui.pb_run.clicked.connect(self.addLayers)  # Noch Ergebnis als layer hinzufügen!!!
            # self.ui.pb_run.clicked.connect(self.iface.addRasterLayer(self.outRaster, str.split(os.path.basename(self.outRaster), ".")[0]))
        else:
            # pass
            print("not checked")

        # Run the conversion of the rastersegment to vector polygon segments
        # segments2Vector contains an if clause that responds to the status of checkBox_createVectorSegments
        # if self.ui.checkBox_createVectorSegments.isChecked()==True:
        if self.ui.checkBox_createVectorSegments.isChecked():
            self.ui.pb_run.clicked.connect(self.segments2Vector)
        else:
            # pass
            print("not checked")

        """ direkt bei slic mal ausprobieren
        # Open output as new layer in QGIS, if checkBox isChecked
        if self.ui.checkBox_openAsLayerInQGIS.isChecked():
            #self.ui.pb_run.clicked.connect(self.addLayers)  # Noch Ergebnis als layer hinzufügen!!!
            self.ui.pb_run.clicked.connect(self.iface.addRasterLayer(self.outRaster, str.split(os.path.basename(self.outRaster), ".")[0]))
        else:
            pass"""

        if self.ui.checkBox_calculateOutRasterSegmentsAvgColor.isChecked():
            self.ui.pb_run.clicked.connect(self.rasterSegmentsAvgColor)
        else:
            pass


        # create segment statistics as vector
        if self.ui.checkBox_createVectorStatistics.isChecked():
            self.ui.pb_run.clicked.connect(self.vectorSegments2stats)
            self.ui.pb_run.clicked.connect(self.statistics) # TODO Läuft noch nicht, lieber die andere func nutzen, siehe oben
        else:
            #pass
            print("not checked")




    def watershed(self):
        """Compute the Watershed Superpixel algorithm using the watershed function of the scikit-image python library"""
        # See https://scikit-image.org/docs/dev/api/skimage.segmentation.html?highlight=watershed#skimage.segmentation.watershed
        # from skimage.segmentation import watershed # organize imports at the beginning / top

        # Nachfolgender code ist angepasst aus dem tutorial von:
        # https://opensourceoptions.com/blog/python-geographic-object-based-image-analysis-geobia/
        driverTiff = gdal.GetDriverByName('GTiff')  # GDAL assign GTiff file driver (besser rasterio nehmen?)
        raster_dataset = gdal.Open(self.inRaster.dataProvider().dataSourceUri())  # GDAL open file from inRaster path
        nbands = raster_dataset.RasterCount # get number of raster bands
        band_data = []                      # create a list for the raster bands
        for i in range(1, nbands + 1):      # starting with band as 1
            band = raster_dataset.GetRasterBand(i).ReadAsArray()  # reads each band as a ---> np array <---
            band_data.append(band)          # appends the band as a np array to the band_data
        band_data = np.dstack(band_data)    # put all in a single variable as a ---> stack of the bands <---

        # normalize the raster band values <<<<<<<<<<<<<<<<<< HIER NÖTIG? -> Ja, needs int als input
        # https://scikit-image.org/docs/dev/api/skimage.segmentation.html?highlight=watershed#skimage.segmentation.watershed
        # scale image values from 0.0 - 1.0
        img = exposure.rescale_intensity(band_data)

        # COMPACT WATERSHED
        from skimage.segmentation import watershed
        from skimage.filters import sobel
        from skimage.color import rgb2gray
        # Watershed needs a gradient, computed on a gray input image:
        
        # TODO HIER WENN MEHR BÄNDER; DANN
        # (height, width, channels) = img.shape[:3]
        if img.shape[-1] > 1:  # if more than 1 channel is present in image, than compute gradient image, else pass
            gradient = sobel(rgb2gray(img))
            # https://scikit-image.org/docs/dev/api/skimage.filters.html#skimage.filters.sobel
            # https://scikit-image.org/docs/dev/api/skimage.color.html?highlight=rgb2gray#skimage.color.rgb2gray
        else:
            gradient = img  # if the image has only one band, set it as gradient # TODO: Ist das in Ordnung?

        #gradient = sobel(rgb2gray(img)) # TODO: Check, if this is OK or needs my if clause aove
        
        self.segments_watershed = watershed(gradient,                          # input is the grayscale gradient image
                                       markers=self.markers_watershed,         # get markers value from spinbox in ui
                                       compactness=self.compactness_watershed) # get compactness ...

        # ---> save segments to raster <----
        segments_fn = self.outRaster  # to get the name from the input field or picker
        segments_ds = driverTiff.Create(segments_fn,
                                        raster_dataset.RasterXSize,
                                        raster_dataset.RasterYSize,
                                        1,  # 1 Kanal output!!!!
                                        gdal.GDT_Float32)
        segments_ds.SetGeoTransform(raster_dataset.GetGeoTransform())   # transform
        segments_ds.SetProjection(raster_dataset.GetProjectionRef())    # assign the CRS
        segments_ds.GetRasterBand(1).WriteArray(self.segments_watershed)     # hier wird segments geschrieben <<<<<<<<<<<<<
        segments_ds = None
        # Funktion noch in der run function aufrufen!

        self.checkCheckBoxStatus()


    # QUICKSHIFT
    from skimage.segmentation import quickshift
    # See: https://scikit-image.org/docs/dev/api/skimage.segmentation.html?highlight=quickshift#skimage.segmentation.quickshift
    # segments_quick = quickshift(img, kernel_size=3, max_dist=max_dist, ratio=ratio)
    def quickshift(self):
        """
        # Alternativ mit rasterio
        # https://rasterio.readthedocs.io/en/latest/quickstart.html#saving-raster-data
        # A dataset for storing the example grid is opened like so
        new_dataset = rasterio.open(
            '/tmp/new.tif',
            'w',
            driver = 'GTiff',
            height = Z.shape[0],
            width = Z.shape[1],
            count = 1,
            dtype = Z.dtype,
            crs = '+proj=latlong',
            transform = transform,)
        # Values for the height, width, and dtype keyword arguments are taken directly from attrib. of the 2-D array, Z.
        # Not all raster formats can support the 64-bit float values in Z, but the GeoTIFF format can.

        # Saving raster data
        new_dataset.write(Z, 1)
        new_dataset.close()
        """
        # ---> https://rasterio.readthedocs.io/en/latest/topics/writing.html <----
        # An array is written to a new single band TIFF.
        # For rasterio, see: https://rasterio.readthedocs.io/en/latest/quickstart.html

        # Nachfolgender code ist angepasst aus dem Tutorial von:
        # https://opensourceoptions.com/blog/python-geographic-object-based-image-analysis-geobia/
        driverTiff = gdal.GetDriverByName('GTiff')  # GDAL assign GTiff file driver (besser rasterio nehmen?)
        raster_dataset = gdal.Open(self.inRaster.dataProvider().dataSourceUri())  # GDAL open file from inRaster path
        nbands = raster_dataset.RasterCount  # get number of raster bands
        band_data = []                       # create a list for the raster bands
        for i in range(1, nbands + 1):       # starting with band as 1
            band = raster_dataset.GetRasterBand(i).ReadAsArray()  # reads each band as ---> np array <---
            band_data.append(band)           # appends the band as a np array to the band_data list
        band_data = np.dstack(band_data)     # put all in a single variable as a ---> stack of the bands <---

        # normalize the raster band values <<<<<<<<<<<<<<<<<< HIER NÖTIG? -> NEIN, image as ndarray (width, height, channels) als input
        # https://scikit-image.org/docs/dev/api/skimage.segmentation.html?highlight=watershed#skimage.segmentation.watershed
        # scale image values from 0.0 - 1.0
        img = exposure.rescale_intensity(band_data)



        #img = band_data  # image soll sein image(width, height, channels) ndarray

        from skimage.segmentation import quickshift
        # See: https://scikit-image.org/docs/dev/api/skimage.segmentation.html?highlight=watershed#skimage.segmentation.quickshift
        # segments_quick = quickshift(img, kernel_size=3, max_dist=max_dist, ratio=ratio)

        #quickshift(image, ratio=1.0, kernel_size=5, max_dist=10,return_tree=False, sigma=0, convert2lab=True, random_seed=42):
        self.segments_quickshift = quickshift(img,
                                         kernel_size=self.kernelSize_quickshift,
                                         max_dist=self.maxDist_quickshift,  # float
                                         ratio=self.ratio_quickshift,  # float von 0 bis 1
                                         convert2lab=False, # For 1 Grayband set to  False
                                         random_seed=42
                                         )

        # ---> save segments to raster <----
        #segments_fn = self.outRaster  # get the name for the output raster from the ui input field or picker
        segments_ds = driverTiff.Create(self.outRaster, #segments_fn,   # save a raster (*.tif) with the chosen name
                                        raster_dataset.RasterXSize,
                                        raster_dataset.RasterYSize,
                                        1,                              # output is 1 band <<<<<<<<<<<
                                        #self.segments_quickshift)
                                        gdal.GDT_Float32)
        segments_ds.SetGeoTransform(raster_dataset.GetGeoTransform())   # transform
        segments_ds.SetProjection(raster_dataset.GetProjectionRef())    # assign the CRS
        segments_ds.GetRasterBand(1).WriteArray(self.segments_quickshift)    # write segments <<<<<<<<<<<<<
        segments_ds = None                                              # clear to free resources
        # Funktion noch in der run function aufrufen!

        self.checkCheckBoxStatus()
        
        
        
        
        
        
    # FELZENSZWALB
    from skimage.segmentation import felzenszwalb
    # See: https://scikit-image.org/docs/dev/api/skimage.segmentation.html?highlight=felzenszwalb#skimage.segmentation.felzenszwalb
    # segments_felzenszwalb = felzenszwalb(img, scale=100, sigma=0.5, min_size=400)
    def felzenszwalb(self):

        """
        # Alternativ mit rasterio
        # https://rasterio.readthedocs.io/en/latest/quickstart.html#saving-raster-data
        # A dataset for storing the example grid is opened like so
        new_dataset = rasterio.open(
            '/tmp/new.tif',
            'w',
            driver = 'GTiff',
            height = Z.shape[0],
            width = Z.shape[1],
            count = 1,
            dtype = Z.dtype,
            crs = '+proj=latlong',
            transform = transform,)
        # Values for the height, width, and dtype keyword arguments are taken directly from attrib. of the 2-D array, Z.
        # Not all raster formats can support the 64-bit float values in Z, but the GeoTIFF format can.

        # Saving raster data
        new_dataset.write(Z, 1)
        new_dataset.close()
        """
        # ---> https://rasterio.readthedocs.io/en/latest/topics/writing.html <----
        # An array is written to a new single band TIFF.
        # For rasterio, see: https://rasterio.readthedocs.io/en/latest/quickstart.html

        # Nachfolgender code ist angepasst aus dem tutorial von:
        # https://opensourceoptions.com/blog/python-geographic-object-based-image-analysis-geobia/
        driverTiff = gdal.GetDriverByName('GTiff')  # GDAL assign GTiff file driver (besser rasterio nehmen?)
        raster_dataset = gdal.Open(self.inRaster.dataProvider().dataSourceUri())  # GDAL open file from inRaster path
        nbands = raster_dataset.RasterCount  # get number of raster bands
        band_data = []  # create a list for the raster bands
        for i in range(1, nbands + 1):  # starting with band as 1
            band = raster_dataset.GetRasterBand(i).ReadAsArray()  # reads each band as ---> np array <---
            band_data.append(band)  # append the band as a np array to the band_data list
        band_data = np.dstack(band_data)  # put all in a single variable as a ---> stack of the bands <---

        # normalize the raster band values <<<<<<<<<<<<<<<<<< HIER NÖTIG? -> NEIN, image as ndarray (width, height, channels) als input
        # https://scikit-image.org/docs/dev/api/skimage.segmentation.html?highlight=watershed#skimage.segmentation.watershed
        # scale image values from 0.0 - 1.0
        #img = exposure.rescale_intensity(band_data)



        img = band_data  # image soll sein image(width, height, channels) ndarray


        self.multichannel_felzenszwalb = True # because last axis means channels.

        from skimage.segmentation import felzenszwalb
        # See: https://scikit-image.org/docs/dev/api/skimage.segmentation.html?highlight=felzenszwalb#skimage.segmentation.felzenszwalb
        # segments_felzenszwalb = felzenszwalb(img, scale=100, sigma=0.5, min_size=400)
        self.segments_felzenszwalb = felzenszwalb(img,
                                                  scale=self.scale_felzenszwalb,
                                                  sigma=self.sigma_felzenszwalb,
                                                  min_size=self.minSize_felzenszwalb,
                                                  multichannel=self.multichannel_felzenszwalb)

        # ---> save segments to raster <----
        # segments_fn = self.outRaster  # to get the name from the input field or picker
        segments_ds = driverTiff.Create(self.outRaster, #segments_fn,
                                        raster_dataset.RasterXSize,
                                        raster_dataset.RasterYSize,
                                        1,  # 1 Kanal output!!!!
                                        gdal.GDT_Float32)
        segments_ds.SetGeoTransform(raster_dataset.GetGeoTransform())   # transform
        segments_ds.SetProjection(raster_dataset.GetProjectionRef())    # assign the CRS
        segments_ds.GetRasterBand(1).WriteArray(self.segments_felzenszwalb)  # hier wird segments geschrieben <<<<<<<<<<<<<
        segments_ds = None
        # Funktion noch in der run function aufrufen!

        self.checkCheckBoxStatus()


    ################
    def switchTab(self):
        # Setting the current active tab by index nr. WORKS
        # self.ui.tabWidget.setCurrentIndex(4)
        # set active tab by name, see example:
        # https://stackoverflow.com/questions/45828478/how-to-set-current-tab-of-qtabwidget-by-name
        self.ui.tabWidget.setCurrentWidget(self.ui.tabWidget.findChild(QWidget, "tab_slic"))

        # TODO: BAUSTELLE:::::::::::::::
        #def runSelectedTabAlgorithm(self):  # TODO: woanders hin schieben

        # Runs the algorithm of the opened tab
        #####  see: https://stackoverflow.com/questions/63122385/pyqt5-tab-widget-how-can-i-get-the-index-of-active-tab-window-on-mouse-click
        # run this line in the init function:
        #self.ui.tabwidget.tabBarClicked.connect(self.handle_tabbar_clicked)  # every time the tab is clicked, its index is send to the function


    # TODO STATISTICS +++++++++++ WIE OUTPUT GESTALTEN?
    def statistics(self):
        # Calculates raster statistics

        # see: https://gis.stackexchange.com/questions/188294/using-zonal-stats-with-python-in-qgis-to-calculate-statistics-for-each-image/188303#188303
        
        # >>> see: https://github.com/perrygeo/python-rasterstats

        # https://pythonhosted.org/rasterstats/manual.html#basic-example

        ##  calculate statistics for each image that I have with a specify shapefile and save result after
        # You need to use layer.source() to get the path of the rasters which is required by the zonal_stats module.
        # Your code should look like:
        from rasterstats import zonal_stats
        #layers = QgsMapLayerRegistry.instance().mapLayers().values()
        #layers = self.iface.instance().mapLayers().values()
        layers = self.inRaster
        for layer in layers:
            #stats = zonal_stats("/home/myshape.shp", layer.source())
            vectorStats = zonal_stats(self.outVector, # vector input
                                layer.source(), # raster input
                                stats = ['count',
                                         'min',
                                         'max',
                                         'mean',
                                         'median',
                                         'majority',
                                         'sum',
                                         'std',
                                         'minority',
                                         'unique',
                                         'range',
                                         'nodata'])

            #[OUTPUT] : vectorStats

        ### TODO eventuell mit geopandas als shp file speichern???

        # eventuell mit merge? # https://geopandas.org/docs/user_guide/mergingdata.html
        #name_gdf.to_file("name.shp")





        ### ODER, see: https://nbviewer.jupyter.org/github/perrygeo/python-rasterstats/blob/master/docs/notebooks/Basic%20Usage.ipynb
        #from rasterstats import raster_stats
        #elev = '/data/projects/murdock/zonal_fcid_test/dem_aea2_feet.tif'
        #polys = '/data/projects/murdock/zonal_fcid_test/fcid.shp'
        #stats = raster_stats(polys, elev, stats="*")
        #len(stats)




    """
    def rasterToVector(self):
        #Convert the raster segments to vector

        # load the raster segments
        # segments bei jedem algo als globale variable bereitstellen! TODO
        # TODO:::::::::::::::::::::::::::::::
        # DER CODE HIER PASST NOCH NICHT:
        driverTiff = gdal.GetDriverByName('GTiff')  # GDAL assign GTiff file driver (besser rasterio nehmen?)
        raster_dataset = gdal.Open(self.inRaster.dataProvider().dataSourceUri())  # GDAL open file from inRaster path
        nbands = raster_dataset.RasterCount  # get number of raster bands
        band_data = []  # create a list for the raster bands
        for i in range(1, nbands + 1):  # starting with band as 1
            band = raster_dataset.GetRasterBand(i).ReadAsArray()  # reads each band as ---> np array <---
            band_data.append(band)  # append the band as a np array to the band_data list
        band_data = np.dstack(band_data)  # put all in a single variable as a ---> stack of the bands <---

        # normalize the raster band values
        # scale image values from 0.0 - 1.0
        img = exposure.rescale_intensity(band_data)


        # TAKE THE SEGMENTS raster file
        self.rasterSegments()  # muss als globale variable bereit gestellt werden // global x


        # TODO TODO DOTODODODODODODO
        # Convert a Raster to a Vector using GDAL
        # Code from: https://subscription.packtpub.com/book/big_data_and_business_intelligence/9781783555079/3/ch03lvl1sec29/converting-a-raster-geotiff-to-a-vector-shapefile-using-gdal

        # !/usr/bin/env python
        # -*- coding: utf-8 -*-

        #  Import the ogr and gdal modules and go straight ahead
        #  and open the raster we want to convert by passing it the filename on disk and getting a raster band:
        from osgeo import ogr
        from osgeo import gdal

        #  get raster data source
        # example: https://gis.stackexchange.com/questions/144058/loading-raster-layer-using-pyqgis?rq=1

        # open_image = gdal.Open( "../geodata/cadaster_borders-2tone-black-white.png" )
        open_image = gdal.Open("../geodata/cadaster_borders-2tone-black-white.png")

        # input_band = open_image.GetRasterBand(3)
        input_band = open_image.GetRasterBand(3)

        #input_band = gdal.Open(self.setRasterLine(outFile))  # <<<<<<<<<<<<<<

        #  Set up the output vector file as a Shapefile with output_shp, and then get a Shapefile driver.
        #  Now, we can create the output from our driver and create a layer as follows:
        #  create output data source
        output_shp = "../geodata/cadaster_raster"
        shp_driver = ogr.GetDriverByName("ESRI Shapefile")

        #  create output file name
        output_shapefile = shp_driver.CreateDataSource(output_shp + ".shp")
        new_shapefile = output_shapefile.CreateLayer(output_shp, srs=None)

        #  The final step is to run the gdal.Polygonize function that does the heavy lifting
        #  by converting our raster to a vector as follows:
        gdal.Polygonize(input_band, None, new_shapefile, -1, [], callback=None)
        new_shapefile.SyncToDisk()

        #  Execute the new script as follows:
        # $ python ch03-06_raster2shp.py
    """


    def addLayers(self):
        """Add raster to QGIS map interface"""
        rlayer = self.iface.addRasterLayer(self.outRaster, str.split(os.path.basename(self.outRaster), ".")[0])
        #rlayer.renderer().setOpacity(0.7)  # add styling # TODO Throws an error 'NoneType' object has no attribute 'renderer'
        # transparency
        # see: https://gis.stackexchange.com/questions/154323/qgis-set-all-layers-with-custom-transparency-with-python?noredirect=1&lq=1


    def openWebsite(self, url):
        """
        Opens URL in a web browser

        :return: open website in browser
        """
        QDesktopServices.openUrl(QUrl(url))


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr('Superpixelplugin'),  # 'Superpixelplugin'),  # u'&Test SLIC'),
                action)
            self.iface.removeToolBarIcon(action)

        # removes the processing plugins
        #QgsApplication.processingRegistry().removeProvider(self.provider)


    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started

        # show the dialog ############# => jetzt ja das MainWindow
        self.ui.show()

        # Run the dialog event loop
        #result = self.ui.exec_() ##################--------------------------

        #self.loadRasters()
        # self.loadVectors()
        # self.getAlgoChoice()
        """
        # OK Button löst Funktionen aus
        self.accepted.connect(self.setVariables(),  # GUI eingegebene parameter einlesen
                              self.slic(),
                              self.addLayers()
                              )
        """
        # EXPERIMENT
        #self.setVariables()

        # GUI eingegebene parameter einlesen
        #self.ui.pb_run.clicked.connect(self.slic())

        # self.addLayers() # Noch layer hinzufügen!!!

        # https://gis.stackexchange.com/questions/354346/qgis-plugin-with-dockwidget-and-mainwindow
        #result = self.ui.exec_()
        """
        # See if OK was pressed ----> ETWA IN RUN BUTTON CLICKED EINBAUEN?
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            # pass
            # Die gewünschten Funktionen bei OK click ausführen!
            self.setVariables()  # erst variablen aus GUI eingabe in variablen speichern und als parameter übernehmen

            self.loadRasters()

            # Eventuell if checked checkbox enabled:
            self.slic()  # die parametrisierte slic function ausführen

            # self.watershed()
            # self.felzenszwalb()
            # self.quickshift()

            # Load and show result as layer in QGIS
            # vielleicht if load layers combobox checked is true, dann:
            self.addLayers()  # die Ergebnisse in QGIS als layer laden
        """

        # , TODO:::: https://create-qgis-plugin.readthedocs.io/en/latest/step2a_gui.html
        # set_progress = self.progressBar.setValue(100),
        # log = self.log



# In case the GUI would be run standalone from commandline (As an application)
if __name__ == '__main__':
    app = QgsApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec_()
             )
