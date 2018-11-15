import value_init as VI
import parameter_config as PC

"""
This script will fill a file for each pkg defined in DC.taskTypes
If a file already exists it will only append to it, not overwrite it.
FORMAT per line: [Task, Task, ...]
"""


for pkg in PC.taskTypes:
    PC.make_tasks(pkg)
    VI.plot_task_parameters(pkg)


