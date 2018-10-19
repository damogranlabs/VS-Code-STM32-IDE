# VS Code STM32 IDE
Source: [Damogran Labs: https://damogranlabs.com/](https://damogranlabs.com/2018/10/vs-code-stm32-ide/)  
Date: 15.10.2018  
Version: 1.0  

## About
This project transform VS Code to a great IDE that can be used with STM32CubeMX tool to create a projects without any limitations and code size restrictions, without any bloatware and fast user setup (once all prerequisites are installed). Project is based on python scripts and is therefore fully customizable. OpenOCD tool and Cortex-Debug VS Code plugin is used for debug purposes.  

Debug capabilities are somehow limited, but can be good enough for most simple projects - see below.

[![VS Code as STM32 IDE](https://github.com/damogranlabs/VS-Code-STM32-IDE/blob/master/_images/videoThumbnail.PNG)](https://www.youtube.com/watch?v=rWjb43kLHdQ)

## How does it work?
Scripts generate all necessary VS Code workspace files ('c_cpp_properties.json', 'tasks.json' and 'launch.json') that IDE needs for autocomplete and compile/build/debug/download actions. New 'Makefile' is generated from CubeMX and user data on each update. All user settings are stored and can be changed in one file: 'c_cpp_properties.json'.  
  
Additionally, 'buildData.json' file is created for user inspection of all paths/settings (this file is also used by all 'update*.py' scripts and should not be modified directly).

# Setup
Install procedure is simple since all needed files can be downloaded online and setup shouldn't take no more than 5 minutes. It is strongly advised to stick to default recommended paths while installing following tools.  
Tools needed: Python, GNU Eclipse ARM Embedded GCC, GNU Eclipse Windows Build Tools, GNU MCU Eclipse OpenOCD and CPU-specific files. 

**Python**  
There are many posts how to install python. This project needs a valid *python* terminal command to execute tasks and set up files.

**Download GNU Eclipse tools:**
* [GNU Eclipse ARM Embedded GCC](https://github.com/gnu-mcu-eclipse/arm-none-eabi-gcc/releases)
* [GNU Eclipse Windows Build Tools](https://github.com/gnu-mcu-eclipse/windows-build-tools/releases)
* [GNU MCU Eclipse OpenOCD](https://github.com/gnu-mcu-eclipse/openocd/releases)  
  
After download, extract all directiories in [recommended](https://gnu-mcu-eclipse.github.io/toolchain/arm/install/#manual-install) path: *%userprofile%\AppData\Roaming\GNU MCU Eclipse*.  

**Install Cortex-Debug and Python plugin from VS Code extension marketplace**  
This is needed for debug purposes and workspace file generation scripts.

**Dowload CPU specific SVD file (System Viewer Description)**  
This file is (recommended by ST) downloaded from [Keil official page](https://www.keil.com/dd2/pack/). Just search for your chosen STM32 CPU family (ex.: STM32F0...), download and unpack with any archive software.  
I recommend to unpack it in the same directory as other GNU Eclipse tools (eg: *%userprofile%\AppData\Roaming\GNU MCU Eclipse*) so everything is neatly organised in one place and files can be reused in other projects (this files will not be changed).  

At the end, folder structure should look like this:  
![Folder structure](https://github.com/damogranlabs/VS-Code-STM32-IDE/blob/master/_images/folderStructure.PNG)

# First steps
Once all prerequisites are installed, work flow is very simple.
* Create CubeMX project and select 'Makefile' as output file.
* Open generated folder with VS Code and save it as workspace.
* Copy 'ideScripts' folder inside this workspace folder.
* Run update.py script with python.
* Code, compile, build, ...
* Debug, download, reset, run, stop, ...
  
Need to re-generate CubeMX project? Do it, than run 'Update workspace' task and continue with work. User settings will remain intact as long as the are in a valid json format. Anyway, backup files are created in case of mistake/error.  
Need to add user specific files/folders? Edit 'c_cpp_properties.json' file and update again.
  
Note: on first 'update.py' script run, user must specify absolute paths to few files (tool paths). This are than stored in 'buildData.json' and update is not neccessary as long as the same 'buildData.json' file exists and paths are valid. Alternatively paths can be updated by running 'updatePaths.py' script.

![Example folder structure](https://github.com/damogranlabs/VS-Code-STM32-IDE/blob/master/_images/exampleFolderStructure.PNG)
 
# Coding and running code on CPU
Once all files are generated, autocomplete and all includes/definitions should be accessible with VS Code.  
Scripts generate following tasks, which should work out of the box. 

## Building/compiling tasks:
* Build (execute 'make' command - compile all source files and generate output binaries)
* Compile (compile currently opened source file with the same compiler flags as specified in 'Makefile')
* Clean (delete) build folder
  
## Target control tasks:
* Download code and run CPU (program .elf output file and run CPU without attaching debugger)
* Reset and run CPU (do not download code, execute reset and run CPU without attaching debugger)
* Stop CPU
* Run CPU
  
![Tasks](https://github.com/damogranlabs/VS-Code-STM32-IDE/blob/master/_images/tasks.PNG)  

  
## Debug 
Two launch (debug) configurations are currently implemented automatically in 'launch.json': debug embedded project and selected python
Press F5 and debug code (download code, reset and stop CPU is performed). This functions are currently supported:  
* run/stop
* step
* set/delete breakpoints (only in STOP state)
* restart (reset)  
  
Debug capabilities are currently slightly limited (*Cortex-Debug* extension), but it might be improved soon:
* breakpoints can be set on non-valid places
* more than available breakpoints can be set (OpenOCD shows number of available BPs at the beginning)
* after reset, location is not refreshed.
  
Anyway, any non-beginner shouldn't have much problems with this limitations.  
![Launch configurations](https://github.com/damogranlabs/VS-Code-STM32-IDE/blob/master/_images/launchConfigurations.PNG)


## Even more?
Need to know more details (and FAQ)? see [README_DETAILS.md](https://github.com/damogranlabs/VS-Code-STM32-IDE/blob/master/README_DETAILS.md).  
Suggestions, details, ideas, bugs? Use [Issues tab](https://github.com/damogranlabs/VS-Code-STM32-IDE/issues).  
