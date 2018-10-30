import value_init as VI
import parameter_config as PC

"""
This script will fill a file for each pkg defined in DC.taskTypes
If a file already exists it will only append to it, not overwrite it.
"""


for pkg in PC.taskTypes:
	tasks = ''
	for i in range(6):
		tasks += str(VI.generate_tasks_of_type(PC.tasksPerLine, pkg, PC.taskParameters)[pkg])+'\n'
	with open('./data_new_tasks_'+pkg, 'a') as file:
		file.write(tasks)