'''
Common utilities for 'update*.py' scripts.

This script can be called standalone to verify if folder structure is correct and to print out all workspace
paths.
'''

import os
import shutil
import sys

__version__ = '1.2'  # this is inherited by all 'update*.py' scripts

########################################################################################################################
# Global utilities and paths
########################################################################################################################

workspacePath = None  # absolute path to workspace folder
workspaceFilePath = None  # absolute file path to '*.code-workspace' file
ideScriptsPath = None  # absolute path to 'ideScripts' folder

makefilePath = None
makefileBackupPath = None
cPropertiesPath = None
cPropertiesBackupPath = None
buildDataPath = None
tasksPath = None
tasksBackupPath = None
launchPath = None
launchBackupPath = None


def printAndQuit(msg):
    '''
    Unrecoverable error, print and quit with system
    '''
    msg = "\n**** ERROR (unrecoverable) ****\n\t" + str(msg)
    sys.exit(msg)


def fileFolderExists(path):
    if path is not None:
        return os.path.exists(path)
    else:
        return False


def copyAndRename(filePath, newName):
    if not fileFolderExists(filePath):
        errorMsg = "Can't copy and rename file " + str(filePath) + ", does not exist or other error."
        printAndQuit(errorMsg)

    fileFolderPath = os.path.dirname(filePath)
    copyFilePath = os.path.join(fileFolderPath, newName)
    shutil.copyfile(filePath, copyFilePath)

    msg = "Copy of file (new name: " + newName + "):\n\t" + str(filePath)
    print(msg)


def verifyFolderStructure():
    '''
    Verify if 'ideScript' folder is in the same folder as '*.code-workspace' file.
    If it is, update project relevant paths.
    '''
    global workspacePath
    global workspaceFilePath
    global ideScriptsPath

    global makefilePath
    global makefileBackupPath
    global cPropertiesPath
    global cPropertiesBackupPath
    global buildDataPath
    global tasksPath
    global tasksBackupPath
    global launchPath
    global launchBackupPath

    thisFolderPath = os.path.dirname(__file__)

    workspacePath = os.path.dirname(thisFolderPath)
    workspacePath = pathWithForwardSlashes(workspacePath)

    vscodeWorkspaceFolder = os.path.join(workspacePath, ".vscode")
    if not fileFolderExists(vscodeWorkspaceFolder):
        try:
            print("Creating '.vscode' subfolder.")
            os.mkdir(vscodeWorkspaceFolder)
        except Exception as err:
            errorMsg = "Exception error creating '.vscode' subfolder:\n"
            errorMsg += str(err)
            printAndQuit(errorMsg)

    ideScriptsPath = os.path.join(workspacePath, 'ideScripts')
    ideScriptsPath = pathWithForwardSlashes(ideScriptsPath)

    for item in os.listdir(workspacePath):
        if item.endswith('.code-workspace'):
            # workspace '*.code-workspace' file found
            workspaceFilePath = os.path.join(workspacePath, item)
            workspaceFilePath = pathWithForwardSlashes(workspaceFilePath)

            if fileFolderExists(ideScriptsPath):
                # 'ideScripts' folder found in the same folder as '*.code-workspace' file. Structure seems OK.
                cPropertiesPath = os.path.join(workspacePath, '.vscode', 'c_cpp_properties.json')
                cPropertiesPath = pathWithForwardSlashes(cPropertiesPath)
                cPropertiesBackupPath = cPropertiesPath + ".backup"

                makefilePath = os.path.join(workspacePath, 'Makefile')
                makefilePath = pathWithForwardSlashes(makefilePath)
                makefileBackupPath = makefilePath + ".backup"

                buildDataPath = os.path.join(workspacePath, '.vscode', 'buildData.json')
                buildDataPath = pathWithForwardSlashes(buildDataPath)
                # does not have backup file, always regenerated

                tasksPath = os.path.join(workspacePath, '.vscode', 'tasks.json')
                tasksPath = pathWithForwardSlashes(tasksPath)
                tasksBackupPath = tasksPath + ".backup"

                launchPath = os.path.join(workspacePath, '.vscode', 'launch.json')
                launchPath = pathWithForwardSlashes(launchPath)
                launchBackupPath = launchPath + ".backup"
                return

            errorMsg = "'ideScripts' folder not found in the same folder as '*.code-workspace' file.\n"
            errorMsg += "Did you rename it?"
            printAndQuit(errorMsg)
    else:
        errorMsg = "Invalid file/folder structure!"
        errorMsg += "'ideScripts' folder should be in the same folder as '*.code-workspace' file.\n"
        errorMsg += "All other '*.py' files should be inside 'ideScripts' folder. Do not rename any files or folders."
        printAndQuit(errorMsg)


def printWorkspacePaths():
    print("\nWorkspace root folder: " + workspacePath)
    print("VS Code workspace file: " + workspaceFilePath)
    print("'ideScripts' folder: " + ideScriptsPath)
    print("\n'Makefile': " + makefilePath)
    print("'Makefile.backup': " + makefileBackupPath)
    print("\n'c_cpp_properties.json': " + cPropertiesPath)
    print("'c_cpp_properties.json.backup': " + cPropertiesBackupPath)
    print("\n'buildData.json': " + buildDataPath)
    print("\n'tasks.json': " + tasksPath)
    print("'tasks.json.backup': " + tasksBackupPath)
    print("\n'launch.json': " + launchPath)
    print("'launch.json.backup': " + launchBackupPath)
    print()


def createBuildFolder(folderName='build'):
    '''
    Create (if not already created) build folder with specified name where objects are stored when 'make' is executed. 
    '''
    buildFolderPath = os.path.join(workspacePath, folderName)
    if not fileFolderExists(buildFolderPath):
        os.mkdir(buildFolderPath)
        print("Build folder created: " + buildFolderPath)
    else:
        print("Build folder already exist: '" + buildFolderPath + "'")


def getWorkspaceName():
    iocFiles = []

    for f in os.listdir(workspacePath):
        if f.endswith(".ioc"):
            iocFiles.append(f)

    if len(iocFiles) > 1:
        errorMsg = "More than one .ioc file in workspace directory. Only one is allowed."
        printAndQuit(errorMsg)

    name = iocFiles[0].rstrip('.ioc')
    return name


def stripStartOfString(dataList, stringToStrip):
    newData = []

    for data in dataList:
        if data.find(stringToStrip) != -1:
            item = data[len(stringToStrip):]
            newData.append(item)
        else:
            newData.append(data)

    return newData


def preappendString(data, stringToAppend):
    if type(data) is list:
        for itemIndex, item in enumerate(data):
            data[itemIndex] = stringToAppend + item
    else:
        data = stringToAppend + data

    return data


def askUserForPathUpdate(pathName):
    '''
    Ask if user will update compiler path by entering path in terminal window.
    Return True/False
    '''
    print("\n\n??? Do you wish to update path to '" + pathName + "'?")
    print("Type 'y' or 'n' and press Enter:")
    while(True):
        userAnswer = input()
        if userAnswer not in ['y', 'n']:
            print("Type 'y' or 'n' and press Enter: ", end="")
        else:
            break

    if userAnswer == 'n':
        print("\tDo not update path.")
        return False
    else:  # 'y'
        return True


def getUserPath(pathName):
    '''
    Get absolute path from user (by entering path in terminal window).
    '''
    msg = "\n\n??? Enter path to '" + pathName + "':\n\tPaste here and press Enter: "
    path = input(msg)
    path = path.replace('\"', '')  # remove " "
    path = path.replace('\'', '')  # remove ' '
    path = pathWithForwardSlashes(path)
    return path


def pathWithForwardSlashes(path):
    path = os.path.normpath(path)
    path = path.replace("\\", "/")
    return path


def getGccIncludePath(gccExePath):
    '''
    Get path to '...\include' folder from 'gccExePath', where standard libs and headers. Needed for VS Code Intellisense.

    If ARM GCC folder structure remains the same as official, .exe is located in \bin folder.
    Other headers can be found in '\lib\gcc\arm-none-eabi\***\include' folder, which is found by searching for
    <stdint.h>.
    '''
    gccExeFolderPath = os.path.dirname(gccExePath)
    gccFolderPath = os.path.dirname(gccExeFolderPath)
    searchPath = os.path.join(gccFolderPath, "lib", "gcc", "arm-none-eabi")

    searchForFile = "stdint.h"
    for root, dirs, files in os.walk(searchPath, topdown=False):
        if searchForFile in files:
            folderPath = pathWithForwardSlashes(root)
            return folderPath

    errorMsg = "Unable to find 'include' subfolder with " + searchForFile + " file on path:\n\t"
    errorMsg += searchPath
    printAndQuit(errorMsg)


def getSTLinkPath(openOCDTargetPath):
    '''
    Get path to '.../scripts/interface/stlink.cfg' file from 'openOCDTargetPath'

    Default (official) folder structure:
    .../openOCD/
        - /scripts/
            - /target/  ('openOCDTargetPath' specified with user input)
            - /interface/stlink.cfg
    '''
    fileName = 'stlink.cfg'

    targetFolderPath = os.path.dirname(openOCDTargetPath)
    scriptsFolderPath = os.path.dirname(targetFolderPath)
    interfaceFolderPath = os.path.join(scriptsFolderPath, 'interface')

    stLinkPath = os.path.join(interfaceFolderPath, fileName)
    stLinkPath = pathWithForwardSlashes(stLinkPath)
    if not fileFolderExists(stLinkPath):
        errorMsg = "Unable to find path to openOCD stlink.cfg configuration file on path:\n\t" + str(stLinkPath)
        printAndQuit(errorMsg)

    return stLinkPath


def getBuildElfFilePath(buildDirPath, projectName):
    '''
    Returns .elf file path.
    '''
    elfFile = projectName + ".elf"
    buildFileName = os.path.join(workspacePath, buildDirPath, elfFile)
    buildFileName = pathWithForwardSlashes(buildFileName)

    return buildFileName


########################################################################################################################
if __name__ == "__main__":
    verifyFolderStructure()

    print("Workspace generation script version: " + __version__)
    printWorkspacePaths()
