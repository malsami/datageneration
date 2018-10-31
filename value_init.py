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
            pkg_list = task_dict[input_parameter['PKG'][random_value((1,5))]]
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


def create_task(s_pkg='hey', s_arg1=0, s_criticaltime=0, s_numberofjobs=1, s_offset=0, s_period=1000, s_priority=126, s_quota=10, s_caps=50):
    p_pkg = {"pkg" : s_pkg}
    p_arg1 = {"config" : {"arg1" : s_arg1}}
    p_priority = priority.Value(s_priority)
    p_period = period.Value(s_period)
    p_criticaltime = criticaltime.Value(s_criticaltime)
    p_offset = {'offset' : s_offset}
    p_numberofjobs = {'numberofjobs' : s_numberofjobs}
    p_quota = {'quota' : str(s_quota)+'M'}
    p_caps = {'caps': s_caps}
    return Task(p_pkg, p_arg1, p_period, p_priority, p_criticaltime, p_offset, p_numberofjobs, p_quota, p_caps) 


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
	return period - stoptime


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
        i_pkg = parameters['PKG'][random_value((1,5))]

        i_arg = random_value(parameters['ARG'][i_pkg])
        i_priority = random_value(parameters['PRIORITY'])
        i_period = random_value(parameters['PERIOD'])*1000
        i_criticaltime = CRITICALTIME(i_period)
        i_offset = random_value(parameters['OFFSET'])*1000
        i_numberofjobs = random_value(parameters['NUMBEROFJOBS'])
        i_quota = random_value(parameters['QUOTA'])
        i_caps = random_value(parameters['CAPS'])
        tasks[i_pkg].append(create_task(i_pkg, i_arg, i_criticaltime, i_numberofjobs, i_offset, i_period, i_priority, i_quota, i_caps))
    
    return tasks

def generate_tasks_of_type(n, pkg, parameters):
    
    tasks = []
    for i in range(n):
        i_pkg = pkg 
        i_arg = base_for_pkg(i_pkg) ** random_value(parameters['ARG'][i_pkg])
        i_priority = random_value(parameters['PRIORITY'])
        i_period = random_value(parameters['PERIOD'])*1000
        i_criticaltime = CRITICALTIME(i_period)
        i_offset = random_value(parameters['OFFSET'])*1000
        i_numberofjobs = random_value(parameters['NUMBEROFJOBS'])
        i_quota = random_value(parameters['QUOTA'])
        i_caps = random_value(parameters['CAPS'])
        tasks.append(create_task(i_pkg, i_arg, i_criticaltime, i_numberofjobs, i_offset, i_period, i_priority, i_quota, i_caps))

    return {pkg:tasks}

if __name__ == '__main__':
    try:
        generate_tasks(int(sys.argv[1]))
    except KeyboardInterrupt:
        print('Interrupted')