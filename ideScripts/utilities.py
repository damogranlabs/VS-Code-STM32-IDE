'''
Common utilities for 'update*.py' scripts.

This script can be called standalone to verify if folder structure is correct and to print out all workspace
paths.
'''

import os
import shutil
import sys
import traceback

__version__ = '1.3'  # this is inherited by all 'update*.py' scripts

########################################################################################################################
# Global utilities and paths
########################################################################################################################

workspacePath = None  # absolute path to workspace folder
workspaceFilePath = None  # absolute file path to '*.code-workspace' file
cubeMxProjectFilePath = None  # absolute path to *.ioc STM32CubeMX workspace file
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
    msg = "\n**** ERROR (unrecoverable) ****\n" + str(msg)
    print(msg)

    if sys.exc_info()[2]:  # was exception raised?
        print("\nTraceback:")
        traceback.print_exc()
    sys.exit(1)


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
    Verify if folder structure is correct.
    'ideScript' folder must be placed in the root of the project, where:
        - exactly one '*.code-workspace' file must exist (this is also Workspace name)
        - '.vscode' folder is present (it is created if it doesn't exist jet)

    If this requirements are met, all paths are built - but not checked (they are checked in their respective .py files).
        - build, launch, tasks, cpp properties files
        - Makefile
        - STM32CubeMX '.ioc'
        - backup file paths
    '''
    global workspacePath
    global workspaceFilePath
    global cubeMxProjectFilePath
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

    thisFolderPath = os.path.dirname(sys.argv[0])
    workspacePath = pathWithForwardSlashes(os.path.dirname(thisFolderPath))
    ideScriptsPath = pathWithForwardSlashes(os.path.join(workspacePath, 'ideScripts'))

    codeWorkspaces = getCodeWorkspaces()
    if len(codeWorkspaces) == 1:
        # '*.code-workspace' file found
        workspaceFilePath = codeWorkspaces[0]  # file existance is previously checked in getCodeWorkspaces()
    else:
        errorMsg = "Invalid folder/file structure:\n"
        errorMsg += "Exactly one VS Code workspace ('*.code-workspace') file must exist "
        errorMsg += "in the root folder where 'ideScripts' folder is placed.\n"
        errorMsg += "Expecting one '*.code-workspace' file in: " + workspacePath
        printAndQuit(errorMsg)

    vscodeFolder = pathWithForwardSlashes(os.path.join(workspacePath, ".vscode"))
    if not fileFolderExists(vscodeFolder):
        try:
            os.mkdir(vscodeFolder)
            print("'.vscode' folder created.")
        except Exception as err:
            errorMsg = "Exception error creating '.vscode' subfolder:\n" + str(err)
            printAndQuit(errorMsg)
    else:
        print("Existing '.vscode' folder used.")

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

    cubeMxFiles = getCubeMXProjectFiles()
    if len(cubeMxFiles) == 1:
        cubeMxProjectFilePath = cubeMxFiles[0]
        print("One STM32CubeMX file found: " + cubeMxProjectFilePath)
    else:  # more iocFiles:
        cubeMxProjectFilePath = None
        print("WARNING: None or more than one STM32CubeMX files found. None or one expected.")


def printWorkspacePaths():
    print("\nWorkspace root folder: " + workspacePath)
    print("VS Code workspace file: " + workspaceFilePath)
    if cubeMxProjectFilePath is not None:
        print("CubeMX project file: " + cubeMxProjectFilePath)
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


def getCubeMXProjectFiles():
    '''
    Returns list of all STM32CubeMX '.ioc' files in root directory.
    '''
    iocFiles = []
    for theFile in os.listdir(workspacePath):
        if theFile.endswith('.ioc'):
            filePath = pathWithForwardSlashes(os.path.join(workspacePath, theFile))
            iocFiles.append(filePath)

    return iocFiles


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


def getCubeWorkspaces():
    '''
    Search workspacePath for files that ends with '.ioc' (STM32CubeMX projects).
    Returns list of all available STM32CubeMX workspace paths.

    Only root directory is searched.
    '''
    iocFiles = []

    for theFile in os.listdir(workspacePath):
        if theFile.endswith(".ioc"):
            theFilePath = os.path.join(workspacePath, theFile)
            iocFiles.append(pathWithForwardSlashes(theFile))

    return iocFiles


def getCodeWorkspaces():
    '''
    Search workspacePath for files that ends with '.code-workspace' (VS Code workspaces).
    Returns list of all available VS Code workspace paths.

    Only root directory is searched.
    '''
    codeFiles = []

    for theFile in os.listdir(workspacePath):
        if theFile.endswith(".code-workspace"):
            theFilePath = os.path.join(workspacePath, theFile)
            codeFiles.append(pathWithForwardSlashes(theFilePath))

    return codeFiles


def getWorkspaceName():
    '''
    Return name (without extension) for this project '.code-workspace' file.

    Return first available file name without extension.
    '''
    _, fileNameExt = os.path.split(workspaceFilePath)
    fileName, _ = os.path.splitext(fileNameExt)
    return fileName


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


def stringToList(string, separator):
    '''
    Get list of unparsed string items into list. Strip any redundant spaces.
    '''
    allItems = []
    items = string.split(separator)
    for item in items:
        item = item.strip()
        allItems.append(item)

    return allItems


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


def getAllFilesInFolderTree(pathToFolder):
    '''
    Get the list of all files in directory tree at given path
    '''
    allFiles = []
    if os.path.exists(pathToFolder):
        for (dirPath, dirNames, fileNames) in os.walk(pathToFolder):
            for theFile in fileNames:
                filePath = os.path.join(dirPath, theFile)
                filePath = pathWithForwardSlashes(filePath)
                allFiles.append(filePath)

    return allFiles


########################################################################################################################
if __name__ == "__main__":
    print("Workspace generation script version: " + __version__)
    verifyFolderStructure()
    print("This workspace name:", getWorkspaceName())
    printWorkspacePaths()
