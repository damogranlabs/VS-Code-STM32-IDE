# Readme (details)
This file answers some of the frequently asked questions and explains inner working and details of specific 'update*.py' scripts. Also, see README.md in this folder.

## FAQ:
* **What files can I modify?**  
  Basically, user should modify only 'c_cpp_properties.json' file, specifically 'user_*' fields. Other paths should be updated either with CubeMX or 'updatePaths.py' script.  

* **Can workspace files/folders paths contain spaces?**  
  No. This is a common issue and must be avoided - all user defined source folders and files must be without spaces, since GNU Make does not handle any paths with spaces. Although paths to GCC/GNU/OpenOCD executables can include spaces in default VS Code terminal configuration, it is still advised to avoid them. Generally it is a good idea to use non-spaced paths and avoid uneccessary problems. [See this issue.](https://github.com/damogranlabs/VS-Code-STM32-IDE/issues/1)  

* **Can I add my custom tasks and launch configurations?**  
  Yes. See **updateTasks.py** description. Also, see *#TODO USER* markings in 'update*.py' code for specific how-to.

* **Will user fields be overwritten when any of 'update\*.py' script is called?**  
  No. If '.json' files are a valid files, data is merged eg.: custom tasks are added to existing ones (only the same labeled tasks are overwritten). If '.json' files are not valid, '.backup' file is created and new valid file is created from template. User fields in 'c_cpp_properties.json' must be properly added, see example.

* **What is .SVD file needed for?**  
  SVD file is a CPU-specific register description file. It is needed for Cortex-Debug plugin to correctly display core/system registers and for OpenOCD to properly interface with chosen CPU. This files can be found from [Keil MDK Software Pack](https://www.keil.com/dd2/pack/).

* **Where do compiler flags in 'buildData.json' come from?**  
  This flags are fetched from current 'Makefile' with 'print-VARIABLE' function, which is added specifically for this purpose. Once project is updated with 'update.py' script, 'buildData.json' shows merged user and CubeMX compiler settings, while new 'Makefile' has added user settings to original 'Makefile'.

* **How do I compile specific file?**  
  Run 'Compile' task. Currently only C source files are supported by this task (assembler flags are not added to compile command).

* **Can I add custom compiler flags/switches?**  
  Yes. 'user_cFlags' and 'user_asmFlags' fields in 'c_cpp_properties.json' fields are meant for this purpose and are added to new 'Makefile' once *Update workspace* task is executed.

* **What and why is '-j' switch in 'Build' task?**  
  This switch manages number of 'make' parallel jobs, which could speed up build time. It was added upon [#FeatureRequest](https://github.com/damogranlabs/VS-Code-STM32-IDE/issues/5) and is calculated: NUMBER OF CORES * 1.5, as it is advised on many forums.
  It will be removed if users will report unwanted behaviour or unsuccesfull builds. Anyway, it has no impact on the compiled code.

* **I don't have 'Open CubeMX project' task!?!**  
  If workspace directory contain no '\*.ioc' files, this task is not generated.  
  If there is more than one '\*.ioc' file, at least one such file name must match with the name of VS Code workspace file.  
  If only one '\*.ioc' file is found, this file is chosen for this task.

* **Where can I see when the workspace files were updated the last time?**  
  *Version* and *last run timestamp* are updated on every run of 'update.py' script and can be seen in 'Makefile' and 'buildData.json'.
  

# update.py
This is a parent script of all 'update*.py' scripts. It is the only file that needs to be called if 'Makefile' was modified with STM32CubeMX tool or if user modified 'c_cpp_properties.json'.  
Script calls other 'update*.py' scripts and generate all the necessary files for VS Code. See other scripts descriptions below for details.

## updatePaths.py
This script checks and updates paths to all necessary files/folders: Python3, GCC compiler, Make tool, OpenOCD (and configuration files), and SVD description file. Script automatically fills data in 'buildData.json' which is later needed for other scripts.  
If this script is executed manually, tool paths are re-checked and the user is asked if he wishes to update paths.  

## updateWorkspaceSources.py
This script (re)generate 'c_cpp_properties.json' file from existing 'Makefile' and 'c_cpp_properties.json' file. User can modify (add paths to sources/folders and defines) only fields marked with "user_*", otherwise fields will be overwritten with next update procedure.
Data fetched from 'Makefile' and user fields are stored in 'buildData.json' at the end.  
  
If any of files/paths are missing or invalid, new ones are created (and backup file is generated if available), and data is restored to default (see 'templateStrings.py' and 'updateWorkspaceSources.py' file).  

File adds 'print-variable' function to 'Makefile', while creating a backup 'Makefile'. Function is needed for fetching data from 'Makefile' with (example) 'make print-CFLAGS' call.

## updateWorkspaceFile.py
This file adds "cortex-debug" keys to '*.code-workspace' file. It is needed for Cortex-Debug extension and should not be modified by user. Instead, this fields are fetched from 'buildData.json' file.

## updateMakefile.py
This script generate new 'Makefile' from old 'Makefile' and user data. User data specified in 'c_cpp_properties.json' is merged with existing data from 'Makefile' and stored into 'buildData.json'. New 'Makefile' is created by making a copy and appending specific strings (c/asm sources, includes and defines) with proper multi-line escaping ( '\\' ).

## updateTasks.py
This script (re)generate 'tasks.json' file in '.vscode' workspace subfolder. Tasks could be separated to:  

**Building/compiling tasks:**
* Build (execute 'make' command - compile all source files and generate output binaries)
* Compile (compile currently opened source file with the same compiler flags as specified in 'Makefile')
* Clean build folder (delete)
  
**Target control tasks:**
* Build, Download code and run CPU (executes 'Build' task before 'Download code and run CPU' task)
* Download code and run CPU (program .elf output file and run CPU without attaching debugger)
* Reset and run CPU (do not download code, execute reset and run CPU without attaching debugger)
* Stop CPU
* Run CPU
  
**Python/IDE tasks:**
* Update (calls 'update.py' script and update all workspace sources)
* Open CubeMX project (Opens STM32CubeMX project if appropriate '*.ioc' file is found in workspace folder). Note: on linux STM32CubeMX must be configured as the default application for .ioc files for this task to work.
  
User can add custom tasks in two ways: add task to 'updateTasks.py' file (added always even if 'tasks.json' previously does not exist) or add task directly to 'tasks.json' file.  
If 'tasks.json' file already exists when 'updateTasks.py' script is called, data is merged and task will not be overwritten. But, if existing 'tasks.json' file is not valid (faulty json format), backup is created and new clean 'tasks.json' file is generated, overwriting user added task (could be found in .backup file).  
See *#TODO USER* markings inside file for how to add custom tasks.

## updateLaunchConfig.py
This script (re)generate 'launch.json' file inside '.vscode' workspace subfolder. Two tasks are currently implemented:
* Debug (runs build task, download code to the target, attach debugger and stop asap)
* Run current python file (run currently opened .py file)
  
Data for Debug Launch configuration is fetched from 'buildData.json' and should not be modified by user. Instead user should correctly specify target .cfg and .svd file with 'updatePaths.py'.  
Other launch configurations can be added in the similar way as tasks, see *updateTasks.py* description.

## updateBuildData.py
This file (re)generate 'buildData.json' file inside '.vscode' workspace subfolder. This file contains all workspace paths, sources, defines and compiler settings combined from 'Makefile', 'c_cpp_properties.json' file and user defined tools paths. File is used by 'update*.py' scripts and can be used for user to inspect what settings are used/generated by CubeMX.  
User should not modify this file, since it will be overwritten or tasks/launch configurations will be invalid. Instead, user should set CubeMX options, update paths with 'updatePaths.py' and correctly set data in 'c_cpp_properties.json' file.  
Once 'buildData.json' contains valid tools paths, 'toolsPaths.json' file is created/updated in VS Code user data folder, this is typically in *%APPDATA%Code/User* for windows or *~/.config/Code/User* in linux.

## templateStrings.py
This file content is used from other 'update*.py' scripts as a template to generate other '*.json' fields. User can modify default strings as long as it sticks to a valid .json format.  

## importKeilProject.py
This file imports existing Keil uVision project. [See readme here](https://github.com/damogranlabs/VS-Code-STM32-IDE/blob/master/README_KEIL_IMPORTER.md).  

--------
## How it actually works?
First, all scripts check if file/folder structure is as expected ('\*.ioc' file in the same folder as '\*.code-workspace' file). Existing tools paths are checked and updated, and 'buildData.json' is created with this data. Once all common configuration paths are valid, these are storred in 'toolsPaths.json', so user does not need to enter them when creating new workspace.  
'Makefile' is checked to see if it was already altered with previous 'update' actions. If this is not the original 'Makefile', original is restored from 'Makefile.backup' file. 'print-variable' function is added to enable fetching internal 'Makefile' variables (sources and compiler flags) and 'c_cpp_properties.json' file is created/merged with existing one. Data in 'c_cpp_properties.json' from 'Makefile' is stored in 'cubemx_*' fields and is needed for *compile* task later on.  
On update, new 'Makefile' is generated with merged data from old 'Makefile' and *user_* fields from 'c_cpp_properties.json'. 'buildData.json' is updated with new 'Makefile' variables.  
Tasks and Launch configurations are generated with paths and data from existing 'buildData.json'. At the end, 'cortex-debug' settings are applied to '\*.code-workspace' file. 
