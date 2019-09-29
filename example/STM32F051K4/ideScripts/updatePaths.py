'''
This script can be run to update paths to gcc, openOCD and other tools/files/folders.
Script verify and add data to 'buildData.json' file.
'''
import os
import shutil

import utilities as utils
import updateBuildData as build
import updateTasks as tasks
import updateLaunchConfig as launch
import updateWorkspaceFile as workspaceFile

__version__ = utils.__version__


class UpdatePaths():
    def __init__(self):
        self.bStr = build.BuildDataStrings()

        # list of paths with explanatory names and (optionally) default path
        # keys must match with 'self.bStr.toolsPaths' list
        self.pathsDescriptionsData = {
            self.bStr.gccExePath: {
                "name": "arm-none-eabi-gcc executable (arm-none-eabi-gcc.exe)",
                "defaultPath": "arm-none-eabi-gcc"},
            self.bStr.buildToolsPath: {
                "name": "make executable (make.exe)",
                "defaultPath": "make"},
            self.bStr.openOcdPath: {
                "name": "OpenOCD executable (openocd.exe)",
                "defaultPath": "openocd"},
            self.bStr.openOcdInterfacePath: {
                "name": "OpenOCD ST Link interface path ('stlink.cfg')",
                "defaultPath": "./scripts/interface/stlink.cfg"},
            self.bStr.stm32SvdPath: {
                "name": "STM target '*.svd' file (.../Keil*/CMSIS/SVD/STM32F0x1.svd)",
                "defaultPath": None}
        }

    def verifyToolsPaths(self, toolsPaths, request=False):
        '''
        This function checks if paths in 'toolsPaths.json' are a valid paths.
        If any path is not valid/missing, user is asked for update via updatePath().
        If 'request' is set to True, user is asked to update path even if it is a valid path.

        Returns updated valid tools paths.
        '''
        for pathName in self.bStr.toolsPaths:
            try:
                mustBeUpdated = False
                if pathName in toolsPaths:
                    # 'toolsPaths.json' keys are not lists. Always a plain path (string)
                    if not utils.pathExists(toolsPaths[pathName]):
                        mustBeUpdated = True
                        # path not valid, check if command
                        if utils.commandExists(toolsPaths[pathName]):
                            mustBeUpdated = False

                    if mustBeUpdated:
                        if toolsPaths[pathName] != '':
                            # avoid reporting invalid file path, if there is an empty string
                            msg = "\n\nInvalid path detected in '" + pathName + "' key."
                            print(msg)
                    else:
                        if request:
                            msg = "\n\nValid path(s) for " + pathName + " detected: '" + toolsPaths[pathName] + "'."
                            msg += "\n\tUpdate? [y/n]: "
                            if utils.getYesNoAnswer(msg):
                                mustBeUpdated = True

                else:  # this key is missing in toolsPaths.json!
                    mustBeUpdated = True

                if mustBeUpdated:
                    if pathName in self.bStr.derivedPaths:
                        continue

                    elif pathName == self.bStr.openOcdConfig:
                        # get openOcdConfig - special handler
                        toolsPaths[pathName] = utils.getOpenOcdConfig(toolsPaths[self.bStr.openOcdPath])

                    elif pathName in self.pathsDescriptionsData:
                        name = self.pathsDescriptionsData[pathName]['name']
                        defaultPath = self.pathsDescriptionsData[pathName]['defaultPath']
                        toolsPaths[pathName] = self.updatePath(name, defaultPath)

                    else:
                        toolsPaths[pathName] = self.updatePath(pathName, None)

            except Exception as err:
                toolsPaths[pathName] = self.updatePath(pathName, None)

        for pathName in self.bStr.derivedPaths:
            if pathName == self.bStr.pythonExec:
                toolsPaths[self.bStr.pythonExec] = utils.getPython3Executable()

            elif pathName == self.bStr.gccInludePath:
                toolsPaths[self.bStr.gccInludePath] = utils.getGccIncludePath(toolsPaths[self.bStr.gccExePath])

            else:
                errorMsg = "ideScripts design error: pathName '" + pathName + "' is in 'self.bStr.derivedPaths' list, "
                errorMsg += "but no 'get()' handler is specified."
                utils.printAndQuit(errorMsg)

        return toolsPaths

    def verifyTargetConfigurationPaths(self, buildData, request=False):
        '''
        This function checks if 'buildData.json' contains targetConfiguration paths.
        If any path is not valid/missing, user is asked for update via updatePath().
        If 'request' is set to True, user is asked to update path even if it is a valid path.

        Returns buildData with a valid, updated tools paths.
        '''
        for pathName in self.bStr.targetConfigurationPaths:
            mustBeUpdated = False

            if pathName in self.bStr.derivedPaths:
                # derived paths, build later
                continue

            if pathName not in buildData:
                mustBeUpdated = True

            else:
                if isinstance(buildData[pathName], list):
                    if not buildData[pathName]:
                        mustBeUpdated = True
                    else:
                        for path in buildData[pathName]:
                            if not utils.pathExists(path):
                                mustBeUpdated = True
                                break

                else:  # not a list, a single path expected
                    if not utils.pathExists(buildData[pathName]):
                        mustBeUpdated = True
                        # path not valid, check if command
                        if utils.commandExists(buildData[pathName]):
                            mustBeUpdated = False

            if mustBeUpdated:
                notify = True
                # avoid reporting invalid file path, if there is an empty string/list
                if isinstance(buildData[pathName], list):
                    if not buildData[pathName]:
                        notify = False
                else:
                    if buildData[pathName] == '':
                        notify = False

                if notify:
                    msg = "\n\nInvalid path detected in 'buildData.json' '" + pathName + "' key."
                    print(msg)
            else:
                if request:
                    msg = "\n\nValid path(s) for " + pathName + " detected: '" + str(buildData[pathName]) + "'."
                    msg += "\n\tUpdate? [y/n]: "
                    if utils.getYesNoAnswer(msg):
                        mustBeUpdated = True

            if mustBeUpdated:
                if pathName == self.bStr.openOcdConfig:
                    # get openOcdConfig - special handler
                    buildData[pathName] = utils.getOpenOcdConfig(buildData[self.bStr.openOcdPath])

                elif pathName in self.bStr.derivedPaths:
                    name = self.bStr.derivedPaths[pathName]['name']
                    defaultPath = self.bStr.derivedPaths[pathName]['defaultPath']
                    buildData[pathName] = self.updatePath(name, defaultPath)

                else:
                    buildData[pathName] = self.updatePath(pathName, None)

        return buildData

    def copyTargetConfigurationFiles(self, buildData):
        '''
        This function checks if paths to target configuration files listed in 'BuildDataStrings.targetConfigurationPaths'
        are available, stored inside this workspace '.vscode' subfolder. Once this files are copied, paths are updated and
        new buildData is returned.

        Paths are previously checked/updated in 'verifyTargetConfigurationPaths()'
        '''
        for pathName in self.bStr.targetConfigurationPaths:
            currentPaths = buildData[pathName]

            if isinstance(currentPaths, list):
                isList = True
            else:
                isList = False
                currentPaths = [currentPaths]

            newPaths = []
            for currentPath in currentPaths:
                fileName = utils.getFileName(currentPath, withExtension=True)
                fileInVsCodeFolder = os.path.join(utils.vsCodeFolderPath, fileName)

                if not utils.pathExists(fileInVsCodeFolder):
                    # file does not exist in '.vscode' folder
                    try:
                        newPath = shutil.copy(currentPath, utils.vsCodeFolderPath)
                    except Exception as err:
                        errorMsg = "Unable to copy file '" + fileName + "' to '.vscode' folder. Exception:\n" + str(err)
                        utils.printAndQuit(errorMsg)

                newPath = os.path.relpath(fileInVsCodeFolder)
                newPath = utils.pathWithForwardSlashes(newPath)
                newPaths.append(newPath)

            if isList:
                buildData[pathName] = newPaths
            else:
                buildData[pathName] = newPaths[0]

        return buildData

    def updatePath(self, pathName, default):
        '''
        This function is called when a path is detected as invalid or the user requests to update paths.
        '''
        pathDefault = None

        # check if default is a path
        if utils.pathExists(default):
            pathDefault = default

        # not a path command, check if it's a command
        elif utils.commandExists(default):
            pathDefault = shutil.which(default)

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
    tasks = tasks.Tasks()
    launch = launch.LaunchConfigurations()
    wksFile = workspaceFile.UpdateWorkspaceFile()

    # update build data
    buildData = bData.prepareBuildData(request=True)
    bData.overwriteBuildDataFile(buildData)

    # update tasks
    tasks.checkTasksFile()
    tasksData = tasks.getTasksData()
    tasksData = tasks.addAllTasks(tasksData)
    tasks.overwriteTasksFile(tasksData)

    # update launch configurations
    launch.checkLaunchFile()
    launchData = launch.getLaunchData()
    launchData = launch.addAllLaunchConfigurations(launchData)
    launch.overwriteLaunchFile(launchData)

    # update workspace file with "cortex-debug" specifics
    wksFile.checkWorkspaceFile()
    wksData = wksFile.getWorkspaceFileData()
    wksData = wksFile.addBuildDataToWorkspaceFile(wksData, buildData)
    wksFile.overwriteWorkspaceFile(wksData)
