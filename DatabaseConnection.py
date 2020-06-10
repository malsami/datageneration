import sqlite3
from time import localtime

class DatabaseConnection:
    def __init__(self, name, existing=False):
        date = localtime()
        date_string = '{year}_{month}_{day}_{hour}_{minute}_{second}'.format(year=date.tm_year,
                                                                             month=date.tm_mon,
                                                                             day=date.tm_mday,
                                                                             hour=date.tm_hour,
                                                                             minute=date.tm_min,
                                                                             second=date.tm_sec)
        if existing:
            self.db = sqlite3.connect(name)
        else:
            self.db = sqlite3.connect(name+date_string+'.db')
        self.cursor =self.db.cursor()
        self.create_tables()
        self.tasks = {}
        self.taskset_counter = -1
        self.job_counter = -1
        self.task_counter = -1
        if existing:
            self.read_tasks_and_counter()

    def read_tasks_and_counter(self):
        # TODO:
        #  read Task table and fill self.tasks dict
        #  read size of TaskSet and set self.taskset_counter
        #  read size of Job and set self.job_counter
        read_tasks = ('SELECT * FROM Task')
        pass

    def create_tables(self):
        #TaskSet
        self.cursor.execute(
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
        # Task
        self.cursor.execute(
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
        # Jobs
        self.cursor.execute(
            '''CREATE TABLE IF NOT EXISTS Job 
            (Set_ID INTEGER, 
            Task_ID INTEGER, 
            Job_ID INTEGER,
            Start_Date INT, 
            End_Date INT, 
            Exit_Value STRING, 
            TaskSet_Task_ID INT,
            TaskSet_Job_Number INT,
            PRIMARY KEY (TASK_ID,SET_ID, Job_ID),
            FOREIGN KEY(TASK_ID) REFERENCES Task(Task_ID),
            FOREIGN KEY(Set_ID) REFERENCES TaskSet(Set_ID)
            )
            '''
        )
        self.commit()

    def task_to_db(self, task):
        try:
            self.tasks[self.get_task_hash(task)]
        except KeyError:
            self.task_counter += 1
            self.tasks[self.get_task_hash(task)] = self.task_counter
            task_values = [self.task_counter,  # task_id
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
            self.cursor.execute('INSERT INTO Task VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', task_values)
            self.commit()

    def put_job_to_Jobs_table(self, job):
        if len(job) != 8:
            raise Exception("not enough values to write")
        # SET_ID, Task_ID, Job_ID, Start_Date, End_Date, Exit_Value, TaskSet_Task_ID, TaskSet_Job_Number
        self.cursor.execute('INSERT INTO Job VALUES (?,?,?,?,?,?,?,?)', job)

    def put_taskset_to_TaskSet_table(self, taskset):
        if len(taskset) != 6:
            raise Exception("not enough values to write")
        # SET_ID, Successful, TASK1_ID, TASK2_ID, TASK3_ID, TASK4_ID
        self.cursor.execute('INSERT INTO TaskSet VALUES (?,?,?,?,?,?)', taskset)

    def taskset_to_db(self, taskset):
        self.taskset_counter += 1
        success = self.calculate_success(taskset)
        taskset_values = [self.taskset_counter, success]
        for task in taskset:
            task_id = self.tasks[self.get_task_hash(task)]
            taskset_values.append(task_id)
            taskset_task_id = task['id']
            for job_number, job in task['jobs'].items():
                if len(job) != 3:
                    continue
                self.job_counter += 1
                try:
                    start_date, stop_date, exit_value = job
                    self.put_job_to_Jobs_table(job=(self.taskset_counter,
                                                    task_id,
                                                    self.job_counter,
                                                    start_date,
                                                    stop_date,
                                                    exit_value,
                                                    taskset_task_id,
                                                    int(job_number)))

                except IndexError as e:
                    print('there was an error: ', job, '\n and the task: ', task)
        taskset_values = taskset_values + [-1] * (6 - len(taskset_values))
        self.put_taskset_to_TaskSet_table(taskset=taskset_values)

    def close(self):
        self.cursor.close()

    def commit(self):
        self.db.commit()

    @staticmethod
    def calculate_success(taskset):
        successful = True
        for task in taskset:
            for _, job in task['jobs'].items():
                try:
                    successful &= job[2] == 'EXIT'
                except IndexError:
                    return 0
        return 1 if successful else 0

    @staticmethod
    def get_task_hash(task):
        # returns a string containing 52 digits per task
        # print(task)
        PKGTOINT = {'hey': 1,
                    'pi': 2,
                    'tumatmul': 3,
                    'cond_mod': 4
                    }
        hash_value = ''
        hash_value += str(PKGTOINT[task['pkg']])
        hash_value += str(task['priority']).zfill(3)  # fine
        hash_value += str(task['deadline']).zfill(5)
        hash_value += str(task['period']).zfill(5)
        hash_value += str(task['criticaltime']).zfill(5)
        hash_value += str(task['numberofjobs']).zfill(3)
        hash_value += str(task['offset']).zfill(5)
        hash_value += task['quota'][:-1].zfill(3)
        hash_value += str(task['caps']).zfill(3)
        hash_value += str(task['cores']).zfill(2)
        hash_value += str(task['coreoffset']).zfill(2)
        hash_value += str(task['config']['arg1']).zfill(15)  # todo, can be much bigger

        return hash_value