# Boilerplate code taken from: https://docs.qgis.org/3.16/en/docs/pyqgis_developer_cookbook/processing.html

from qgis.core import QgsProcessingProvider
#from qgis.PyQt.QtGui import QIcon

# from processing_provider.example_processing_algorithm import ExampleProcessingAlgorithm
# from processing_provider.rasteralg import RasterAlg

from slic_processing_algorithm import SuperpixelProcessingPluginSLIC
# from processing_provider.quickshift_processing_algorithm import SuperpixelProcessingPluginQuickShift
# from processing_provider.watershed_processing_algorithm import SuperpixelProcessingPluginWatershed
# from processing_provider.felzenszwalb_processing_algorithm import SuperpixelProcessingPluginFelzenszwalb

class MyProcessingProvider(QgsProcessingProvider):
    # Load and add the superpixel algorithms to the processing tools
    def loadAlgorithms(self, *args, **kwargs):
        # self.addAlgorithm(ExampleProcessingAlgorithm())
        # self.addAlgorithm(RasterAlg())
        self.addAlgorithm(SuperpixelProcessingPluginSLIC())
        # self.addAlgorithm(SuperpixelProcessingPluginQuickShift())
        # self.addAlgorithm(SuperpixelProcessingPluginWatershed())
        # self.addAlgorithm(SuperpixelProcessingPluginFelzenszwalb())

    def id(self, *args, **kwargs):
        """The ID of your plugin, used for identifying the provider.

        This string should be a unique, short, character only string,
        eg "qgis" or "gdal". This string should not be localised.
        """
        return 'my_plugin_provider'

    def name(self, *args, **kwargs):
        """The human friendly name of your plugin in Processing.

        This string should be as short as possible (e.g. "Lastools", not
        "Lastools version 1.0.1 64-bit") and localised.
        """
        return self.tr('My Plugin Section')#Superpixelplugin')

    def icon(self):
        """Should return a QIcon which is used for your provider inside
        the Processing toolbox.
        """
        return QgsProcessingProvider.icon(self)
