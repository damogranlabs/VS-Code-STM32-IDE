'''
Update/generate 'tasks.json' file in .vscode subfolder.

'tasks.json' fields description:
https://code.visualstudio.com/docs/editor/tasks
'''

import os
import json

import utilities as utils
import templateStrings as tmpStr

import updatePaths as pth
import updateWorkspaceSources as wks
import updateMakefile as mkf
import updateBuildData as build

__version__ = utils.__version__


class Tasks():
    def __init__(self):
        self.cPStr = wks.CPropertiesStrings()
        self.mkfStr = mkf.MakefileStrings()
        self.bStr = build.BuildDataStrings()

    def checkTasksFile(self):
        '''
        Check if 'tasks.json' file exists. If it does, check if it is a valid JSON file.
        If it doesn't exist, create new according to template.
        '''
        if utils.fileFolderExists(utils.tasksPath):
            # file exists, check if it loads OK
            try:
                with open(utils.tasksPath, 'r') as tasksFile:
                    json.load(tasksFile)

                    print("Existing 'tasks.json' file found.")
                    return

            except Exception as err:
                errorMsg = "Invalid 'tasks.json' file. Creating backup and new one.\n"
                errorMsg += "Possible cause: invalid json format or comments (not supported by this scripts). Error:\n"
                errorMsg += str(err)
                print(errorMsg)

                utils.copyAndRename(utils.tasksPath, utils.tasksBackupPath)

                self.createTasksFile()

        else:  # 'tasks.json' file does not exist jet, create it according to template string
            self.createTasksFile()

    def createTasksFile(self):
        '''
        Create fresh 'tasks.json' file.
        '''
        try:
            with open(utils.tasksPath, 'w') as tasksFile:
                data = json.loads(tmpStr.tasksFileTemplate)
                dataToWrite = json.dumps(data, indent=4, sort_keys=False)

                tasksFile.seek(0)
                tasksFile.truncate()
                tasksFile.write(dataToWrite)

                print("New 'tasks.json' file created.")

        except Exception as err:
            errorMsg = "Exception error creating new 'tasks.json' file:\n"
            errorMsg += str(err)
            utils.printAndQuit(errorMsg)

    def getTasksData(self):
        '''
        Get data from current 'tasks.json' file.
        File existance is previoulsy checked in 'checkTasksFile()'.
        '''
        with open(utils.tasksPath, 'r') as tasksFile:
            data = json.load(tasksFile)

            return data

    def overwriteTasksFile(self, data):
        '''
        Overwrite existing 'tasks.json' file with new data.
        '''
        try:
            with open(utils.tasksPath, 'r+') as tasksFile:
                tasksFile.seek(0)
                tasksFile.truncate()
                dataToWrite = json.dumps(data, indent=4, sort_keys=False)
                tasksFile.write(dataToWrite)

            print("'tasks.json' file updated!")

        except Exception as err:
            errorMsg = "Exception error overwriting 'tasks.json' file:\n"
            errorMsg += str(err)
            utils.printAndQuit(errorMsg)

    def addOrReplaceTask(self, data, taskData):
        '''
        Check wether tasks with this "label" already exists. If it doesn't, create new task, overwrite otherwise.
        '''
        thisTaskName = taskData["label"]

        taskExist = False
        listOfTasks = data["tasks"]
        for taskIndex, task in enumerate(listOfTasks):
            if task["label"] == thisTaskName:
                # task with this name already exist, replace it's content
                data["tasks"][taskIndex] = taskData
                taskExist = True

        if not taskExist:
            data["tasks"].append(taskData)

        return data

    def addAllTasks(self, tasksData):
        '''
        Merge and return all combined tasks data.
        '''
        # building and compiling project tasks
        tasksData = self.addBuildTask(tasksData)
        tasksData = self.addCompileTask(tasksData)
        # tasksData = self.addCleanBuildFolderTask(tasksData) # TODO is this really needed?
        tasksData = self.addDeleteBuildFolderTask(tasksData)

        # debugging and target control tasts
        tasksData = self.addDownloadAndRunTask(tasksData)
        tasksData = self.addResetAndRunTask(tasksData)
        tasksData = self.addHaltTask(tasksData)
        tasksData = self.addRunTask(tasksData)

        # other tasks
        tasksData = self.addRunCurrentPythonFileTask(tasksData)  # common "run python file" task
        tasksData = self.addUpdateTask(tasksData)   # update all files for VS Code so it can be used as IDE

        # TODO USER should add its own tasks here

        return tasksData

    ########################################################################################################################
    # User can add other common tasks here
    # TODO USER:
    #   - copy any of tasks below
    #   - edit (add, remove),  taskTemplateFields
    #   - add your new task function to addAllTasks() function
    ########################################################################################################################
    def addRunCurrentPythonFileTask(self, tasksData):
        '''
        Create/repair 'Run Python file' task, which runs current active file.
        '''
        # User edit BEGIN

        taskData = """
        {
            "label": "Run Python file",
            "type": "shell",
            "command": "python",
            "args": [
                "${file}"
            ],
            "presentation": {
                "focus": true
            },
            "problemMatcher": []
        }
        """
        jsonTaskData = json.loads(taskData)

        # User edit END
        tasksData = self.addOrReplaceTask(tasksData, jsonTaskData)
        return tasksData

    def addBuildTask(self, tasksData):
        '''
        Add build task (execute 'make' command).
        '''
        # User edit BEGIN

        taskData = """
        {
            "label": "Build project",
            "type": "shell",
            "command": "specified below",
            "args": ["specified below"],
            "problemMatcher": {
                "pattern": {
                    "regexp": "^(.*):(\\\\d+):(\\\\d+):\\\\s+(warning|error):\\\\s+(.*)$",
                    "file": 1,
                    "line": 2,
                    "column": 3,
                    "severity": 4,
                    "message": 5
                }
            },
            "presentation": {
                "focus": true
            }
        }
        """
        jsonTaskData = json.loads(taskData)

        buildData = build.BuildData().getBuildData()
        jsonTaskData["command"] = buildData[self.bStr.buildToolsPath]

        gccFolderPath = os.path.dirname(buildData[self.bStr.gccExePath])
        gccFolderPath = utils.pathWithForwardSlashes(gccFolderPath)
        jsonTaskData["args"] = ["GCC_PATH=" + gccFolderPath]   # specify compiler path to make command

        # User edit END
        tasksData = self.addOrReplaceTask(tasksData, jsonTaskData)
        return tasksData

    def addCleanBuildFolderTask(self, tasksData):
        '''
        Add clean task (execute 'make clean-build-dir' command).

        Note: Currenly disabled (also in Makefile).
        '''
        # User edit BEGIN

        taskData = """
        {
            "label": "Clean build folder",
            "type": "shell",
            "command": "specified below",
            "args": ["specified below"],
            "problemMatcher": [],
            "presentation": {
                "focus": false
            }
        }
        """
        jsonTaskData = json.loads(taskData)

        buildData = build.BuildData().getBuildData()
        jsonTaskData["command"] = buildData[self.bStr.buildToolsPath]
        jsonTaskData["args"] = [tmpStr.cleanBuildDirFunctionName]

        # User edit END
        tasksData = self.addOrReplaceTask(tasksData, jsonTaskData)
        return tasksData

    def addDeleteBuildFolderTask(self, tasksData):
        '''
        Add delte task (execute 'make clean' command).
        '''
        # User edit BEGIN
        taskData = """
        {
            "label": "Delete build folder",
            "type": "shell",
            "command": "specified below",
            "args": ["clean"],
            "problemMatcher": [],
            "presentation": {
                "focus": false
            }
        }
        """
        jsonTaskData = json.loads(taskData)

        buildData = build.BuildData().getBuildData()
        jsonTaskData["command"] = buildData[self.bStr.buildToolsPath]

        # User edit END
        tasksData = self.addOrReplaceTask(tasksData, jsonTaskData)
        return tasksData

    def addCompileTask(self, tasksData):
        '''
        Add compile current file task (execute 'make clean' command).
        '''
        # User edit BEGIN

        taskData = """
        {
            "label": "Compile current file",
            "type": "shell",
            "command": "will be replaced with GCC path below",
            "args": ["will be replaced with path from buildData.json"],
            "problemMatcher": {
                "pattern": {
                    "regexp": "^(.*):(\\\\d+):(\\\\d+):\\\\s+(warning|error):\\\\s+(.*)$",
                    "file": 1,
                    "line": 2,
                    "column": 3,
                    "severity": 4,
                    "message": 5
                }
            },
            "presentation": {
                "focus": true
            }
        }
        """
        jsonTaskData = json.loads(taskData)

        # get compiler C flags, defines, includes, ... from 'buildData.json'
        buildData = build.BuildData().getBuildData()

        # defines
        cDefines = buildData[self.bStr.cDefines]
        cDefines = utils.preappendString(cDefines, '-D')

        # includes
        cIncludes = buildData[self.bStr.cIncludes]
        cIncludes = utils.preappendString(cIncludes, '-I')

        # build directory
        buildDir = buildData[self.bStr.buildDirPath]

        # c flags
        cFlags = buildData[self.bStr.cFlags]
        for flagIndex, flag in enumerate(cFlags):
            if flag == "-MF":
                newFlagString = "-MF'" + buildDir + "/${fileBasenameNoExtension}.d'"
                cFlags[flagIndex] = newFlagString
                continue

        # output file
        outputFilePath = "'" + buildDir + "/${fileBasenameNoExtension}.o'"
        outputFile = ["-o"]
        outputFile.append(outputFilePath)

        # compile file string
        fileString = "'${relativeFile}'"
        fileString = [fileString]

        jsonTaskData["command"] = buildData[self.bStr.gccExePath]
        jsonTaskData["args"] = ["-c"]   # only compile switch
        jsonTaskData["args"].extend(cDefines)
        jsonTaskData["args"].extend(cIncludes)
        jsonTaskData["args"].extend(cFlags)
        jsonTaskData["args"].extend(fileString)
        jsonTaskData["args"].extend(outputFile)

        # User edit END
        tasksData = self.addOrReplaceTask(tasksData, jsonTaskData)
        return tasksData

    ########################################################################################################################
    # Debugging and target control tasks
    ########################################################################################################################
    def addDownloadAndRunTask(self, tasksData):
        '''
        Create/repair 'CPU: Download and run' task.
        '''
        # User edit BEGIN
        taskData = """
        {
            "label": "CPU: Download and run",
            "type": "shell",
            "command": "specified below",
            "args": ["specified below"],
            "problemMatcher": []
        }
        """
        jsonTaskData = json.loads(taskData)

        buildData = build.BuildData().getBuildData()
        jsonTaskData["command"] = buildData[self.bStr.openOCDPath]
        jsonTaskData["args"] = []
        jsonTaskData["args"].append("-f")
        jsonTaskData["args"].append(buildData[self.bStr.openOCDInterfacePath])
        jsonTaskData["args"].append("-f")
        jsonTaskData["args"].append(buildData[self.bStr.openOCDTargetPath])

        # -c program filename [verify] [reset] [exit] [offset] ([] are optional arguments)
        # Note: due problems with VS Code OpenOCD Tasks in case of workspace path containing spaces, target executable is passed
        # as relative path. Not a problem since VS Code shell is started from workspace folder.
        workspacePath = utils.workspacePath
        targetExecutablePath = buildData[self.bStr.targetExecutablePath]
        relativeTargetExecutablePath = os.path.relpath(targetExecutablePath, workspacePath)
        relativeTargetExecutablePath = utils.pathWithForwardSlashes(relativeTargetExecutablePath)
        jsonTaskData["args"].append("-c")
        programString = "program " + relativeTargetExecutablePath + " verify reset exit"
        jsonTaskData["args"].append(programString)

        # User edit END
        tasksData = self.addOrReplaceTask(tasksData, jsonTaskData)
        return tasksData

    def addResetAndRunTask(self, tasksData):
        '''
        Create/repair 'CPU: Reset and run' task.
        '''
        # User edit BEGIN
        taskData = """
        {
            "label": "CPU: Reset and run",
            "type": "shell",
            "command": "specified below",
            "args": ["specified below"],
            "problemMatcher": []
        }
        """
        jsonTaskData = json.loads(taskData)

        buildData = build.BuildData().getBuildData()
        jsonTaskData["command"] = buildData[self.bStr.openOCDPath]
        jsonTaskData["args"] = []
        jsonTaskData["args"].append("-f")
        jsonTaskData["args"].append(buildData[self.bStr.openOCDInterfacePath])
        jsonTaskData["args"].append("-f")
        jsonTaskData["args"].append(buildData[self.bStr.openOCDTargetPath])

        jsonTaskData["args"].append("-c init")  # init must be executed before other commands!
        jsonTaskData["args"].append("-c reset")
        jsonTaskData["args"].append("-c exit")

        # User edit END
        tasksData = self.addOrReplaceTask(tasksData, jsonTaskData)
        return tasksData

    def addHaltTask(self, tasksData):
        '''
        Create/repair 'CPU: Halt' task.
        '''
        # User edit BEGIN
        taskData = """
        {
            "label": "CPU: Halt",
            "type": "shell",
            "command": "specified below",
            "args": ["specified below"],
            "problemMatcher": []
        }
        """
        jsonTaskData = json.loads(taskData)

        buildData = build.BuildData().getBuildData()
        jsonTaskData["command"] = buildData[self.bStr.openOCDPath]
        jsonTaskData["args"] = []
        jsonTaskData["args"].append("-f")
        jsonTaskData["args"].append(buildData[self.bStr.openOCDInterfacePath])
        jsonTaskData["args"].append("-f")
        jsonTaskData["args"].append(buildData[self.bStr.openOCDTargetPath])

        jsonTaskData["args"].append("-c init")  # init must be executed before other commands!
        jsonTaskData["args"].append("-c halt")
        jsonTaskData["args"].append("-c exit")

        # User edit END
        tasksData = self.addOrReplaceTask(tasksData, jsonTaskData)
        return tasksData

    def addRunTask(self, tasksData):
        '''
        Create/repair 'CPU: Run' task.
        '''
        # User edit BEGIN
        taskData = """
        {
            "label": "CPU: Run",
            "type": "shell",
            "command": "specified below",
            "args": ["specified below"],
            "problemMatcher": []
        }
        """
        jsonTaskData = json.loads(taskData)

        buildData = build.BuildData().getBuildData()
        jsonTaskData["command"] = buildData[self.bStr.openOCDPath]
        jsonTaskData["args"] = []
        jsonTaskData["args"].append("-f")
        jsonTaskData["args"].append(buildData[self.bStr.openOCDInterfacePath])
        jsonTaskData["args"].append("-f")
        jsonTaskData["args"].append(buildData[self.bStr.openOCDTargetPath])

        jsonTaskData["args"].append("-c init")  # init must be executed before other commands!
        jsonTaskData["args"].append("-c resume  ")
        jsonTaskData["args"].append("-c exit")

        # User edit END
        tasksData = self.addOrReplaceTask(tasksData, jsonTaskData)
        return tasksData

    ########################################################################################################################
    # Other tasks
    ########################################################################################################################

    def addUpdateTask(self, tasksData):
        '''
        Create/repair 'Update workspace' task, which runs update.py script.
        '''
        # User edit BEGIN

        taskData = """
        {
            "label": "Update workspace",
            "type": "shell",
            "command": "python",
            "args": [
                "${workspaceFolder}/ideScripts/update.py"
            ],
            "presentation": {
                "focus": true
            },
            "problemMatcher": []
        }
        """
        jsonTaskData = json.loads(taskData)

        # User edit END
        tasksData = self.addOrReplaceTask(tasksData, jsonTaskData)
        return tasksData


########################################################################################################################
if __name__ == "__main__":
    utils.verifyFolderStructure()

    paths = pth.UpdatePaths()
    bData = build.BuildData()
    cP = wks.CProperties()
    makefile = mkf.Makefile()
    tasks = Tasks()

    # check if 'buildData.json' exists. Create it or/and get tool paths
    bData.checkBuildDataFile()
    buildData = bData.getBuildData()
    if not paths.verifyExistingPaths(buildData):
        buildData = paths.forceUpdatePaths(buildData)
        bData.overwriteBuildDataFile(buildData)
    makeExePath = buildData[bData.bStr.buildToolsPath]
    gccExePath = buildData[bData.bStr.gccExePath]

    # create taks file
    tasks.checkTasksFile()
    tasksData = tasks.getTasksData()
    tasksData = tasks.addAllTasks(tasksData)

    tasks.overwriteTasksFile(tasksData)
