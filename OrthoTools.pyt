import arcpy
import os
import getpass
import unicodedata
import xml.etree.ElementTree as ET
import linecache
#Sets scratch environment
user = getpass.getuser()#gets user name
gdbPath = os.path.join("C:/Users/" + user.lower() + "/Documents/ArcGIS/Default.gdb") #sets workspace to the users default gdb



class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "OrthoTools"
        self.alias = "OrthoTools"
        # List of tool classes associated with this toolbox
        self.tools = [DeliveryTilesDGNtoSHP, ADSFltInfotoSHP, AirportBoundaryCreator, TileLayout, USNGTileLayout, RasterFootprint, OverlapTiles]


class DeliveryTilesDGNtoSHP(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "DeliveryTiles DGN to SHP"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        # DGN_Polygon
        param_1 = arcpy.Parameter()
        param_1.name = u'DGN_Path'
        param_1.displayName = u'DGN Path'
        param_1.parameterType = 'Required'
        param_1.direction = 'Input'
        param_1.datatype = u'CAD Drawing Dataset'

        # Output_Shapefile
        param_2 = arcpy.Parameter()
        param_2.name = u'Output_Shapefile'
        param_2.displayName = u'Output Shapefile'
        param_2.parameterType = 'Required'
        param_2.direction = 'Output'
        param_2.datatype = u'Shapefile'

        # Coordinate_System
        param_3 = arcpy.Parameter()
        param_3.name = u'Coordinate_System'
        param_3.displayName = u'Coordinate System'
        param_3.parameterType = 'Required'
        param_3.direction = 'Input'
        param_3.datatype = u'Spatial Reference'

        return [param_1, param_2, param_3]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""

        dgnPath = parameters[0].valueAsText
        shpPath = parameters[1].valueAsText
        spatialRef = parameters[2].valueAsText

        polyPath = dgnPath + "\\Polygon"
        annoPath = dgnPath + "\\Annotation"
        polyName = gdbPath + "\\dgn2shp_poly"
        annoName = gdbPath + "\\dgn2shp_anno"
        arcpy.env.workspace = gdbPath
        arcpy.env.qualifiedFieldNames = False
        arcpy.env.overwriteOutput = True
        arcpy.env.outputCoordinateSystem = spatialRef
        try:
            arcpy.FeatureToPolygon_management(polyPath, polyName, "", "ATTRIBUTES", "")
            arcpy.FeatureToPoint_management(annoPath, annoName , "CENTROID")
            arcpy.AddMessage("DGN successfully converted")
            arcpy.SpatialJoin_analysis(polyName, annoName, shpPath, "JOIN_ONE_TO_ONE", "KEEP_ALL", "", "INTERSECTS", "", "")
            arcpy.AddField_management(shpPath, "TILE", "TEXT")
            arcpy.AddMessage("Feature Converted to Polygon!")
            arcpy.CalculateField_management(shpPath, "TILE", "!Text!", "PYTHON_9.3", "")
            arcpy.AddMessage("Tile text successfully calculated")
            inDBF = shpPath
            desc = arcpy.Describe(inDBF)
            fieldObjList = arcpy.ListFields(inDBF)
            deleteFields = []
            keepFields = ["FID", "Shape", "TILE"]
            for field in fieldObjList:
                if field.name not in keepFields:
                    deleteFields.append(field.name)
                    arcpy.AddMessage(field.name + " will be deleted!")
            arcpy.DeleteField_management(shpPath, deleteFields)
            arcpy.AddMessage(str(len(deleteFields)) + " were deleted from the attribute table.")
        except:
            arcpy.AddMessage("Process completed. Shapefile is located: " + shpPath)

        return


class ADSFltInfotoSHP(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Populate ADS FlightInfo"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        # _stp_Directory
        param_1 = arcpy.Parameter()
        param_1.name = u'_stp_Directory'
        param_1.displayName = u'.stp Directory'
        param_1.parameterType = 'Required'
        param_1.direction = 'Input'
        param_1.datatype = u'Workspace'

        # Flightline_Shapefile
        param_2 = arcpy.Parameter()
        param_2.name = u'ADS_Shapefile'
        param_2.displayName = u'ADS Shapefile'
        param_2.parameterType = 'Required'
        param_2.direction = 'Input'
        param_2.datatype = u'Shapefile'

        # NadirBand
        param_3 = arcpy.Parameter()
        param_3.name = u'NadirBand'
        param_3.displayName = u'NadirBand'
        param_3.parameterType = 'Required'
        param_3.direction = 'Input'
        param_3.datatype = u'String'
        param_3.value = u'red'
        param_3.filter.list = [u'red', u'green', u'blue']

        # Output
        param_4 = arcpy.Parameter()
        param_4.name = u'Output_Shapefile'
        param_4.displayName = u'Output Shapefile'
        param_4.parameterType = 'Required'
        param_4.direction = 'Output'
        param_4.datatype = u'Shapefile'

        # Projection
        param_5 = arcpy.Parameter()
        param_5.name = u'Coordinate_System'
        param_5.displayName = u'Coordinate System'
        param_5.parameterType = 'Required'
        param_5.direction = 'Input'
        param_5.datatype = u'Spatial Reference'

        return [param_1, param_2, param_3, param_4, param_5]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):

        infoPath = parameters[0].valueAsText #Path to info file
        clShpPath = parameters[1].valueAsText #Stores path to centerline shpfile
        nadirBand = parameters[2].valueAsText #Stores band to use
        outputFolder = parameters[3].valueAsText #Stores output
        newSpatRef = parameters[4].valueAsText #Stores new CS
        folderPath = os.path.dirname(outputFolder) # Store the directory path
        outName = os.path.basename(outputFolder) #Stores the filename
        infoList = []
        txtOutName = os.path.join(folderPath,"flt_info.txt") #Creates text doc to store values
        arcpy.env.workspace = gdbPath
        arcpy.env.qualifiedFieldNames = False
        arcpy.env.overwriteOutput = True
        #Sets the NadirBand based on user input
        if nadirBand.lower() == "red":
            nadirBand = "REDN00A"
        elif nadirBand.lower() == "blue":
            nadirBand = "BLUN00A"
        else:
            nadirBand = "GRNN00A"
        messages.AddMessage("Scratch Environment set to: %s" % gdbPath)
        txt = open(txtOutName, 'w') #Opens documents

        #Creates and populates text doc
        def txtCreate():
            headerValues = ['LINEID', 'FLT_START', 'FLT_STOP', 'AVG_ALT']# Value variables
            for h in headerValues: #loops over head values and adds to txt doc
                txt.write(('%s' + ",") % h)
            txt.write("\n") #move to next line
            messages.AddMessage("Header values added to text.")

        #function loops over dir to find info files and append to infolist
        def get_path():
            for f in os.listdir(infoPath): # loops over dir
                if f.endswith('.stp'): #logic to find info files
                    infoList.append(f) #appends to list
                    messages.AddMessage("Info file: %s added to list." %os.path.basename(f))

        #function populates txt doc with values from the info files.
        def pop_file():
            for f in infoList:
                    LINEID = f.rstrip(nadirBand + '.stp')
                    infoFile = infoPath + "\\" + f
                    messages.AddMessage(infoFile)
                    values = []
                    altvalues = []
                    values.append(LINEID)
                    tree = ET.parse(infoFile)
                    root = tree.getroot()
                    elem = root.findall("./Start")
                    for e in elem:
                        for f in e:
                            if f.tag == 'time':
                                values.append(f.text[-8:-3])
                            elif f.tag == 'altitude':
                                altvalues.append(round(float(f.text), 2))
                    elem = root.findall("./Stop")
                    for e in elem:
                        for f in e:
                            if f.tag == 'time':
                                values.append(f.text[-8:-3])
                            elif f.tag == 'altitude':
                                altvalues.append(round(float(f.text), 2))
                    values.append(str((altvalues[0] + altvalues[1]) / 2))
                    txt.write(values[0] + ',' + values[1] + ',' + values[2] + ',' + values[3])
                    txt.write("\n")
                    linecache.clearcache()

        #Creates shapefile
        def shp_create():
            arcpy.MakeFeatureLayer_management(clShpPath, "lyr")
            messages.AddMessage("Flightline Shapefile converted to layer")
            arcpy.SelectLayerByAttribute_management("lyr", "NEW_SELECTION", ("\"BANDID\"" + " = " + "\'" + nadirBand + "\'"))
            messages.AddMessage("Selected LINEID by: %s band." % nadirBand)
            messages.AddMessage("Shapefile Projected")
            arcpy.AddJoin_management("lyr", "LINEID", txtOutName, "LINEID", "KEEP_COMMON")
            messages.AddMessage("Text file and shape joined.")
            arcpy.FeatureClassToFeatureClass_conversion("lyr", gdbPath, outName.strip(".shp"))
            arcpy.Project_management(os.path.join(gdbPath, outName.strip(".shp")),os.path.join(folderPath, outName), newSpatRef)
            messages.AddMessage("Shapefile created.")

        #Cleans up shapefile
        def mod_table():
            keepFields = ['FID', 'Shape', 'LINEID', 'FLT_START', 'FLT_STOP', 'AVG_ALT', 'FLIGHTDAT']
            dropFields = []
            desc = arcpy.Describe(os.path.join(folderPath, outName))
            fieldList = arcpy.ListFields(os.path.join(folderPath, outName))
            for field in fieldList:
                if field.name not in keepFields:
                    dropFields.append(field.name)
            arcpy.DeleteField_management(os.path.join(folderPath, outName), dropFields)
            messages.AddMessage("Unnecessary fields removed.")

        txtCreate()
        get_path()
        pop_file()
        txt.close()
        shp_create()
        mod_table()
        return


class AirportBoundaryCreator(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Airport Boundary Creator"
        self.description = u'This script will convert the "APPROACH" and "HORIZONTAL SURFACE CONICAL" layer attributes in an airport layout dgn to a shapefile and Microstation V7 dxf format files.'
        self.canRunInBackground = False

    def getParameterInfo(self):
        # Input_DGN
        param_1 = arcpy.Parameter()
        param_1.name = u'DGN_Path'
        param_1.displayName = u'DGN Path'
        param_1.parameterType = 'Required'
        param_1.direction = 'Input'
        param_1.datatype = u'CAD Drawing Dataset'

        # Output
        param_2 = arcpy.Parameter()
        param_2.name = u'Output_Shapefile'
        param_2.displayName = u'Output Shapefile'
        param_2.parameterType = 'Required'
        param_2.direction = 'Output'
        param_2.datatype = u'Shapefile'

        # Coordinate_System
        param_3 = arcpy.Parameter()
        param_3.name = u'Coordinate_System'
        param_3.displayName = u'Coordinate System'
        param_3.parameterType = 'Required'
        param_3.direction = 'Input'
        param_3.datatype = u'Spatial Reference'

        return [param_1, param_2, param_3]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):

        #Local Variables
        input = parameters[0].valueAsText + "\\Polyline"
        output = parameters[1].valueAsText
        spatialRef = parameters[2].valueAsText

        #Environmental Variables
        arcpy.env.workspace = gdbPath
        arcpy.env.qualifiedFieldNames = False
        arcpy.env.overwriteOutput = True
        arcpy.env.outputCoordinateSystem = spatialRef
        arcpy.AddMessage("Environmental Variables Set.")
        tmpOutput = gdbPath.rstrip("Default.gdb")

        #Creates a temp layer from dgn approach and conical levels
        try:
            arcpy.MakeFeatureLayer_management(input, "lyr")
            arcpy.SelectLayerByAttribute_management("lyr", "NEW_SELECTION", (""" "Layer" = 'APPROACH' OR "Layer" = 'HORIZONTAL CONICAL SURFACE' """))
            arcpy.FeatureClassToFeatureClass_conversion("lyr", gdbPath, "deleteMe")
        except:
            messages.AddMessage("Error creating layer.")
            messages.AddMessage("Check DGN for Approach and Horizontal Conical Surface.")
            arcpy.GetMessages()

        #converts layer to shapefile
        try:
            deleteMePath = os.path.join(tmpOutput, "deleteMe.shp" )
            arcpy.FeatureToPolygon_management("deleteMe", deleteMePath)
            arcpy.Dissolve_management(deleteMePath, output)
            messages.AddMessage("Shapefile created!")
            arcpy.Delete_management(deleteMePath, "")
            arcpy.Delete_management("deleteMe", "")
            arcpy.ExportCAD_conversion(output, "DXF_R14", (output.rstrip("shp") + "dxf"))
            messages.AddMessage("DXF created!")
            messages.AddMessage("Files outputted to:" + output)
        except:
            messages.AddMessage("Error converting shapefile and DXF!")
            arcpy.GetMessages()
        return

class TileLayout(object):

    def __init__(self):
        self.label = u'Make Image Tiles'
        self.description = u'Creates grid cells over a shapefile extent. The script takes 4 inputs from the user: the boundary shapefile, the output location, and the tile sizes.'
        self.canRunInBackground = False
    def getParameterInfo(self):
        # Shapefile_Path
        param_1 = arcpy.Parameter()
        param_1.name = u'Boundary_Shapefile_Path'
        param_1.displayName = u'Boundary Shapefile Path'
        param_1.parameterType = 'Required'
        param_1.direction = 'Input'
        param_1.datatype = u'Feature Class'

        # Output_Path
        param_2 = arcpy.Parameter()
        param_2.name = u'Output_Shapefile'
        param_2.displayName = u'Output Shapefile'
        param_2.parameterType = 'Required'
        param_2.direction = 'Output'
        param_2.datatype = u'Feature Class'

        # X_Tile_Size
        param_3 = arcpy.Parameter()
        param_3.name = u'Width'
        param_3.displayName = u'Width'
        param_3.parameterType = 'Required'
        param_3.direction = 'Input'
        param_3.datatype = u'String'

        # Y_Tile_Size
        param_4 = arcpy.Parameter()
        param_4.name = u'Height'
        param_4.displayName = u'Height'
        param_4.parameterType = 'Required'
        param_4.direction = 'Input'
        param_4.datatype = u'String'

        # Prefix
        param_5 = arcpy.Parameter()
        param_5.name = u'Prefix'
        param_5.displayName = u'Prefix'
        param_5.parameterType = 'Optional'
        param_5.direction = 'Input'
        param_5.datatype = u'String'

        return [param_1, param_2, param_3, param_4, param_5]
    def isLicensed(self):
        return True
    def updateParameters(self, parameters):
        validator = getattr(self, 'ToolValidator', None)
        if validator:
             return validator(parameters).updateParameters()
    def updateMessages(self, parameters):
        validator = getattr(self, 'ToolValidator', None)
        if validator:
             return validator(parameters).updateMessages()
    def execute(self, parameters, messages):

        #arcpy environmental variables
        arcpy.env.workspace = gdbPath
        arcpy.env.qualifiedFieldNames = False
        arcpy.env.overwriteOutput = True

        # Local variables:
        inTiles = parameters[0].valueAsText  #input shapefile
        outTiles = parameters[1].valueAsText #output shapefile
        xTiles = parameters[2].valueAsText  #tile width
        yTiles = parameters[3].valueAsText   #tile height
        preFix = parameters[4].valueAsText   #Tile Prefix
        xTiles = float(xTiles)
        yTiles = float(yTiles)

        #Checks if a prefix was entered by user

        #creates the tile layout and creates name
        def createTiles():
            # Feature class shape check
            descInTiles = arcpy.Describe(inTiles)
            if descInTiles.shapetype == "Point" or descInTiles.shapetype == "MultiPoint":
                messages.AddIDMessage("Error", 732)
                print messages.AddMessage("INVALID DATA TYPE. PLEASE SELECT A NON-POINT FEATURECLASS")
            else:
                #Get the extend of boundary
                desc = arcpy.Describe(inTiles)
                xMax = int(desc.extent.XMax / xTiles) * xTiles + xTiles
                yMax = int(desc.extent.YMax / yTiles) * yTiles + yTiles
                xMin = int(desc.extent.XMin / xTiles) * xTiles - xTiles
                yMin = int(desc.extent.YMin / yTiles) * yTiles - yTiles
                originCoor = str(xMax) + " " + str(yMax)
                endCoor = str(xMin) + " " + str(yMin)
                yAxis = str(xMin) + " " + str(yMin + 10)

                try:
                    #Create Tiles
                    arcpy.CreateFishnet_management("allTiles", endCoor, yAxis, xTiles, yTiles, "", "", originCoor, "NO_LABELS", inTiles, "POLYGON") #create fishnet tool
                    messages.AddMessage("Tile Layout Created.....")
                    arcpy.AddField_management("allTiles", "NAME", "TEXT") # add a name field
                    messages.AddMessage("Name field added to table.....")
                    with arcpy.da.UpdateCursor("allTiles", ["NAME", "SHAPE@XY"]) as cursor: #cursor iterates over table
                        for row in cursor: #iterates over each row of the table
                            coordName = row[1] #gets the xy centeroid for the current tile
                            pointX, pointY = float(coordName[0]), float(coordName[1]) #seperates the coordinates and assigns them to variables
                            roundX, roundY = ((round(pointX, -2))), ((round(pointY, -2))) #rounds the xy variables
                            roundX, roundY = round(pointX, -2) - (float(xTiles) * float(.5)), round(pointY, -2) - (float(yTiles) * float(.5)) # gets coordinates of the lower left coordinate
                            if preFix is None:
                                name = str(roundX)[-8:-5] + str(roundY)[-8:-5] # creates name from lower left coordinate
                            else:
                                name = preFix + str(roundX)[-8:-5] + str(roundY)[-8:-5]
                            messages.AddMessage("Added %s to the Tile Name field" % name)
                            row[0] = name #assigns the name to the tile field
                            arcpy.SetProgressorPosition()
                            cursor.updateRow(row) # updates the row

                        del cursor
                except:
                    print arcpy.GetMessages()

        # removes all tiles that fall outside the boundary
        def removeTiles():
            try:
                head, tail = outTiles.split(".")
                head = os.path.basename(head)
                outTilesDirName = os.path.dirname(outTiles)
                arcpy.MakeFeatureLayer_management(inTiles, "copyBoundary")
                arcpy.MakeFeatureLayer_management("allTiles", "finalTiles")
                arcpy.SelectLayerByLocation_management("finalTiles", "INTERSECT", "copyBoundary")
                arcpy.CopyFeatures_management("finalTiles", head)
                arcpy.FeatureClassToShapefile_conversion(head, outTilesDirName)
                messages.AddMessage("Unnecessary Tiles Removed!.")
            except:
                messages.AddMessage("Error Remove unnecessary tiles.")
                arcpy.GetMessages()

        #Deletes unnecesary fields and layers created by the script
        def cleanUp():
            try:
                head, tail = outTiles.split(".")
                head = os.path.basename(head)
                delFields = ["SHAPE_Leng", "SHAPE_AREA"]
                arcpy.DeleteField_management(outTiles, delFields) #deletes fields
                arcpy.Delete_management("allTiles", "")
                messages.AddMessage(os.path.basename(outTiles))
                arcpy.Delete_management(head, "")
                messages.AddMessage("Cleaned up shapefile.")
            except:
                messages.AddMessage("Error Deleting Unnecessary Tiles and cleaning up default GDB")
                arcpy.GetMessages()


        createTiles()
        removeTiles()
        cleanUp()

class USNGTileLayout(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "USNG Tile Layout"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        # InTiles
        param_1 = arcpy.Parameter()
        param_1.name = u'Boundary_Shapefile_Path'
        param_1.displayName = u'Boundary Shapefile Path'
        param_1.parameterType = 'Required'
        param_1.direction = 'Input'
        param_1.datatype = u'Feature Class'

        # OutTiles
        param_2 = arcpy.Parameter()
        param_2.name = u'Output_Shapefile'
        param_2.displayName = u'Output Shapefile'
        param_2.parameterType = 'Required'
        param_2.direction = 'Output'
        param_2.datatype = u'Feature Class'

        # Width
        param_3 = arcpy.Parameter()
        param_3.name = u'Width'
        param_3.displayName = u'Width'
        param_3.parameterType = 'Required'
        param_3.direction = 'Input'
        param_3.datatype = u'String'

        # Height
        param_4 = arcpy.Parameter()
        param_4.name = u'Height'
        param_4.displayName = u'Height'
        param_4.parameterType = 'Required'
        param_4.direction = 'Input'
        param_4.datatype = u'String'

        #UTM Zone
        param_5 = arcpy.Parameter()
        param_5.name = u'UTM_Zone'
        param_5.displayName = u'UTM Zone'
        param_5.parameterType = 'Optional'
        param_5.direction = 'Input'
        param_5.datatype = u'String'

        return [param_1, param_2, param_3, param_4, param_5]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        #arcpy environmental variables
        arcpy.env.workspace = gdbPath
        arcpy.env.qualifiedFieldNames = False
        arcpy.env.overwriteOutput = True

        # Local variables:
        inTiles = parameters[0].valueAsText  #input shapefile
        outTiles = parameters[1].valueAsText #output shapefile
        xTiles = parameters[2].valueAsText    #tile width
        yTiles = parameters[3].valueAsText   #tile height
        utmZone = parameters[4].valueAsText #UTMZone
        xTiles = float(xTiles)
        yTiles = float(yTiles)
        head, tail = outTiles.split(".")
        head = os.path.basename(head)
        outTilesDirName = os.path.dirname(outTiles)
        ddValues = dict()
        utmValues = dict()
        sr = arcpy.SpatialReference(4269)


        #creates the tile layout and creates name
        def createTiles():
            # Feature class shape check
            descInTiles = arcpy.Describe(inTiles)
            descSR = descInTiles.SpatialReference
            if descInTiles.shapetype == "Point" or descInTiles.shapetype == "MultiPoint":
                messages.AddIDMessage("Error", 732)
                print messages.AddMessage("INVALID DATA TYPE. PLEASE CHECK FEATURE CLASS SHAPE.")
            else:
                #Get the extend of boundary
                desc = arcpy.Describe(inTiles)
                xMax = int(desc.extent.XMax / xTiles) * xTiles + xTiles
                yMax = int(desc.extent.YMax / yTiles) * yTiles + yTiles
                xMin = int(desc.extent.XMin / xTiles) * xTiles - xTiles
                yMin = int(desc.extent.YMin / yTiles) * yTiles - yTiles
                originCoor = str(xMax) + " " + str(yMax)
                endCoor = str(xMin) + " " + str(yMin)
                yAxis = str(xMin) + " " + str(yMin + 10)
                try:
                    # Create Tiles
                    arcpy.CreateFishnet_management("allTiles", endCoor, yAxis, xTiles, yTiles, "", "", originCoor, "NO_LABELS",
                                                   inTiles, "POLYGON")  # create fishnet tool
                    messages.AddMessage("Tile Layout Created.....")
                    arcpy.AddField_management("allTiles", "TILE", "TEXT")
                    arcpy.AddField_management("allTiles", "X", "TEXT")
                    arcpy.AddField_management("allTiles", "Y", "TEXT")
                    arcpy.AddField_management("allTiles", "XY", "TEXT")
                    messages.AddMessage("Fields added to table.....")
                except:
                    print arcpy.GetMessages()

        # removes all tiles that fall outside the boundary
        def removeTiles():
            try:
                arcpy.MakeFeatureLayer_management(inTiles, "copyBoundary")
                arcpy.MakeFeatureLayer_management("allTiles", "finalTiles")
                arcpy.SelectLayerByLocation_management("finalTiles", "INTERSECT", "copyBoundary")
                arcpy.CopyFeatures_management("finalTiles", head)
                arcpy.FeatureClassToShapefile_conversion(head, outTilesDirName)
                messages.AddMessage("Unnecessary Tiles Removed!.")
            except:
                messages.AddMessage("Error Remove unnecessary tiles.")
                arcpy.GetMessages()

        #Deletes unnecessary fields and layers created by the script
        def USNG_TileNaming():
            desc = arcpy.Describe(outTiles)
            shapeFieldName = desc.ShapeFieldName
            utmRows = arcpy.SearchCursor(outTiles)
            for utm in utmRows:
                feat = utm.getValue(shapeFieldName)
                OID = utm.getValue(desc.OIDFieldName)
                u = feat.extent.XMin
                t = feat.extent.YMin
                ut = str(u) + " " + str(t)
                utmValues[OID] = ut

            messages.AddMessage("UTM Coordinates obtained")

            ddRows = arcpy.SearchCursor(outTiles, spatial_reference = sr)
            for row in ddRows:
                feat = row.getValue(shapeFieldName)
                FID = row.getValue(desc.OIDFieldName)
                x = feat.extent.XMin
                y = feat.extent.YMin
                xy = str(x) + " " + str(y)
                ddValues[FID] = xy

            messages.AddMessage("Decimal Degree coordinates obtained.")

            with arcpy.da.UpdateCursor(outTiles,["FID" , "XY"]) as cursor:
                for row in cursor:
                    for UTM, LL in utmValues.items():
                        if row[0] == UTM:
                            row[1] = LL
                    arcpy.SetProgressorPosition()
                    cursor.updateRow(row)

            messages.AddMessage("UTM Coordinates added to table.")

            with arcpy.da.UpdateCursor(outTiles, ["FID", "X", "Y"]) as cursor:
                for row in cursor:
                    for FID, XY in ddValues.items():
                        if row[0] == FID:
                            X, Y = XY.split(" ")
                            row[1] = X
                            row[2] = Y
                    arcpy.SetProgressorPosition()
                    cursor.updateRow(row)

                del cursor

            messages.AddMessage("Decimal Degree coordinates added to table.")

            arcpy.ConvertCoordinateNotation_management(outTiles, "USNG_notation", "X", "Y", "DDM_2", "USNG")
            arcpy.MakeFeatureLayer_management(outTiles, "temp")
            with arcpy.da.UpdateCursor("USNG_notation", ["USNG", "XY"]) as cursor:
                for row in cursor:
                    a, b, c, d = row[0].split(" ")
                    x,y = row[1].split(" ")
                    x = x[1:4]
                    y = y[2:5]
                    if utmZone is None:
                        name = a + b + x + y
                    else:
                        a = a[2:]
                        name = utmZone + a + b + x + y
                    row[0] = name
                    arcpy.SetProgressorPosition()
                    cursor.updateRow(row)
                del cursor
            arcpy.AddJoin_management("temp", "X", "USNG_notation", "X", "KEEP_COMMON")
            arcpy.CalculateField_management("temp", "TILE", "!USNG!", "PYTHON_9.3", "")
            arcpy.CopyFeatures_management("temp", head)
            arcpy.FeatureClassToShapefile_conversion(head, outTilesDirName)
            messages.AddMessage("Tiles named to USNG standards.")

        def cleanUp():
            try:
                fieldList = arcpy.ListFields(outTiles)
                deleteFields = []
                keepFields = ["FID", "OID", "Shape", "TILE"]
                for field in fieldList:
                    if field.name not in keepFields:
                        deleteFields.append(field.name)
                arcpy.DeleteField_management(outTiles, deleteFields)
                for f in fieldList:
                    messages.AddMessage("Field: {0} deleted.".format(f.name))
                arcpy.Delete_management("allTiles", "")
                arcpy.Delete_management(os.path.join(outTilesDirName, head + "_1.shp"))
                arcpy.Delete_management("USNG_Tiles", "")
                arcpy.Delete_management("USNG_notation", "")
                arcpy.Delete_management(head, "")
                messages.AddMessage("Shapefile cleaned up.")
            except:
                messages.AddMessage("Error Deleting Unnecessary Tiles and cleaning up default GDB")
                arcpy.GetMessages()

        createTiles()
        removeTiles()
        USNG_TileNaming()
        cleanUp()
        return

class RasterFootprint(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Raster Footprint Generator"
        self.description = u'Will Generate a footprint shapefile for all selected rasters'
        self.canRunInBackground = False

    def getParameterInfo(self):
        # Rasters
        param_1 = arcpy.Parameter()
        param_1.name = u'Rasters'
        param_1.displayName = u'Rasters'
        param_1.parameterType = 'Required'
        param_1.direction = 'Input'
        param_1.datatype = u'Raster Layer'
        param_1.multiValue = True

        # Out_Shapefile
        param_2 = arcpy.Parameter()
        param_2.name = u'Out_Shapefile'
        param_2.displayName = u'Output Shapefile'
        param_2.parameterType = 'Required'
        param_2.direction = 'Output'
        param_2.datatype = u'Shapefile'

        # Coordinate_System
        param_3 = arcpy.Parameter()
        param_3.name = u'Coordinate_System'
        param_3.displayName = u'Coordinate System'
        param_3.parameterType = 'Required'
        param_3.direction = 'Input'
        param_3.datatype = u'Coordinate System'

        return [param_1, param_2, param_3]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        import arcpy
        from arcpy.sa import *


        #inputs
        inRaster = parameters[0].valueAsText
        outSHP = parameters[1].valueAsText
        sr = parameters[2].valueAsText

        #arcpy environmental variables
        arcpy.env.workspace = gdbPath
        arcpy.env.qualifiedFieldNames = False
        arcpy.env.overwriteOutput = True
        arcpy.env.outputCoordinateSystem = sr

        #VARIABLES
        head, tail = os.path.split(outSHP)
        name, shp = tail.split(".")
        rasterArray = []
        for raster in inRaster.split(";"):
            rasterArray.append(raster)
        rasterNames = []
        for r in rasterArray:
            tempName = os.path.basename(r)
            b, e = tempName.split(".")
            rasterNames.append(b)
        ext = e
        count = 0
        arcpy.CreateFeatureclass_management(head, tail, "Polygon")
        arcpy.AddField_management(outSHP, ext, "TEXT")

        for raster in rasterArray:
            tempName = os.path.basename(raster)
            b, e = tempName.split(".")
            array = arcpy.Array()
            point = arcpy.Point()
            coord = Raster(raster).extent
            cursor = arcpy.da.InsertCursor(outSHP, 'SHAPE@')
            array.add(arcpy.Point(coord.XMax, coord.YMax))
            array.add(arcpy.Point(coord.XMax, coord.YMin))
            array.add(arcpy.Point(coord.XMin, coord.YMin))
            array.add(arcpy.Point(coord.XMin, coord.YMax))
            cursor.insertRow([arcpy.Polygon(array)])
            messages.AddMessage(("Footprint for raster {0} was created.").format(b))
            del cursor

        with arcpy.da.UpdateCursor(outSHP, ext) as cursor:
            for row in cursor:
                row[0] = rasterNames[count]
                messages.AddMessage(("{0} field was updated.").format(rasterNames[count]))
                arcpy.SetProgressorPosition()
                cursor.updateRow(row)
                count += 1
            del cursor

        arcpy.DeleteField_management(outSHP, "Id")
        return
class OverlapTiles(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Overlap Tiles"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        # Input Shapefile
        param_1 = arcpy.Parameter()
        param_1.name = u'Input shapefile'
        param_1.displayName = u'Input shapefile'
        param_1.parameterType = 'Required'
        param_1.direction = 'Input'
        param_1.datatype = u'Shapefile'

        # Output_Shapefile
        param_2 = arcpy.Parameter()
        param_2.name = u'Output_Shapefile'
        param_2.displayName = u'Output Shapefile'
        param_2.parameterType = 'Required'
        param_2.direction = 'Output'
        param_2.datatype = u'Shapefile'

        # Coordinate_System
        param_3 = arcpy.Parameter()
        param_3.name = u'X_overlap'
        param_3.displayName = u'X Overlap'
        param_3.parameterType = 'Required'
        param_3.direction = 'Input'
        param_3.datatype = u'String'

        # Y adjustment
        param_4 = arcpy.Parameter()
        param_4.name = u'Y_overlap'
        param_4.displayName = u'Y Overlap'
        param_4.parameterType = 'Required'
        param_4.direction = 'Input'
        param_4.datatype = u'String'

        return [param_1, param_2, param_3, param_4]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""

        inSHP = parameters[0].valueAsText
        outSHP = parameters[1].valueAsText
        x = parameters[2].valueAsText
        y = parameters[3].valueAsText
        x = int(x)
        y = int(y)

        #arcpy environmental variables
        arcpy.env.workspace = gdbPath
        arcpy.env.qualifiedFieldNames = False
        arcpy.env.overwriteOutput = True

        arcpy.CopyFeatures_management(inSHP, outSHP)

        with arcpy.da.UpdateCursor(outSHP, 'SHAPE@') as cursor:
            for row in cursor:
                array = arcpy.Array()
                array.add(arcpy.Point(row[0].extent.XMin - x, row[0].extent.YMin - y))
                array.add(arcpy.Point(row[0].extent.XMin - x, row[0].extent.YMax + y))
                array.add(arcpy.Point(row[0].extent.XMax + x, row[0].extent.YMax + y))
                array.add(arcpy.Point(row[0].extent.XMax + x, row[0].extent.YMin - y))
                row[0] = arcpy.Polygon(array)
                arcpy.SetProgressorPosition()
                cursor.updateRow(row)

        return
