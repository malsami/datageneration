import sys
sys.path.append('../')
import value_init as VI
import distributor_config as DC


# this needs to be filled with generated tasks
TASKS = { 'hey':[],
            'pi':[],
            'tumatmul':[],
            'cond_mod':[],
            'cond_42':[]
            }

# this will be filled throughout execution / can be used as lookup to avoid generating additional bad set, which were already executed
BADTASKS = { 'hey':[],
            'pi':[],
            'tumatmul':[],
            'cond_mod':[],
            'cond_42':[]
            }

# good (successful) tasksets, key represents the size of the taskset
TASKSETS = {1:[],
            2:[],
            3:[],
            4:[],
            5:[]
            }

BADTASKSETS = { 1:[],
				2:[],
				3:[],
				4:[],
				5:[]
				}


APPLICABLE_TASKTYPES = DC.taskTypes # should be filled with the string literals ('hey', 'pi',...) of the task types, which shhould be used

MONITORLISTS = [] #holds triples (numberOfTasksInJob, numberOfProcessedTasksInJob, [])

def read_tasks(path='../datageneration/new_tasks'):
	# read from file provided in 'path' and load into TASKS and BADTASKS above
	# possible format as string would be a tuple per line e.g.: ('hey', [Task, Task, ...])
	pass


def read_tasksets(path):
	# read from file provided in 'path' and load into TASKS and BADTASKS above
	# possible format as string would be a tuple per line e.g.: (1, [Taskset, Taskset, ...])
	pass


def generate_job(numberOfTasksets=1, tasksetSize=1):
	# returns the parameters for a distributor job as a tuple: ([Taskset], ValueTestingMonitor)
	# [Taskset] is a new list of tasksets
	# the list is numberOfTasksets long and each Taskset consists of tasksetSize Tasks
	# only new Tasksets (not contained in TASKSETS nor in BADTASKSETS) should be included
	# otherwise, a new taskset is to be generated in its place
	# the outputlist of ValueTestingMonitor can be accessed via its 'out' attribute
	pass


def check_monitors():
	# this processes the MONITORLISTS
	indicesToBeRemoved = []
	for index in range(len(MONITORLISTS)): 
		if MONITORLISTS[index][0]==MONITORLISTS[index][1]: #numberOfTasksInJob == numberOfProcessedTasksInJob
			indicesToBeRemoved.append(index)
		elif MONITORLISTS[index][2]: # check if new finished taskset
			# until empty:
			# 	pop first element and sort into correct attribute
			# 	increment MONITORLISTS[index][1] which is numberOfProcessedTasksInJob
	for i in indicesToBeRemoved.sort(reverse=True): # so we dont have to worry about messing the indices up when deleting elements
		del MONITORLISTS[i]
	pass


def main():
	# FIRST TIME and RESUME: only one of the two will be executed
	# FIRST TIME EXECUTION:
	#	- generate tasks outside and just read from file, on command filling the TASKS dict (load initial state)
	currentTasksetSize = 1
	read_tasks()

	# RESUME EXECUTION:
	# 	- load potential previous findings into attributes (load state)
	currentTasksetSize = # provide an value as arg
	read_tasks('providing path to previous saved data') # provide filepath as argument
	read_tasksets('providing path to previous saved data') # provide filepath as argument

	# HAPPENS EVERY TIME
	# initialize distributor on target plattform
	distributor = Distributor(max_machine=DC.numberOfMachinesToStartWith, session_type=DC.sessionType, max_allowed=DC.maxAllowedNumberOfMachnes, logging_level=DC.loggingLevel, startup_delay=DC.delayAfterStartOfGenode, set_tries=DC.timesTasksetIsTriedBeforeLabeldBad, timeout=DC.genodeTimeout)

	# always generate DC.maxAllowedNumberOfMachnes tasksets, s.t. the machines don't have to wait
	# have at least two jobs in the queue for continous execution
	newJob = generate_job(numberOfTasksets=DC.maxAllowedNumberOfMachnes, tasksetSize=2)
	#add triple to MONITROLISTS after adding a new job
	pass
	while True:
		# main programm loop
		# have output to explain controll options
		# 	- read additional tasks from file if lists in TASKS become smaller than a certain threshold (for that output the length of the tasklists on command, then make adding more available)
		# 	- change(increase) the current size of the tasksets to be executed
		# 	- halt the execution and shutdown machines via kill_all_machines() or shut_down_all_machines()
		# 		kill_all_machines, unlike shut_down_all_machines, does not wait untill the execution of the current taskset is finished
		# 	- resume execution of the scheduled tasksets
		#	- a clean exit that aborts execution and saves current findings
		# unrelated to user input:
		#	- check if a taskset is finished and put it into according attribute
		#	- once the length of the added jobs (can check MONITORLISTS) drops under a certain threshold, generate more jobs and add them to the job_list in the distributor
		#	- once all possible combinations of tasks or tasksets are exhausted, increase the level of tasks per set(check by total number of TASKSETS and BADTASKSETS for that length and compare to combinatorial value from length below (length of tasks for tasksetsize=1))

		pass
	# when finished save all data to textfile or pickle it to a file adjust read_tasks and read_tasksets accoringly
	# including TASKS, BADTASKS, TASKSETS, BADTASKSETS


if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		print('\nInterrupted')
		if session_type==sessions[0]:
			clean_function(42)
		#logger.error('##################################################')
		sys.exit(0)