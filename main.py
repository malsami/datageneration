import sys
sys.path.append('../')
from signal import signal, alarm, SIGALRM
from distributor_service.distributor import Distributor
from distributor_service.monitors.dataGenerationMonitor import DataGenerationMonitor
from distributor_service.clean import clean_function
import value_init as VI
from taskgen.task import Task
from taskgen.taskset import TaskSet
from random import shuffle
import parameter_config as PC

# this needs to be filled with generated tasks

CURRENTTASKSETSIZE = 1
HALT = False
RUNNING = True
WAITING = False
FINISHED = False

# good (successful) tasksets, key represents the size of the taskset
# list elements are tuples: (bool, TaskSet)
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

#list elements are task hashes
TASKS = {'hey': [],
         'pi': [],
         'tumatmul': [],
         'cond_mod': [],
         'cond_42': []
         }

# holds triples as list [numberOfTasksInJob, numberOfProcessedTasksInJob, [Taskset]]
# tasksetTries=0 if successful; Job=[startTime, exitTime, eventType]
MONITORLISTS = []

# list of taskset hashes
POSSIBLETASKSETS = []

# list of TaskSet objects
RUNNINGTASKSETS = []


def load_tasks(path='./data_new_tasks_'):
    # read from file provided in 'path' for each pkg in PC.taskTypes and load into TASKS
    # format per line in file e.g.: [task_hash, task_hash, ...]
    global TASKS

    for package in PC.taskTypes:
        with open(path + package) as task_file:
            for line in task_file:  # Every line is a list of tasks in this file
                TASKS[package] += eval(line)


def load_tasksets(include_possibilities=True):
    # read from file provided in 'path' and load into TASKS and BADTASKS above
    # possible format as string would be a tuple per line e.g.: (1, [Taskset, Taskset, ...])

    # Write the tasksets to the file in the format above before reading

    global TASKSETS
    global BADTASKSETS
    for option in ('good', 'bad'):
        with open('./data_{}_tasksets'.format(option), 'r') as taskset_file:
            for line in tasket_file:# line format: (int, [ (bool,[{}]) ] )
                level, tasksetList = eval(line)# level indicates size of tasksets
                for successful, tasksetInfo in tasksetList:
                    taskset = TaskSet([])
                    for taskDict in tasksetInfo:
                        taskset.append(Task(taskDict))
                    if successful:
                        TASKSETS[level].append((successful,taskset))
                    else:
                        BADTASKSETS[level].append((successful,taskset))
    if include_possibilities:
        global POSSIBLETASKSETS
        with open('./data_possible_tasksets','r') as taskset_file:
            for line in taskset_file:# format: [taskset_hash], taskset_hash is type string
                POSSIBLETASKSETS += eval(line)



"""
    This function is for basic book-keeping and we will write the good,bad,and unevaluated tasksets into the appropriate
    files. 
"""


def write_tasksets_to_file(save_possibilities=False):# should only be True if execution aborts
    with open("./data_bad_tasksets", "w") as bad_f:# each line is (int, [ (bool,[{}]) ] )
        # Writing bad taskset into the file
        for element in BADTASKSETS.items():
            bad_f.write(str(element) + '\n')
    with open("./data_good_tasksets", "w") as good_f:# each line is (int, [ (bool,[{}]) ] )
        for element in TASKSETS.items():
            good_f.write(str(element) + '\n')
    if save_possibilities:
        with open("./data_possible_tasksets", "w") as possible_f: # each line is [taskset_hash], taskset_hash is a string
            # Writing the tasksets which have not been evaluated yet beack into possibilities and then save
            POSSIBLETASKSETS += [PC.get_taskset_hash(taskset) for taskset in RUNNINGTASKSETS]
            possible_f.write(str(POSSIBLETASKSETS) + '\n')
                

""" Build the taskset list. 
    When building the taskset of size n, it will combine the taskset of size n-1 with the tasksets of 1
"""


def generate_possible_tasksets():
    global POSSIBLETASKSETS
    # filling POSSIBLETASKSETS dictionary
    if CURRENTTASKSETSIZE == 1:
        for pkg in PC.taskTypes:
            POSSIBLETASKSETS += TASKS[pkg]
    else:
        for i in range(len(TASKSETS[1])):
            limiter = 0
            if CURRENTTASKSETSIZE == 2:
                limiter = i + 1
            for j in range(limiter, len(TASKSETS[CURRENTTASKSETSIZE - 1])):
                current_single_element = PC.get_taskset_hash(TASKSETS[1][i])
                current_multi_element = PC.get_taskset_hash(TASKSETS[CURRENTTASKSETSIZE - 1][j])
                POSSIBLETASKSETS.append(current_single_element+current_multi_element)
    shuffle(POSSIBLETASKSETS)


def add_job(distributor, numberOfTasksets=1, tasksetSize=1):
    # adds a new job of length numberOfTasksets to the distributor and add the monitors list (triple) to MONITORLISTS
    # distributor.add_job([Taskset], DataGenerationMonitor)
    # the list is numberOfTasksets long and each Taskset consists of tasksetSize Tasks
    # otherwise, a new taskset is to be generated in its place
    # the outputlist of DataGenerationMonitor can be accessed via its 'out' attribute

    monitor = DataGenerationMonitor([])
    tasksetList = []
    # take numberOfTasksets Tasksets from POSSIBLETASKSETS and add them to tasksetList
    for i in range(numberOfTasksets*6):
        try:
            taskset = POSSIBLETASKSETS.pop()
            if CURRENTTASKSETSIZE == 1:
                TASKS[PC.taskParameters['PKG'][int(taskset[:1])]].remove(taskset)
            tasksetList.append(PC.hash_to_taskset(taskset))
            # add them also to RUNNINGTASKSETS
            RUNNINGTASKSETS.append(tasksetList[-1])
        except IndexError:
            break
    distributor.add_job(tasksetList, monitor=monitor, is_list=True)
    MONITORLISTS.append([len(tasksetList), 0, monitor.out])


def check_monitors():
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
    indicesToBeRemoved.sort(reverse=True)
    for i in indicesToBeRemoved:  # so we dont have to worry about messing the indices up when deleting elements
        del MONITORLISTS[i]


def evaluate_taskset(taskset):
    global TASKSETS
    global BADTASKSETS
    global RUNNINGTASKSETS
    # This will evaluate the provided taskset and sort it into the according attribute
    #print('eval method')
    successful = True
    tasksetSize = 0
    for task in taskset:
        tasksetSize += 1
        for _, job in task['jobs'].items():
            successful = successful and job[2] == 'EXIT'
    if successful:
        TASKSETS[tasksetSize].append((successful, taskset))
    else:
        BADTASKSETS[tasksetSize].append((successful, taskset))
    RUNNINGTASKSETS.remove(taskset)


def currentTasksetSizeExhauseted():
    global POSSIBLETASKSETS
    global CURRENTTASKSETSIZE
    global RUNNING
    global WAITING
    RUNNING = not HALT and RUNNINGTASKSETS
    WAITING = not POSSIBLETASKSETS and RUNNING 
    if not POSSIBLETASKSETS and not RUNNINGTASKSETS:
        RUNNING = True
        CURRENTTASKSETSIZE += 1
        generate_possible_tasksets()
        if not POSSIBLETASKSETS:
            FINISHED = True



def show_status():
    #TODO show stats
    try:
        print('you can increase the current level (i) or if you are still on level 1 you can add more tasks for a pkg, just type name of one of these: {}'.format(PC.taskTypes))
        alarm(10)
        option = input()
        alarm(0)
        if option == 'i':
            #TODO increase current lvl MAYBE BY ENFORCING WAIT (only RUNNINGTASKSETS will be finished)
            return
        if CURRENTTASKSETSIZE == 1 and option in PC.taskTypes:
            if option == 'hey':
                pass
            elif option == 'pi':
                pass
            elif option == 'tumatmul':
                pass
            elif option == 'cond_42':
                pass
            elif option == 'cond_mod':
                pass
    except ZeroDivisionError:
        pass
    return


def halt_machines(distributor, hard=False):
    global HALT
    global RUNNINGTASKSETS
    global POSSIBLETASKSETS
    global MONITORLISTS
    HALT = True
    if hard:
        distributor.kill_all_machines()
    else:
        distributor.shut_down_all_machines()
    # ask if current running should be cleared (clear jobQueue)
    try:
        print('Do you also want to clear the current RUNNINGTASKSETS?[y/n]')
        alarm(10)
        option = input()
        alarm(0)
        if option == 'y':
            print('will clear distributor jobQueue, RUNNINGTASKSETS and MONITORLISTS...')
            # clear distributor jobsQueue
            distributor._jobs_list_lock = threading.Lock() #DANGER - this was not intended, but i think here we should have the option to - Robert
            distributor._jobs = [] #DANGER - this was not intended, but i think here we should have the option to - Robert
            # move tasksets from RUNNINGTASKSETS to POSSIBLETASKSETS
            for taskset in RUNNINGTASKSETS:
                POSSIBLETASKSETS.append(PC.get_taskset_hash(taskset))
            RUNNINGTASKSETS = []
            # clear MONITORLISTS
            MONITORLISTS = []
            print('cleared')
            return
    except ZeroDivisionError:
        pass
    print('not cleared.')
    return


def resume(distributor):
    if not RUNNINGTASKSETS:
        add_job(distributor=distributor, numberOfTasksets=PC.maxAllowedNumberOfMachines, tasksetSize=CURRENTTASKSETSIZE)
        add_job(distributor=distributor, numberOfTasksets=PC.maxAllowedNumberOfMachines, tasksetSize=CURRENTTASKSETSIZE)
    else:
        distributor.resume()
    HALT = False

def main(initialExecution=True):
    global CURRENTTASKSETSIZE
    global RUNNINGTASKSETS
    global TASKSETS
    global BADTASKSETS
    global MONITORLISTS
    # initialize distributor on target plattform
    distributor = Distributor(max_machine=PC.numberOfMachinesToStartWith, session_type=PC.sessionType,
                              max_allowed=PC.maxAllowedNumberOfMachines, logging_level=PC.loggingLevel,
                              startup_delay=PC.delayAfterStartOfGenode, set_tries=PC.timesTasksetIsTriedBeforeLabeldBad,
                              timeout=PC.genodeTimeout)
    if initialExecution:
        # FIRST TIME EXECUTION:
        # load tasks from file(s)
        load_tasks()
        #print(type(TASKS['hey']))
        #print(TASKS['hey'][0:5])
        generate_possible_tasksets()
        # print('HEEEEREEEE\n\n\n',type(POSSIBLETASKSETS[1][0]))
    else:
        # RESUME EXECUTION:
        # 	- load potential previous findings into attributes (load state)
        load_tasksets()
        if POSSIBLETASKSETS:
            CURRENTTASKSETSIZE = PC.get_taskset_size(POSSIBLETASKSETS[0])
        else:
            # throw away highest level of TASKSETS
            # set CURRENTTASKSETSIZE to this level
            max_key = 0
            for key,itemList in TASKSETS.items():
                if not itemList:
                    max_key = max(max_key, key)
            TASKSETS[max_key] = []
            CURRENTTASKSETSIZE = max_key
            generate_possible_tasksets()

    # HAPPENS EVERY TIME
    
    # always generate PC.maxAllowedNumberOfMachines tasksets, s.t. the machines don't have to wait
    # have at least two jobs in the queue for continous execution
    add_job(distributor=distributor, numberOfTasksets=PC.maxAllowedNumberOfMachines, tasksetSize=CURRENTTASKSETSIZE)
    add_job(distributor=distributor, numberOfTasksets=PC.maxAllowedNumberOfMachines, tasksetSize=CURRENTTASKSETSIZE)

    # creating a signal for alarm - will be called upton alarm
    signal(SIGALRM, lambda x, y: 1 / 0)
    # have output to explain controll options
    inputMessage = 'THIS IS THE TEXT THAT IS SHOWN EACH TIME AN ACTION CAN BE PERFORMED.'
    print(inputMessage)
    option = ''
    while not FINISHED:
        # main programm loop
        # wait for input:
        try:
            alarm(10)  # argument should be a variable
            option = input()
            alarm(0)
        except ZeroDivisionError:
            option = ''
        # act depending on option provided
        if option == 'ss': # show status
            show_status()
            # print('show current length of all tasks lists(each pkg)')
            # print('offer to read more lines from according file')
            print(inputMessage)
        elif option == 'h':
            halt(distributor) # hard=False
            print(inputMessage)
        elif option =='k':
            # kill all machines
            halt(distributor, hard=True)
            print(inputMessage)
        elif option == 'r':
            resume()# execution
            print(inputMessage)
        elif option == 's':
            # saving current progress (TASKSETS, BADTASKSETS)
            write_tasksets_to_file() # default is without possibletasksets
            print(inputMessage)
        elif option == 'x':
            # a clean exit that aborts execution and saves current findings and clean up if qemusession
            distributor.kill_all_machines()
            MONITORLISTS = []
            write_tasksets_to_file(save_possibilities=True)
            if PC.sessionType == 'QemuSession':
                clean_function(PC.maxAllowedNumberOfMachines)
        elif option == '':
            pass
        else:
            print(option, 'was not a possible option!')
            print(inputMessage)
        print('\n\n\n\n\n',TASKSETS,'\n\n\n\n',BADTASKSETS,'\n\n\n\n', RUNNINGTASKSETS,'\n\n\n\n',MONITORLISTS)
        # unrelated to user input:
        check_monitors()  # check if a taskset is finished and put it into according attribute
        currentTasksetSizeExhauseted()  # increments CURRENTTASKSETSIZE if current size is exhausted
        if not WAITING and len(RUNNINGTASKSETS) < PC.maxAllowedNumberOfMachines * 6:
            add_job(distributor=distributor, numberOfTasksets=PC.maxAllowedNumberOfMachines,
                    tasksetSize=CURRENTTASKSETSIZE)
    # end of while
    print('finished execution')
    write_tasksets_to_file()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nInterrupted')
        if PC.sessionType == 'QemuSession':
            clean_function(PC.maxAllowedNumberOfMachines)
        # logger.error('##################################################')
        sys.exit(0)
