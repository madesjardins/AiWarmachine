# AiWarmachine
A Warmachine (SteamForged Games, MKIV) tabletop wargaming companion and nemesis application.
The game engine is not yet available, but

# Installation
1. Install Python >= 3.10 (https://www.python.org/downloads/).
2. Install numpy using pip in a cmd prompt: `pip install numpy`
3. Install PyQt6 using pip in a cmd prompt: `pip install PyQt6`
4. Install OpenCV using pip in a cmd prompt: `pip install opencv-python`
5. Install sounddevice using pip in a cmd prompt: `pip install sounddevice`
6. Install pygame using pip in a cmd prompt: `pip install pygame`
7. Install Vosk using pip in a cmd prompt: `pip install vosk`
8. Install piper.exe (https://github.com/rhasspy/piper) in "apps/piper"
9. Download piper voices in "apps/piper/voices" and rename files to make sure "X.onnx" files have corresponding "X.onnx.json" files.
10. Install Java (https://www.java.com/en/download/)
11. Install PyBoof using pip in a cmd prompt: `pip install pyboof`
12. Change line 160 of "...\\Python3XX\\Lib\\site-packages\\pyboof\\\_\_init\_\_.py" for:`    pbg.mmap_file = mmap.mmap(pbg.mmap_fid.fileno(), length=0)`
13. Download and unzip latest release version of AiWarmachine.
14. Download additional files from https://drive.google.com/drive/folders/1DJvlq9WAmmEEuNAgDuJHA60bm_lzKuBN?usp=share_link

Some other minor python packages might be missing from this list and you'll see an error message in the terminal.
Simply doing a `pip install` with the missing package name will install the right stuff.

# Launch
Simply double click on ./launch_aiwarmachine.bat on Windows or use ./launch_aiwarmachine.sh on Linux.

Check the wiki of this repository for more information.
