import sqlite3
from time import localtime

class DatabaseConnection:
    def __init__(self, name, existing=False):
        date = localtime()
        self.level={}
        self.task_hashes_to_id = {}
        self.job_counter = 0
        self.task_counter = 0
        self.provided_hashes = []
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
        self.create_task_table(existing)
        if existing:
            self.create_levels_and_read_counter()


    def create_task_table(self, existing):
        # Task
        if existing:
            self.cursor.execute('SELECT * from Task')
            rows = self.cursor.fetchall()
            for Task_ID, Priority, Deadline, Quota, CAPS, PKG, ARG, CORES, COREOFFSET , CRITICALTIME, Period, Number_of_Jobs, OFFSET in rows:
                task = {'pkg':PKG,
                        'priority': Priority,
                        'deadline': Deadline,
                        'period': Period,
                        'criticaltime': CRITICALTIME,
                        'numberofjobs': Number_of_Jobs,
                        'offset': OFFSET,
                        'quota': Quota,
                        'caps':CAPS,
                        'cores':CORES,
                        'coreoffset':COREOFFSET,
                        'config':{'arg1':ARG}
                }
                hash = self.get_task_hash(task)
                self.task_hashes_to_id[hash] = Task_ID
                self.task_counter += 1
        else:
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
            self.commit()

    def create_levels_and_read_counter(self):
        table_name_query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        self.cursor.execute(table_name_query)
        table_names = self.cursor.fetchall()
        for name in table_names:
            _, index = name[0].split('_')
            self.create_tables_for_taskset_size(int(index))
        for key in self.level:
            for table, table_size in (('taskset_table','taskset_table_size'),
                                      ('job_table','job_table_size'),
                                      ('possible_table','possible_table_size')):
                taskset_query = 'SELECT COUNT(*) FROM {}'.format(self.level[key][table])
                self.cursor.execute(taskset_query)
                self.level[key][table_size] = int(self.cursor.fetchall()[0])


    def create_tables_for_taskset_size(self, size):
        # has to be called from outside before tasksets can be written
        try:
            self.level[size]
            print('tables and info already exists')
        except KeyError:
            self.level[size] = {
                'taskset_table' : 'TaskSet_{}'.format(str(size)),
                'taskset_table_size': 0,
                'job_table' : 'Job_{}'.format(str(size)),
                'job_table_size' : 0,
                'possible_table': 'PossibleTaskSets_{}'.format(str(size)),
                'possible_table_size': 0
            }
            self._create_taskset_job_and_possible_table_for_size(size)

    def _create_taskset_job_and_possible_table_for_size(self, n):
        self._create_taskset_table_of_size(n)
        self._create_possible_table_for_size(n)
        self._create_job_table_for_size(n)

    def _create_taskset_table_of_size(self, n):
        query = 'CREATE TABLE IF NOT EXISTS {} (Set_ID INTEGER, Successful INT, '.format(self.level[n]['taskset_table'])
        for i in range(1,n+1):
            query += 'TASK{}_ID INTEGER, '.format(str(i))
        query += 'PRIMARY KEY (Set_ID))'
        self.cursor.execute(query)
        self.commit()

    def _create_job_table_for_size(self, n):
        query = 'CREATE TABLE IF NOT EXISTS {}'.format(self.level[n]['job_table'])
        query += '(Set_ID INTEGER, ' \
                 'Task_ID INTEGER, ' \
                 'Job_ID INTEGER, ' \
                 'Start_Date INT, ' \
                 'End_Date INT, ' \
                 'Exit_Value STRING, ' \
                 'TaskSet_Task_ID INT, ' \
                 'TaskSet_Job_Number INT, ' \
                 'PRIMARY KEY (TASK_ID,SET_ID, Job_ID), ' \
                 'FOREIGN KEY(TASK_ID) REFERENCES Task(Task_ID), '
        query += 'FOREIGN KEY(Set_ID) REFERENCES {}(Set_ID))'.format(self.level[n]['taskset_table'])
        self.cursor.execute(query)
        self.commit()

    def _create_possible_table_for_size(self, n):
        query = 'CREATE TABLE IF NOT EXISTS {} (Possible_ID INTEGER, TasksetHash STRING,PRIMARY KEY (Possible_ID))'.format(self.level[n]['possible_table'])
        self.cursor.execute(query)
        self.commit()


    def get_available_taskset_sizes(self):
        return list(self.level.keys())

    def get_taskset_ids_of_size(self, successful, size) -> [int]:
        successful_condition = 'Successful == 1' if successful else 'Successful == 1'
        # return list of taskset ids of all tasksets of size n, if successful is True then only the successful otherwise the unsuccessful
        self.cursor.execute('SELECT SET_ID from {tasksetTable} where {successful}'.format(tasksetTable=self.level[size]['taskset_table'],successful=successful_condition))
        rows = self.cursor.fetchall()
        return [r[0] for r in rows]

    def get_hash_of_taskset(self, taskset_id, size) -> str:
        self.cursor.execute('SELECT * from {} where SET_ID == {}'.format(self.level[size]['taskset_table'],taskset_id))
        taskset_row = self.cursor.fetchall()
        taskset_hash = ''
        for i in taskset_row[2:]:
            for hash, task_id in self.task_hashes_to_id.items():
                if task_id == i:
                    taskset_hash += hash
        return taskset_hash

    def status(self) -> str:
        status = 'Current Database Status:\n'
        status += 'Tasks in Task Table: {}\n'.format(self.task_counter)
        for size, values in self.level.items():
            status += 'Taskset size: {}:\n'.format(size)
            status += 'Tasksets in Table: {}\n'.format(values['taskset_table_size'])
            status += 'Hashes in Possible Table: {}\n'.format(values['possible_table_size'])
            status += 'Jobs in Job Table: {}\n'.format(values['job_table_size'])
        return status


    def have_possible_tasksets_of_size(self, size):
        return self.level[size]['possible_table_size'] > 0

    def get_n_hashes_of_size_from_possible(self, n, size) -> []:
        #max n is currently 1000
        # but overhead necessary, as some might be already in execution, thus testing for self.provided_hashes
        self.cursor.execute('SELECT Possible_ID, TasksetHash from {possible_table} LIMIT 1000'.format(possible_table=self.level[size]['possible_table']))
        counter = 0
        return_list = []
        rows = self.cursor.fetchall()
        if not rows:
            return return_list
        for Possible_ID, TasksetHash in rows:
            if TasksetHash not in self.provided_hashes:
                self.provided_hashes.append(TasksetHash)
                counter += 1
                return_list.append(TasksetHash)
            if counter == n:
                return return_list
        return return_list

    def add_taskset_hash_to_possible(self, *, taskset_hash, size):
        if self.check_hashed_taskset_in_taskset_or_possible(taskset_hash=taskset_hash, size=size):
            return
        self.level[size]['possible_table_size'] += 1
        query = 'INSERT INTO {possible_table} VALUES (?,?)'.format(possible_table=self.level[size]['possible_table'])
        self.cursor.execute(query, (self.possible[size],taskset_hash))

    def check_hashed_taskset_in_taskset_or_possible(self, taskset_hash, size) -> bool:
        # check if in possible
        query = 'SELECT * FROM {possible_table} WHERE TasksetHash=={taskset_hash}'.format(
            possible_table=self.level[size]['possible_table'],
            taskset_hash=taskset_hash)
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        if rows:
            return True
        # else check if in taskset table
        task_hash_length = len(taskset_hash)/size
        task_ids = [self.task_hashes_to_id(taskset_hash[i*task_hash_length:(i+1)*task_hash_length])for i in range(size)]
        query = 'SELECT * FROM {taskset} WHERE TASK1_ID=={task_id}'.format(taskset=self.level[size]['taskset_table'],
                                                                           task_id=task_ids[0])
        for i in range(1,len(task_ids)):
            query += ' and TASK{ID}_ID=={task_id}'.format(ID=i, task_id=task_ids[i])
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        if rows:
            return True
        else:
            return False


    def _remove_taskset_hash_from_possible(self, taskset_hash, size):
        query = 'DELETE FROM {} WHERE TasksetHash=={}'.format(self.level[size]['possible_table'],taskset_hash)
        self.cursor.execute(query)
        self.commit()
        self.level[size]['possible_table_size'] -= 1


    def _add_job_to_Jobs_table(self, job, taskset_size):
        if len(job) != 8:
            raise Exception("not enough values to write")
        query = 'INSERT INTO {} VALUES (?,?,?,?,?,?,?,?)'.format(self.level[taskset_size]['job_table'])
        # SET_ID, Task_ID, Job_ID, Start_Date, End_Date, Exit_Value, TaskSet_Task_ID, TaskSet_Job_Number
        self.cursor.execute(query, job)

    def _add_taskset_to_TaskSet_table(self, taskset, size):
        # SET_ID, Successful, TASK1_ID, ...
        query = 'INSERT INTO {} VALUES (?,?,?'.format(self.level[size]['taskset_table'])
        for _ in range(2,size+1):
            query += ',?'
        query += ')'
        #print(query,size, taskset)
        self.cursor.execute(query, taskset)

    def add_task_to_db(self, task):
        try:
            self.task_hashes_to_id[self.get_task_hash(task)]
        except KeyError:
            self.task_hashes_to_id[self.get_task_hash(task)] = self.task_counter
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
            self.task_counter += 1

    def add_taskset_to_db(self, taskset, size):
        success = self.calculate_success(taskset)
        taskset_values = [self.level[size]['taskset_table_size'], success]
        for task in taskset:
            task_id = self.task_hashes_to_id[self.get_task_hash(task)]
            taskset_values.append(task_id)
            taskset_task_id = task['id']
            for job_number, job in task['jobs'].items():
                if len(job) != 3:
                    print('job that is to short: ',job, 'for task id', task_id, 'and taskset id', self.level[size]['taskset_table_size'])
                    continue
                try:
                    start_date, stop_date, exit_value = job
                    self._add_job_to_Jobs_table(job=(self.level[size]['taskset_table_size'],
                                                     task_id,
                                                     self.level[size]['job_table_size'],
                                                     start_date,
                                                     stop_date,
                                                     exit_value,
                                                     taskset_task_id,
                                                     int(job_number)), taskset_size=size)
                    self.level[size]['job_table_size'] += 1
                except IndexError as e:
                    print('there was an error: ', job, '\n and the task id: ', task_id, 'and taskset id', self.level[size]['taskset_table_size'])
        self._add_taskset_to_TaskSet_table(taskset=taskset_values, size=size)
        taskset_hash = ''
        for task in taskset:
            taskset_hash += self.get_task_hash(task)
        self._remove_taskset_hash_from_possible(taskset_hash, size)
        self.level[size]['taskset_table_size'] += 1

    def close(self):
        self.cursor.close()

    def commit(self):
        self.db.commit()

    @staticmethod
    def calculate_success(taskset):
        successful = True
        read_at_least_one_job = False
        for task in taskset:
            for _, job in task['jobs'].items():
                try:
                    successful &= job[2] == 'EXIT'
                    read_at_least_one_job = True
                except IndexError:
                    print('index error while calculating success with job',job, 'in taskset', taskset)
                    return 0
        return 1 if successful and read_at_least_one_job else 0

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
        hash_value += str(task['config']['arg1']).zfill(15)

        return hash_value
