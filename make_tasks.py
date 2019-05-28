import value_init as VI
import parameter_config as PC

"""
This script will fill a file for each pkg defined in DC.taskTypes
If a file already exists it will only append to it, not overwrite it.
FORMAT per line: [Task, Task, ...]
"""


for pkg in PC.taskTypes:
    PC.make_tasks(pkg)
    # use this if you want to see the output
    # this was commented out because it is normally used on a server with no DISPLAY attached
    #VI.plot_task_parameters(pkg)


