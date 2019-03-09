About:
This is a basic example how to use VS Code STM32 ideScripts.

At the moment, this code is generated for a custom board (until my Discovery board is fixed). Anyway, for example and 
simple debug test, it should be OK.

'.vscode' folder and its files were/are created by running 'ideScripts/update.py' script.

'buildData.json' is intentionally renamed to 'buildData.json.backup', just as an example of what my tools paths are. By running
'ideScripts/update.py' script, this paths are cached and user only needs to set them once. 

Once Update process is over, user can modify code and compile or build application by available tasks (CTRL + P, run task), 
or debug application by executing 'Cortex debug (STM32F051K4)' launch configuration.

For a more details, see the github repository:
https://github.com/damogranlabs/VS-Code-STM32-IDE