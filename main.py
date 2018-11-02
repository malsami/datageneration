import sys

sys.path.append('../')
from signal import signal, alarm, SIGALRM
from distributor_service.distributor import Distributor
from distributor_service.monitors.dataGenerationMonitor import DataGenerationMonitor
import value_init as VI
from taskgen.task import Task
from taskgen.taskset import TaskSet
import copy
import parameter_config as PC

# this needs to be filled with generated tasks
TASKS = {'hey': [],
         'pi': [],
         'tumatmul': [],
         'cond_mod': [],
         'cond_42': []
         }

RUNNINGTASKSETS = {1: [],
            2: [],
            3: [],
            4: [],
            5: []
            }

CURRENTTASKSETSIZE = 1
RUNNING = True

# good (successful) tasksets, key represents the size of the taskset
TASKSETS = {1: [],
            2: [],
            3: [],
            4: [],
            5: []
            }

BADTASKSETS = {1: [],
               2: [],
               3: [],
               4: [],
               5: []
               }


# holds triples (numberOfTasksInJob, numberOfProcessedTasksInJob, [])
# elements of the list (third item) follow this format:
# (tasksetTries, {id : (Task, [Job]) })
# tasksetTries=0 if successful; Job=(startTime, exitTime, eventType)
MONITORLISTS = []

POSSIBLETASKSETS = {1: [],
               2: [],
               3: [],
               4: [],
               5: []
               }


def read_tasks(path='../datageneration/data_new_tasks_'):
    # read from file provided in 'path' and load into TASKS and BADTASKS above
    # possible format as string would be a tuple per line e.g.: ('hey', [Task, Task, ...])
    global TASKS

    for package in PC.taskTypes:
        with open(path + package) as task_file:
            for line in task_file:  # Every line is a list of tasks in this file
                task_list = eval(line)

                for taskString in range(len(task_list)):
                    task = Task(task_list[taskString])  # for readability
                    TASKS[package].append(task)


def read_tasksets(path = "unevaluated_taskset", resume_running_taskset = True):
    # read from file provided in 'path' and load into TASKS and BADTASKS above
    # possible format as string would be a tuple per line e.g.: (1, [Taskset, Taskset, ...])

    # Write the tasksets to the file in the format above before reading

    global TASKSETS
    global BADTASKSETS
    global RUNNINGTASKSETS

    for package in PC.taskTypes:
        with open(path) as tasket_file:
            for line in tasket_file:
                taskset_object = eval(line)
                size = taskset_object[0]
                taskset = taskset_object[1]

                # Whether we want to pick up where we were last writing or we want to read the marked files
                if resume_running_taskset:
                    RUNNINGTASKSETS[size].append(taskset)
                else:
                    if  evaluate_taskset(taskset):
                        TASKSETS[size].append(taskset)
                    else:
                        BADTASKSETS[size].append(taskset)


"""
    This function is for basic book-keeping and we will write the good,bad,and unevaluated tasksets into the appropriate
    files. 
"""
def write_tasksets_to_file(tasksetsAreEvaluated = False):


    if(tasksetsAreEvaluated):
        with open("data_bad_taskset", "w") as b_f:
            # Writing bad taskset into the file
            for element in BADTASKSETS.items():
                b_f.write(str(element) + '\n')

        with open("data_good_taskset", "w") as g_f:
            # Writing good taskset into the file
            for element in TASKSETS.items():
                g_f.write(str(element) + '\n')
    else:
        with open("unevaluated_taskset", "w") as u_f:
            # Writing the tasksets which have not been evaluated yet
            for element in RUNNINGTASKSETS.items():
                u_f.write(str(element) + '\n')


""" Build the taskset list. 
	When building the taskset of size n, it will combine the taskset of size n-1 with the tasksets of 1
"""



def generate_possible_tasksets():
	# filling POSSIBLETASKSETS dictionary
    if CURRENTTASKSETSIZE == 1:
        for pkg in PC.taskTypes:
            raw_taskset = TaskSet(TASKS[pkg]) # Assign the tasks to a specific Taskset
            POSSIBLETASKSETS[1].append(raw_taskset)
    else:
        # Assuming we have already filled them

        for i in range(len(TASKSETS[1])):
            j = i # To avoid duplicate tasks
            for j in range(len(TASKSETS[CURRENTTASKSETSIZE - 1])):
                current_single_element = TASKSETS[1][i]
                current_multi_element = TASKSETS[CURRENTTASKSETSIZE - 1][j]
                combined_raw_taskset = current_single_element + current_multi_element
                POSSIBLETASKSETS[CURRENTTASKSETSIZE].append(copy.deepcopy(combined_raw_taskset))



def add_job(distributor, numberOfTasksets=1, tasksetSize=1):
    # adds a new job of length numberOfTasksets to the distributor and add the monitors list (triple) to MONITORLISTS
    # distributor.add_job([Taskset], DataGenerationMonitor)
    # the list is numberOfTasksets long and each Taskset consists of tasksetSize Tasks
    # otherwise, a new taskset is to be generated in its place
    # the outputlist of DataGenerationMonitor can be accessed via its 'out' attribute
    
    monitor = DataGenerationMonitor([])
    tasksetList = []
    # take numberOfTasksets Tasksets from POSSIBLETASKSETS and add them to tasksetList
    for i in range(numberOfTasksets):
    	try:
    		tasksetList += POSSIBLETASKSETS[tasksetSize].pop()
    		# add them also to RUNNINGTASKSETS
    		RUNNINGTASKSETS[tasksetSize].append(tasksetList[-1])
    	except IndexError:
    		break
    distributor.add_job(tasksetList, monitor)
    MONITORLISTS.append((len(tasksetList), 0, monitor.out))


def check_monitors():
    # this processes the MONITORLISTS
    global MONITORLISTS
    indicesToBeRemoved = []
    for index in range(len(MONITORLISTS)):
        if MONITORLISTS[index][0] == MONITORLISTS[index][1]:  # numberOfTasksInJob == numberOfProcessedTasksInJob
            indicesToBeRemoved.append(index)
        elif MONITORLISTS[index][2]:  # check if new finished taskset
            try:
                while True:  # until empty:
                    # pop first element and sort into correct attribute
                    taskset = MONITORLISTS[index][2].pop(0)
                    evaluate_taskset(taskset)
                    # increment MONITORLISTS[index][1] which is numberOfProcessedTasksInJob
                    MONITORLISTS[index][1] += 1
            except IndexError:
                continue
    for i in indicesToBeRemoved.sort(
            reverse=True):  # so we dont have to worry about messing the indices up when deleting elements
        del MONITORLISTS[i]


def evaluate_taskset(taskset):
    # This will evaluate the provided taskset and sort it into the according attribute
    successful = True
    tasksetSize = 0
    for task in taskset:
    	tasksetSize += 1
    	for job in task['jobs']:
    		successful = successful and job[2] == 'EXIT'
    if successful:
    	TASKSETS[tasksetSize].append(taskset)
    else:
    	BADTASKSETS[tasksetSize].append(taskset)
    RUNNINGTASKSETS[tasksetSize].remove(taskset)


def currentTasksetSizeExhauseted():
    if not POSSIBLETASKSETS[CURRENTTASKSETSIZE]:
    	CURRENTTASKSETSIZE += 1
    	generate_possible_tasksets()
    	if not POSSIBLETASKSETS[CURRENTTASKSETSIZE]:
    		RUNNING = False


def main(initialExecution=True):
    global CURRENTTASKSETSIZE
    # FIRST TIME and RESUME: only one of the two will be executed
    if initialExecution:
        # FIRST TIME EXECUTION:
        #	- generate tasks outside and just read from file, on command filling the TASKS dict (load initial state)
        read_tasks()
    else:
        # RESUME EXECUTION:
        # 	- load potential previous findings into attributes (load state)
        read_tasks('providing path to previous saved data')  # provide filepath as argument
        read_tasksets('providing path to previous saved data')  # provide filepath as argument
        CURRENTTASKSETSIZE = 1  # derive from read data

    # HAPPENS EVERY TIME
    # initialize distributor on target plattform
    distributor = Distributor(max_machine=PC.numberOfMachinesToStartWith, session_type=PC.sessionType,
                              max_allowed=PC.maxAllowedNumberOfMachnes, logging_level=PC.loggingLevel,
                              startup_delay=PC.delayAfterStartOfGenode, set_tries=PC.timesTasksetIsTriedBeforeLabeldBad,
                              timeout=PC.genodeTimeout)

    # always generate PC.maxAllowedNumberOfMachnes tasksets, s.t. the machines don't have to wait
    # have at least two jobs in the queue for continous execution
    add_job(distributor=distributor, numberOfTasksets=PC.maxAllowedNumberOfMachnes, tasksetSize=CURRENTTASKSETSIZE)
    # add triple to MONITORLISTS after adding a new job
    # creating a signal for alarm - will be called upton alarm
    signal(SIGALRM, lambda x, y: 1 / 0)
    # have output to explain controll options
    inputMessage = 'THIS IS THE TEXT THAT IS SHOWN EACH TIME AN ACTION CAN BE PERFORMED.'
    print(inputMessage)
    option = ''
    while RUNNING:
        # main programm loop
        # wait for input:
        try:
            alarm(30)  # argument should be a variable
            option = input()
        except ZeroDivisionError:
            option = ''
        # act depending on option provided
        if option == 'rt':
            # read additional tasks from file if lists in TASKS become smaller than a certain threshold (for that output the length of the tasklists on command, then make adding more available)
            print('show current length of all tasks lists(each pkg)')
            print('offer to read more lines from according file')
            print(inputMessage)
        elif option == 'cs':
            # change(increase) the current size of the tasksets to be executed
            print(inputMessage)
        elif option == 'h':
            # halt the execution and shutdown machines via kill_all_machines() or shut_down_all_machines()
            #	kill_all_machines, unlike shut_down_all_machines, does not wait untill the execution of the current taskset is finished
            print(inputMessage)
        elif option == 'r':
            # resume execution of the scheduled tasksets
            print(inputMessage)
        elif option == 's':
            # save current progress to file TODO: more thinking about continous execution and saving data
            print(inputMessage)
        elif option == 'x':
            # a clean exit that aborts execution and saves current findings and clean up if qemusession
            pass
        elif option == '':
            pass
        else:
            print(option, 'was not a possible option!')
            print(inputMessage)

        # unrelated to user input:
        check_monitors()  # check if a taskset is finished and put it into according attribute
        currentTasksetSizeExhauseted()  # increments CURRENTTASKSETSIZE if current size is exhausted
        if len(RUNNINGTASKSETS[CURRENTTASKSETSIZE]) < PC.maxAllowedNumberOfMachnes * 2:
    		add_job(distributor=distributor, numberOfTasksets=PC.maxAllowedNumberOfMachnes, tasksetSize=CURRENTTASKSETSIZE)
    # end of while

        # when finished save all data to textfile or pickle it to a file adjust read_tasks and read_tasksets accoringly
        # including TASKS, BADTASKS, TASKSETS, BADTASKSETS


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nInterrupted')
        if PC.sessionType == 'QemuSession':
            clean_function(42)
        # logger.error('##################################################')
        sys.exit(0)
