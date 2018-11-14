import sys
sys.path.append('../')
import random
import copy
import matplotlib.pyplot as plt
from taskgen.blocks import *
from taskgen.task import Task
from taskgen.taskset import TaskSet


def task_dict_to_list(task_dict,pkg):
	return [TaskSet([t]) for t in task_dict[pkg]]


def combine_random(task_dict, number_of_wanted_sets, tasks_per_set,input_parameter):
    resulting_list = []
    for i in range(number_of_wanted_sets):
        t = TaskSet([])
        for s in range(tasks_per_set):
            pkg_list = task_dict[input_parameter['PKG'][random_value((1,len(input_parameter['PKG'])))]]
            t.append(copy.deepcopy(pkg_list[random_value((0,len(pkg_list)-1))]))
        if verify_list_of_tasks(t):
            resulting_list.append(t)
        else:
            raise Exception('Two tasks had the same id:'+str(t))
    return resulting_list

def verify_list_of_tasks(task_list):
    ids = []
    for task in task_list:
        if task['id']in ids:
            return False
        else:
            ids.append(task['id'])
    return True


def create_task(input_pkg='hey', input_priority=1, input_deadline=0, input_period=1000, input_criticaltime=0, input_numberofjobs=1, input_offset=0, input_quota=10, input_caps=50, input_cores=2, input_coreoffset=1, input_arg1=0):
    dict_pkg = {"pkg" : input_pkg}
    dict_priority = {'priority' : input_priority}
    dict_deadline = {'deadline' : input_deadline}
    dict_period = {'period' : input_period}
    dict_criticaltime = {'criticaltime' : input_criticaltime}
    dict_numberofjobs = {'numberofjobs' : input_numberofjobs}
    dict_offset = {'offset' : input_offset}
    dict_quota = {'quota' : str(input_quota)+'M'}
    dict_caps = {'caps': input_caps}
    dict_cores = {'cores' : input_cores}
    dict_coreoffset = {'coreoffset' : input_coreoffset}
    dict_arg1 = {"config" : {"arg1" : input_arg1}}
    return Task(dict_pkg, dict_priority, dict_deadline, dict_period, dict_criticaltime, dict_numberofjobs, dict_offset, dict_quota, dict_caps, dict_cores, dict_coreoffset, dict_arg1)


def plot_distribution(x,y,titel, ylable, xlable,info=False):
	fig, ax = plt.subplots()
	ax.bar(x,y)
	ax.set_title(titel)
	ax.set_ylabel(ylable)
	ax.set_xlabel(xlable)
	if info:
		for i in x:
			ax.text(i,y[i-1]/2, '%d' %y[i-1], ha='center', va='bottom')
	plt.show()


def random_value(scope):
	return random.randint(scope[0],scope[1])


def CRITICALTIME(period):
	stoptime = 500
	return max(period - stoptime,0)


def base_for_pkg(pkg):
    if pkg == 'cond_mod':
        return 3
    else:
        return 2
    


def generate_tasks(n, parameters):
    tasks = { 'hey':[],
            'pi':[],
            'tumatmul':[],
            'cond_mod':[],
            'cond_42':[]
            }
    for i in range(n):
        i_pkg = parameters['PKG'][random_value((1,len(parameters['PKG'])))]
        i_priority = random_value(parameters['PRIORITY'])
        i_deadline = 0
        i_period = random_value(parameters['PERIOD'])*1000
        i_criticaltime = CRITICALTIME(i_period)
        i_numberofjobs = random_value(parameters['NUMBEROFJOBS'])
        i_offset = random_value(parameters['OFFSET'])*1000
        i_quota = random_value(parameters['QUOTA'])
        i_caps = random_value(parameters['CAPS'])
        i_cores = 2
        i_coreoffset = 1
        i_arg = random_value(parameters['ARG'][i_pkg])
        tasks[i_pkg].append(create_task(input_pkg=i_pkg, input_priority=i_priority, input_deadline=i_deadline, input_period=i_period, input_criticaltime=i_criticaltime, input_numberofjobs=i_numberofjobs, input_offset=i_offset, input_quota=i_quota, input_caps=i_caps, input_cores=i_cores, input_coreoffset=i_coreoffset, input_arg1=i_arg))
    return tasks

def generate_tasks_of_type(n, pkg, parameters):
    
    tasks = []
    for i in range(n):
        i_pkg = pkg 
        i_priority = random_value(parameters['PRIORITY'])
        i_deadline = 0
        i_period = random_value(parameters['PERIOD'])*1000
        i_criticaltime = CRITICALTIME(i_period)
        i_numberofjobs = random_value(parameters['NUMBEROFJOBS'])
        i_offset = random_value(parameters['OFFSET'])*1000
        i_quota = random_value(parameters['QUOTA'])
        i_caps = random_value(parameters['CAPS'])
        i_cores = 2
        i_coreoffset = 1
        i_arg = base_for_pkg(i_pkg) ** random_value(parameters['ARG'][i_pkg])
        tasks.append(create_task(input_pkg=i_pkg, input_priority=i_priority, input_deadline=i_deadline, input_period=i_period, input_criticaltime=i_criticaltime, input_numberofjobs=i_numberofjobs, input_offset=i_offset, input_quota=i_quota, input_caps=i_caps, input_cores=i_cores, input_coreoffset=i_coreoffset, input_arg1=i_arg))
    return {pkg:tasks}

if __name__ == '__main__':
    try:
        generate_tasks(int(sys.argv[1]))
    except KeyboardInterrupt:
        print('Interrupted')