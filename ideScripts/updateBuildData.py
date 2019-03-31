'''
Update/generate 'buildData.json' file in '.vscode' subfolder from new Makefile.
This file also handles 'toolsPaths.json' file.
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

    # list of paths that are automatically built (default, system or once their 'parent' paths are valid)
    derivedPaths = [
        pythonExec,
        gccInludePath
    ]

    # list of target-specific configuration paths that must exist in 'buildData.json'
    targetConfigurationPaths = [
        openOcdConfig,
        stm32SvdPath
    ]

    # list of paths that can be cached in 'toolsPaths.json'
    toolsPaths = [
        gccExePath,
        buildToolsPath,
        pythonExec,
        openOcdPath,
        openOcdInterfacePath
    ]


class BuildData():
    def __init__(self):
        self.mkfStr = mkf.MakefileStrings()
        self.cPStr = wks.CPropertiesStrings()
        self.bStr = BuildDataStrings()

    def prepareBuildData(self, request=False):
        '''
        This function is used in all 'update*.py' scripts and makes sure, that 'toolsPaths.json' and 'buildData.json' with a 
        valid tools/target cofniguration paths exist. Invalid paths are updated (requested from the user).
        Returns available, valid build data.

        Note: tools paths listed in 'BuildDataStrings.toolsPaths' are stored in system local 'toolsPaths.json' file, and are 
        copied (overwritten) to 'buildData.json' on first 'Update' task run. This makes it possible for multiple code contributors.
        '''
        paths = pth.UpdatePaths()

        self.checkBuildDataFile()
        buildData = self.getBuildData()

        if self.checkToolsPathFile():  # a valid toolsPaths.json exists
            toolsPathsData = self.getToolsPathsData()

        else:
            # no valid data from 'toolsPaths.json' file
            # try to get data from current 'buildData.json' - backward compatibility for paths that already exist in 'buildData.json'
            toolsPathsData = json.loads(tmpStr.toolsPathsTemplate)
            for path in self.bStr.toolsPaths:
                if path in buildData:
                    if utils.pathExists(buildData[path]):
                        toolsPathsData[path] = buildData[path]

        # update/overwrite tools paths file. Don't mind if paths are already valid.
        toolsPathsData = paths.verifyToolsPaths(toolsPathsData, request)
        self.createUserToolsFile(toolsPathsData)

        buildData = self.addToolsPathsToBuildData(buildData, toolsPathsData)

        templateBuildData = json.loads(tmpStr.buildDataTemplate)
        buildData = utils.mergeCurrentDataWithTemplate(buildData, templateBuildData)

        buildData = paths.verifyTargetConfigurationPaths(buildData, request)
        buildData = paths.copyTargetConfigurationFiles(buildData)

        return buildData

    def checkToolsPathFile(self):
        '''
        Returns True if 'toolsPaths.json' file exists and is a valid JSON file.
        If it is not a valid JSON, delete it and return False.
        '''
        if utils.pathExists(utils.toolsPaths):
            # file exists, check if it loads OK
            try:
                with open(utils.toolsPaths, 'r') as toolsFileHandler:
                    json.load(toolsFileHandler)
                    print("Valid 'toolsPaths.json' file found.")
                return True

            except Exception as err:
                errorMsg = "Invalid 'toolsPaths.json' file. Error:\n" + str(err)
                print(errorMsg)

                try:
                    os.remove(utils.toolsPaths)
                    msg = "\tDeleted. New 'toolsPaths.json' will be created on first workspace update."
                    print(msg)
                except Exception as err:
                    errorMsg = "Error deleting 'toolsPaths.json'. Error:\n" + str(err)
                    utils.printAndQuit(errorMsg)

        # else: toolsPaths.json does not exist
        return False

    def checkBuildDataFile(self):
        '''
        This function makes sure 'buildData.json' is available. 
        If existing 'buildData.json' file is a valid JSON, it returns immediately. 
        If it is not a valid JSON file OR it does not exist, new 'buildData.json' file is created from template.

        Note: There is no backup file for buildData.json, since it is always regenerated on Update task.
        '''
        if utils.pathExists(utils.buildDataPath):
            # file exists, check if it loads OK
            try:
                with open(utils.buildDataPath, 'r') as buildDataFileHandler:
                    json.load(buildDataFileHandler)
                    print("Valid 'buildData.json' file found.")

                return

            except Exception as err:
                errorMsg = "Invalid 'buildData.json' file. Error:\n" + str(err)
                print(errorMsg)

                try:
                    os.remove(utils.buildDataPath)
                    msg = "\tDeleted. New 'buildData.json' will be created on first workspace update."
                    print(msg)
                except Exception as err:
                    errorMsg = "Error deleting 'buildData.json'. Error:\n" + str(err)
                    utils.printAndQuit(errorMsg)

        # else: buildData.json does not exist
        self.createBuildDataFile()

    def createUserToolsFile(self, toolsPaths):
        '''
        Create 'toolsPaths.json' file with current tools paths.
        This pats are absolute and not project-specific.
        '''
        data = json.loads(tmpStr.toolsPathsTemplate)
        try:
            data["VERSION"] = __version__
            data["LAST_RUN"] = str(datetime.datetime.now())

            for path in self.bStr.toolsPaths:
                data[path] = toolsPaths[path]

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

            print("New template 'buildData.json' file created.")
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

    def addToolsPathsToBuildData(self, buildData, toolsPaths):
        '''
        Get tools paths from 'toolsPaths.json' and add it to buildData
        Returns new data.
        '''
        allToolsPaths = []
        allToolsPaths.extend(self.bStr.toolsPaths)
        allToolsPaths.extend(self.bStr.derivedPaths)
        for path in allToolsPaths:
            try:
                buildData[path] = toolsPaths[path]
            except Exception as err:
                errorMsg = "Missing '" + path + "' key in tools paths data:\n" + str(toolsPaths)
                print("Warning:", errorMsg)

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
        else:
            buildData.pop(self.bStr.cubeMxProjectPath)
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
