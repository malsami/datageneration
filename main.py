import sys
import select
from distributor.distributorClass import Distributor
from distributor.monitors.dataGenerationMonitor import DataGenerationMonitor
from distributor.clean import clean_function, clean_panda

import value_init as VI
from taskgen.task import Task
from taskgen.taskset import TaskSet
from random import shuffle
import threading
import parameter_config as PC
from DatabaseConnection import DatabaseConnection

# this needs to be filled with generated tasks

CURRENTTASKSETSIZE = 1
newLevel = -1
HALT = False
RUNNING = True
WAITING = False
FINISHED = False

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


SAVE_POSSIBLES = {  1 : []
                }
# list of TaskSet objects
RUNNINGTASKSETS = []

DATABASE = None

def load_tasks(packages=PC.taskTypes):
    # read from package specific file and load into TASKS
    # format per line in file e.g.: [task_hash, task_hash, ...]
    global TASKS
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
                    for task in newTasks:
                        DATABASE.add_task_to_db(task=task)

    print('lines loaded:',[(t,TASKSLINES[t]) for t in PC.taskTypes])


def generate_possible_tasksets():
    """
    fills the PossibleTaskSets_<CURRENTTASKSETSIZE> Table in the DATABASE
    by combining the tasksets of size 1 with the successful tasksets of CURRENTTASKSETSIZE -1
    :param resuming:
    :return:
    """
    commit_counter = 0
    print(CURRENTTASKSETSIZE, 'in generate possible tasksets')
    if CURRENTTASKSETSIZE == 1:
        for pkg in PC.taskTypes:
            for task in TASKS[pkg]:
                DATABASE.add_taskset_hash_to_possible(taskset_hash=task, size=CURRENTTASKSETSIZE)
                if commit_counter % 1000 == 0:
                    DATABASE.commit()
                    commit_counter = 0
                commit_counter += 1
    else:
        for single_taskset_id in DATABASE.get_taskset_ids_of_size(successful=True,size=1):
            current_single_element = DATABASE.get_hash_of_taskset(taskset_id=single_taskset_id, size=1)
            for multiple_taskset_id in DATABASE.get_taskset_ids_of_size(successful=True,size=CURRENTTASKSETSIZE - 1):
                current_multi_element = DATABASE.get_hash_of_taskset(taskset_id=multiple_taskset_id, size=CURRENTTASKSETSIZE-1)
                DATABASE.add_taskset_hash_to_possible(taskset_hash=current_single_element+current_multi_element, size=CURRENTTASKSETSIZE)
                if commit_counter % 1000 == 0:
                    DATABASE.commit()
                    commit_counter = 0
                commit_counter += 1



def add_job(distributor, numberOfTasksets=1):
    # adds a new job of length numberOfTasksets to the distributor and add the monitors list (triple) to MONITORLISTS
    # distributor.add_job([Taskset], DataGenerationMonitor)
    # the list is numberOfTasksets long and each Taskset consists of tasksetSize Tasks
    # otherwise, a new taskset is to be generated in its place
    # the outputlist of DataGenerationMonitor can be accessed via its 'out' attribute
    global MONITORLISTS
    global RUNNINGTASKSETS

    monitor = DataGenerationMonitor([])
    tasksetList = []
    for taskset_hash in DATABASE.get_n_hashes_of_size_from_possible(n=numberOfTasksets*6, size=CURRENTTASKSETSIZE):
        try:
            tasksetList.append(PC.hash_to_taskset(taskset_hash))
            # add them also to RUNNINGTASKSETS
            RUNNINGTASKSETS.append(tasksetList[-1])
        except IndexError:
            break
    if tasksetList:
        distributor.add_job(tasksetList, monitor=monitor)
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
                    DATABASE.add_taskset_to_db(taskset=taskset,size=CURRENTTASKSETSIZE)
                    RUNNINGTASKSETS.remove(taskset)
                    # increment MONITORLISTS[index][1] which is numberOfProcessedTasksInJob
                    MONITORLISTS[index][1] += 1
            except IndexError:
                continue
    indicesToBeRemoved.sort(reverse=True)
    for i in indicesToBeRemoved:  # so we dont have to worry about messing the indices up when deleting elements
        del MONITORLISTS[i]

def currentTasksetSizeExhauseted():
    global CURRENTTASKSETSIZE
    global RUNNING
    global WAITING
    global FINISHED
    global newLevel
    have_possible_tasksets_on_current = DATABASE.have_possible_tasksets_of_size(size=CURRENTTASKSETSIZE)
    RUNNING = (not HALT) and RUNNINGTASKSETS
    WAITING = not have_possible_tasksets_on_current and RUNNING
    if not have_possible_tasksets_on_current and not RUNNINGTASKSETS:
        if newLevel > 0:
            CURRENTTASKSETSIZE = newLevel
            newLevel = -1
        else:
            CURRENTTASKSETSIZE += 1
        DATABASE.create_tables_for_taskset_size(size=CURRENTTASKSETSIZE)
        generate_possible_tasksets()
        if not have_possible_tasksets_on_current and not DATABASE.get_taskset_ids_of_size(successful=True, size=CURRENTTASKSETSIZE)+DATABASE.get_taskset_ids_of_size(successful=False, n=CURRENTTASKSETSIZE):
            FINISHED = True

def offer_to_change_current_taskset_size():
    global newLevel
    taskset_sizes = DATABASE.get_available_taskset_sizes()
    print('you can change the current taskset size to one of the following:',taskset_sizes)
    i, _, _ = select.select([sys.stdin], [], [], 10)
    if i:
        option = sys.stdin.readline().strip()
        try:
            intOption = int(option)
            if intOption in taskset_sizes:
                newLevel = intOption
                print('RUNNINGTASKSETS will be finished and then the level will be set to {}.'.format(intOption))
                return
            else:
                print('{} was not a viable option.'.format(intOption))
        except ValueError:
            print('{} was not a viable option.'.format(option))

def show_status():
    print('Current Level:', CURRENTTASKSETSIZE)
    print('Number of Running Tasksets:', len(RUNNINGTASKSETS))
    print(DATABASE.status())
    offer_to_change_current_taskset_size()

def halt_machines(distributor, hard=False):
    global HALT
    global RUNNINGTASKSETS
    global MONITORLISTS
    HALT = True
    if hard:
        distributor.kill_all_machines()
    else:
        distributor.shut_down_all_machines()
    RUNNINGTASKSETS = []
    # clear MONITORLISTS
    MONITORLISTS = []
    print('cleared')
    return


def resume(distributor):
    global HALT
    if not RUNNINGTASKSETS:
        add_job(distributor=distributor, numberOfTasksets=PC.maxAllowedNumberOfMachines)
        add_job(distributor=distributor, numberOfTasksets=PC.maxAllowedNumberOfMachines)
    else:
        distributor.resume()
    HALT = False


def clean_up_machines():
    if PC.sessionType == 'QemuSession':
        clean_function(PC.maxAllowedNumberOfMachines)
    if PC.sessionType == 'PandaSession':
        clean_panda(PC.maxAllowedNumberOfMachines)


def main(db_path, initialExecution=True):
    global CURRENTTASKSETSIZE
    global RUNNINGTASKSETS
    global MONITORLISTS
    global DATABASE
    DATABASE = DatabaseConnection(db_path,existing=not(initialExecution))
    # initialize distributor on target plattform
    distributor = Distributor(max_machine=PC.numberOfMachinesToStartWith, session_type=PC.sessionType,
                              max_allowed=PC.maxAllowedNumberOfMachines, logging_level=PC.loggingLevel,
                              startup_delay=PC.delayAfterStartOfGenode, set_tries=PC.timesTasksetIsTriedBeforeLabeldBad,
                              timeout=PC.genodeTimeout)
    if initialExecution:
        # FIRST TIME EXECUTION:
        # load tasks from file(s)
        load_tasks()
        generate_possible_tasksets()
    else:
        # RESUME EXECUTION:
        CURRENTTASKSETSIZE = max(DATABASE.get_available_taskset_sizes())
        if not DATABASE.have_possible_tasksets_of_size(CURRENTTASKSETSIZE):
            generate_possible_tasksets()
    # HAPPENS EVERY TIME
    
    # always generate PC.maxAllowedNumberOfMachines tasksets, s.t. the machines don't have to wait
    # have at least two jobs in the queue for continuous execution
    add_job(distributor=distributor, numberOfTasksets=PC.maxAllowedNumberOfMachines)
    add_job(distributor=distributor, numberOfTasksets=PC.maxAllowedNumberOfMachines)

    # have output to explain controll options
    inputMessage = 'options are (d)ebug, show status(s), (h)alt/(k)ill machines, (r)esume machines, e(x)it.'
    print(inputMessage)
    option = ''
    while not FINISHED:
        # main programm loop
        option = get_option(message=inputMessage, possible=('d','s','h','k','r','x'), wait_time=10)
        # act depending on option provided
        if option == 's': # show status
            show_status()
            print(inputMessage)
        elif option == 'h':
            halt_machines(distributor) # hard=False
            print(inputMessage)
        elif option == 'k':
            # kill all machines
            halt_machines(distributor, hard=True)
            print(inputMessage)
        elif option == 'r':
            resume(distributor)# execution
            print(inputMessage)
        elif option == 'x':
            # a clean exit that aborts execution and saves current findings and clean up if qemusession
            distributor.kill_all_machines()
            clean_up_machines()
            sys.exit(0)
        elif option == 'd':
            print('\n\n\n\nCurrent Level:', CURRENTTASKSETSIZE)
            print('\n\n\nNumber of Running Tasksets:', len(RUNNINGTASKSETS))
            print('\n\n\n',DATABASE.status())
            print('\n\n\nRunningTasksets:\n', RUNNINGTASKSETS,'\n\n\nMonitorLists:\n',MONITORLISTS,'\n')
            print(inputMessage)

        # unrelated to user input:
        check_monitors()  # check if a taskset is finished and put it into according attribute
        currentTasksetSizeExhauseted()  # increments CURRENTTASKSETSIZE if current size is exhausted
        if not WAITING and len(RUNNINGTASKSETS) < PC.maxAllowedNumberOfMachines * 6:
            add_job(distributor=distributor, numberOfTasksets=PC.maxAllowedNumberOfMachines)
    # end of while
    print('finished execution')

def get_option(message, possible, wait_time) -> str:
    # wait for input:
    i, _, _ = select.select([sys.stdin], [], [], wait_time)
    if i:
        option = sys.stdin.readline().strip()
        if option not in possible:
            print(option, 'was not a possible option!')
            print(message)
    else:
        option = ''
        return option


if __name__ == '__main__':
    try:
        try:
            initialize = not (sys.argv[1] == 'c')
            db_path = sys.argv[2]
        except IndexError as e:
            initialize = True
            db_path = './data/database'
        main(db_path=db_path, initialExecution=initialize)
    except KeyboardInterrupt:
        print('\nInterrupted')
        clean_up_machines()
        # logger.error('##################################################')
        sys.exit(0)
