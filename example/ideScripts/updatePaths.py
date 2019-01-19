'''
This script can be run to update paths to gcc, openOCD and other tools/files/folders.
Script verify and add data to 'buildData.json' file.
'''

import sys

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
            (self.bStr.gccExePath, "arm-none-eabi-gcc.exe"),
            (self.bStr.buildToolsPath, "make.exe"),
            (self.bStr.openOCDPath, "openocd.exe"),
            (self.bStr.openOCDTargetPath, "STM target '*.cfg' file (example: ...scripts/target/stm32f0x.cfg)"),
            (self.bStr.stm32svdPath, "STM target '*.svd' file (example: .../Keil*/CMSIS/SVD/STM32F0x8.svd)")
        ]

    def forceUpdatePaths(self, buildData):
        '''
        This function is called when there are no valid paths found in existing 'buildData.json' file.
        '''
        for path, pathName in self.toolsList:
            while True:
                newPath = utils.getUserPath(pathName)
                if utils.fileFolderExists(newPath):
                    buildData[path] = newPath

                    msg = "\tPath to '" + pathName + "' updated."
                    print(msg)
                    break  # out of while loop
                else:
                    msg = "\tPath to '" + pathName + "' not valid:\n\t" + str(newPath)
                    print(msg)

        print("Tools paths updated.\n")
        return buildData

    def askToUpdate(self, buildData):
        '''
        Ask/force user to update tools paths. 
        If there is no valid path, user is forced to update path.
        If there is a valid path, user is asked if he wish to update path.
        Returns updated paths (buildData).
        '''
        for path, pathName in self.toolsList:
            if buildData[path] != '':
                if not utils.fileFolderExists(buildData[path]):
                    # buildData path is not empty, but path is not valid. Force update.
                    buildData[path] = utils.getUserPath(pathName)
                else:
                    # valid path, ask user for update
                    if utils.askUserForPathUpdate(pathName, currentPath=buildData[path]):
                        buildData[path] = utils.getUserPath(pathName)
            else:
                # no path currently available specified, force update.
                buildData[path] = utils.getUserPath(pathName)

        print("Chosen paths updated.\n")
        return buildData

    def verifyExistingPaths(self, buildData):
        '''
        This function checks if paths specified in 'self.toolsList' exists in 'buildData.json'. 
        If any path is not valid, user is asked for update.

        Returns updated valid paths.
        '''
        for path, pathName in self.toolsList:
            try:
                pathToCheck = buildData[path]
                if not utils.fileFolderExists(pathToCheck):
                    # path not valid
                    buildData[path] = utils.getUserPath(pathName)
                else:
                    # a valid path exists, ask user if he wish to update
                    continue
            except:
                buildData = self.forceUpdatePaths(buildData)

        gccExePath = buildData[self.bStr.gccExePath]
        buildData[self.bStr.gccInludePath] = utils.getGccIncludePath(gccExePath)

        openOCDTargetPath = buildData[self.bStr.openOCDTargetPath]
        buildData[self.bStr.openOCDInterfacePath] = utils.getSTLinkPath(openOCDTargetPath)

        return buildData


########################################################################################################################
if __name__ == "__main__":
    utils.verifyFolderStructure()

    paths = UpdatePaths()
    bData = build.BuildData()

    buildData = bData.prepareBuildData()
    paths.askToUpdate(buildData)

    bData.overwriteBuildDataFile(buildData)
    bData.createUserToolsFile(buildData)
