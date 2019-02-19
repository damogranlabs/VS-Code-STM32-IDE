'''
This script can be run to update paths to gcc, openOCD and other tools/files/folders.
Script verify and add data to 'buildData.json' file.
'''

import sys
import shutil

import utilities as utils

import updateWorkspaceSources as wks
import updateMakefile as mkf
import updateBuildData as build
import updateTasks as tasks

__version__ = utils.__version__


class UpdatePaths():
    def __init__(self):
        self.bStr = build.BuildDataStrings()

        # list of paths with explanatory names and (optionally) default path
        self.toolsList = {
            self.bStr.gccExePath: {
                "name": "arm-none-eabi-gcc executable (arm-none-eabi-gcc.exe)",
                "defaultPath": "arm-none-eabi-gcc"},
            self.bStr.buildToolsPath: {
                "name": "make executable (make.exe)",
                "defaultPath":  "make"},
            self.bStr.openOcdPath: {
                "name": "OpenOCD executable (openocd.exe)",
                "defaultPath": "openocd"},
            self.bStr.stm32SvdPath: {
                "name": "STM target '*.svd' file (.../Keil*/CMSIS/SVD/STM32F0x1.svd)",
                "defaultPath": utils.workspacePath+"SVD"}
        }

    def verifyExistingPaths(self, buildData, request=False):
        '''
        This function checks if configuration paths (not workspace sources) from 'buildData.json' are valid paths.
        Common configuration paths are previoulsy fetched from 'toolsPaths.json'.
        If any path is not valid/missing, user is asked for update via updatePath().

        Returns updated valid paths.
        '''
        for pathName in self.bStr.configurationPaths:
            mustBeUpdated = False
            try:
                isPathValid = False
                if pathName in buildData:
                    pathToCheck = buildData[pathName]
                    if isinstance(pathToCheck, list):
                        for path in pathToCheck:
                            if not utils.pathExists(path):
                                break
                        else:
                            isPathValid = True
                    else:  # not a list, a single path expected
                        if utils.pathExists(pathToCheck):
                            isPathValid = True
                        else:
                            # path not valid, check if command
                            if utils.commandExists(pathToCheck):
                                isPathValid = True

                if isPathValid:
                    if request:  # if the user made the path verification request
                        msg = "\n\nValid paths for " + pathName + " detected: '" + str(pathToCheck) + "'.\n\tUpdate? [y/n]: "
                        if utils.getYesNoAnswer(msg):
                            mustBeUpdated = True
                else:
                    # non-valid path, must be updated
                    mustBeUpdated = True

                if mustBeUpdated:
                    if pathName in [self.bStr.pythonExec, self.bStr.gccInludePath]:
                        # derived paths, build later
                        continue

                    elif pathName in self.toolsList:
                        name = self.toolsList[pathName]["name"]
                        defaultPath = self.toolsList[pathName]["defaultPath"]
                        buildData[pathName] = self.updatePath(name, defaultPath)

                    # handle special paths cases - custom get() handlers
                    elif pathName == self.bStr.openOcdInterfacePath:
                        buildData[pathName] = utils.getOpenOcdInterface(buildData[self.bStr.openOcdPath])

                    elif pathName == self.bStr.openOcdConfig:
                        # get openOcdConfig
                        buildData[self.bStr.openOcdConfig] = utils.getOpenOcdConfig(buildData[self.bStr.openOcdInterfacePath])

                    # basic path question, default name
                    else:
                        buildData[pathName] = self.updatePath(pathName, None)

            except Exception as err:
                buildData[pathName] = self.updatePath(pathName, None)

        # get gccIncludePath
        buildData[self.bStr.gccInludePath] = utils.getGccIncludePath(buildData[self.bStr.gccExePath])
        # get python3 executable
        buildData[self.bStr.pythonExec] = utils.getPython3Executable()

        return buildData

    def updatePath(self, pathName, default):
        '''
        This function is called when a path is detected as invalid or the user requests to update paths.
        '''
        # check if default path is command
        pathDefault = None
        if utils.commandExists(default):
            pathDefault = shutil.which(default)
        # if not a command, check if it's a path
        elif utils.pathExists(default):
            pathDefault = default

        if pathDefault is not None:
            msg = "\n\tDefault path to '" + pathName + "' detected at '" + pathDefault + "'\n\tUse this path? [y/n]: "
            if utils.getYesNoAnswer(msg):
                return pathDefault

        # default not detected or user wants custom path/command
        newPath = utils.getUserPath(pathName)
        return newPath


########################################################################################################################
if __name__ == "__main__":
    utils.verifyFolderStructure()

    paths = UpdatePaths()
    bData = build.BuildData()

    buildData = bData.prepareBuildData()
    buildData = paths.verifyExistingPaths(buildData, request=True)

    bData.overwriteBuildDataFile(buildData)
    bData.createUserToolsFile(buildData)
