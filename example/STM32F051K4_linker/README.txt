About
This example shows how already available linker files can be added to the project using 'ldSources' (and other 'ld*' fields)
in 'c_cpp_properties.json' file.

At the moment, this code is generated for a custom board (until my Discovery board is fixed). Anyway, for example and 
simple debug test, it should be OK.

'buildData.json' is intentionally renamed to 'buildData.json.backup', just as an example of what my tools paths are. By running
'ideScripts/update.py' script, this paths are cached and user only needs to set them once. 

In this case, 'main.c' file was compiled to produce 'main.o' obj file. 'main.c' was than excluded from Makefile (and Makefile.backup), and 'main.o' was added to 'ldSources' in 'c_cpp_properties.json' file. Since 'main.o' is placed in 'Libs' sub-directory, 'Libs' was added to 'ldIncludes'.

For a more generic how-to used ideScripts, see the github repository and other examples:
https://github.com/damogranlabs/VS-Code-STM32-IDE