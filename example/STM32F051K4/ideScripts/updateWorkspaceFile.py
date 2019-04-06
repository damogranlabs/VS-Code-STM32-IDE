'''
Update existing VS Code workspace file with debug paths in "settings":
    - "cortex-debug.armToolchainPath"
    - "cortex-debug.openocdPath"
'''
import os
import json

import utilities as utils
import updatePaths as pth
import updateBuildData as build

__version__ = utils.__version__


class UpdateWorkspaceFile():
    def __init__(self):
        self.bStr = build.BuildDataStrings()

    def checkWorkspaceFile(self):
        '''
        Check if workspace '*.code-workspace' file exists. If it does, check if it is a valid JSON file.
        If it doesn't exist report error and quit.
        '''
        workspaceFiles = utils.getCodeWorkspaces()
        if len(workspaceFiles) == 1:
            _, fileName = os.path.split(workspaceFiles[0])
            workspaceFileName, _ = os.path.splitext(fileName)
            if utils.pathExists(utils.workspaceFilePath):
                # file exists, check if it loads OK
                try:
                    with open(utils.workspaceFilePath, 'r') as workspaceFile:
                        workspaceFileData = json.load(workspaceFile)

                        print("Existing " + fileName + " file found.")

                except Exception as err:
                    errorMsg = "Invalid " + fileName + " file.\n"
                    errorMsg += "Possible cause: invalid json format or comments (not supported by this scripts). Error:\n"
                    errorMsg += str(err)
                    print(errorMsg)

        # else: verified in 'utils.verifyFolderStructure()'

    def getWorkspaceFileData(self):
        '''
        Get data from current '*.code-workspace' file.
        File existance is previoulsy checked in 'checkWorkspaceFile()'.
        '''
        with open(utils.workspaceFilePath, 'r') as workspaceFile:
            data = json.load(workspaceFile)

        return data

    def addBuildDataToWorkspaceFile(self, workspaceData, buildData):
        '''
        This function ads "cortex-debug.*" items to workspace file, if they don't exist yet.
        Returns new data.
        '''
        armToolchainPath = os.path.dirname(buildData[self.bStr.gccExePath])
        armToolchainPath = utils.pathWithForwardSlashes(armToolchainPath)

        if 'settings' not in workspaceData:
            workspaceData["settings"] = {}

        workspaceData["settings"]["cortex-debug.armToolchainPath"] = armToolchainPath
        workspaceData["settings"]["cortex-debug.openocdPath"] = buildData[self.bStr.openOcdPath]

        return workspaceData

    def overwriteWorkspaceFile(self, data):
        '''
        Overwrite existing '*.code-workspace' file with new data.
        '''
        try:
            with open(utils.workspaceFilePath, 'r+') as workspaceFile:
                workspaceFile.seek(0)
                workspaceFile.truncate()
                dataToWrite = json.dumps(data, indent=4, sort_keys=False)
                workspaceFile.write(dataToWrite)

            print("'*.code-workspace' file updated!")

        except Exception as err:
            errorMsg = "Exception error overwriting '*.code-workspace' file:\n"
            errorMsg += str(err)
            utils.printAndQuit(errorMsg)


########################################################################################################################
if __name__ == "__main__":
    utils.verifyFolderStructure()

    paths = pth.UpdatePaths()
    bData = build.BuildData()
    wksFile = UpdateWorkspaceFile()

    # build data (update tools paths if neccessary)
    buildData = bData.prepareBuildData()

    wksFile.checkWorkspaceFile()
    wksData = wksFile.getWorkspaceFileData()
    wksData = wksFile.addBuildDataToWorkspaceFile(wksData, buildData)

    wksFile.overwriteWorkspaceFile(wksData)
