import sys
sys.path.append('../')
import logging
import value_init as VI
from taskgen.taskset import TaskSet
# these are parameters to configure the distributor
availableSessions = ['QemuSession','PandaSession']
sessionType = availableSessions[0]

numberOfMachinesToStartWith = 1
maxAllowedNumberOfMachines = 1
loggingLevel = logging.DEBUG
delayAfterStartOfGenode = 60
timesTasksetIsTriedBeforeLabeldBad = 2
genodeTimeout = 30


taskTypes = ['hey'] # to use all available task types use the following list instead:['hey', 'pi', 'tumatmul', 'cond_mod', 'cond_42']

tasksPerLine = 100 # number of tasks put in one list
linesPerCall = 6 # lines per file written in one execution

taskParameters = {	'PKG':
						{1:'hey',
						 2:'pi',
						 3:'tumatmul',
						 4:'cond_mod',
						 5:'cond_42'
						},
				'ARG':
						{'hey':(0,1),#23-28
						'pi':(13,21),#84-1600
						'tumatmul':(12,19),#104-2700
						'cond_mod':(25,30),#130-3000
						'cond_42':(2,4)
						},
				'PRIORITY': (1,127), # think we can put constraint on this and just provide maybe 5 different values, so values appear more often and in the end with fp scheduling only the difference should matter(?)
				'PERIOD': (1,8),
				'OFFSET': (0,1),
				'NUMBEROFJOBS': (1,1),#(1,10),
				'QUOTA': (100, 100), #(1, 100),# we could just assign arbitrary big values to this and to caps as well, cause a working task, which is the assumption for an initial taskset, would have good values for that and both (caps and ram) are available in abundance 
				'CAPS': (235, 235) #(10, 235)
				}

PKGTOINT = {'hey' : 1,
			'pi' : 2,
			'tumatmul' : 3,
			'cond_mod' : 4,
			'cond_42' : 5
			}
HASH_LENGTH_PER_TASK = 31

def get_taskset_size(hash_value):
	return len(hash_value)/HASH_LENGTH_PER_TASK

def get_taskset_hash(taskset):
	# returns a string containing 31 digits per task
	hash_value = ''
	for task in taskset:
		hash_value += get_task_hash(task)
	return hash_value

def get_task_hash(task):
	# returns a string containing 31 digits per task
	hash_value = ''
	hash_value += str(PKGTOINT[task['pkg']])
	hash_value += str(task['config']['arg1']).zfill(2)
	hash_value += str(task['priority']).zfill(3)
	hash_value += str(task['period']).zfill(5)
	hash_value += str(task['offset']).zfill(5)
	hash_value += str(task['numberofjobs']).zfill(3)
	hash_value += task['quota'][:-1].zfill(4)
	hash_value += str(task['caps']).zfill(3)
	hash_value += str(task['criticaltime']).zfill(5)
	return hash_value


def hash_to_taskset(hash_value):
	taskset = TaskSet([])
	for i in range(int(len(hash_value)/31)):
		hash_offset = i*31
		pkg = taskParameters['PKG'][int(hash_value[hash_offset : hash_offset +1])]
		arg = int(hash_value[hash_offset +1:hash_offset +3])
		priority = int(hash_value[hash_offset +3:hash_offset +6])
		period = int(hash_value[hash_offset +6:hash_offset +11])
		offset = int(hash_value[hash_offset +11:hash_offset +16])
		numberofjobs = int(hash_value[hash_offset +16:hash_offset +19])
		quota = int(hash_value[hash_offset +19:hash_offset +23])
		caps = int(hash_value[hash_offset +23:hash_offset +26])
		criticaltime = int(hash_value[hash_offset +26:hash_offset +31])
		# print('Task {}:\npkg: {},\narg: {},\npriority: {},\nperiod: {},\noffset: {},\nnumberofjobs: {},\nquota: {},\ncaps:{}'.format(i,pkg,arg,priority,period,offset,numberofjobs,quota,caps))
		taskset.append(VI.create_task(s_pkg='pkg', s_arg1=arg, s_criticaltime=criticaltime, s_numberofjobs=numberofjobs, s_offset=offset, s_period=period, s_priority=priority, s_quota=quota, s_caps=caps))
	return taskset

