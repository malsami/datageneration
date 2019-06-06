import sqlite3
import sys

taskset_id = []
taskset_list = []
tasks = []
single_tasks = []
job_ID = 0
def parse_from_files(fileSuffix=''):
    for state in ('good','bad'):
        with open('data/'+state+'_tasksets'+fileSuffix,'r') as file:
            print('data/'+state+'_tasksets'+fileSuffix) 
            # each line in the file represents a tuple (tasksetsize, listOfTasksets)
            # listOfTasksets is a list of tuples (success:bool, Taskset)
            for line in file:
                level = eval(line[1:2])
                splitlist = (line[5:-2]+',').split('(')
                for text in splitlist[1:]:
                    dataTuple = '('+text[:-2]
                    success_taskset = eval(dataTuple)
                    taskset_list.append(success_taskset)
                    if level == 1:
                        #print('there was a level 1')
                        taskhash = get_task_hash(success_taskset[1][0]) 
                        if not taskhash in tasks:
                            tasks.append(taskhash)
                            single_tasks.append(success_taskset[1][0])
                        else:
                            print(taskhash, 'was double')


PKGTOINT = {'hey' : 1,
            'pi' : 2,
            'tumatmul' : 3,
            'cond_mod' : 4#,
            #'cond_42' : 5
            }

def get_task_hash(task):
    # returns a string containing 52 digits per task
    #print(task)
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


def write_tasks_to_db():
    for task in single_tasks:
        task_values = [tasks.index(get_task_hash(task)), # task_id
                         task['priority'],
                         task['deadline'],
                         task['quota'],
                         task['caps'],
                         task['pkg'],
                         task['config']['arg1'],
                         task['cores'],
                         task['coreoffset'],
                         task['criticaltime'],
                         task['period'],
                         task['numberofjobs'],
                         task['offset']
                         ]

        db.execute('INSERT INTO Task VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', task_values)


def write_taskset_and_job_to_db():
    global job_ID
    taskset_counter = 0
    for success, taskset in taskset_list:
        taskset_values = [taskset_counter, 1] if success else [taskset_counter, 0]
        for task in taskset:
            task_id = tasks.index(get_task_hash(task))
            taskset_values.append(task_id)
            for number,job in task['jobs'].items():
                try:
                    job_values = (taskset_counter, task_id, job_ID, job[0], job[1], job[2])
                    db.execute('INSERT INTO Job VALUES (?,?,?,?,?,?)', job_values)
                    job_ID += 1
                except IndexError as e:
                    print('there was an error: ',job,'\n and the task: ',task)
                    
        taskset_values = taskset_values + [-1]*(6-len(taskset_values))
        db.execute('INSERT INTO TaskSet VALUES (?,?,?,?,?,?)', taskset_values)
        taskset_counter += 1


def create_tables():
    db.execute(
        '''
        CREATE TABLE IF NOT EXISTS TaskSet
        (Set_ID INTEGER,
        Successful INT,
        TASK1_ID INTEGER,
        TASK2_ID INTEGER,
        TASK3_ID INTEGER,
        TASK4_ID INTEGER,
        PRIMARY KEY (Set_ID)
        )
        '''
    )

    db.execute(
        '''
        CREATE TABLE IF NOT EXISTS Task 
        (Task_ID INTEGER, 
         Priority INT, 
         Deadline INT, 
         Quota INT,
         CAPS INT,
         PKG STRING, 
         Arg INT, 
         CORES INT,
         COREOFFSET INT,
         CRITICALTIME INT,
         Period INT, 
         Number_of_Jobs INT,
         OFFSET INT,
         PRIMARY KEY (Task_ID)
         )
         '''
    )

    db.execute(
        '''CREATE TABLE IF NOT EXISTS Job 
        (Set_ID INTEGER, 
        Task_ID INTEGER, 
        Job_ID INTEGER,
        Start_Date INT, 
        End_Date INT, 
        Exit_Value STRING, 
        PRIMARY KEY (TASK_ID,SET_ID, Job_ID),
        FOREIGN KEY(TASK_ID) REFERENCES Task(Task_ID),
        FOREIGN KEY(Set_ID) REFERENCES TaskSet(Set_ID)
        )
        '''
    )


if __name__ == "__main__":
    name = sys.argv[1]
    try:
        fileSuffix = sys.argv[2]
    except IndexError:
        fileSuffix = ''
    database = sqlite3.connect(name+'.db')
    db = database.cursor()

    db.execute('DROP TABLE IF EXISTS Task')
    db.execute('DROP TABLE IF EXISTS Job')
    db.execute('DROP TABLE IF EXISTS TaskSet')

    create_tables()
    if fileSuffix == 'A' or fileSuffix == 'B':
        parse_from_files(fileSuffix)
    elif fileSuffix == '':
        parse_from_files()
    else:
        raise ValueError("sys.argv[2] was '"+fileSuffix+"' but viable options are only 'A', 'B' or nothing" )
    write_tasks_to_db()
    write_taskset_and_job_to_db()

    database.commit()
    db.close()
