'''
This script runs all other updateXxx.py scripts.
It should be called once CubeMX project was generated/re-generated or user settings were modified.

- add 'print-variable' capabilities to Makefile
- update/generate 'c_cpp_properties.json'
- update/generate 'buildData.json' and 'toolsPaths.json'
- update/generate 'tasks.json'
- update/generate 'launch.json'
'''
import sys
import time
import traceback

import updateWorkspaceFile as workspaceFile
import updateLaunchConfig as launch
import updateTasks as tasks
import updateBuildData as build
import updateMakefile as mkf
import updateWorkspaceSources as wks
import updatePaths as pth
import utilities as utils

__version__ = utils.__version__

if sys.version_info[0] < 3:
    raise Exception("Python 3 or later is required")

########################################################################################################################
if __name__ == "__main__":
    startTime = time.time()
    print("Update started.\n")
    status = 'OK'
    errorMsg = ''
    try:
        utils.verifyFolderStructure()

        paths = pth.UpdatePaths()
        bData = build.BuildData()
        cP = wks.CProperties()
        makefile = mkf.Makefile()
        tasks = tasks.Tasks()
        launch = launch.LaunchConfigurations()
        wksFile = workspaceFile.UpdateWorkspaceFile()

        # Makefile must exist
        makefile.checkMakefileFile()  # no point in continuing if Makefile does not exist
        makefile.restoreOriginalMakefile()

        # build data (update tools paths if neccessary)
        buildData = bData.prepareBuildData()

        # data from original makefile
        makeExePath = buildData[bData.bStr.buildToolsPath]
        gccExePath = buildData[bData.bStr.gccExePath]
        makefileData = makefile.getMakefileData(makeExePath, gccExePath)

        # create/update 'c_cpp_properties.json'
        cP.checkCPropertiesFile()
        cPropertiesData = cP.getCPropertiesData()
        cPropertiesData = cP.addMakefileDataToCPropertiesFile(cPropertiesData, makefileData)
        cPropertiesData = cP.addBuildDataToCPropertiesFile(cPropertiesData, buildData)
        cPropertiesData = cP.addCustomDataToCPropertiesFile(cPropertiesData, makefileData, buildData)
        cP.overwriteCPropertiesFile(cPropertiesData)

        # update Makefile
        makefile.createNewMakefile()
        makefileData = makefile.getMakefileData(makeExePath, gccExePath)  # get data from new Makefile

        # update buildData.json
        buildData = bData.addMakefileDataToBuildDataFile(buildData, makefileData)
        buildData = bData.addCubeMxProjectPathToBuildData(buildData)
        bData.overwriteBuildDataFile(buildData)

        # create build folder
        buildFolderName = makefileData[mkf.MakefileStrings.buildDir]
        utils.createBuildFolder(buildFolderName)

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

    except Exception as err:
        status = "ERROR"
        errorMsg = "Unexpected error occured during 'Update' procedure. Exception:\n" + traceback.format_exc()

    overallTime = int(time.time() - startTime)
    msg = "\n" + status + " (" + str(overallTime) + " seconds).\n" + errorMsg
    print(msg)
