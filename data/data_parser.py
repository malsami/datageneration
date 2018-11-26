import sqlite3

taskset_id = []
taskset_list = []


def parse_to_file(path='good_tasksets90'):
    with open('good_tasksets90') as f:
        # Each taskset is stored as a single line in the file
        for line in f:
            taskset_id.append(eval(line)[0])
            taskset_list.append(eval(line)[1])

# Good_Task = 1, Bad_Task = -1
def write_tasks_db(taskset_list, task_exit = 1):

    taskset_ctr = 0
    for taskset in taskset_list:
        task_ctr = 0
        for task in taskset:
            proto_task = task[1]  # Weil 1st 'True|False' ist.
            job = proto_task[0]['jobs']

            db_taskset = (taskset_ctr, task_exit)
            # print(task_ctr)
            task_prop = (task_ctr, taskset_ctr,
                         proto_task[0]['priority'],
                         proto_task[0]['deadline'],
                         proto_task[0]['quota'],
                         proto_task[0]['caps'],
                         proto_task[0]['cores'],
                         proto_task[0]['pkg'],
                         proto_task[0]['offset'],
                         proto_task[0]['config']['arg1'],
                         proto_task[0]['period'],
                         proto_task[0]['numberofjobs'])

            db.execute('INSERT INTO Task VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', task_prop)
            write_jb_db(job, task_ctr, taskset_ctr)
            task_ctr += 1

        db.execute('INSERT INTO GoodTaskSet VALUES (?,?)', db_taskset)
        taskset_ctr += 1


# proto_task = taskset_list[0][0][1]

def write_jb_db(job, task_ctr, taskset_ctr):
    for key in job:
        start_date = job[key][0]
        end_date = job[key][1]
        exit_value = job[key][2]

        db_job = (int(key), task_ctr, taskset_ctr, start_date, end_date, exit_value)

        db.execute('INSERT INTO Job VALUES (?,?,?,?,?,?)', db_job)


if __name__ == "__main__":

    database = sqlite3.connect('example.db')
    db = database.cursor()

    db.execute('DROP TABLE IF EXISTS Task')
    db.execute('DROP TABLE IF EXISTS Job')
    db.execute('DROP TABLE IF EXISTS GoodTaskSet')
    db.execute('DROP TABLE IF EXISTS BadTaskSet')

    db.execute(
        '''
        CREATE TABLE IF NOT EXISTS GoodTaskSet
        (Set_ID INTEGER,
        Exit_Value INT,
        PRIMARY KEY (Set_ID)
        )
        '''


    )

    db.execute(
        '''
        CREATE TABLE IF NOT EXISTS Task 
        (Task_ID INTEGER, 
         Set_ID INTEGER, 
         Priority INT, 
         Deadline INT, 
         Quota STRING, 
         CAPS INT,
         CORES INT,
         PKG STRING, 
         OFFSET INT,
         Arg INT, 
         Period INT, 
         Number_of_Jobs INT,
         PRIMARY KEY (Task_ID, Set_ID),
         FOREIGN KEY (Set_ID) REFERENCES TaskSet(Set_ID)
         )
         '''
    )

    db.execute(
        '''CREATE TABLE IF NOT EXISTS Job 
        (Job_ID INTEGER, 
        Task_ID INTEGER, 
        Set_ID INTEGER, 
        Start_Date INT, 
        End_Date INT, 
        Exit_Value STRING, 
        PRIMARY KEY (Job_ID,TASK_ID,SET_ID),
        FOREIGN KEY(TASK_ID) REFERENCES Task(Task_ID),
        FOREIGN KEY(Set_ID) REFERENCES TaskSet(Set_ID)
        )
        '''
    )

    parse_to_file()
    write_tasks_db(taskset_list)

    database.commit()
    db.close()