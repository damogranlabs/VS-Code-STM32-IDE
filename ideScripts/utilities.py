'''
Common utilities for 'update*.py' scripts.

This script can be called standalone to verify if folder structure is correct and to print out all workspace
paths.
'''

import os
import shutil
import subprocess
import sys
import traceback
import platform

import templateStrings as tmpStr

__version__ = '1.7'  # this is inherited by all 'update*.py' scripts

########################################################################################################################
# Global utilities and paths
########################################################################################################################

workspacePath = None  # absolute path to workspace folder
workspaceFilePath = None  # absolute file path to '*.code-workspace' file
cubeMxProjectFilePath = None  # absolute path to *.ioc STM32CubeMX workspace file
ideScriptsPath = None  # absolute path to 'ideScripts' folder
vsCodeFolderPath = None  # absolute path to workspace '.vscode' folder

makefilePath = None
makefileBackupPath = None
cPropertiesPath = None
cPropertiesBackupPath = None
buildDataPath = None
toolsPaths = None  # absolute path to toolsPaths.json with common user settings
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


def pathExists(path):
    '''
    Checks if a path exists.
    '''
    if path is not None:
        return os.path.exists(path)
    else:
        return False


def commandExists(command):
    '''
    Checks if a command exists.
    '''
    if command is not None:
        if shutil.which(command):
            return True

    return False


def getFileName(path, withExtension=False, exception=True):
    '''
    Returns file name of a given 'path', with or without extension.
    If given path is not a file, exception is raised if 'exception' is set to True. Otherwise, None is returned.
    '''
    if os.path.isfile(path):
        _, fileNameExt = os.path.split(path)
        if withExtension:
            return fileNameExt
        else:
            fileName, _ = os.path.splitext(fileNameExt)
            return fileName
    else:
        if exception:
            errorMsg = "Cannot get a file name - given path is not a file:\n\t" + path
            raise Exception(errorMsg)
        else:
            return None


def detectOs():
    '''
    This function detects the operating system that python is running in. We use this for OS specific operations
    '''
    if platform.system() == "Darwin":
        osIs = "osx"
    elif os.name == "nt":
        osIs = "windows"
    elif os.name == "java":
        osIs = "java"
    elif os.name == "posix":
        release = platform.release()  # get system release
        release = release.lower()
        if release.endswith("microsoft"):  # Detect windows subsystem for linux (wsl)
            osIs = "wsl"
        else:
            osIs = "unix"
    return osIs


def copyAndRename(filePath, newPath):
    '''
    Copy file from 'filePath' to a new 'newPath'. 
    '''
    if not pathExists(filePath):
        errorMsg = "Can't copy non-existing file: " + str(filePath)
        printAndQuit(errorMsg)

    shutil.copyfile(filePath, newPath)
    newFileName = getFileName(newPath)
    msg = "Copy of file (new name: " + newFileName + "): " + str(filePath)
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
    global vsCodeFolderPath

    global makefilePath
    global makefileBackupPath
    global cPropertiesPath
    global cPropertiesBackupPath
    global buildDataPath
    global toolsPaths
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
    if not pathExists(vscodeFolder):
        try:
            os.mkdir(vscodeFolder)
            print("'.vscode' folder created.")
        except Exception as err:
            errorMsg = "Exception error creating '.vscode' subfolder:\n" + str(err)
            printAndQuit(errorMsg)
    else:
        print("Existing '.vscode' folder used.")
    vsCodeFolderPath = vscodeFolder

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

    osIs = detectOs()
    if osIs == "windows":
        vsCodeSettingsFolderPath = tmpStr.defaultVsCodeSettingsFolder_WIN
    elif osIs == "unix":
        vsCodeSettingsFolderPath = tmpStr.defaultVsCodeSettingsFolder_UNIX
    elif osIs == "osx":
        vsCodeSettingsFolderPath = tmpStr.defaultVsCodeSettingsFolder_OSX
    toolsPaths = os.path.join(vsCodeSettingsFolderPath, 'toolsPaths.json')
    toolsPaths = pathWithForwardSlashes(toolsPaths)

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
    print("\nWorkspace root folder:", workspacePath)
    print("VS Code workspace file:", workspaceFilePath)
    print("CubeMX project file:", cubeMxProjectFilePath)
    print("'ideScripts' folder:", ideScriptsPath)

    print("\n'Makefile':", makefilePath)
    print("'Makefile.backup':", makefileBackupPath)

    print("\n'c_cpp_properties.json':", cPropertiesPath)
    print("'c_cpp_properties.json.backup':", cPropertiesBackupPath)
    print("\n'tasks.json':", tasksPath)
    print("'tasks.json.backup':", tasksBackupPath)
    print("\n'launch.json':", launchPath)
    print("'launch.json.backup':", launchBackupPath)

    print("\n'buildData.json':", buildDataPath)
    print("'toolsPaths.json':", toolsPaths)
    print()


def getCubeMXProjectFiles():
    '''
    Returns list of all STM32CubeMX '.ioc' files in root directory.
    Since only root directory is searched, all files (paths) are relative to root dir.
    '''
    iocFiles = []
    for theFile in os.listdir(workspacePath):
        if theFile.endswith('.ioc'):
            iocFiles.append(theFile)

    return iocFiles


def createBuildFolder(folderName='build'):
    '''
    Create (if not already created) build folder with specified name where objects are stored when 'make' is executed.
    '''
    buildFolderPath = os.path.join(workspacePath, folderName)
    buildFolderPath = pathWithForwardSlashes(buildFolderPath)
    if not pathExists(buildFolderPath):
        os.mkdir(buildFolderPath)
        print("Build folder created: " + buildFolderPath)
    else:
        print("Build folder already exist: '" + buildFolderPath + "'")


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
    return getFileName(workspaceFilePath)


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


def mergeCurrentDataWithTemplate(currentData, templateData):
    '''
    Merge all fields from both, currentData and templateData and return merged dict.
    This is needed for backward compatibility and adding missing default fields.
    '''
    def recursiveClone(template, data):
        for key, value in data.items():
            if key not in template:
                template[key] = {}  # create a dict in case it must be copied recursively

            if isinstance(value, dict):
                template[key] = recursiveClone(template[key], value)
            else:
                template[key] = value
        return template

    mergedData = recursiveClone(templateData, currentData)

    return mergedData


def getYesNoAnswer(msg):
    '''
    Asks the user a generic yes/no question.
    Returns True for yes, False for no
    '''
    while(True):
        resp = input(msg).lower()
        if resp == 'y':
            return True
        elif resp == 'n':
            return False
        else:
            continue


def getUserPath(pathName):
    '''
    Get path or command from user (by entering path in terminal window).
    Repeated as long as user does not enter a valid path or command to file/folder/executable.
    '''
    while True:
        msg = "\n\tEnter path or command for '" + pathName + "':\n\tPaste here and press Enter: "
        path = input(msg)
        path = pathWithoutQuotes(path)
        path = pathWithForwardSlashes(path)

        if pathExists(path):
            break
        elif commandExists(path):
            break
        else:
            print("\tPath/command not valid: ", path)

    return path


def pathWithoutQuotes(path):
    path = path.replace('\"', '')  # remove " "
    path = path.replace('\'', '')  # remove ' '
    path = path.strip()  # remove any redundant spaces

    return path


def pathWithForwardSlashes(path):
    path = os.path.normpath(path)
    path = path.replace("\\", "/")
    return path


def getGccIncludePath(gccExePath):
    '''
    Get path to '...\include' folder from 'gccExePath', where standard libs and headers. Needed for VS Code Intellisense.

    If ARM GCC folder structure remains the same as official, the executable is located in \bin folder.
    Other headers can be found in '\lib\gcc\arm-none-eabi\***\include' folder, which is found by searching for
    <stdint.h>.
    '''
    gccExeFolderPath = os.path.dirname(gccExePath)
    gccFolderPath = os.path.dirname(gccExeFolderPath)
    searchPath = os.path.join(gccFolderPath, "lib", "gcc", "arm-none-eabi")

    fileName = "stdint.h"
    filePath = findFileInFolderTree(searchPath, fileName)
    if filePath is None:
        errorMsg = "Unable to find " + fileName + " file on path: " + searchPath
        errorMsg += "\nOfficial GCC folder structure must remain intact!"
        printAndQuit(errorMsg)

    folderPath = os.path.dirname(filePath)
    return folderPath


def getPython3Executable():
    '''
    Uses detectOs() to determine the correct python command to use for python related tasks
    '''
    osIs = detectOs()

    if osIs == "unix" or osIs == "wsl" or osIs=="osx":  # detected unix based system
        pythonExec = "python3"
    else:  # windows or other system
        pythonExec = "python"

    if not commandExists(pythonExec):
        msg = "\n\tPython version 3 or later installation not detected, please install or enter custom path/command below."
        print(msg)
        pythonExec = getUserPath(pythonExec)

    return pythonExec


def getOpenOcdInterface(openOcdPath):
    '''
    Try to get OpenOCD interface file (TODO: currently hard-coded 'stlink.cfg') from 'openocd.exe' (openOcdPath) path.
    If such path can't be found ask user for update.
    Returns absolute path to 'stlink.cfg' file.
    '''
    openOcdExeFolderPath = os.path.dirname(openOcdPath)  # ../bin
    openOcdRootPath = os.path.dirname(openOcdExeFolderPath)  # ../
    # interfaceFolderPath = os.path.join(openOcdRootPath, 'scripts', 'interface') # only on windwos, linux has different structure

    # get openOcdInterfacePath from
    # TODO here of once anything other than stlink will be supported
    fileName = "stlink.cfg"
    openOcdInterfacePath = findFileInFolderTree(openOcdRootPath, fileName)
    if openOcdInterfacePath is None:
        openOcdInterfacePath = getUserPath("stlink.cfg interface")

    return openOcdInterfacePath


def getOpenOcdConfig(openOcdInterfacePath):
    '''
    Get openOCD configuration files from user, eg. 'interface/stlink.cfg, target/stm32f0x.cfg'
    Paths can be passed in absolute or relative form, separated by comma. Optionally enclosed in " or '.
    Returns the list of absolute paths to these config files.
    '''
    openOcdScriptsPath = os.path.dirname(os.path.dirname(openOcdInterfacePath))

    while(True):
        msg = "\n\tEnter path(s) to OpenOCD configuration file(s):\n\t\t"
        msg += "Example: 'target/stm32f0x.cfg'. Absolute or relative to OpenOCD /scripts/ folder.\n\t\t"
        msg += "If more than one file is needed, separate with comma.\n\t\t"
        msg += "Paste here and press Enter: "
        configFilesStr = input(msg)

        allConfigFiles = []
        configFiles = configFilesStr.split(',')
        for theFile in configFiles:
            # ex.: " C:/asd/foo bar/fail.cfg " , ' C:/asd/bar foo/fail.cfg' ,
            theFile = theFile.strip()
            theFile = theFile.strip('\'')
            theFile = theFile.strip('\"')
            theFile = theFile.strip()
            theFile = pathWithForwardSlashes(theFile)

            if pathExists(theFile):  # file is an absolute path
                allConfigFiles.append(theFile)
            else:
                # arg is a relative path. Must be relative to OpenOCD 'scripts' folder
                theFileAbs = os.path.join(openOcdScriptsPath, theFile)
                theFileAbs = pathWithForwardSlashes(theFileAbs)
                if pathExists(theFileAbs):
                    allConfigFiles.append(theFileAbs)
                else:
                    msg = "\tConfiguration invalid (file not found): \'" + theFileAbs + "\'"
                    print(msg)
                    break
        else:
            break  # break loop if config detected successfully
        continue  # continue if unsuccessful

    return allConfigFiles


def getStm32SvdFile(stm32SvdPath):
    ''' # TODO HERE - deprecated? no use cases?
    Get stm32SvdFile from user, eg. 'STM32F042x.svd'
    Validates that file exists
    '''
    while True:
        msg = "\n\tEnter SVD File name (eg: 'STM32F042x.svd'), or 'ls' to list available SVD files.\n\tSVD file name: "
        fileName = input(msg)

        if fileName == "ls":
            print(os.listdir(stm32SvdPath))
            continue

        stm32SvdFilePath = os.path.join(stm32SvdPath, fileName)
        stm32SvdFilePath = pathWithForwardSlashes(stm32SvdFilePath)

        if pathExists(stm32SvdFilePath):
            break
        else:
            print("\tSVD File '" + fileName + "' not found")
            continue

    return fileName


def getBuildElfFilePath(buildDirPath, projectName):
    '''
    Returns .elf file path.
    '''
    elfFile = projectName + ".elf"
    buildFileName = os.path.join(buildDirPath, elfFile)
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


def findFileInFolderTree(searchPath, fileName):
    '''
    Find a file in a folder or subfolders, and return absolute path to the file.
    Returns None if unsuccessful.
    '''

    for root, dirs, files in os.walk(searchPath, topdown=False):
        if fileName in files:
            filePath = os.path.join(root, fileName)
            filePath = pathWithForwardSlashes(filePath)
            return filePath

    return None


def findExecutablePath(extension, raiseException=False):
    '''
    Find default associated path of a given file extension, for example 'pdf'.
    '''
    arguments = "for /f \"delims== tokens=2\" %a in (\'assoc "
    arguments += "." + extension
    arguments += "\') do @ftype %a"

    errorMsg = "Unable to get associated program for ." + extension + "."
    try:
        proc = subprocess.run(arguments, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        if proc.returncode == 0:
            returnString = str(proc.stdout)
            path = returnString.split('=')[1]
            path = path.split('\"')[0]
            path = path.strip()
            path = os.path.normpath(path)
            if os.path.exists(path):
                return path
        else:
            print(errorMsg)

    except Exception as err:
        errorMsg += "Exception:\n" + str(err)

    if raiseException:
        raise Exception(errorMsg)
    else:
        return None


########################################################################################################################
if __name__ == "__main__":
    print("Workspace generation script version: " + __version__)
    verifyFolderStructure()
    print("This workspace name:", getWorkspaceName())
    printWorkspacePaths()
