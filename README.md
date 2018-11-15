# datageneration
This repository contains scripts and other files associated with the projects data generation.

## make\_tasks.py

This calls a helper function in the *parameter\_config.py* to generate a file per task type defined in the *parameter\_config.taskTypes*. Each file consists of *parameter\_config.linesPerCall* lines and each line is a list of hash values with *parameter\_config.tasksPerLine* values.

## main.py

The *main.py* can be called without argument, but for each task in *parameter\_config.taskTypes* there has to exist a file (created by executing *make\_tasks.py*). *main.py* can also be called with the argument **c** to continue the execution with data loaded from the following files: *bad\_tasksets*, *good\_tasksets* and, if available, *possible\_tasksets*. These contain information gained by a previous execution of *main.py*.

## Helper Functions

### parameter\_config.py

what is done here

### value\_init.py

what is done here
