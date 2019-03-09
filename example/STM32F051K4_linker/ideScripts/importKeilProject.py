'''
This file gets data from Keil project and creates:
    - base Makefile which can be used with VS Code STM32 IDE ideScripts
    - VS Code workspace
'''
import copy
import json
import os
import shutil
import subprocess
import sys
from xml.dom import minidom

import templateStrings as tmpStr
import updateMakefile as mkf
import utilities as utils
from updateMakefile import MakefileStrings as mkfStr

__version__ = '1.0'


class Paths():
    def __init__(self):
        self.rootFolder = None  # path where ideScripts folder is placed

        self.cubeMxExe = None  # path to STM32CubeMX executable
        self.tmpCubeMxFolder = None  # path to temporary folder, there CubeMx performs its magic
        self.tmpCubeMxScript = None  # path to temporary script file for CubeMx
        self.tmpMakefile = None  # tempory Makefile that is later modified and copied to ideScripts root folder
        self.outputMakefile = None  # final clean Makefile that is later used by ideScripts

        self.keilProjectFolder = None  # path to Keil project file directory
        self.keilProject = None  # path to Keil project file


class KeilProjectData:
    def __init__(self):
        self.projName = None
        self.cpuName = None
        self.stmExactCpuName = None
        self.svdFile = None

        self.cDefines = []
        self.asmDefines = []

        self.cIncludes = []  # relative paths
        self.asmIncludes = []

        self.allSources = []
        self.cSources = []
        self.asmSources = []

        self.cCompilerSettings = []
        self.asmCompilerSettings = []
        self.linkerSettings = []


def getCubeMxExePath():
    '''
    Get absolute path to STM32CubeMX.exe either by windows default associated program or user input.
    '''
    cubeMxPath = utils.findExecutablePath('ioc', raiseException=False)
    if cubeMxPath is not None:
        if os.path.exists(cubeMxPath):
            cubeMxPath = utils.pathWithForwardSlashes(cubeMxPath)
            print("STM32CubeMX.exe path automatically updated.")
            return cubeMxPath
    else:
        while cubeMxPath is None:
            cubeMxPath = utils.getUserPath('STM32CubeMX.exe')
            if os.path.exists(cubeMxPath):
                cubeMxPath = utils.pathWithForwardSlashes(cubeMxPath)
                return cubeMxPath
            else:
                cubeMxPath = None


def getKeilProjectPath(paths: Paths):
    '''
    Try to find Keil *.uvprojx file. If found, this file is used as project file.
    If not found, throw error.
    If multiple files found, user is asked to enter specific file path.

    Return files absolute paths: *.uvprojx
    '''
    KEIL_PROJECT_FILE_EXTENSION = '.uvprojx'

    # Get the list of all files in directory tree at given path
    allFiles = utils.getAllFilesInFolderTree(paths.rootFolder)
    keilProjectFiles = []
    for theFile in allFiles:
        if theFile.find(KEIL_PROJECT_FILE_EXTENSION) != -1:
            keilProjectFiles.append(theFile)

    if len(keilProjectFiles) == 0:
        errorMsg = "Unable to find any Keil project files ending with " + KEIL_PROJECT_FILE_EXTENSION + ". "
        errorMsg += "Is folder structure correct?\n\t"
        errorMsg += "Searched files in folder tree: " + paths.rootFolder
        raise Exception(errorMsg)

    elif len(keilProjectFiles) == 1:
        # only one keil project file available, take this one
        print("Keil project file found:", keilProjectFiles[0])
        return keilProjectFiles[0]

    else:
        print("More than one Keil project files available. Select the right one.")
        keilProjectPath = None
        while keilProjectPath is None:
            keilProjectPath = utils.getUserPath('Keil project (.uvprojx)')
            if os.path.exists(keilProjectPath):
                break
            else:
                keilProjectPath = None

        print("Keil project path updated.")
        return keilProjectPath


def getKeilProjectData(paths: Paths) -> KeilProjectData:
    '''
    Read Keil project file and return filled KeilProjectData class.

    Some blocks are placed in try...except statements - error is thrown if xml field does not contain any items.
    '''
    projData = KeilProjectData()

    _, fileName = os.path.split(paths.keilProject)
    projData.projName, _ = os.path.splitext(fileName)

    projFileData = minidom.parse(paths.keilProject)
    projData.cpuName = projFileData.getElementsByTagName('Device')[0].firstChild.data

    svdFile = projFileData.getElementsByTagName('SFDFile')[0].firstChild.data
    _, projData.svdFile = os.path.split(svdFile)

    # c stuff
    _cads = projFileData.getElementsByTagName('Cads')[0]
    try:  # c defines
        cDefines = _cads.getElementsByTagName('Define')[0].firstChild.data
        projData.cDefines = utils.stringToList(cDefines, ',')
    except Exception as err:
        print("WARNING: unable to get C Defines: error or no items")
    try:  # c include folders
        cIncludes = _cads.getElementsByTagName('IncludePath')[0].firstChild.data
        cIncludesList = utils.stringToList(cIncludes, ';')
        projData.cIncludes = _fixRelativePaths(paths, cIncludesList)
    except Exception as err:
        print("WARNING: unable to get C Includes (folders): error or no items")
    try:  # c miscelaneous controls
        cMiscControls = _cads.getElementsByTagName('MiscControls')[0].firstChild.data
        projData.cCompilerSettings = utils.stringToList(cMiscControls, ',')
    except Exception as err:
        print("WARNING: unable to get C Miscelaneous settings: error or no items")

    # asm stuff
    _aads = projFileData.getElementsByTagName('Aads')[0]
    try:  # asm defines
        asmDefines = _aads.getElementsByTagName('Define')[0].firstChild.data
        projData.asmDefines = utils.stringToList(asmDefines, ',')
    except Exception as err:
        print("WARNING: unable to get Asm Defines: error or no items")
    try:  # asm include folders
        asmIncludes = _aads.getElementsByTagName('IncludePath')[0].firstChild.data
        asmIncludes = utils.stringToList(asmIncludes, ';')
        projData.asmIncludes = _fixRelativePaths(paths, asmIncludes)
    except Exception as err:
        print("WARNING: unable to get Asm Includes (folders): error or no items")
    try:  # asm miscelaneous controls
        asmMiscControls = _aads.getElementsByTagName('MiscControls')[0].firstChild.data
        projData.asmCompilerSettings = utils.stringToList(asmMiscControls, ',')
    except Exception as err:
        print("WARNING: unable to get Asm Miscelaneous settings: error or no items")

    # get linker misc controls
    _lads = projFileData.getElementsByTagName('Cads')[0]
    try:  # asm miscelaneous controls
        linkerMiscControls = _lads.getElementsByTagName('MiscControls')[0].firstChild.data
        projData.linkerSettings = utils.stringToList(linkerMiscControls, ',')
    except Exception as err:
        print("WARNING: unable to get Linker Miscelaneous settings: error or no items")

    # get all source files. Add only '.c' and '.s' files. Throw error on exception, this data is mandatory.
    files = projFileData.getElementsByTagName('FilePath')
    cSourceFiles = []
    asmSourceFiles = []
    for fileData in files:
        filePathList = _fixRelativePaths(paths, [fileData.firstChild.data])
        if len(filePathList) == 1:
            filePath = filePathList[0]
            projData.allSources.append(filePath)

            _, extension = os.path.splitext(filePath)
            if extension == '.c':
                cSourceFiles.append(filePath)
            elif extension == '.s':
                asmSourceFiles.append(filePath)
            else:
                msg = "WARNING: this file is not '.c' or '.s'. Not added to project (user must handle this manually).\n"
                msg += "\t" + filePath
                print(msg)
        else:
            # missing file reported in _fixRelativePaths
            msg = "WARNING: seems like none or more than one file is specified. This is not a valid Keil project syntax: "
            msg += str(filePathList)
            print(msg)

    projData.cSources = cSourceFiles
    print("\nC source files added:\n\t" + '\n\t'.join(cSourceFiles))
    projData.asmSources = asmSourceFiles
    print("\nAsm source files added:\n\t" + '\n\t'.join(asmSourceFiles) + '\n')

    return projData


def _fixRelativePaths(paths: Paths, relativePaths: list):
    '''
    Correct relative paths according to the folder structure as it is expected.
    Relative paths in Keil project file are relative to the keil file path,
    while we need paths relative to root folder where 'ideScripts' is.

    Return list of a VALID relative paths paths.
    '''
    keilProjectAbsPath = os.path.normpath(os.path.join(paths.rootFolder, paths.keilProject))

    allPaths = []
    for relativePath in relativePaths:
        if os.path.isabs(relativePath):
            relativePath = os.path.normpath(relativePath)
            relativePath = utils.pathWithForwardSlashes(relativePath)
            allPaths.append(relativePath)
            continue

        absolutePath = os.path.normpath(os.path.join(paths.keilProjectFolder, relativePath))
        if os.path.exists(absolutePath):
            # path is valid, build correct relative path
            try:
                newRelativePath = os.path.relpath(absolutePath, paths.rootFolder)
                newRelativePath = utils.pathWithForwardSlashes(newRelativePath)
                allPaths.append(newRelativePath)
            except:
                absolutePath = utils.pathWithForwardSlashes(absolutePath)
                allPaths.append(absolutePath)
        else:
            print("WARNING: unable to find file/folder:", absolutePath)
            print("\tBuilt from relative path:", relativePath)

    return allPaths


def _getAbsolutePaths(relativePaths):
    '''
    Get list of relative paths and try to build absolute paths.
    If any path does not exist, print warning message.
    Return list of valid absolute paths.
    '''
    absolutePaths = []
    for relativePath in relativePaths:
        relativePath = relativePath.strip()
        relativePath = os.path.normpath(os.path.join(paths.keilProjectFolder, relativePath))
        if os.path.exists(relativePath):
            relativePath = utils.pathWithForwardSlashes(relativePath)
            absolutePaths.append(relativePath)
        else:
            print("WARNING: unable to find file/folder:", relativePath)

    return absolutePaths


def createMakefileTemplate(paths: Paths, keilProjData: KeilProjectData):
    '''
    Create Makefile template with CubeMX.
    '''
    # create script that CubeMX executes
    paths.tmpCubeMxFolder = os.path.join(paths.rootFolder, tmpStr.cubeMxTmpFolderName)
    paths.tmpCubeMxFolder = utils.pathWithForwardSlashes(paths.tmpCubeMxFolder)
    if not os.path.exists(paths.tmpCubeMxFolder):
        try:
            os.mkdir(paths.tmpCubeMxFolder)
        except Exception as err:
            errorMsg = "Unable to create existing temporary folder:\n" + str(err)
            print(errorMsg)

    # even if any error occured, try to create files anyway
    _createCubeMxTmpScript(paths, keilProjData)

    # run CubeMX as subprocess with this script as a parameter
    cmd = ['java', '-jar', paths.cubeMxExe, '-s', paths.tmpCubeMxScript]
    if _checkCubeMxFirmwarePackage(paths, keilProjData):
        cmd.append('-q')  # no-gui mode
        print("\tSTM32CubeMX GUI set to non-visible mode.")
    else:
        print("\tSTM32CubeMX GUI set to visible because of repository warning.")

    try:
        print("Generating template Makefile with STM32CubeMX...")
        proc = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        if proc.returncode == 0:
            print("\tSTM32CubeMX project generated.")
        else:
            errorMsg = "CubeMx returned non-zero exit code. Something went wrong:\n"
            errorMsg += str(proc.stderr) + '\n'
            errorMsg += str(proc.stdout)

            utils.printAndQuit(errorMsg)
    except Exception as err:
        errorMsg = "Exception error while creating template Makefile with STM32CubeMX:\n" + str(err)
        utils.printAndQuit(errorMsg)

    # get makefile path
    allGeneratedFiles = utils.getAllFilesInFolderTree(paths.tmpCubeMxFolder)
    for theFile in allGeneratedFiles:
        _, fileName = os.path.split(theFile)
        if fileName == 'Makefile':
            paths.tmpMakefile = theFile
            print("\tMakefile found: " + paths.tmpMakefile)

            _copyStartupFile(paths, keilProjData)
            return
    else:
        errorMsg = "Unable to find template Makefile generated by STM32CubeMX. Was project really generated?"
        utils.printAndQuit(errorMsg)


def _copyStartupFile(paths: Paths, keilProjData: KeilProjectData):
    '''
    Get '*.s' startup file in the same folder as CubeMX template Makefile file and
    copy it into the same location as current startup file is.
    '''
    # find CubeMX temporary generated startup file
    filesInMakefileDir = os.listdir(os.path.dirname(paths.tmpMakefile))
    for theFile in filesInMakefileDir:
        name, ext = os.path.splitext(theFile)
        if ext == '.s':
            startupFile = os.path.join(os.path.dirname(paths.tmpMakefile), theFile)
            newStartupFilePath = os.path.join(paths.rootFolder, theFile)
            try:
                shutil.copy(startupFile, newStartupFilePath)
                print("Default STM32CubeMX startup file copied to:", newStartupFilePath)

                relativeStartupFilePath = os.path.relpath(newStartupFilePath, paths.rootFolder)
                relativeStartupFilePath = utils.pathWithForwardSlashes(relativeStartupFilePath)
                break
            except Exception as err:
                pass
                #print("Seems like default STM32CubeMX startup file already exist:", newStartupFilePath)

    # find startup file in current keil project data and replace it with this one
    if len(keilProjData.asmSources) == 1:
        # no problem only one '*.s' file, assume this is the startup file
        originalStartupFile = keilProjData.asmSources[0]
        keilProjData.asmSources = [relativeStartupFilePath]

        msg = "Default " + originalStartupFile + " source was replaced with CubeMX one: " + relativeStartupFilePath
        print(msg)
        return

    else:
        # more than one assembler file found, try to find file with 'startup' string or throw error
        possibleStartupFiles = []
        for startupFileListIndex, asmFile in enumerate(keilProjData.asmSources):
            _, fileName = os.path.split(asmFile)
            if fileName.lower().find('startup') != -1:
                possibleStartupFiles.append((asmFile, startupFileListIndex))  # asm file, file index in list

        if len(possibleStartupFiles) == 1:
            # OK, only one file with startup string
            originalStartupFile = keilProjData.asmSources[possibleStartupFiles[0][1]]
            keilProjData.asmSources[possibleStartupFiles[0][1]] = relativeStartupFilePath

            msg = "WARNING: Multiple '*.s' files found. "
            msg += originalStartupFile + " source file was replaced with CubeMX one: " + relativeStartupFilePath
            print(msg)

        else:
            errorMsg = "Multiple '*.s' source files listed. Can't determine startup file (searched with 'startup' string)."
            errorMsg += "\n\tAsm files: " + str(keilProjData.asmSources)
            utils.printAndQuit(errorMsg)


def cleanTempMakefile(paths: Paths):
    '''
    Clean default generated Makefile data (sources, includes, names, ...).
    '''
    makefile = mkf.Makefile()

    try:
        with open(paths.tmpMakefile, 'r') as makefileHandler:
            data = makefileHandler.readlines()

        # do not change project name intentionally
        # data = makefile.searchAndCleanData(data, makefile.mkfStr.projectName)

        data = makefile.searchAndCleanData(data, makefile.mkfStr.cSources)
        data = makefile.searchAndCleanData(data, makefile.mkfStr.asmSources)

        data = makefile.searchAndCleanData(data, makefile.mkfStr.cDefines)
        data = makefile.searchAndCleanData(data, makefile.mkfStr.asmDefines)

        data = makefile.searchAndCleanData(data, makefile.mkfStr.cIncludes)
        data = makefile.searchAndCleanData(data, makefile.mkfStr.asmIncludes)

        data = makefile.searchAndCleanData(data, makefile.mkfStr.cIncludes)

        print("Makefile template prepared.")
        return data

    except Exception as err:
        errorMsg = "Exception during Makefile template preparation:\n" + str(err)
        utils.printAndQuit(errorMsg)


def createNewMakefile(paths: Paths, keilProjData: KeilProjectData, newMakefileData):
    '''
    Fill and write new makefile with data from Keil project.
    '''
    makefile = mkf.Makefile()
    try:
        # sources
        data = makefile.searchAndAppend(newMakefileData, makefile.mkfStr.cSources, keilProjData.cSources)
        data = makefile.searchAndAppend(newMakefileData, makefile.mkfStr.asmSources, keilProjData.asmSources)

        # includes
        data = makefile.searchAndAppend(newMakefileData, makefile.mkfStr.cIncludes, keilProjData.cIncludes, preappend='-I')
        data = makefile.searchAndAppend(newMakefileData, makefile.mkfStr.asmIncludes, keilProjData.asmIncludes, preappend='-I')

        # defines
        data = makefile.searchAndAppend(newMakefileData, makefile.mkfStr.cDefines, keilProjData.cDefines, preappend='-D')
        data = makefile.searchAndAppend(newMakefileData, makefile.mkfStr.asmDefines, keilProjData.asmDefines, preappend='-D')

        # compiler flags
        # TODO should import?
        # data = makefile.searchAndAppend(newMakefileData, makefile.mkfStr.cFlags, keilProjData.cCompilerSettings)
        # data = makefile.searchAndAppend(newMakefileData, makefile.mkfStr.asmFlags, keilProjData.asmCompilerSettings)
        if keilProjData.cCompilerSettings:
            print("WARNING: C compiler settings not imported (user must handle manualy):", str(keilProjData.cCompilerSettings))
        if keilProjData.asmCompilerSettings:
            print("WARNING: Asm compiler settings not imported (user must handle manualy):", str(keilProjData.asmCompilerSettings))
        if keilProjData.linkerSettings:
            print("WARNING: Linker settings not imported (user must handle manualy):", str(keilProjData.linkerSettings))

        with open(paths.outputMakefile, 'w+') as newMakefileHandler:
            newMakefileHandler.writelines(data)

        print("Makefile created in: " + paths.outputMakefile)

    except Exception as err:
        errorMsg = "Exception during creating new Makefile:\n" + str(err)
        utils.printAndQuit(errorMsg)


def _getCPUName(paths: Paths, keilProjData: KeilProjectData):
    '''
    Try to get correct CPU family name from Keil project device tag.

    STM32 CPU name, passed to CubeMX is not the same as Keil device name.
    CubeMX device firmware pack must be installed so CubeMX is able to generate template Makefile.
    '''
    cubeMxMcuFolderPath = os.path.join(os.path.dirname(paths.cubeMxExe), 'db', 'mcu')
    allFamiliesFilePath = os.path.join(cubeMxMcuFolderPath, 'families.xml')

    allFiles = os.listdir(cubeMxMcuFolderPath)
    for theFile in allFiles:
        theFilePath = os.path.join(cubeMxMcuFolderPath, theFile)
        if os.path.isfile(theFilePath):
            if theFile.find(keilProjData.cpuName) != -1:
                fileName, ext = os.path.splitext(theFile)
                return fileName

    errorMsg = "Unable to find matching STM32 CPU name for Keil project device: " + keilProjData.cpuName
    utils.printAndQuit(errorMsg)

    stm32McuData = minidom.parse(allFamiliesFilePath)

    # build possible device family name search strings. Search order is important
    allMcuData = stm32McuData.getElementsByTagName('Mcu')
    minimumSearchStringLenght = len('STM32xx')
    numOfStrippedCharacters = len(keilProjData.cpuName) - minimumSearchStringLenght
    possibleDeviceSearchString = []
    possibleDeviceSearchString.append(keilProjData.cpuName)
    for charIndexFromBack in range(-1, -numOfStrippedCharacters-1, -1):
        possibleDeviceSearchString.append(keilProjData.cpuName[:charIndexFromBack])

    # find possible mcu ref names
    allPossibleMcu = [None] * len(allMcuData)
    subFamilyMcuData = None
    for thisDeviceSearchString in possibleDeviceSearchString:
        thisSearchStringPossibleMcu = []
        for mcuData in allMcuData:
            thisMcuName = mcuData.attributes._attrs['RPN'].value
            if thisMcuName.find(thisDeviceSearchString) != -1:
                thisSearchStringPossibleMcu.append(thisMcuName)

        if thisSearchStringPossibleMcu:
            if len(thisSearchStringPossibleMcu) <= len(allPossibleMcu):
                allPossibleMcu = copy.copy(thisSearchStringPossibleMcu)
            break

    if not allPossibleMcu:
        errorMsg = "Unable to find any (even partly) matching device name:" + keilProjData.cpuName
        utils.printAndQuit(errorMsg)
    allPossibleMcu = list(set(allPossibleMcu))  # remove cuplicates

    # all possible MCUs are listed, ask user to select correct one
    if len(allPossibleMcu) == 1:
        keilProjData.stmExactCpuName = allPossibleMcu[0]
        return allPossibleMcu[0]
    else:
        msg = "\n\n??? Please select exact CPU..."
        for mcuIndex, mcu in enumerate(allPossibleMcu):
            msg += '\n\t' + str(mcuIndex) + ': ' + mcu
        limits = list(range(0, len(allPossibleMcu)))
        askMsg = "Type number (0 - " + str(len(allPossibleMcu)) + ") and press Enter:"
        print(msg + '\n' + askMsg)

        while(True):
            userAnswer = input()
            try:
                userNumber = int(userAnswer)
            except:
                print(askMsg)
                continue
            if userNumber not in limits:
                print(askMsg)
            else:
                print("--> " + allPossibleMcu[userNumber] + " selected.")
                keilProjData.stmExactCpuName = allPossibleMcu[userNumber]
                return allPossibleMcu[userNumber]


def _checkCubeMxFirmwarePackage(paths: Paths, keilProjData: KeilProjectData):
    '''
    Check if this cpu family firmware package can be found inside CubeMX local repository.
    Returns True if found, False otherwise.
    '''
    errorMsg = ''
    try:
        # get all files inside local repository
        appDataFolder = os.path.expandvars(os.environ['APPDATA'])
        stm32CubeRepositoryFolder = os.path.join(appDataFolder, '..', '..', 'STM32Cube', 'Repository')
        stm32CubeRepositoryFolder = os.path.normpath(stm32CubeRepositoryFolder)

        # get start of package name
        cpuFamilyName = keilProjData.cpuName[len('STM32'):len('STM32xx')]
        fwPackageName = 'STM32Cube_FW_' + cpuFamilyName

        # search if any folder name contains fwPackageName
        for item in os.listdir(stm32CubeRepositoryFolder):
            if os.path.isdir(os.path.join(stm32CubeRepositoryFolder, item)):
                if item.find(fwPackageName) != -1:
                    print("Seems like STM32CubeMX " + fwPackageName + "* package is installed.")
                    return True

    except Exception as err:
        errorMsg = "\nException:\n" + str(err)

    msg = "WARNING: unable to check if STM32Cube " + keilProjData.cpuName + " firmware package is installed."
    msg += errorMsg
    print(msg)
    return False


def _createCubeMxTmpScript(paths: Paths, keilProjData: KeilProjectData):
    '''
    Create tempory script for CubeMX Makefile generation.
    Raises exception on error.
    '''
    paths.tmpCubeMxScript = os.path.join(paths.tmpCubeMxFolder, tmpStr.cubeMxTmpFileName)
    paths.tmpCubeMxScript = utils.pathWithForwardSlashes(paths.tmpCubeMxScript)

    dataToWrite = "// Temporary script for generating Base Makefile with STM32CubeMX.\n"
    dataToWrite += "load " + _getCPUName(paths, keilProjData) + "\n"
    dataToWrite += "project name " + keilProjData.projName + "\n"
    dataToWrite += "project toolchain Makefile\n"
    dataToWrite += "project path \"" + paths.tmpCubeMxFolder + "\"\n"
    dataToWrite += "project generate\n"
    dataToWrite += "exit"

    with open(paths.tmpCubeMxScript, 'w+') as scriptHandler:
        scriptHandler.write(dataToWrite)

    print("Temporary STM32CubeMX script created.")


def deleteTemporaryFiles(paths: Paths):
    '''
    Delete (clean) CubeMX temporary files.
    '''
    try:
        shutil.rmtree(paths.tmpCubeMxFolder)
        print("STM32CubeMX temporary files deleted.")
    except Exception as err:
        errorMsg = "Exception while deleting STM32CubeMX temporary files:\n" + str(err)
        raise Exception(err)


def _separateAbsoluteAndRelativePaths(pathsListToSeparate: list):
    '''
    This function splits pathsListToSeparate to relative and absolute paths.
    Returns two lists: absolutePaths, relativePaths
    '''
    absPaths = []
    relPaths = []
    for path in pathsListToSeparate:
        if os.path.isabs(path):
            absPaths.append(path)
        else:
            relPaths.append(path)

    return absPaths, relPaths


def createVSCodeWorkspace(paths: Paths, keilProjData: KeilProjectData):
    '''
    Create VS Code workspace so user can easily run 'update.py' from ideScripts.
    '''
    # add non-relative source folders to VS Code workspace folders.
    allPaths = []
    # TODO are c and asm includes folders needed in Code workspace?
    # allPaths.extend(keilProjData.cIncludes)
    # allPaths.extend(keilProjData.asmIncludes)
    cSourcesFolders = [os.path.dirname(source) for source in keilProjData.cSources]
    allPaths.extend(list(set(cSourcesFolders)))
    asmSourcesFolders = [os.path.dirname(source) for source in keilProjData.asmSources]
    allPaths.extend(list(set(asmSourcesFolders)))
    absPaths, relPaths = _separateAbsoluteAndRelativePaths(allPaths)

    dataToWrite = """
    {
        "folders": [
        {
            "path": "."
        }
    """
    for absPath in absPaths:
        addToFoldersStr = ",{ \"path\": \"" + absPath + "\"}"
        dataToWrite += addToFoldersStr
    dataToWrite += "]"
    dataToWrite += ",\"settings\": { }"
    dataToWrite += "}"
    data = json.loads(dataToWrite)
    data = json.dumps(data, indent=4, sort_keys=False)

    codeWorkspaceFileName = keilProjData.projName + '.code-workspace'
    codeWorkspaceFilePath = os.path.join(paths.rootFolder, codeWorkspaceFileName)
    with open(codeWorkspaceFilePath, 'w+') as fileHandler:
        fileHandler.write(data)

    print("VS Code workspace file created:", codeWorkspaceFilePath)


if __name__ == "__main__":
    paths = Paths()
    thisFileAbsPath = os.path.abspath(sys.argv[0])
    paths.rootFolder = os.path.dirname(os.path.dirname(thisFileAbsPath))
    paths.rootFolder = utils.pathWithForwardSlashes(paths.rootFolder)

    paths.cubeMxExe = getCubeMxExePath()
    paths.keilProject = getKeilProjectPath(paths)
    paths.keilProjectFolder = utils.pathWithForwardSlashes(os.path.dirname(paths.keilProject))
    paths.outputMakefile = utils.pathWithForwardSlashes(os.path.join(paths.rootFolder, 'Makefile'))

    keilProjData = getKeilProjectData(paths)

    createMakefileTemplate(paths, keilProjData)
    cleanMakefileData = cleanTempMakefile(paths)
    createNewMakefile(paths, keilProjData, cleanMakefileData)
    deleteTemporaryFiles(paths)

    createVSCodeWorkspace(paths, keilProjData)
