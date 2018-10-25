import sys
sys.path.append('../')
import value_init as VI


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





def main():
	# FIRST TIME EXECUTION:
	#	- generate tasks outside and just read from file on command filling the TASKS dict (load initial state)
	#
	# RESUME EXECUTION:
	# 	- load potential previous findings into attributes (load state)
	#
	# HAPPENS EVERY TIME
	# initialize distributor on target plattform
	# always generate numberOfMachines tasksets more than there are machines, s.t. the machines don't have to wait
	# 
	pass
	while True:
		# main programm loop
		# 	- read additional tasks from file if lists in TASKS become smaller than a certain threshold
		# 	- halt the execution and shutdown machines via kill_all_machines() or shut_down_all_machines()
		# 		kill_all_machines, unlike shut_down_all_machines, does not wait untill the execution of the current taskset is finished
		# 	- resume execution of the scheduled tasksets
		#	- a clean exit that aborts execution and saves current findings
		# once the length of the added jobs drops under a certain threshold, generate more sets and add them to the job_list in the distributor
		# 

		pass


if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		print('\nInterrupted')
		if session_type==sessions[0]:
			clean_function(42)
		#logger.error('##################################################')
		sys.exit(0)