# SegmentDeshuffle
This repo is for distributing the source code and instructions for use of the the SegmentDeshuffle.exe and compilation instructions.

# How does this bug present itself?
The segment shuffle presents itself within continuous data files. The data packets in .nsx files will be packaged out of order for a ~30 samples for every ~30 minutes of recording in 30 kHz data, but this can vary. The data within the packets is valid. The timestamp in the packet header is also valid. However, if you analyze saved data without explicitly controlling the data index by the data timestamp and instead rely on the index on saved file, your analyses may be off.

# Am I affected by the Segment Shuffle bug?
You may be affected if:
* You saved continuous data (*.ns1-6) using Gemini Hubs with firmware 7.6.0, 7.6.1, and 7.6.1.1.
* You used File Spec 3.0.

You are more likely to be affected if:
* You recorded data with a high-channel count hub, such as a 1-256ch or 257-512ch model.
* You have a configuration where you detect many spikes, such as when you keep the spike threshold within the noise band.

# What does the SegmentDeshuffle tool do?
`SegmentDeshuffle.exe` is an appication built in python. The tool will do the following:
* Scan a saved file and will notify you if segment shuffles have been found.
* If shuffles are found, the tool will ask the user to create a new file.
* The application will scan through the shuffles and properly order them in the file created by the application.
* The tool will also tell you if it found out of order packets, but not in a way that is predicatble, which may occur if your data is corrupted.

# How do I use the SegmentDeshuffle tool? 
`SegmentShuffle.exe` is currently only packaged as a Windows .exe executable. However, with this source code, it should be straightforward to modify compilation for other operating systems like Linux or MAC. The compiling tool, `pyinstaller`, has default behavior where it should recognize your operating system and create an application that functions within that operating system.

## How do I use the unmodified application?
To use the Windows `SegmentShuffle.exe`, find the executable available for download in the repo's "Releases" section. Double click the executable in its saved location.

## What if I don't want to use an application?
Users who have python workflows in their data analyses can wrap the two `.py` files in this repo into their workflows.

## How do I make a new application that differs from what is released?
To compile modified code for your own workflows as a custom application, use the following steps:
1. Create a virtual python environment or create a python project in your python IDE of your choice. Clone this repo into the environment/project.
2. Modify `main.py` with your desired edits.
3. Assure the python package `pyinstaller` is within the path.
4. In a terminal or command prompt, `cd` to `[path]` where `helper.py` and `main.py` are contained.
5. From there, execute the following code:
    ```
    C:\[path]> pyinstaller -F main.py -n SegmentDeshuffle -c
    ```
6. Locate the associated `.\dist` folder. The executable will be there. Note: you can rename the executable to your liking by changing `SegmentDeshuffle` to a name of your choosing.
