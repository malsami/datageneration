import sys
sys.path.append('../')
from signal import signal, alarm, SIGALRM
from distributor.distributorClass import Distributor
from distributor.monitors.dataGenerationMonitor import DataGenerationMonitor
from distributor.clean import clean_function, clean_panda
import value_init as VI
from taskgen.task import Task
from taskgen.taskset import TaskSet
from random import shuffle
import threading
import parameter_config as PC

# this needs to be filled with generated tasks

CURRENTTASKSETSIZE = 1
newLevel = -1
HALT = False
RUNNING = True
WAITING = False
FINISHED = False

# good (successful) tasksets, key represents the size of the taskset
# list elements are tuples: (bool, TaskSet)
TASKSETS = {1: []
            }

BADTASKSETS = {1: []
               }

#list elements are task hashes
TASKS = {'hey': [],
         'pi': [],
         'tumatmul': [],
         'cond_mod': [],
         'cond_42': []
         }
TASKSLINES = {  'hey' : 0,
                'pi': 0,
                'tumatmul': 0,
                'cond_mod': 0,
                'cond_42': 0
            }

# holds triples as list [numberOfTasksInJob, numberOfProcessedTasksInJob, [Taskset]]
# tasksetTries=0 if successful; Job=[startTime, exitTime, eventType]
MONITORLISTS = []

# list of taskset hashes
POSSIBLETASKSETS = []

SAVE_POSSIBLES = {  1 : []
                }
# list of TaskSet objects
RUNNINGTASKSETS = []


def load_tasks(packages=PC.taskTypes, addToPossible=False):
    # read from package specific file and load into TASKS
    # format per line in file e.g.: [task_hash, task_hash, ...]
    global TASKS
    global POSSIBLETASKSETS
    global TASKSLINES

    linecounter = 0 # keeps track of read lines
    path='./data/new_tasks_'
    for pkg in packages:
        with open(path + pkg) as task_file:
            for line in task_file:
                if linecounter < TASKSLINES[pkg]:
                    linecounter += 1
                else:
                    linecounter += 1
                    TASKSLINES[pkg] += 1
                    newTasks = eval(line)
                    TASKS[pkg] += newTasks
                    if addToPossible:
                        POSSIBLETASKSETS += newTasks
    if addToPossible:
        remove_known_tasksets_from_possible()
        shuffle(POSSIBLETASKSETS)
    print('lines loaded:',[(t,TASKSLINES[t]) for t in PC.taskTypes])


def load_tasksets(include_possibilities=True):
    # read from files and load into TASKSETS and BADTASKSETS above
    # format: a tuple per line: (level, [Taskset, Taskset, ...])
    # include_possibilities decides whether or not POSSIBLETASKSETS should be restored 
    global TASKSETS
    global BADTASKSETS
    global POSSIBLETASKSETS

    for option in ('good', 'bad'):
        with open('./data/{}_tasksets'.format(option), 'r') as taskset_file:
            for line in taskset_file:# line format: (int, [ (bool,[{}]) ] )
                level, tasksetList = eval(line)# level indicates size of tasksets
                add_if_not_exists(level)
                for successful, tasksetInfo in tasksetList:
                    taskset = TaskSet([])
                    for taskDict in tasksetInfo:
                        taskset.append(Task(taskDict))
                    if successful:
                        TASKSETS[level].append((successful,taskset))
                    else:
                        BADTASKSETS[level].append((successful,taskset))
    if include_possibilities:
        try:
            with open('./data/possible_tasksets','r') as taskset_file:
                for line in taskset_file:# format: [taskset_hash], taskset_hash is type string
                    POSSIBLETASKSETS += eval(line)
        except FileNotFoundError as e:
            print('There were no possible tasksets.')

"""
    write_tasksets_to_file() is for basic book-keeping and we will write the good,bad and possible tasksets into the appropriate
    files. 
"""
def write_tasksets_to_file(save_possibilities=False, fileversion=''):# should only be True if execution aborts
    global POSSIBLETASKSETS
    with open("./data/bad_tasksets"+fileversion, "w") as bad_f:# each line is (int, [ (bool,[{}]) ] )
        # Writing bad taskset into the file
        for element in BADTASKSETS.items():
            bad_f.write(str(element) + '\n')
    with open("./data/good_tasksets"+fileversion, "w") as good_f:# each line is (int, [ (bool,[{}]) ] )
        for element in TASKSETS.items():
            good_f.write(str(element) + '\n')
    if save_possibilities:
        with open("./data/possible_tasksets", "w") as possible_f: # each line is [taskset_hash], taskset_hash is a string
            # Writing the tasksets which have not been evaluated yet beack into possibilities and then save
            POSSIBLETASKSETS += [PC.get_taskset_hash(taskset) for taskset in RUNNINGTASKSETS]
            possible_f.write(str(POSSIBLETASKSETS) + '\n')
                

""" Build the taskset list. 
    When building the taskset of size n, it will combine the taskset of size n-1 with the tasksets of 1
"""
def generate_possible_tasksets(resuming=False):
    global POSSIBLETASKSETS
    print(CURRENTTASKSETSIZE, 'in generate possible tasksets')
    # filling POSSIBLETASKSETS dictionary
    if CURRENTTASKSETSIZE == 1:
        for pkg in PC.taskTypes:
            POSSIBLETASKSETS += TASKS[pkg]
    else:
        for i in range(len(TASKSETS[1])):
            limiter = i + 1 if CURRENTTASKSETSIZE == 2 else 0 
            for j in range(limiter, len(TASKSETS[CURRENTTASKSETSIZE - 1])):
                current_single_element = PC.get_taskset_hash(TASKSETS[1][i][1])
                current_multi_element = PC.get_taskset_hash(TASKSETS[CURRENTTASKSETSIZE - 1][j][1])
                POSSIBLETASKSETS.append(current_single_element+current_multi_element)
    remove_known_tasksets_from_possible()
    shuffle(POSSIBLETASKSETS)


def remove_known_tasksets_from_possible():
    global POSSIBLETASKSETS
    if CURRENTTASKSETSIZE in TASKSETS and TASKSETS[CURRENTTASKSETSIZE]:
        for success, taskset in TASKSETS[CURRENTTASKSETSIZE]:
            try:
                POSSIBLETASKSETS.remove(PC.get_taskset_hash(taskset))
                if CURRENTTASKSETSIZE == 1:
                    for task in taskset:
                        TASKS[task['pkg']].remove(PC.get_taskset_hash(taskset))
            except ValueError as e:
                pass
    if CURRENTTASKSETSIZE in BADTASKSETS and BADTASKSETS[CURRENTTASKSETSIZE]:
        for success, taskset in BADTASKSETS[CURRENTTASKSETSIZE]:
            try:
                POSSIBLETASKSETS.remove(PC.get_taskset_hash(taskset))
                if CURRENTTASKSETSIZE == 1:
                    TASKS[taskset[0]['pkg']].remove(PC.get_taskset_hash(taskset))
            except ValueError as e:
                pass


def add_job(distributor, numberOfTasksets=1, tasksetSize=1):
    # adds a new job of length numberOfTasksets to the distributor and add the monitors list (triple) to MONITORLISTS
    # distributor.add_job([Taskset], DataGenerationMonitor)
    # the list is numberOfTasksets long and each Taskset consists of tasksetSize Tasks
    # otherwise, a new taskset is to be generated in its place
    # the outputlist of DataGenerationMonitor can be accessed via its 'out' attribute
    global MONITORLISTS
    global POSSIBLETASKSETS
    global TASKS
    global RUNNINGTASKSETS

    monitor = DataGenerationMonitor([])
    tasksetList = []
    # take numberOfTasksets Tasksets from POSSIBLETASKSETS and add them to tasksetList
    for i in range(numberOfTasksets*6):
        try:
            taskset = POSSIBLETASKSETS.pop()
            if CURRENTTASKSETSIZE == 1:
                # print(taskset,'\n',TASKS)
                TASKS[PC.taskParameters['PKG'][int(taskset[:1])]].remove(taskset)
            tasksetList.append(PC.hash_to_taskset(taskset))
            # add them also to RUNNINGTASKSETS
            RUNNINGTASKSETS.append(tasksetList[-1])
        except IndexError:
            break
    if tasksetList:
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


def add_if_not_exists(level):
    global TASKSETS
    global BADTASKSETS
    if not level in TASKSETS:
        TASKSETS[level] = []
    if not level in BADTASKSETS:
        BADTASKSETS[level] = []


def currentTasksetSizeExhauseted():
    global POSSIBLETASKSETS
    global CURRENTTASKSETSIZE
    global RUNNING
    global WAITING
    global FINISHED
    global newLevel
    RUNNING = not HALT and RUNNINGTASKSETS
    WAITING = not POSSIBLETASKSETS and RUNNING 
    if not POSSIBLETASKSETS and not RUNNINGTASKSETS:
        if newLevel > 0:
            CURRENTTASKSETSIZE = newLevel
            newLevel = -1
        else:
            CURRENTTASKSETSIZE += 1
        add_if_not_exists(CURRENTTASKSETSIZE)
        generate_possible_tasksets()
        if not POSSIBLETASKSETS and not TASKSETS[CURRENTTASKSETSIZE]:
            FINISHED = True


def show_status():
    global POSSIBLETASKSETS
    global newLevel

    print("Current Level: ", CURRENTTASKSETSIZE)
    #print("Number of [GOOD/TOTAL] tasksets on the {}. level: [{}/{}]".format(CURRENTTASKSETSIZE, len(TASKSETS[CURRENTTASKSETSIZE]), len(TASKSETS[CURRENTTASKSETSIZE])+len(BADTASKSETS[CURRENTTASKSETSIZE])))
    for i in list(TASKSETS.keys())[::-1]:
        print("Number of [GOOD/TOTAL] tasksets on the {}. level: [{}/{}]".format(i, len(TASKSETS[i]), len(TASKSETS[i])+len(BADTASKSETS[i])))
    print("Number of Running Tasksets: ", len(RUNNINGTASKSETS))
    print("Number of possible Tasksets on current level:", len(POSSIBLETASKSETS))
    for pkg in PC.taskTypes:
        print("Number of tasks in TASKS[", pkg, "]: ", len(TASKS[pkg]))

    try:
        print('you can increase the current level (i)')
        print('or you can set the level to one of these values: {}'.format(list(TASKSETS.keys())))
        if CURRENTTASKSETSIZE == 1:
            print('you can also add more tasks for a pkg, just type the name of one of these: {}'.format(PC.taskTypes))
        alarm(10)
        option = input()
        alarm(0)
        if option == 'i':
            print('RUNNINGTASKSETS will be finished and then the level will be raised.')
            SAVE_POSSIBLES[CURRENTTASKSETSIZE] = POSSIBLETASKSETS
            POSSIBLETASKSETS = []
            return
        if CURRENTTASKSETSIZE == 1 and option in PC.taskTypes:
            if option in PC.taskTypes:
                PC.make_tasks(option)
                load_tasks(packages=[option], addToPossible=True)
        else:
            try:
                intOption = int(option)
                if intOption in TASKSETS:
                    # print(intOption,type(intOption),[x for k,l in TASKS.items() for x in l],'\n', TASKS)
                    if intOption == 1 and not [x for k,l in TASKS.items() for x in l]: 
                        try:
                            print('There is no unexecuted Tasks, do you want to add more of everything? [y/n]')
                            alarm(5)
                            option = input()
                            alarm(0)
                            if option == 'y':
                                for task in PC.taskTypes:
                                    PC.make_tasks(task)
                                    load_tasks(packages=[task], addToPossible=False)
                        except ZeroDivisionError:
                            pass
                    newLevel = intOption
                    print('RUNNINGTASKSETS will be finished and then the level will be set to {}.'.format(intOption))
                    SAVE_POSSIBLES[CURRENTTASKSETSIZE] = POSSIBLETASKSETS
                    POSSIBLETASKSETS = []
                    return
                else:
                    print('{} was not a viable option.'.format(intOption))
            except ValueError:
                print('{} was not a viable option.'.format(option))
    except ZeroDivisionError:
        pass
    return


def halt_machines(distributor, hard=False):
    global HALT
    global RUNNINGTASKSETS
    global POSSIBLETASKSETS
    global MONITORLISTS
    global TASKS
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
                tasksetHash = PC.get_taskset_hash(taskset)
                if CURRENTTASKSETSIZE == 1:
                    TASKS[PC.taskParameters['PKG'][int(tasksetHash[:1])]].append(tasksetHash)
                POSSIBLETASKSETS.append(tasksetHash)
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
    global HALT
    if not RUNNINGTASKSETS:
        add_job(distributor=distributor, numberOfTasksets=PC.maxAllowedNumberOfMachines, tasksetSize=CURRENTTASKSETSIZE)
        add_job(distributor=distributor, numberOfTasksets=PC.maxAllowedNumberOfMachines, tasksetSize=CURRENTTASKSETSIZE)
    else:
        distributor.resume()
    HALT = False


def clean_up_machines():
    if PC.sessionType == 'QemuSession':
        clean_function(PC.maxAllowedNumberOfMachines)
    if PC.sessionType == 'PandaSession':
        clean_panda(PC.maxAllowedNumberOfMachines)


def main(initialExecution=True):
    global CURRENTTASKSETSIZE
    global RUNNINGTASKSETS
    global TASKSETS
    global BADTASKSETS
    global MONITORLISTS
    lapCounter = 0
    aORb = True
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
            if CURRENTTASKSETSIZE == 1:
                for taskset in POSSIBLETASKSETS:
                    TASKS[PC.taskParameters['PKG'][int(taskset[:1])]].append(taskset)
        else:
            # set CURRENTTASKSETSIZE to highest level with data
            max_key = 0
            for key,itemList in TASKSETS.items():
                print(key, len(itemList))
                if itemList:
                    max_key = max(max_key, key)
            CURRENTTASKSETSIZE = max_key
            #print(TASKSETS)
            generate_possible_tasksets()

    # HAPPENS EVERY TIME
    
    # always generate PC.maxAllowedNumberOfMachines tasksets, s.t. the machines don't have to wait
    # have at least two jobs in the queue for continous execution
    add_job(distributor=distributor, numberOfTasksets=PC.maxAllowedNumberOfMachines, tasksetSize=CURRENTTASKSETSIZE)
    add_job(distributor=distributor, numberOfTasksets=PC.maxAllowedNumberOfMachines, tasksetSize=CURRENTTASKSETSIZE)

    # creating a signal for alarm - will be called upton alarm
    signal(SIGALRM, lambda x, y: 1 / 0)
    # have output to explain controll options
    inputMessage = 'options are (d)ebug, show status(ss), (h)alt/(k)ill machines, (r)esume machines, (s)ave current progress, e(x)it.'
    print(inputMessage)
    option = ''
    while not FINISHED:
        lapCounter += 1
        if lapCounter > PC.savedEveryNLaps:
            lapCounter = 0
            if aORb:
                write_tasksets_to_file(fileversion='A')
                aORb = not aORb
            else:
                write_tasksets_to_file(fileversion='B')
                aORb = not aORb
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
            halt_machines(distributor) # hard=False
            print(inputMessage)
        elif option =='k':
            # kill all machines
            halt_machines(distributor, hard=True)
            print(inputMessage)
        elif option == 'r':
            resume(distributor)# execution
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
            clean_up_machines()
            sys.exit(0)
        elif option == 'd':
            print('\n\n\n\nTasksets:\n',TASKSETS,'\n\n\nBadTasksets:\n',BADTASKSETS,'\n\n\nRunningTasksets:\n', RUNNINGTASKSETS,'\n\n\nMonitorLists:\n',MONITORLISTS,'\n')
            print(inputMessage)
        elif option == '':
            # print('lap...') 
            pass
        else:
            print(option, 'was not a possible option!')
            print(inputMessage)
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
        initialize = True
        try:
            initialize = not (sys.argv[1] == 'c')
        except IndexError as e:
            pass
        main(initialExecution=initialize)
    except KeyboardInterrupt:
        print('\nInterrupted')
        clean_up_machines()
        # logger.error('##################################################')
        sys.exit(0)
