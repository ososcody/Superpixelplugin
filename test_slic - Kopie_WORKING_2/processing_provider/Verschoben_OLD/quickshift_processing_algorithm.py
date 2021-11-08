# Skript build arount the boiler plate code from:
# https://gis.stackexchange.com/questions/282773/writing-a-python-processing-script-with-qgis-3-0?rq=1
# See API: https://qgis.org/pyqgis/3.16/core/QgsProcessingAlgorithm.html
# And: https://docs.qgis.org/3.16/en/docs/pyqgis_developer_cookbook/processing.html

import numpy as np  # eventuell rasterio nehmen?
import gdal
from osgeo import gdal
from osgeo.gdalconst import GDT_Float32
from qgis.core import QgsProcessingParameterFeatureSource
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterRasterDestination


from skimage import exposure
#from skimage.segmentation import slic  # import slic
from skimage.segmentation import quickshift
#from skimage.segmentation import watershed
#from skimage.segmentation import felzenszwalb
#from skimage.color import label2rgb  # Import the label2rgb function from the color module

from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterRasterDestination)

from qgis import processing

class SuperpixelProcessingPluginQuickShift(QgsProcessingAlgorithm):  # Class inherits from QgsProcessingAlgorithm
    INPUT_RASTER_A = 'INPUT_RASTER_A'
    # INPUT_RASTER_B = 'INPUT_RASTER_B'

    # INPUT_DOUBLE = 'INPUT_DOUBLE'

    KERNELSIZE = 'KERNELSIZE'
    MAXDIST = 'MAXDIST'
    RATIO = 'RATIO'

    OUTPUT_RASTER_A = 'OUTPUT_RASTER_A'

    # OUTPUT_RASTER_B = 'OUTPUT_RASTER_B'

    def __init__(self):
        super().__init__()

    def name(self):
        return "QuickShift"

    def tr(self, text):
        return QCoreApplication.translate("Superpixel Processing Plugin - QuickShift Algorithm", text)

    def displayName(self):
        return self.tr("Superpixelplugin - QuickShift Algorithm")

    def group(self):
        return self.tr("Superpixelalgorithms")

    def groupId(self):
        return "superpixelalgorithms"

    def shortHelpString(self):
        return self.tr("The QuickShift Superpixel Algorithm, \n"
                       "originally proposed by VEDALDI et al. (2008), see: Vedaldi, A. & Soatto, S. (2008). "
                       "Quick Shift and Kernel Methods For Mode Seeking, European Conference on Computer Vision (S. 705–718)., "
                       "here in the implementation of "
                       "Scikit-image, see: van der Walt, S., Schönberger, J.L., Nunez-Iglesias, J., & Boulogne, F., et al. (2014). "
                       "Scikit-image: Image Processing in Python. PeerJ, 2, e453. DOI 10.7717/peerj.453"
                       "\n"
                       "Parameters: \n"
                       "Kernelsize: "
                       "Setting a high width for the smoothing Gaussian kernel results in lesser segments."
                       "\n"
                       "Maximum Distances: "
                       "A high maximum distance means the cut-off limit for the distances produces less segments."
                       "\n"
                       "Ratio: Set a value from 0 to 1."
                       "A higher ratio increases the weight of the color-space."
                       )

    def helpUrl(self):
        return "https://qgis.org"

    def createInstance(self):
        return SuperpixelProcessingPluginQuickShift()

    def initAlgorithm(self, config=None):
        # See: https://docs.qgis.org/3.16/en/docs/user_manual/processing/scripts.html

        """
        # See: https://gis.stackexchange.com/questions/377793/how-to-group-parameters-in-pyqgis-processing-plugin
        param = QgsProcessingParameterString(
            self.NAME_OF_THE_PARAMETER,
            tr('Your label'),
            optional=False,
            defaultValue='If any default)

        # The line below will take default flags already there and adds the Advanced one
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        """

        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT_RASTER_A,
                #self.tr("Input Raster A")))  #, None, False))
                self.tr("Input Raster A"), None, False))

        # self.addParameter(QgsProcessingParameterRasterLayer(
        #    self.INPUT_RASTER_B,
        #    self.tr("Input Raster B"), None, False))



        #self.addParameter(
        #    QgsProcessingParameterFeatureSource(
        #        self.INPUT_RASTER_A,
        #        self.tr('Input layer'),
        #        [QgsProcessing.TypeRaster]#VectorAnyGeometry]
        #    )
        #)



        # self.addParameter(QgsProcessingParameterNumber(
        #    self.INPUT_DOUBLE,
        #    self.tr("Input Double"),
        #    QgsProcessingParameterNumber.Double,
        #    QVariant(1.0)))


        self.addParameter(QgsProcessingParameterNumber(
            self.KERNELSIZE,
            self.tr("Kernel Size"),
            QgsProcessingParameterNumber.Double,
            QVariant(5)))

        self.addParameter(QgsProcessingParameterNumber(
            self.MAXDIST,
            self.tr("Max. Distance"),
            QgsProcessingParameterNumber.Double,
            QVariant(10)))

        self.addParameter(QgsProcessingParameterNumber(
            self.RATIO,
            self.tr("Ratio"),
            QgsProcessingParameterNumber.Double,
            QVariant(1.0)))

        self.addParameter(QgsProcessingParameterRasterDestination(  # RASTER OUTPUT
            self.OUTPUT_RASTER_A,
            self.tr("Output Raster Segments"),
            None, False))

        # self.addParameter(QgsProcessingParameterRasterDestination(
        #    self.OUTPUT_RASTER_B,
        #    self.tr("Output Raster B"),
        #    None, False))

    def processAlgorithm(self, parameters, context, feedback):
        #raster_a = self.parameterAsRasterLayer(parameters, self.INPUT_RASTER_A, context)
        #raster_a = self.parameterAsRasterLayer(parameters, self.INPUT_RASTER_A, context)
        # raster_b = self.parameterAsRasterLayer(parameters, self.INPUT_RASTER_B, context)

        # Experiment, ob AsSource oder AsRasterLayer...
        # TODO raster_a = self.parameterAsSource(parameters, self.INPUT_RASTER_A, context)
        self.raster_a = self.parameterAsRasterLayer(parameters, self.INPUT_RASTER_A, context)
        # !!!! JETZT HIER GANZ WICHTIG DIESER SCHRITT::
        # Code snippet verändert nach: https://gis.stackexchange.com/questions/357074/save-numpy-array-as-raster-in-a-processing-toolbox-qgis3
        # set provider to raster input as a dataProvider
        provider = self.raster_a.dataProvider()
        # get the filepath of the input raster as a string
        self.filepath_raster_a = str(provider.dataSourceUri())
        # ~~~~

        # See filetypes: https://qgis.org/pyqgis/3.16/core/QgsProcessingAlgorithm.html
        # double_val = self.parameterAsDouble(parameters, self.INPUT_DOUBLE,context)
        self.maxDist_quickshift = self.parameterAsDouble(parameters, self.MAXDIST, context)
        self.kernelSize_quickshift = self.parameterAsDouble(parameters, self.KERNELSIZE, context)
        self.ratio_quickshift = self.parameterAsDouble(parameters, self.RATIO, context)

        output_path_raster_a = self.parameterAsOutputLayer(parameters, self.OUTPUT_RASTER_A, context)
        # output_path_raster_b = self.parameterAsOutputLayer(parameters, self.OUTPUT_RASTER_B, context)

        # DO SOME CALCULATION

        # Nachfolgender code ist angepasst aus dem tutorial von:
        # https://opensourceoptions.com/blog/python-geographic-object-based-image-analysis-geobia/
        driverTiff = gdal.GetDriverByName('GTiff')  # GDAL assign GTiff file driver (besser rasterio nehmen?)
        # global raster_dataset # set as a global variable

        raster_dataset = gdal.Open(
            #self.inRaster.dataProvider().dataSourceUri())  # use GDAL to open file from inRaster path
            #self.INPUT_RASTER_A.source())#.dataProvider().dataSourceUri())
            # TODO::::
            self.filepath_raster_a)

        self.nbands = raster_dataset.RasterCount  # get number of raster bands
        band_data = []  # create a list for the raster bands
        for i in range(1, self.nbands + 1):  # starting with band as 1
            band = raster_dataset.GetRasterBand(i).ReadAsArray()  # reads each band as ---> np array <---
            band_data.append(band)  # append the band as a np array to the band_data list
        band_data = np.dstack(band_data)  # put all in a single variable as a ---> stack of the bands <---

        # self.progressBar.setValue(10)
        # ---> https://rasterio.readthedocs.io/en/latest/topics/writing.html <----
        # An array is written to a new single band TIFF.
        # For rasterio, see: https://rasterio.readthedocs.io/en/latest/quickstart.html


        # normalize the raster band values <<<<<<<<<<<<<<<<<< HIER NÖTIG? -> NEIN, image as ndarray (width, height, channels) als input
        # https://scikit-image.org/docs/dev/api/skimage.segmentation.html?highlight=watershed#skimage.segmentation.watershed
        # scale image values from 0.0 - 1.0
        img = exposure.rescale_intensity(band_data)        # TODO NORMALIZEN?

        #img = band_data  # image soll sein image(width, height, channels) ndarray

        from skimage.segmentation import quickshift
        # See: https://scikit-image.org/docs/dev/api/skimage.segmentation.html?highlight=watershed#skimage.segmentation.quickshift
        # segments_quick = quickshift(img, kernel_size=3, max_dist=max_dist, ratio=ratio)

        """
        # Check if multiband data:
        # TODO HIER WENN MEHR BÄNDER; DANN
        # (height, width, channels) = img.shape[:3]
        if band_data.shape[-1] > 1: # if more than 1 channel is present in image, than compute gradient image, else pass
            self.multichannel = True
        else:
            self.multichannel = False

        # normalize the raster band values
        # scale image values from 0.0 - 1.0
        self.img_normalized = exposure.rescale_intensity(band_data)

        # self.progressBar.setValue(20)

        # ---> jetzt kommt QuickShift <---
        # self.img_normalized ist jetzt normalized (values from 0.0 - 1.0)

        # TODO: update variables???
        #self.setVariables()
        # ~~~~ NEW ~~~

        # self.progressBar.setValue(30)
        """

        self.segments_quickshift = quickshift(image=img,
                                              kernel_size=self.kernelSize_quickshift,
                                              max_dist=self.maxDist_quickshift,
                                              ratio=self.ratio_quickshift,
                                              random_seed=42,
                                              convert2lab=False) # For 1 Grayband set to  False
                                              #multichannel=self.multichannel)  # =True  # TODO: eventuell noch checkbox einbauen?
        # )  # max_iter = 10 standard # argument multichannel = true standard!!!

        # self.progressBar.setValue(80)

        # ---> save segments to raster <----
        # segments_fn = self.outRaster  # to get the name from the input field or picker#

        segments_ds = driverTiff.Create(output_path_raster_a, # TODO  self.OUTPUT_RASTER_A,  # self.outRaster,  # segments_fn,
                                        raster_dataset.RasterXSize,
                                        raster_dataset.RasterYSize,
                                        1,
                                        #gdal.DataType(self.segments_quickshift)) # raster_dataset.DataType)
                                        gdal.GDT_Float32)  # TODO Typ automatisch wäre besser?
        segments_ds.SetGeoTransform(raster_dataset.GetGeoTransform())  # transform
        segments_ds.SetProjection(raster_dataset.GetProjectionRef())  # assign the CRS
        segments_ds.GetRasterBand(1).WriteArray(self.segments_quickshift)  # hier wird segments geschrieben
        segments_ds = None

        """
        results = {}
        results[self.OUTPUT_RASTER_A] = output_path_raster_a
        # results[self.OUTPUT_RASTER_B] = output_path_raster_b
        return results
        """
        return {self.OUTPUT_RASTER_A: output_path_raster_a}
