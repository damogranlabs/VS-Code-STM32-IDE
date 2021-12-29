# VS Code STM32 IDE
Source: [Damogran Labs: https://damogranlabs.com/](https://damogranlabs.com/2018/10/vs-code-stm32-ide/)  
Version: 1.7  

# UPDATE (29.12.2021):
After a couple of weeks of testing, I can confirm that all he things covered in this project are now replaced (and even better) with [VS Code Makefile tools plugin](https://marketplace.visualstudio.com/items?itemName=ms-vscode.makefile-tools). Anyway, 3 years in a such rapid changing SW development world, I consider this project a success, even though closed.  

## About
This project transform VS Code to a great IDE that can be used with STM32CubeMX tool to create a projects without any limitations and code size restrictions, without any bloatware and fast user setup (once all prerequisites are installed). Project is based on python scripts and is therefore fully customizable. OpenOCD tool and Cortex-Debug VS Code plugin is used for debug purposes.  

Debug capabilities are somehow limited, but can be good enough for most simple projects - see below.  
**Keil project import** script available. [See README_KEIL_IMPORTER.](https://github.com/damogranlabs/VS-Code-STM32-IDE/blob/master/README_KEIL_IMPORTER.md)  

[![VS Code as STM32 IDE](https://github.com/damogranlabs/VS-Code-STM32-IDE/blob/master/_images/videoThumbnail.PNG)](https://www.youtube.com/watch?v=rWjb43kLHdQ)  
*Video is now slightly outdated - now setup and workflow is even beter.*

## How does it work?
Scripts generate all necessary VS Code workspace files ('c_cpp_properties.json', 'tasks.json' and 'launch.json') that IDE needs for autocomplete and compile/build/debug/download actions. New 'Makefile' is generated from CubeMX and user data on each update. All user settings are stored and can be changed in one file: 'c_cpp_properties.json'.  
  
Additionally, 'buildData.json' and 'toolsPaths.json' file is created for user inspection of all paths/settings (this file is also used by all 'update*.py' scripts and should not be modified directly).

# Setup
Install procedure is simple since all needed files can be downloaded online and setup shouldn't take no more than 5 minutes.
It is strongly advised use the default recommended paths while installing the following tools and to **use non-spaced paths** - avoiding unwanted problems. [See this issue.](https://github.com/damogranlabs/VS-Code-STM32-IDE/issues/1) 

**Python**  
There are many posts how to install python. This project needs a valid `python` or `python3` terminal command to execute tasks and set up files. Python version 3 or later is required.  

**STM32CubeMX**  
Download and install STM32CubeMX for your system from [ST's website.](https://www.st.com/content/st_com/en/products/development-tools/software-development-tools/stm32-software-development-tools/stm32-configurators-and-code-generators/stm32cubemx.html) Note that you will need to create an account (it's free) to access the download. Setup is as easy as running the installation executable for your system and following the prompts. Running CubeMX requires java on your system. Enter `java -version`  in your terminal to check it's installed.

**Important:** Latest version of STM32CubeMX has some bugs which (at least some of them) were [already reported](https://community.st.com/s/question/0D50X0000AU1swrSQB/stm32cubemx-makefile-not-properly-generated-for-stm32l1-device). Consider using older version until this issues are fixed

**Install Cortex-Debug and Python plugin from VS Code extension marketplace**  
This is needed for debug purposes and workspace file generation scripts.

**Download CPU specific SVD file (System Viewer Description)**  
This file is (recommended by ST) downloaded from [Keil official page](https://www.keil.com/dd2/pack/). Just search for your chosen STM32 CPU family (ex.: STM32F0...), download and unpack with any archive software.  
I recommend to unpack it in the same directory as the other tools (eg: *%userprofile%\AppData\Roaming\GNU MCU Eclipse* on windows, or somewhere like the home directory on linux) so everything is neatly organized in one place and files can be reused in other projects (these files will not be changed).  

## Windows specific steps
Tools needed: Python, GNU Eclipse ARM Embedded GCC, GNU Eclipse Windows Build Tools, GNU MCU Eclipse OpenOCD and CPU-specific files.  

**Download GNU Eclipse tools:**
* [GNU Eclipse ARM Embedded GCC](https://github.com/xpack-dev-tools/arm-none-eabi-gcc-xpack/releases)  
* [GNU Eclipse Windows Build Tools](https://github.com/gnu-mcu-eclipse/windows-build-tools/releases/tag/v2.12-20190422/)
* [GNU MCU Eclipse OpenOCD](https://github.com/ilg-archived/openocd/releases/tag/v0.10.0-12-20190422)  
  
After download, extract all directories in [recommended](https://gnu-mcu-eclipse.github.io/toolchain/arm/install/#manual-install) path: *%userprofile%\AppData\Roaming\GNU MCU Eclipse*.  

At the end, folder structure should look like this:  
![Folder structure](https://github.com/damogranlabs/VS-Code-STM32-IDE/blob/master/_images/folderStructure.PNG)

## Linux specific steps
Note: the following steps were performed on Ubuntu.

First, ensure you are up-to-date:  
`sudo apt update && sudo apt upgrade`

**Install build-essential**
The build-essential package contains development tools like `make`, `g++` and `gcc` which we will need for compiling our projects:  
`sudo apt install build-essential`

**Install arm-gcc**  
Download the latest [GNU Arm Embedded Toolchain](https://developer.arm.com/open-source/gnu-toolchain/gnu-rm/downloads) for Linux 64.  
Navigate to the folder containing the downloaded file and extract as follows to install:  
`sudo tar -C /usr/local -xjf gcc-arm-none-eabi-8-2018-q4-major-linux.tar.bz2 --strip-components 1`

**Install OpenOCD**  
From packages:  
`sudo apt install openocd`  
Or get the latest release from [The Official OpenOCD Github mirror.](https://github.com/ntfreak/openocd) (requires building from source)


# First steps
Once all prerequisites are installed, workflow is very simple.
* Create CubeMX project and select 'Makefile' as output file.
* Open generated folder with VS Code and save it as a workspace.
* Copy 'ideScripts' folder inside this workspace folder.
* Run update.py script with python. Follow simple instructions in terminal.
* Code, compile, build, ...
* Debug, download, reset, run, stop, ...
  
Need to re-generate CubeMX project? Do it, than run 'Update workspace' task and continue with work. User settings will remain intact as long as the are in a valid json format. Anyway, backup files are created in case of mistake/error.  
Need to add user specific files/folders? Edit 'c_cpp_properties.json' file and update again.
  
Note: on first 'update.py' script run, user must specify paths to a few files (tool paths and target configuration files). This are than stored in 'buildData.json/toolsPaths.json' and update is not necessary as long as this files exists and paths are valid. Common tools paths (like GCC and OpenOCD) paths are cached in 'toolsPaths.json' in VS Code user APPDATA, so there is less work when creating new workspaces.  
Alternatively paths can be updated by running 'updatePaths.py' script.  
*From time to time, some backward compatibility is broken - new stuff and improvements are implementing all the time. Anyway, find your old paths in backup files inside .vscode folder.*

![Example folder structure](https://github.com/damogranlabs/VS-Code-STM32-IDE/blob/master/_images/exampleFolderStructure.PNG)
 
# Coding and running code on CPU
Once all files are generated, autocomplete and all includes/definitions should be accessible with VS Code.  
Scripts generate following tasks, which should work out of the box. 

## Building/compiling tasks:
* Build (execute 'make' command - compile all source files and generate output binaries)
* Compile (compile currently opened source file with the same compiler flags as specified in 'Makefile')
* Clean (delete) build folder
  
## Target control tasks:
* Build task + Download code and run CPU task
* Download code and run CPU (program .elf output file and run CPU without attaching debugger)
* Reset and run CPU (do not download code, execute reset and run CPU without attaching debugger)
* Stop CPU
* Run CPU
  
![Tasks](https://github.com/damogranlabs/VS-Code-STM32-IDE/blob/master/_images/tasks.PNG)  

  
## Debug 
Two launch (debug) configurations are currently automatically implemented in 'launch.json': *debug embedded project* and *debug selected python file*.  
Just press F5 and debug code (download code, reset and stop CPU is performed on *debug embedded project*).  
  
This debug features are currently supported:  
* run/stop
* step
* set/delete breakpoints (only in STOP state)
* restart (reset)  
* SFR/register view, write to SFR
  
Debug capabilities are currently slightly limited (*Cortex-Debug* extension), but it might be improved soon:
* breakpoints can be set on non-valid places
* more than available breakpoints can be set (OpenOCD shows number of available BPs at the beginning)
* after reset, location is not refreshed.
  
Anyway, any non-beginner shouldn't have much problems with this limitations.  
![Launch configurations](https://github.com/damogranlabs/VS-Code-STM32-IDE/blob/master/_images/launchConfigurations.PNG)


## Even more?
Need to know more details (and FAQ)? see [README_DETAILS.md](https://github.com/damogranlabs/VS-Code-STM32-IDE/blob/master/README_DETAILS.md).  
Suggestions, details, ideas, bugs? Use [Issues tab](https://github.com/damogranlabs/VS-Code-STM32-IDE/issues).  


--------
## Contributors
Special thanks go to:  
* [@poshcoe](https://github.com/poshcoe)
* [@ali80](https://github.com/ali80)
* [@om2kw](https://github.com/om2kw)
