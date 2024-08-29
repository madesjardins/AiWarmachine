# AiWarmachine
A Warmachine (SteamForged Games, MKIV) tabletop wargaming companion and nemesis application.
Currently, you can use the app to calibrate your camera and projector, set table dimensions and scan MicroQR codes.

# Installation
1. Install Python >= 3.10 (https://www.python.org/downloads/).
2. Install numpy using pip in a cmd prompt: `pip install numpy`
3. Install PyQt6 using pip in a cmd prompt: `pip install PyQt6`
4. Install OpenCV using pip in a cmd prompt: `pip install opencv-python`
5. Install sounddevice using pip in a cmd prompt: `pip install sounddevice`
6. Install pygame using pip in a cmd prompt: `pip install pygame`
7. Install Vosk using pip in a cmd prompt: `pip install vosk`
8. Install piper.exe (https://github.com/rhasspy/piper)
9. Install Java (https://www.java.com/en/download/)
10. Install PyBoof using pip in a cmd prompt: `pip install pyboof`
11. Change line 160 of "...\\Python3XX\\Lib\\site-packages\\pyboof\\\_\_init\_\_.py" for:`    pbg.mmap_file = mmap.mmap(pbg.mmap_fid.fileno(), length=0)`
12. Download and unzip latest release version of AiWarmachine.
13. Download additional files from https://drive.google.com/drive/folders/1DJvlq9WAmmEEuNAgDuJHA60bm_lzKuBN?usp=share_link

# Launch
Simply double click on ./launch_aiwarmachine.bat on Windows or use ./launch_aiwarmachine.sh on Linux.

Check the wiki of this repository for more information.
