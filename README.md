# AiWarmachine
A Warmachine (Privateer Press, MKIV) tabletop wargaming companion and nemesis application.

# Installation
1. Download and install Python >= 3.10 (https://www.python.org/downloads/).
2. Install numpy using pip in a cmd prompt: `pip install numpy`
3. Install PyQt6 using pip in a cmd prompt: `pip install PyQt6`
4. Install OpenCV using pip in a cmd prompt: `pip install opencv-python`
5. Install TensorFlow using pip in a cmd prompt: `pip install tensorflow`
6. Install TensorFlow using pip in a cmd prompt: `pip install vosk`
install piper.exe (https://github.com/rhasspy/piper)
install Java
install PyBoof
change line 160 if "...\Python311\Lib\site-packages\pyboof\__init__.py" for:    pbg.mmap_file = mmap.mmap(pbg.mmap_fid.fileno(), length=0)
7. Download and unzip latest release version of AiWarmachine.
8. Download additional files from https://drive.google.com/drive/folders/1DJvlq9WAmmEEuNAgDuJHA60bm_lzKuBN?usp=share_link

# Launch
At the moment, only an alpha version of the calibration dialog is available to test if all installation steps were done.
Simply double click on ./test/test_calibration.bat on Windows or use ./test/test_calibration.sh on Linux.

Check the wiki of this repository for more information.
