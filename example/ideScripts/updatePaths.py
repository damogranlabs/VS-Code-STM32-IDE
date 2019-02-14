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

        self.toolsList = [
            #(path, name, default, updated?)
            (self.bStr.gccExePath, "arm-none-eabi-gcc", "arm-none-eabi-gcc", False),
            (self.bStr.buildToolsPath, "make", "make", False),
            (self.bStr.openOcdPath, "openocd", "openocd", False),
            (self.bStr.stm32SvdPath, "STM target '*.svd' folder (example: .../Keil*/CMSIS/SVD)", utils.workspacePath+"SVD", False)
        ]

    def verifyExistingPaths(self, buildData, request=False):
        '''
        This function checks if paths specified in 'self.toolsList' exist in 'buildData.json'.
        If any path is not valid, user is asked for update via updatePath.

        Returns updated valid paths.
        '''
        for path, pathName, default, updated in self.toolsList:
            try:
                pathToCheck = buildData[path]
                if not utils.pathExists(pathToCheck):
                    # path not valid, check if command
                    if not utils.commandExists(pathToCheck):
                        # path invalid
                        buildData[path] = self.updatePath(path, pathName, default)
                        updated = True
                else:
                    # path valid
                    if request: # if the user made the path verification request
                        msg = "\n\nValid path to '" + pathName + "' detected at '" + pathToCheck + "'\n\tUpdate existing path? [y/n]: "
                        if utils.getYesNoAnswer(msg):
                            buildData[path] = self.updatePath(path, pathName, default)
                            updated = True
            except:
                buildData[path] = self.updatePath(path, pathName, default)
                updated = True

            # validate derivative paths
            if updated is True:
                if path == self.bStr.gccExePath:
                    # get gccIncludePath
                    gccExePath = buildData[self.bStr.gccExePath]
                    buildData[self.bStr.gccInludePath] = utils.getGccIncludePath(gccExePath)
                elif path == self.bStr.openOcdPath:
                    # get openOcdConfig
                    openOcdPath = buildData[self.bStr.openOcdPath]
                    buildData[self.bStr.openOcdConfig] = utils.getOpenOcdConfig(openOcdPath)
                elif path == self.bStr.stm32SvdPath:
                    # get stm32SvdFile
                    stm32SvdPath = buildData[self.bStr.stm32SvdPath]
                    buildData[self.bStr.stm32SvdFile] = utils.getStm32SvdFile(stm32SvdPath)

            # get python3 path
            buildData[self.bStr.pythonPath] = utils.getPython3Path()

        return buildData


    def updatePath(self, path, pathName, default):
        '''
        This function is called when there are no valid paths found in existing 'buildData.json' file.

        This function is called when a path is detected as invalid or the user requests to update paths.
        '''

        # check if default path is command
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
