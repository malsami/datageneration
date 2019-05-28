import sys
sys.path.append('../')
import logging
import value_init as VI
from taskgen.taskset import TaskSet
# these are parameters to configure the distributor
'''
QemuSession: is for QEMU based boards, normally on the same host as this programm
PandaSession: is for Pandaboards in use with a Mikrotik Switch which is capable of the commands written in "poe_on/off.sh" at the malsami/distributor repository
Rasberry2/3Session: are for the Raspberry Pis, restrictions as stated for Pandaboards
'''

availableSessions = ['QemuSession','PandaSession','Raspberry2Session','Raspberry3Session']


#Machines in the cluster (for Raspberry Pis we had 20 for PandaSession we had less)
numberOfMachinesToStartWith = 20
maxAllowedNumberOfMachines = 20
loggingLevel = logging.DEBUG
delayAfterStartOfGenode = 60
timesTasksetIsTriedBeforeLabeldBad = 2
genodeTimeout = 30
savedEveryNLaps = 90 # times 10s, so one save every 15 min

# Setting the SessionType to the above defined Raspberry2Session
sessionType = availableSessions[2]
taskTypes = ['hey', 'pi', 'tumatmul', 'cond_mod'] # to use all available task types use the following list instead:['hey', 'pi', 'tumatmul', 'cond_mod', 'cond_42']

tasksPerLine = 100 # number of tasks put in one list
linesPerCall = 1 # lines per file written in one execution

taskParameters = {	'PKG': # maximum possible amount of distinct tasksets is 11664
						{1:'hey',
						 2:'pi',
						 3:'tumatmul',
						 4:'cond_mod'#,
						 #5:'cond_42'
						},
				'PRIORITY': (1,5),#127), # think we can put constraint on this and just provide maybe 5 different values, so values appear more often and in the end with fp scheduling only the difference should matter(?)
				'DEADLINE' : (0, 0),
				'PERIOD': (1,8),
				'CRITICALTIME' : (0, 0), # is assigned by function depending on PERIOD
				'NUMBEROFJOBS': (1,8),#(1,10),
				'OFFSET': (0,0),
				# This is the RAM Quota of the tasks, it is set to 100MB and might be way overdimensional. For comparison it was kept this high but might have to be reconsidered
				'QUOTA': (100, 100), #(1, 100),# we could just assign arbitrary big values to this and to caps as well, cause a working task, which is the assumption for an initial taskset, would have good values for that and both (caps and ram) are available in abundance 
				'CAPS': (235, 235), #(10, 235)
				'CORES' : (0, 0),
				'COREOFFSET' : (0, 0),
				'ARG':
						{'hey':(0,0),#23-28
						'pi':(13,21),#84-1600
						'tumatmul':(12,19),#104-2700
						'cond_mod':(25,30)#,#130-3000
						#'cond_42':(2,4)
						}
				}

PKGTOINT = {'hey' : 1,
			'pi' : 2,
			'tumatmul' : 3,
			'cond_mod' : 4#,
			#'cond_42' : 5
			}

PARAMETERINHASH = { # (start, numberOfDigits)
					'PKG' : (0, 1),
					'PRIORITY' : (1, 3),
					'DEADLINE' : (4, 5),
					'PERIOD' : (9, 5),
					'CRITICALTIME' : (14, 5),
					'NUMBEROFJOBS' : (19, 3),
					'OFFSET' : (22, 5),
					'QUOTA' : (27, 3),
					'CAPS' : (30, 3),
					'CORES' : (33, 2),
					'COREOFFSET' : (35, 2),
					'ARG' : (37, 15)
}

HASH_LENGTH_PER_TASK = 52

def get_taskset_size(hash_value):
	return int(len(hash_value)/HASH_LENGTH_PER_TASK)

def get_taskset_hash(taskset):
	# returns a string containing 52 digits per task
	hash_value = ''
	for task in taskset:
		hash_value += get_task_hash(task)
	return hash_value

def get_task_hash(task):
	# returns a string containing 52 digits per task
	hash_value = ''
	hash_value += str(PKGTOINT[task['pkg']])
	hash_value += str(task['priority']).zfill(3) #fine
	hash_value += str(task['deadline']).zfill(5)
	hash_value += str(task['period']).zfill(5)
	hash_value += str(task['criticaltime']).zfill(5)
	hash_value += str(task['numberofjobs']).zfill(3)
	hash_value += str(task['offset']).zfill(5)
	hash_value += task['quota'][:-1].zfill(3)
	hash_value += str(task['caps']).zfill(3)
	hash_value += str(task['cores']).zfill(2)
	hash_value += str(task['coreoffset']).zfill(2)
	hash_value += str(task['config']['arg1']).zfill(15)# todo, can be much bigger
	
	return hash_value


def hash_to_taskset(hash_value):
	taskset = TaskSet([])
	for i in range(int(len(hash_value)/HASH_LENGTH_PER_TASK)):
		hash_offset = i*HASH_LENGTH_PER_TASK
		pkg = taskParameters['PKG'][int(hash_value[hash_offset : hash_offset +1])]
		priority = int(hash_value[hash_offset +1:hash_offset +4])
		deadline = int(hash_value[hash_offset +4:hash_offset +9])
		period = int(hash_value[hash_offset +9:hash_offset +14])
		criticaltime = int(hash_value[hash_offset +14:hash_offset +19])
		numberofjobs = int(hash_value[hash_offset +19:hash_offset +22])
		offset = int(hash_value[hash_offset +22:hash_offset +27])
		quota = int(hash_value[hash_offset +27:hash_offset +30])
		caps = int(hash_value[hash_offset +30:hash_offset +33])
		cores = int(hash_value[hash_offset +33:hash_offset +35])
		coreoffset = int(hash_value[hash_offset +35:hash_offset +37])
		arg = int(hash_value[hash_offset +37:hash_offset +52])
		taskset.append(VI.create_task(input_pkg=pkg, input_priority=priority, input_deadline=deadline, input_period=period, input_criticaltime=criticaltime, input_numberofjobs=numberofjobs, input_offset=offset, input_quota=quota, input_caps=caps, input_cores=cores, input_coreoffset=coreoffset, input_arg1=arg))
	return taskset


def make_tasks(pkg):
	tasks = ''
	for i in range(linesPerCall):
		tasks += str([get_task_hash(task) for task in VI.generate_tasks_of_type(tasksPerLine, pkg, taskParameters)[pkg]])+'\n'
	with open('./data/new_tasks_'+pkg, 'a') as file:
		file.write(tasks)
