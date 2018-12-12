# datageneration
This repository contains scripts and other files associated with the projects data generation.

## make\_tasks.py

This calls a helper function in the *parameter\_config.py* to generate a file per task type defined in the *parameter\_config.taskTypes*. Each file consists of *parameter\_config.linesPerCall* lines and each line is a list of hash values with *parameter\_config.tasksPerLine* values.

## main.py

The *main.py* can be called without argument, but for each task in *parameter\_config.taskTypes* there has to exist a file (created by executing *make\_tasks.py*). *main.py* can also be called with the argument **c** to continue the execution with data loaded from the following files: *bad\_tasksets*, *good\_tasksets* and, if available, *possible\_tasksets*. These contain information gained by a previous execution of *main.py*.

Other options: 

**ss** - 'Show Status'. Print current status of the data generation and the current length of all the task lists

**h** - Halt Machines

**k** - Kill all Machines 

**s** - Save current progress

**x** - Clean exit 



## Helper Functions

### parameter\_config.py

This file contains all the parameters of the variables and data structure we use for the data generation. 

Parameter are randomly chosen within a range of suitable values. ("Priority": (1,5) indicates that a random task will be generated with a random value between 1 and 5. ) This file is referenced numerous time in the data creation while specifying parameters. 

For easy book-keeping and facilitated reading and writing to file, the parameters are stored in a concatenated strings before the main task generation is made. This ensure uniqueness and also an easy reference to the tasks and the tasksets. 



### value\_init.py

This file will initiate the values of the tasks according to the parameter values in parameter_config. This creates the Task object as a list of dictionaries. This package is called from make\_takss.py and with the appropriate parameters which include the number of tasks to make and the package. Depending on the package chosen, the appropriate package will be populated with the selected number of tasks chosen. 

Additionally, this file provides functions for plotting the distribution of the parameters of the tasksets. 

