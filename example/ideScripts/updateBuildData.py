'''
Update/generate 'buildData.json' file in '.vscode' subfolder from new Makefile.
New Makefile is not updated by this script - it is updated with 'updateMakefile.py' or 'updateWorkspaceSources.py'
'''
import os
import json
import datetime

import utilities as utils
import templateStrings as tmpStr

import updatePaths as pth
import updateMakefile as mkf
import updateWorkspaceSources as wks

__version__ = utils.__version__


class BuildDataStrings():
    # project sources, includes, defines, ....
    cSources = 'cSources'
    asmSources = 'asmSources'
    ldSources = 'ldSources'

    cIncludes = 'cIncludes'
    asmIncludes = 'asmIncludes'
    ldIncludes = 'ldIncludes'

    cDefines = 'cDefines'
    asmDefines = 'asmDefines'

    cFlags = 'cFlags'
    asmFlags = 'asmFlags'
    ldFlags = 'ldFlags'

    buildDirPath = 'buildDir'

    # build/interface tools paths, configuration files
    gccInludePath = 'gccInludePath'  # GCC standard libraries root folder path
    gccExePath = 'gccExePath'  # path to 'gcc.exe'

    buildToolsPath = 'buildToolsPath'  # path to 'make.exe'
    targetExecutablePath = 'targetExecutablePath'  # path to downloadable '*.elf' file

    pythonExec = 'pythonExec'

    openOcdPath = 'openOcdPath'  # path to 'openocd.exe'
    openOcdInterfacePath = "openOcdInterfacePath"  # path to OpenOCD interface cofniguration file (currently 'stlink.cfg')
    openOcdConfig = 'openOcdConfig'  # path to target '*.cfg' file

    stm32SvdPath = 'stm32SvdPath'  # path to target '*.svd' file

    cubeMxProjectPath = 'cubeMxProjectPath'

    # list of mandatory paths that must exist in 'buildData.json' to update workspace.
    # Note: order is important!
    configurationPaths = [gccExePath,
                          buildToolsPath,
                          pythonExec,
                          openOcdPath, openOcdInterfacePath, openOcdConfig,
                          stm32SvdPath]
    # list of paths that can be cached in 'toolsPaths.json'
    toolsPaths = [gccExePath,
                  buildToolsPath,
                  pythonExec,
                  openOcdPath, openOcdInterfacePath]


class BuildData():
    def __init__(self):
        self.mkfStr = mkf.MakefileStrings()
        self.cPStr = wks.CPropertiesStrings()
        self.bStr = BuildDataStrings()

    def prepareBuildData(self):
        '''
        This function is used in all 'update*.py' scripts and makes sure, that buildData with a valid tools paths exist.
        Invalid paths are updated (requested from the user).
        Returns available, valid build data.
        '''
        paths = pth.UpdatePaths()

        self.checkBuildDataFile()
        buildData = self.getBuildData()
        if self.checkToolsPathFile():  # toolsPaths.json exists
            buildData = self.addToolsPathsData(buildData)
        buildData = paths.verifyExistingPaths(buildData)

        return buildData

    def checkBuildDataFile(self):
        '''
        Check if 'buildData.json' file exists. If it does, check if it is a valid JSON file.
        If it doesn't exist, create new according to template.
        '''
        if utils.pathExists(utils.buildDataPath):
            # file exists, check if it loads OK
            try:
                with open(utils.buildDataPath, 'r') as buildDataFile:
                    currentData = json.load(buildDataFile)
                    # this is a valid json file
                    print("Existing valid 'buildData.json' file found.")

                # merge current 'buildData.json' with its template
                templateData = json.loads(tmpStr.buildDataTemplate)
                dataToWrite = utils.mergeCurrentDataWithTemplate(currentData, templateData)
                dataToWrite = json.dumps(dataToWrite, indent=4, sort_keys=False)
                with open(utils.buildDataPath, 'w') as buildDataFile:
                    buildDataFile.write(dataToWrite)
                    print("\tKeys updated according to the template.")
                return

            except Exception as err:
                errorMsg = "Invalid 'buildData.json' file. Creating new one. Error:\n"
                errorMsg += "Possible cause: invalid json format or comments (not supported by this scripts). Error:\n"
                errorMsg += str(err)
                print(errorMsg)

                self.createBuildDataFile()

        else:  # 'buildData.json' file does not exist jet, create it according to template string
            self.createBuildDataFile()

    def checkToolsPathFile(self):
        '''
        Returns True if 'toolsPaths.json' file exists and is a valid JSON file.
        If it doesn't exist, delete it and return False.
        '''
        if utils.pathExists(utils.toolsPaths):
            # file exists, check if it loads OK
            try:
                with open(utils.toolsPaths, 'r') as toolsFileHandler:
                    data = json.load(toolsFileHandler)
                    print("Valid 'toolsPaths.json' file found.")
                return True

            except Exception as err:
                errorMsg = "Invalid 'toolsPaths.json' file. Error:\n" + str(err)
                print(errorMsg)

                try:
                    os.remove(utils.toolsPaths)
                    errorMsg = "\tDeleted. New 'toolsPaths.json' will be created on first valid user paths update."
                    print(errorMsg)
                except Exception as err:
                    errorMsg = "\tError deleting 'toolsPaths.json'. Error:\n" + str(err)
                    print(errorMsg)
                return False

        else:  # toolsPaths.json does not exist
            return False

    def createUserToolsFile(self, buildData):
        '''
        Create 'toolsPaths.json' file with current tools absolute paths.
        '''
        data = {}
        try:
            data["ABOUT1"] = "Common tools paths that are automatically filled in buildData.json."
            data["ABOUT2"] = "Delete/correct this file if paths change on system."
            for path in self.bStr.toolsPaths:
                data[path] = buildData[path]

            data = json.dumps(data, indent=4, sort_keys=False)
            with open(utils.toolsPaths, 'w+') as toolsPathsFile:
                toolsPathsFile.write(data)
            print("'toolsPaths.json' file updated!")

        except Exception as err:
            errorMsg = "Exception error overwriting 'toolsPaths.json' file:\n"
            errorMsg += str(err)
            print("WARNING:", errorMsg)

    def createBuildDataFile(self):
        '''
        Create fresh 'buildData.json' file.
        '''
        try:
            data = json.loads(tmpStr.buildDataTemplate)
            dataToWrite = json.dumps(data, indent=4, sort_keys=False)

            with open(utils.buildDataPath, 'w+') as buildDataFile:
                buildDataFile.truncate()
                buildDataFile.write(dataToWrite)

            print("New 'buildData.json' file created.")
        except Exception as err:
            errorMsg = "Exception error creating new 'buildData.json' file:\n"
            errorMsg += str(err)
            utils.printAndQuit(errorMsg)

    def getToolsPathsData(self):
        '''
        Get data from current 'toolsPaths.json' file.
        File existance is previoulsy checked in 'checkToolsPathFile()'.
        '''
        with open(utils.toolsPaths, 'r') as toolsPathsFile:
            data = json.load(toolsPathsFile)

        return data

    def getBuildData(self):
        '''
        Get data from current 'buildData.json' file.
        File existance is previoulsy checked in 'checkBuildDataFile()'.
        '''
        with open(utils.buildDataPath, 'r') as buildDataFile:
            data = json.load(buildDataFile)

        return data

    def addToolsPathsData(self, buildData):
        '''
        If available, add data from 'toolsPaths.json' to buildData
        Returns new data.
        '''
        toolsPathsData = self.getToolsPathsData()

        for path in self.bStr.toolsPaths:
            try:
                buildData[path] = toolsPathsData[path]
            except Exception as err:
                # missing item in toolsPaths.json
                pass

        return buildData

    def addMakefileDataToBuildDataFile(self, buildData, makefileData):
        '''
        This function fills buildData.json file with data from 'Makefile'.
        Returns new data.
        '''
        # sources
        cSources = makefileData[self.mkfStr.cSources]
        buildData[self.bStr.cSources] = cSources

        asmSources = makefileData[self.mkfStr.asmSources]
        buildData[self.bStr.ldSources] = asmSources

        ldSources = makefileData[self.mkfStr.ldSources]
        buildData[self.bStr.ldSources] = ldSources

        # includes
        cIncludes = makefileData[self.mkfStr.cIncludes]
        buildData[self.bStr.cIncludes] = cIncludes

        asmIncludes = makefileData[self.mkfStr.asmIncludes]
        buildData[self.bStr.asmIncludes] = asmIncludes

        ldIncludes = makefileData[self.mkfStr.ldIncludes]
        buildData[self.bStr.ldIncludes] = ldIncludes

        # defines
        cDefines = makefileData[self.mkfStr.cDefines]
        buildData[self.bStr.cDefines] = cDefines

        asmDefines = makefileData[self.mkfStr.asmDefines]
        buildData[self.bStr.asmDefines] = asmDefines

        # compiler flags and paths
        cFlags = makefileData[self.mkfStr.cFlags]
        buildData[self.bStr.cFlags] = cFlags

        asmFlags = makefileData[self.mkfStr.asmFlags]
        buildData[self.bStr.asmFlags] = asmFlags

        ldFlags = makefileData[self.mkfStr.ldFlags]
        buildData[self.bStr.ldFlags] = ldFlags

        # build folder must be always inside workspace folder
        buildDirPath = makefileData[self.mkfStr.buildDir]
        buildData[self.bStr.buildDirPath] = buildDirPath

        # Target executable '.elf' file
        projectName = makefileData[self.mkfStr.projectName]
        targetExecutablePath = utils.getBuildElfFilePath(buildDirPath, projectName)
        buildData[self.bStr.targetExecutablePath] = targetExecutablePath

        return buildData

    def addCubeMxProjectPathToBuildData(self, buildData):
        '''
        If utils.cubeMxProjectFilePath is not None, add/update 'cubeMxProjectPath' field to 'buildData.json'.
        '''
        if utils.cubeMxProjectFilePath is not None:
            buildData[self.bStr.cubeMxProjectPath] = utils.cubeMxProjectFilePath
        return buildData

    def overwriteBuildDataFile(self, data):
        '''
        Overwrite existing 'buildData.json' file with new data.
        '''
        try:
            with open(utils.buildDataPath, 'r+') as buildDataFile:
                data["VERSION"] = __version__
                data["LAST_RUN"] = str(datetime.datetime.now())

                buildDataFile.seek(0)
                buildDataFile.truncate()
                dataToWrite = json.dumps(data, indent=4, sort_keys=False)
                buildDataFile.write(dataToWrite)

            print("'buildData.json' file updated!")

        except Exception as err:
            errorMsg = "Exception error overwriting 'buildData.json' file:\n"
            errorMsg += str(err)
            utils.printAndQuit(errorMsg)


########################################################################################################################
if __name__ == "__main__":
    utils.verifyFolderStructure()

    paths = pth.UpdatePaths()
    makefile = mkf.Makefile()
    bData = BuildData()

    # Makefile must exist - # point in continuing if Makefile does not exist
    makefile.checkMakefileFile()

    # build data (update tools paths if neccessary)
    buildData = bData.prepareBuildData()

    # data from current Makefile
    makeExePath = buildData[bData.bStr.buildToolsPath]
    gccExePath = buildData[bData.bStr.gccExePath]
    makefileData = makefile.getMakefileData(makeExePath, gccExePath)

    # try to add CubeMX project file path
    buildData = bData.addCubeMxProjectPathToBuildData(buildData)

    buildData = bData.addMakefileDataToBuildDataFile(buildData, makefileData)

    bData.overwriteBuildDataFile(buildData)
    bData.createUserToolsFile(buildData)
