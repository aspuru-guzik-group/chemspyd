chemspeed_controller.py and Manager.app
=======================================


chemspeed_controller.py
-----------------------

# Python dependencies
- Python 3.6 and above

# importing chemspeed_controller
- you have 3 methods, each detailed as below

# Usage
- execute the Manager.app first.
- please see test_example.py
- you should be able to import Controller from pylab.instruments
- initiate Controller() and run commands
- use test_example.py for reference


## importing all together in the pylab module
- you will need the system environment to have PYTHONPATH added with PythonLab
    - add Dropbox/PythonLab/
    - windows and linux system have different methods off adding system variables, check online
- you will also need to install the correct conda enviroment
- check PythonLab/packages/setup.py (probably not complete)
- in your script:
    - `from pylab.instruments import Controller`

## adding new paths through sys.path.append
- python can add system paths on the fly
- `import sys; sys.path.append('/your/path/to/folder/'); from chemspeed_controller import Controller`
- Note: you can split `;` above into new lines

## adding new paths permenantly through your system
- you can add the path Dropbox/PythonLab/pylab/chemspeed_controller/ to system enviroment
    - windows and linux system have different methods off adding system variables, check online
- in your script:
    - `from pylab.instruments import Controller`


Manager.app
-----------

# Install Autosuite
- Download and install the AutoSuite software

# Configuration of your Chemspeed
- Extract T101 from Chemspeed.zip -> autosuite -> configurations
- This should normally be under Destop/Chemspeed/Configuration/T101
- Open AutoSuite Configuration Manager (Desktop)
- In Configurations tab, you could create a new configure by new.
- Use add existing folder, point to the T101 path

# Using the app
- Open `Manager.app` (may need to select `Program Files (x86)/Chemspeed/AutoSuite/Bin/AutoSuiteEditor.exe`)
- On the top, press the little T in the toolbar to switch to task view.
- In the first line under the Manager, set the `command_path` variable to a folder that will listen for commands.
- This folder should be the same in the `ChemspeedManager(cmd_folder)`.
- Folder can be empty
- Save the app; then press the triangle play button on top with "S" in it. This will open the AutoSuite Executor.
- Press "Start" button, and wait until it stop in a loop.
- To see the actions, press "Visualization" tab in the Executor to see the arm movement. You can also check temperature, pressure etc.
- Run the example: `python example.py` (remember to set to the same path)
- Happy coding!

# Add new function
- Task 1.7.1 is the macro that reads the command name, the rest are the command execution macro
- First create a macro (preferable with the same command name for clarity)
    - you can copy `stop_manager()`
- In the new macro, under execute if condition, set `command = 'your_comamand_name'`
- If you want to import extra arguments, you can see the example from set_isynth_vacuum
    - you need to define the variable to imported in the macro
    - then import using the 'import csv' task
    - the order of the import in csv needs to be the same order in the python manager class method
- If you need to import zone variables, take a look at task set_drawer
    - you need create both zone (Zone) and zone_text (String)
    - in the csv, import as zone_text
    - use get_zone to convert zone_text to zone
- Create a same class method in Controller, and define the argument and preprocess in the method
    - in the execute, it is important to use the same command name for easy code management
    - remember to add doc strings
    - the order of the import in csv needs to be the same order in the python manager class method
- for every new arguments added, we need to:
    - declare in the task/command macro (with correct unit, and unit type)
    - (if it is zone, you need to call get_zone to convert text to zone)
    - put the variable into your task (or use it in any way you want)
    - put the variables in the python controller new method (you can put in the default value here)
    - import the values to chemspeed variables in the import csv task. the order here is important!
- test it first in simulation if it behaves like what you expect
