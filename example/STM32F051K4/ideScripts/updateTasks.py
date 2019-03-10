'''
Update/generate 'tasks.json' file in .vscode subfolder.

'tasks.json' fields description:
https://code.visualstudio.com/docs/editor/tasks
'''
import copy
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
        if utils.pathExists(utils.tasksPath):
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
        task = self.getBuildTask()
        tasksData = self.addOrReplaceTask(tasksData, task)

        task = self.getCompileTask()
        tasksData = self.addOrReplaceTask(tasksData, task)

        task = self.getDeleteBuildFolderTask()
        tasksData = self.addOrReplaceTask(tasksData, task)

        # debugging and target control tasts
        task = self.getBuildDownloadAndRunTask()
        tasksData = self.addOrReplaceTask(tasksData, task)

        task = self.getDownloadAndRunTask()
        tasksData = self.addOrReplaceTask(tasksData, task)

        task = self.getResetAndRunTask()
        tasksData = self.addOrReplaceTask(tasksData, task)

        task = self.getHaltTask()
        tasksData = self.addOrReplaceTask(tasksData, task)

        task = self.getRunTask()
        tasksData = self.addOrReplaceTask(tasksData, task)

        # update IDE workspace tasks
        task = self.getRunCurrentPythonFileTask()  # common "run python file" task
        tasksData = self.addOrReplaceTask(tasksData, task)

        if utils.cubeMxProjectFilePath is not None:
            task = self.getOpenCubeMXTask()   # open CubeMX project
            tasksData = self.addOrReplaceTask(tasksData, task)

        task = self.getUpdateTask()   # update all files for VS Code so it can be used as IDE
        tasksData = self.addOrReplaceTask(tasksData, task)

        # TODO USER: User can add other custom tasks here
        # - copy any of getXTask() functions below, edit
        # - add this function here as other tasks above

        return tasksData

    ########################################################################################################################
    # Build, compile and clean tasks
    ########################################################################################################################

    def getBuildTask(self):
        '''
        Add build task (execute 'make' command). Also the VS Code default 'build' task.
        '''
        taskData = """
        {
            "label": "will be replaced with templateStrings string",
            "group": {
                "kind": "build",
                "isDefault": true
            },
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
        jsonTaskData["label"] = tmpStr.taskName_build
        jsonTaskData["command"] = buildData[self.bStr.buildToolsPath]

        gccFolderPath = os.path.dirname(buildData[self.bStr.gccExePath])
        gccFolderPath = utils.pathWithForwardSlashes(gccFolderPath)
        jsonTaskData["args"] = ["GCC_PATH=" + gccFolderPath]   # specify compiler path to make command

        numOfCores = os.cpu_count()
        parallelJobsNumber = int(numOfCores * 1.5)  # https://stackoverflow.com/questions/15289250/make-j4-or-j8/15295032
        parallelJobsStr = "-j" + str(parallelJobsNumber)
        jsonTaskData["args"].append(parallelJobsStr)  # set 'make' parallel job execution

        return jsonTaskData

    def getCompileTask(self):
        '''
        Create compile current file task (execute gcc compile command).
        '''
        taskData = """
        {
            "label": "will be replaced with templateStrings string",
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
        jsonTaskData["label"] = tmpStr.taskName_compile

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

        return jsonTaskData

    def getDeleteBuildFolderTask(self):
        '''
        Create delete task (execute 'make clean' command).
        '''
        taskData = """
        {
            "label": "will be replaced with templateStrings string",
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
        jsonTaskData["label"] = tmpStr.taskName_clean
        jsonTaskData["command"] = buildData[self.bStr.buildToolsPath]

        return jsonTaskData

    ########################################################################################################################
    # Debugging and target control tasks
    ########################################################################################################################
    def getBuildDownloadAndRunTask(self):
        '''
        Create Build + Download and run task. Use 'dependsOn' feature to avoid doubling code.
        Note: If multiple 'dependOn' tasks are defined, these tasks are launched simultaneously,
            not chained one after another.
        '''
        jsonTaskData = self.getDownloadAndRunTask()

        jsonTaskData["label"] = tmpStr.taskName_CPU_buildDownloadRun
        jsonTaskData["dependsOn"] = tmpStr.taskName_build

        return jsonTaskData

    def getDownloadAndRunTask(self):
        '''
        Create Download and run task.
        '''
        taskData = """
        {
            "label": "will be replaced with templateStrings string",
            "type": "shell",
            "command": "specified below",
            "args": ["specified below"],
            "problemMatcher": []
        }
        """
        jsonTaskData = json.loads(taskData)

        buildData = build.BuildData().getBuildData()
        jsonTaskData["label"] = tmpStr.taskName_CPU_downloadRun
        jsonTaskData["command"] = buildData[self.bStr.openOcdPath]
        jsonTaskData["args"] = []
        jsonTaskData["args"].append("-f")
        jsonTaskData["args"].append(buildData[self.bStr.openOcdInterfacePath])
        for arg in buildData[self.bStr.openOcdConfig]:
            jsonTaskData["args"].append("-f")
            jsonTaskData["args"].append(arg)

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

        return jsonTaskData

    def getResetAndRunTask(self):
        '''
        Create CPU: Reset and run task.
        '''
        taskData = """
        {
            "label": "will be replaced with templateStrings string",
            "type": "shell",
            "command": "specified below",
            "args": ["specified below"],
            "problemMatcher": []
        }
        """
        jsonTaskData = json.loads(taskData)

        buildData = build.BuildData().getBuildData()
        jsonTaskData["label"] = tmpStr.taskName_CPU_resetRun
        jsonTaskData["command"] = buildData[self.bStr.openOcdPath]
        jsonTaskData["args"] = []
        jsonTaskData["args"].append("-f")
        jsonTaskData["args"].append(buildData[self.bStr.openOcdInterfacePath])
        for arg in buildData[self.bStr.openOcdConfig]:
            jsonTaskData["args"].append("-f")
            jsonTaskData["args"].append(arg)
        jsonTaskData["args"].append("-c init")  # init must be executed before other commands!
        jsonTaskData["args"].append("-c reset")
        jsonTaskData["args"].append("-c exit")

        return jsonTaskData

    def getHaltTask(self):
        '''
        Create Halt/stop task.
        '''
        taskData = """
        {
            "label": "will be replaced with templateStrings string",
            "type": "shell",
            "command": "specified below",
            "args": ["specified below"],
            "problemMatcher": []
        }
        """
        jsonTaskData = json.loads(taskData)

        buildData = build.BuildData().getBuildData()
        jsonTaskData["label"] = tmpStr.taskName_CPU_halt
        jsonTaskData["command"] = buildData[self.bStr.openOcdPath]
        jsonTaskData["args"] = []
        jsonTaskData["args"].append("-f")
        jsonTaskData["args"].append(buildData[self.bStr.openOcdInterfacePath])
        for arg in buildData[self.bStr.openOcdConfig]:
            jsonTaskData["args"].append("-f")
            jsonTaskData["args"].append(arg)

        jsonTaskData["args"].append("-c init")  # init must be executed before other commands!
        jsonTaskData["args"].append("-c halt")
        jsonTaskData["args"].append("-c exit")

        return jsonTaskData

    def getRunTask(self):
        '''
        Create Run task.
        '''
        taskData = """
        {
            "label": "will be replaced with templateStrings string",
            "type": "shell",
            "command": "specified below",
            "args": ["specified below"],
            "problemMatcher": []
        }
        """
        jsonTaskData = json.loads(taskData)

        buildData = build.BuildData().getBuildData()
        jsonTaskData["label"] = tmpStr.taskName_CPU_run
        jsonTaskData["command"] = buildData[self.bStr.openOcdPath]
        jsonTaskData["args"] = []
        jsonTaskData["args"].append("-f")
        jsonTaskData["args"].append(buildData[self.bStr.openOcdInterfacePath])
        for arg in buildData[self.bStr.openOcdConfig]:
            jsonTaskData["args"].append("-f")
            jsonTaskData["args"].append(arg)

        jsonTaskData["args"].append("-c init")  # init must be executed before other commands!
        jsonTaskData["args"].append("-c resume")
        jsonTaskData["args"].append("-c exit")

        return jsonTaskData

    ########################################################################################################################
    # Other tasks
    ########################################################################################################################
    def getRunCurrentPythonFileTask(self):
        '''
        Create Run Python file task, which runs current active Python file.
        '''
        taskData = """
        {
            "label": "will be replaced with templateStrings string",
            "type": "shell",
            "command": "specified below",
            "args": [
                "${file}"
            ],
            "presentation": {
                "focus": true
            },
            "problemMatcher": []
        }
        """
        buildData = build.BuildData().getBuildData()
        jsonTaskData = json.loads(taskData)
        jsonTaskData["label"] = tmpStr.taskName_Python
        jsonTaskData["command"] = buildData[self.bStr.pythonExec]

        return jsonTaskData

    def getOpenCubeMXTask(self):
        '''
        Create Open CubeMX project task. Starts with default program.

        Method of starting CubeMX differs across systems. Note that on linux cubeMX does not associate itself with files by default.
        Use a program like "Main Menu" for GNOME to add CubeMX to the applications list, and then it can be selected as the default program for .ioc files.
        '''
        taskData = """
        {
            "label": "will be replaced with templateStrings string",
            "type": "shell",
            "command": "specified below",
            "args": ["specified below"],
            "presentation": {
                "focus": false
            },
            "problemMatcher": []
        }
        """
        osIs = utils.detectOs()
        if osIs == "unix":
            openCubeCommand = "xdg-open"
        else:
            openCubeCommand = "start"

        jsonTaskData = json.loads(taskData)
        jsonTaskData["label"] = tmpStr.taskName_OpenCubeMX
        jsonTaskData["command"] = openCubeCommand
        jsonTaskData["args"] = [utils.cubeMxProjectFilePath]  # opens with default program

        return jsonTaskData

    def getUpdateTask(self):
        '''
        Create Update workspace task, which runs update.py script.
        '''
        taskData = """
        {
            "label": "will be replaced with templateStrings string",
            "type": "shell",
            "command": "specified below",
            "args": [
                "${workspaceFolder}/ideScripts/update.py"
            ],
            "presentation": {
                "focus": true
            },
            "problemMatcher": []
        }
        """
        buildData = build.BuildData().getBuildData()
        jsonTaskData = json.loads(taskData)
        jsonTaskData["label"] = tmpStr.taskName_updateWorkspace
        jsonTaskData["command"] = buildData[self.bStr.pythonExec]

        return jsonTaskData


########################################################################################################################
if __name__ == "__main__":
    utils.verifyFolderStructure()

    paths = pth.UpdatePaths()
    bData = build.BuildData()
    cP = wks.CProperties()
    makefile = mkf.Makefile()
    tasks = Tasks()

    # build data (update tools paths if neccessary)
    buildData = bData.prepareBuildData()
    bData.createUserToolsFile(buildData)

    # create taks file
    tasks.checkTasksFile()
    tasksData = tasks.getTasksData()
    tasksData = tasks.addAllTasks(tasksData)

    tasks.overwriteTasksFile(tasksData)
