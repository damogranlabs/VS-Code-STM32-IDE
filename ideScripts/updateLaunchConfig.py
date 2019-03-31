'''
Update/generate 'launch.json' file in .vscode subfolder.
'''
import os
import json

import utilities as utils
import templateStrings as tmpStr

import updatePaths as pth
import updateBuildData as build

__version__ = utils.__version__


class LaunchConfigurations():
    def __init__(self):
        self.bStr = build.BuildDataStrings()

    def checkLaunchFile(self):
        '''
        Check if 'launch.json' file exists. If it does, check if it is a valid JSON file.
        If it doesn't exist, create new according to template.
        '''
        if utils.pathExists(utils.launchPath):
            # file exists, check if it loads OK
            try:
                with open(utils.launchPath, 'r') as launchFile:
                    json.load(launchFile)

                    print("Existing 'launch.json' file found.")
                    return

            except Exception as err:
                errorMsg = "Invalid 'launch.json' file. Creating backup and new one.\n"
                errorMsg += "Possible cause: invalid json format or comments (not supported by this scripts). Error:\n"
                errorMsg += str(err)
                print(errorMsg)

                utils.copyAndRename(utils.launchPath, utils.launchBackupPath)

                self.createLaunchFile()

        else:  # 'launch.json' file does not exist jet, create it according to template string
            self.createLaunchFile()

    def createLaunchFile(self):
        '''
        Create fresh 'launch.json' file.
        '''
        try:
            with open(utils.launchPath, 'w') as launchFile:
                data = json.loads(tmpStr.launchFileTemplate)
                dataToWrite = json.dumps(data, indent=4, sort_keys=False)

                launchFile.seek(0)
                launchFile.truncate()
                launchFile.write(dataToWrite)

                print("New 'launch.json' file created.")

        except Exception as err:
            errorMsg = "Exception error creating new 'launch.json' file:\n"
            errorMsg += str(err)
            utils.printAndQuit(errorMsg)

    def getLaunchData(self):
        '''
        Get data from current 'launch.json' file.
        File existance is previoulsy checked in 'checkLaunchFile()'.
        '''
        with open(utils.launchPath, 'r') as launchFile:
            data = json.load(launchFile)

            return data

    def overwriteLaunchFile(self, data):
        '''
        Overwrite existing 'launch.json' file with new data.
        '''
        try:
            with open(utils.launchPath, 'r+') as launchFile:
                launchFile.seek(0)
                launchFile.truncate()
                dataToWrite = json.dumps(data, indent=4, sort_keys=False)
                launchFile.write(dataToWrite)

            print("'launch.json' file updated!")

        except Exception as err:
            errorMsg = "Exception error overwriting 'launch.json' file:\n"
            errorMsg += str(err)
            utils.printAndQuit(errorMsg)

    def addOrReplaceLaunchConfiguration(self, data, launchData):
        '''
        Check wether launch with this "name" already exists. If it doesn't, create new launch configuration, overwrite otherwise.
        '''
        thisConfigurationName = launchData["name"]

        configurationExist = False
        listOfConfigurations = data["configurations"]
        for configurationIndex, config in enumerate(listOfConfigurations):
            if config["name"] == thisConfigurationName:
                # launch with this name already exist, replace it's content
                data["configurations"][configurationIndex] = launchData
                configurationExist = True

        if not configurationExist:
            data["configurations"].append(launchData)

        return data

    def addAllLaunchConfigurations(self, launchData):
        '''
        Merge and return all combined launch configuration data.
        '''
        launchCfg = self.getDebugLaunchConfig()
        launchData = self.addOrReplaceLaunchConfiguration(launchData, launchCfg)

        launchCfg = self.getRunPythonLaunchConfig()
        launchData = self.addOrReplaceLaunchConfiguration(launchData, launchCfg)

        # TODO USER: User can add other launch configurations here
        # - copy any of getXLaunchConfig() functions below, edit
        # - add this function here as other launch configurations above

        return launchData

    ########################################################################################################################

    ########################################################################################################################
    def getDebugLaunchConfig(self):
        '''
        Create/repair 'Cortex debug' launch configuration.
        '''
        configurationData = """
        {
            "name": "will be replaced with templateStrings string",
            "type": "cortex-debug",
            "request": "launch",
            "servertype": "openocd",
            "cwd": "${workspaceFolder}",
            "executable": "will be replaced with path from buildData.json",
            "svdFile": "will be replaced with path from buildData.json",
            "configFiles": ["will be replaced with path from buildData.json"],
            "preLaunchTask": "will be replaced with templateStrings string"
        }
        """
        jsonConfigurationData = json.loads(configurationData)

        buildData = build.BuildData().getBuildData()

        jsonConfigurationData["name"] = tmpStr.launchName_Debug
        jsonConfigurationData["executable"] = buildData[self.bStr.targetExecutablePath]
        jsonConfigurationData["svdFile"] = buildData[self.bStr.stm32SvdPath]
        jsonConfigurationData["configFiles"] = [buildData[self.bStr.openOcdInterfacePath]]
        jsonConfigurationData["configFiles"].extend(buildData[self.bStr.openOcdConfig])
        jsonConfigurationData["preLaunchTask"] = tmpStr.taskName_build

        return jsonConfigurationData

    def getRunPythonLaunchConfig(self):
        '''
        Create 'Debug current Python file' launch configuration.
        '''
        configurationData = """
        {
            "name": "Debug current Python file",
            "type": "python",
            "request": "launch",
            "cwd": "${workspaceFolder}",
            "program": "${file}",
            "console": "integratedTerminal"
        }
        """
        jsonConfigurationData = json.loads(configurationData)

        return jsonConfigurationData


########################################################################################################################
if __name__ == "__main__":
    utils.verifyFolderStructure()

    paths = pth.UpdatePaths()
    bData = build.BuildData()
    launch = LaunchConfigurations()

    # build data (update tools paths if neccessary)
    buildData = bData.prepareBuildData()

    # create taks file
    launch.checkLaunchFile()
    launchData = launch.getLaunchData()
    launchData = launch.addAllLaunchConfigurations(launchData)

    launch.overwriteLaunchFile(launchData)
