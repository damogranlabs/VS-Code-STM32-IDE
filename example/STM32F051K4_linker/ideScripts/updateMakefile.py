'''
Generate (replace existing) Makefile file in workspace folder wtih data from
original Makefile and 'c_cpp_properties.json'.
'''

import os
import datetime
from subprocess import Popen, PIPE

import utilities as utils
import templateStrings as tmpStr

import updatePaths as pth
import updateWorkspaceSources as wks
import updateBuildData as build

__version__ = utils.__version__


class MakefileStrings():
    projectName = 'TARGET'
    buildDir = 'BUILD_DIR'

    cSources = 'C_SOURCES'
    asmSources = 'ASM_SOURCES'
    ldSources = 'LIBS'
    cDefines = 'C_DEFS'
    asmDefines = 'AS_DEFS'
    cIncludes = 'C_INCLUDES'
    asmIncludes = 'AS_INCLUDES'
    ldIncludes = 'LIBDIR'
    cFlags = 'CFLAGS'
    asmFlags = 'ASFLAGS'
    ldFlags = 'LDFLAGS'


class Makefile():
    def __init__(self):
        self.mkfStr = MakefileStrings()
        self.cPStr = wks.CPropertiesStrings()

    def checkMakefileFile(self):
        '''
        Check if 'Makefile' file exists. If it doesn't, report as error.
        '''
        if not utils.pathExists(utils.makefilePath):
            errorMsg = "Makefile does not exist! Did CubeMX generated Makefile?\n"
            errorMsg += "File name must be 'Makefile'."
            utils.printAndQuit(errorMsg)

    def restoreOriginalMakefile(self):
        '''
        Check wether current 'Makefile' has print capabilities. If it has, this means it was already altered by this script.
        If it was, replace it with backup copy: 'Makefile.backup'.
        If it does not have prin capabilities, is is assumed 'Makefile' was regenerated with CubeMX tool - print function is added and backup file is overwritten with this new 'Makefile'.
        At the end, add 'print-variable' capabilities
        '''
        if utils.pathExists(utils.makefileBackupPath):
            # Makefile.backup exists, check if it is original (no print capabilities)
            if self.hasPrintCapabilities(pathToMakefile=utils.makefileBackupPath):
                errorMsg = "Makefile.backup exist, but looks like it was already modified!\n"
                errorMsg += "Did you manually delete, replace or modify any of Makefiles? "
                errorMsg += "Delete all Makefiles and regenerate with CubeMX."
                utils.printAndQuit(errorMsg)

            else:  # OK - seems like original Makefile, replace Makefile with Makefile.backup, add print capabilities
                utils.copyAndRename(utils.makefileBackupPath, utils.makefilePath)

        else:  # Makefile.backup does not exist, check if current Makefile has print capabilities.
            if self.hasPrintCapabilities(pathToMakefile=utils.makefilePath):
                errorMsg = "Looks like Makefile was already modified! Makefile.backup does not exist.\n"
                errorMsg += "Did you manually delete, replace or modify any of Makefiles? "
                errorMsg += "Delete all Makefiles and regenerate with CubeMX."
                utils.printAndQuit(errorMsg)

            else:  # Makefile looks like an original one. Create a backup copy and add print capabilities
                utils.copyAndRename(utils.makefilePath, utils.makefileBackupPath)

        self.addMakefileCustomFunctions(pathToMakefile=utils.makefilePath)

    def getMakefileData(self, makeExePath, gccExePath):
        '''
        Get Makefile data.
        Returns data in dictionary.
        '''
        dataDictionaryList = {}

        # project name
        projectName = self.getMakefileVariable(makeExePath, gccExePath, self.mkfStr.projectName)[0]
        dataDictionaryList[self.mkfStr.projectName] = projectName

        # dir name
        buildDirName = self.getMakefileVariable(makeExePath, gccExePath, self.mkfStr.buildDir)[0]
        dataDictionaryList[self.mkfStr.buildDir] = buildDirName

        # source files
        cSourcesList = self.getMakefileVariable(makeExePath, gccExePath, self.mkfStr.cSources)
        dataDictionaryList[self.mkfStr.cSources] = cSourcesList

        asmSourcesList = self.getMakefileVariable(makeExePath, gccExePath, self.mkfStr.asmSources)
        dataDictionaryList[self.mkfStr.asmSources] = asmSourcesList

        ldSourcesList = self.getMakefileVariable(makeExePath, gccExePath, self.mkfStr.ldSources)
        # ldSourcesList = utils.stripStartOfString(ldSourcesList, '-l') # more readable without stripping
        dataDictionaryList[self.mkfStr.ldSources] = ldSourcesList

        # defines
        asmDefinesList = self.getMakefileVariable(makeExePath, gccExePath, self.mkfStr.asmDefines)
        asmDefinesList = utils.stripStartOfString(asmDefinesList, '-D')
        dataDictionaryList[self.mkfStr.asmDefines] = asmDefinesList

        cDefinesList = self.getMakefileVariable(makeExePath, gccExePath, self.mkfStr.cDefines)
        cDefinesList = utils.stripStartOfString(cDefinesList, '-D')
        dataDictionaryList[self.mkfStr.cDefines] = cDefinesList

        # source & include directories
        asmIncludesList = self.getMakefileVariable(makeExePath, gccExePath, self.mkfStr.asmIncludes)
        asmIncludesList = utils.stripStartOfString(asmIncludesList, '-I')
        dataDictionaryList[self.mkfStr.asmIncludes] = asmIncludesList

        cIncludesList = self.getMakefileVariable(makeExePath, gccExePath, self.mkfStr.cIncludes)
        cIncludesList = utils.stripStartOfString(cIncludesList, '-I')
        dataDictionaryList[self.mkfStr.cIncludes] = cIncludesList

        ldIncludesList = self.getMakefileVariable(makeExePath, gccExePath, self.mkfStr.ldIncludes)
        ldIncludesList = utils.stripStartOfString(ldIncludesList, '-L')
        dataDictionaryList[self.mkfStr.ldIncludes] = ldIncludesList

        # flags
        cFlags = self.getMakefileVariable(makeExePath, gccExePath, self.mkfStr.cFlags)
        dataDictionaryList[self.mkfStr.cFlags] = cFlags

        asmFlags = self.getMakefileVariable(makeExePath, gccExePath, self.mkfStr.asmFlags)
        dataDictionaryList[self.mkfStr.asmFlags] = asmFlags

        ldFlags = self.getMakefileVariable(makeExePath, gccExePath, self.mkfStr.ldFlags)
        dataDictionaryList[self.mkfStr.ldFlags] = ldFlags

        return dataDictionaryList

    def parseMakefileData(self, data, startString):
        '''
        Fetch and unparse data from existing Makefile (generated by CubeMX) starting with 'startString'.
        '''
        endOfLineChars = "\\"
        startString = startString + ' = '
        NOT_FOUND = -1

        items = []
        # find start and end of defines and
        for lineIndex, line in enumerate(data):
            line = line.rstrip('\n')  # strip string of '\n'

            startCharacter = line.find(startString)
            if startCharacter != NOT_FOUND:  # search for start string

                # check if one-liner
                if line.find(endOfLineChars) == NOT_FOUND:
                    line = line[len(startString):]
                    if len(line) != 0:  # check for 'SOMETHING = ' (empty line after '=')
                        # not an empty line after '='
                        items.append(line)  # strip string of start and and characters
                    return items

                else:  # multiline item in Makefile
                    for line2 in data[lineIndex+1:]:
                        line2 = line2.rstrip('\n')
                        if line2.find(endOfLineChars) != NOT_FOUND:
                            line2 = line2.rstrip('\\')  # strip of '\'
                            line2 = line2.rstrip(' ')   # strip of ' '
                            items.append(line2)
                        else:
                            line2 = line2.rstrip('\\')  # strip of '\'
                            line2 = line2.rstrip(' ')   # strip of ' '
                            items.append(line2)
                            return items

        errorMsg = "String item '" + str(startString) + "' not found!\n"
        errorMsg += "Invalid/changed Makefile or this script is outdated (change in CubeMX Makefile syntax?)."
        utils.printAndQuit(errorMsg)

    def createNewMakefile(self):
        '''
        Merge existing Makefile data and user fields from existing 'c_cpp_properties.json.'
        '''
        print("\nCreating new Makefile... ")

        cP = wks.CProperties()
        cPropertiesData = cP.getCPropertiesData()

        with open(utils.makefilePath, 'r') as makefile:
            data = makefile.readlines()

        # sources
        cSources = cP.getCPropertiesKeyData(cPropertiesData, self.cPStr.user_cSources)
        data = self.searchAndAppend(data, self.mkfStr.cSources, cSources)

        asmSources = cP.getCPropertiesKeyData(cPropertiesData, self.cPStr.user_asmSources)
        data = self.searchAndAppend(data, self.mkfStr.asmSources, asmSources)

        ldSources = cP.getCPropertiesKeyData(cPropertiesData, self.cPStr.user_ldSources)
        data = self.searchAndAppend(data, self.mkfStr.ldSources, ldSources, preappend='-l:')

        # includes
        cIncludes = cP.getCPropertiesKeyData(cPropertiesData, self.cPStr.user_cIncludes)
        data = self.searchAndAppend(data, self.mkfStr.cIncludes, cIncludes, preappend='-I')

        asmIncludes = cP.getCPropertiesKeyData(cPropertiesData, self.cPStr.user_asmIncludes)
        data = self.searchAndAppend(data, self.mkfStr.asmIncludes, asmIncludes, preappend='-I')

        ldIncludes = cP.getCPropertiesKeyData(cPropertiesData, self.cPStr.user_ldIncludes)
        data = self.searchAndAppend(data, self.mkfStr.ldIncludes, ldIncludes, preappend='-L')

        # defines
        cDefines = cP.getCPropertiesKeyData(cPropertiesData, self.cPStr.user_cDefines)
        data = self.searchAndAppend(data, self.mkfStr.cDefines, cDefines, preappend='-D')

        asmDefines = cP.getCPropertiesKeyData(cPropertiesData, self.cPStr.user_asmDefines)
        data = self.searchAndAppend(data, self.mkfStr.asmDefines, asmDefines, preappend='-D')

        # compiler flags
        cFlags = cP.getCPropertiesKeyData(cPropertiesData, self.cPStr.user_cFlags)
        data = self.searchAndAppend(data, self.mkfStr.cFlags, cFlags)

        asmFlags = cP.getCPropertiesKeyData(cPropertiesData, self.cPStr.user_asmFlags)
        data = self.searchAndAppend(data, self.mkfStr.asmFlags, asmFlags)

        ldFlags = cP.getCPropertiesKeyData(cPropertiesData, self.cPStr.user_ldFlags)
        data = self.searchAndAppend(data, self.mkfStr.ldFlags, ldFlags)

        data = self.replaceMakefileHeader(data)

        try:
            with open(utils.makefilePath, 'w') as makefile:
                for line in data:
                    makefile.write(line)
            print("New Makefile data succesfully written.")

        except Exception as err:
            errorMsg = "Exception error writing new data to Makefile:\n"
            errorMsg += str(err)
            utils.printAndQuit(errorMsg)

    def searchAndAppend(self, data, searchString, appendData, preappend=None):
        '''
        Search for string in 'data' list and append 'appendData' according to Makefile syntax.
        if 'preappend' is defined, each item of 'appendData' is preappended with this string.
        '''
        NOT_FOUND = -1

        if preappend is not None:
            appendData = utils.preappendString(appendData, preappend)

        for lineIndex, line in enumerate(data):
            line = line.rstrip('\n')  # strip string of '\n'

            if line.find(searchString) != NOT_FOUND:  # search for start string
                if line[0] == '#':  # this is a comment
                    continue

                if line.find("\\") == NOT_FOUND:
                    # one-liner, no '\' sign at the end of the line
                    if type(appendData) is list:  # if this is list
                        if appendData:  # and it is not empty
                            if len(appendData) == 1:  # this list has only one item, add it without '\'
                                if line[-1] != ' ':  # avoid double spaces
                                    line += " "
                                data[lineIndex] = line + appendData[0] + "\n"

                            else:
                                # this is list with multiple items, '\' will be needed
                                line += " \\\n"
                                data[lineIndex] = line

                                for itemIndex, item in enumerate(appendData):
                                    stringToInsert = item
                                    if item != appendData[-1]:  # for last item do not append "\"
                                        stringToInsert += "\\"
                                    stringToInsert += "\n"  # new line must always be added
                                    data.insert(lineIndex + itemIndex + 1, stringToInsert)

                            return data

                    else:  # appendData is string (not list)
                        if appendData != '':
                            if data[lineIndex][-1] != ' ':  # avoid double spaces
                                data[lineIndex] += " "
                            data[lineIndex] += appendData + "\n"

                    return data
                else:  # already a multi-liner, append at the beginning, but in new line
                    if type(appendData) is list:
                        for itemIndex, item in enumerate(appendData):
                            stringToInsert = item + " \\\n"
                            data.insert(lineIndex + itemIndex + 1, stringToInsert)
                    else:  # appendData is string (not list)
                        data[lineIndex] += item + " \\\n"

                    return data

        errorMsg = "String item " + str(searchString) + " not found!"
        utils.printAndQuit(errorMsg)

    def searchAndCleanData(self, data, searchString):
        '''
        Search for string in 'data' list and clear all belonging data according to Makefile syntax.
        '''
        NOT_FOUND = -1

        for lineIndex, line in enumerate(data):
            line = line.rstrip('\n')  # strip string of '\n'

            if line.find(searchString) != NOT_FOUND:  # search for start string
                if line[0] == '#':  # this is a comment
                    continue
                if line.find("\\") == NOT_FOUND:
                    # keep searchString and equaliy sign, append '\n'
                    equalitySignCharIndex = line.find('=')
                    data[lineIndex] = data[lineIndex][: equalitySignCharIndex+1] + ' \n'
                    return data

                else:  # multi-liner, get last line index and delete this lines
                    lastLineIndex = lineIndex + 1
                    while data[lastLineIndex].rstrip('\n') != '':
                        lastLineIndex = lastLineIndex + 1
                        if lastLineIndex >= len(data):
                            errorMsg = "Unable to find end of multi-line Makefile item (" + searchString + "). "
                            errorMsg += "Was Makefile manually modified?"
                            utils.printAndQuit(errorMsg)
                    # delete this lines
                    delLineIndex = lineIndex + 1
                    constLineIndex = lineIndex + 1  # this line will be deleted until an empty line is present
                    while delLineIndex != lastLineIndex:
                        del data[constLineIndex]
                        delLineIndex = delLineIndex + 1
                    # keep searchString and equaliy sign, append '\n'
                    equalitySignCharIndex = line.find('=')
                    data[lineIndex] = line[: equalitySignCharIndex+1] + ' \n'
                    return data

        errorMsg = "String item " + str(searchString) + " not found!"
        utils.printAndQuit(errorMsg)

    ########################################################################################################################

    def getMakefileVariable(self, makeExePath, gccExePath, variableName):
        '''
        Open subproces, call make print-variableName and catch stout.
        Syntax with absolute paths:
            "path to make.exe with spaces" GCC_PATH="path to gccsomething.exe with spaces" print-VARIABLE

        With
        '''
        # change directory to the same folder as Makefile
        cwd = os.getcwd()
        os.chdir(utils.workspacePath)

        printStatement = "print-" + str(variableName)
        gccExeFolderPath = os.path.dirname(gccExePath)
        #gccPath = "\"\"GCC_PATH=" + gccExeFolderPath
        gccPath = "GCC_PATH=\"" + gccExeFolderPath + "\""
        arguments = [makeExePath, gccPath, printStatement]

        proc = Popen(arguments, stdout=PIPE)
        returnString = str((proc.communicate()[0]).decode('UTF-8'))
        returnString = returnString.rstrip('\n')
        returnString = returnString.rstrip('\r')

        os.chdir(cwd)  # change directory back to where it was

        if returnString.find("make: *** No rule to make target") != -1:
            errorMsg = "Can't retrieve " + variableName + " value from makefile."
            utils.printAndQuit(errorMsg)

        # remove "VARIABLE=" string start. This string must be present, or 'Echo is off.' is displayed for empy variables.
        if returnString.find(tmpStr.printMakefileDefaultString) != -1:
            returnString = returnString.replace(tmpStr.printMakefileDefaultString, '')

        returnStringList = returnString.split(' ')  # split string to list and remove empty items
        returnStringListCopy = []
        for itemIndex, item in enumerate(returnStringList):
            # handle strings where print statement (print-variableName) is present, like '-MF"print-VARIABLE"'
            quotedPrintStatement = "\"" + printStatement + "\""
            if item.find(quotedPrintStatement) != -1:
                item = item.replace(quotedPrintStatement, '')
            elif item.find(printStatement) != -1:
                item = item.replace(printStatement, '')

            # handle empty items
            if item not in ['', ' ']:
                returnStringListCopy.append(item)

        return returnStringListCopy

    def replaceMakefileHeader(self, data):
        '''
        Change header, to distinguish between original and new Makefile.
        '''
        # first find last line before '# target', that must not be changed
        lastLine = None
        for lineIndex, line in enumerate(data):
            twoLinesAhead = data[lineIndex + 2]  # first line is ######... and second should be '# target'
            twoLinesAhead = twoLinesAhead.rstrip('\n')  # strip string of '\n'
            if twoLinesAhead.find("# target") != -1:  # search for start string
                lastLine = lineIndex
                break
        if lastLine is None:
            print('')  # previously there was no new line
            errorMsg = "Makefile '# target' string missing.\n"
            errorMsg += "Invalid/changed Makefile or this script is outdated (change in CubeMX Makefile syntax?)."
            utils.printAndQuit(errorMsg)

        else:  # '# target' line found
            # delete current header
            lineIndex = 0
            while lineIndex != lastLine:
                lineIndex = lineIndex + 1
                del data[0]

            # add new header
            for line in reversed(tmpStr.makefileHeader.splitlines()):
                if line.find(tmpStr.versionString) != -1:
                    line = line.replace('***', __version__)
                if line.find(tmpStr.lastRunString) != -1:
                    timestamp = datetime.datetime.now()
                    line = line.replace('***', str(timestamp))

                line = line + "\n"
                data.insert(0, line)

        return data

    def hasPrintCapabilities(self, pathToMakefile):
        '''
        Check wether current Makefile has 'print-variable' function.
        Returns True or False.
        '''
        with open(pathToMakefile, 'r+') as makefile:
            data = makefile.readlines()

            # Try to find existing print function
            for line in reversed(data):
                line = line.rstrip('\n')  # strip string of '\n'
                if line.find(tmpStr.printMakefileVariableFunction) != -1:
                    # existing print function found!
                    return True

        return False

    def addMakefileCustomFunctions(self, pathToMakefile):
        '''
        Add all functions to makefile:
            - print-variable
            - clean-build-dir

        This function is called only if current Makefile does not have 'print-variable' capabilities.
        '''
        with open(pathToMakefile, 'r+') as makefile:
            makefileDataLines = makefile.readlines()

            makefileDataLines = self.addPrintVariableFunction(makefileDataLines)

            makefile.seek(0)
            makefile.truncate()
            for line in makefileDataLines:
                makefile.write(line)

    def addPrintVariableFunction(self, makefileDataLines):
        '''
        Add print Makefile variable capabilities to Makefile
        '''
        makefileDataLines.append("\n\n")
        for line in tmpStr.printMakefileVariable.splitlines():
            line = line + "\n"
            makefileDataLines.append(line)

        print("Makefile 'print-variable' function OK.")
        return makefileDataLines


########################################################################################################################
if __name__ == "__main__":
    utils.verifyFolderStructure()

    paths = pth.UpdatePaths()
    bData = build.BuildData()
    cP = wks.CProperties()
    makefile = Makefile()

    # Makefile must exist
    makefile.checkMakefileFile()  # no point in continuing if Makefile does not exist

    buildData = bData.prepareBuildData()

    makeExePath = buildData[bData.bStr.buildToolsPath]
    gccExePath = buildData[bData.bStr.gccExePath]
    makefileData = makefile.getMakefileData(makeExePath, gccExePath)

    makefile.restoreOriginalMakefile()

    # build data (update tools paths if neccessary)
    buildData = bData.prepareBuildData()

    makeExePath = buildData[bData.bStr.buildToolsPath]
    gccExePath = buildData[bData.bStr.gccExePath]
    makefileData = makefile.getMakefileData(makeExePath, gccExePath)
    buildData = bData.addMakefileDataToBuildDataFile(buildData, makefileData)

    bData.createUserToolsFile(buildData)

    # get data from 'c_cpp_properties.json' and create new Makefile
    cP.checkCPropertiesFile()
    makefile.createNewMakefile()  # reads 'c_cpp_properties.json' internally
