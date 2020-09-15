from DatabaseConnection import DatabaseConnection

def read_from_old_format(db, path='./data/', files=('bad_tasksets','good_tasksets')):
    good_read, bad_read = True,True
    good_finished, bad_finished = False, False
    with open(path+files[0],'r') as bad_taskset_file:
        with open(path+files[1],'r') as good_taskset_file:
            good_taskset = ''
            bad_taskset = ''
            good_taskset_amount = 0
            bad_taskset_amount = 0
            good_taskset_level_count = 0
            bad_taskset_level_count = 0
            end_of_line = '])\n'
            start_of_line = ('(1,', '(2,', '(3,')
            while not (good_finished and bad_finished):
                # if a file is not done, proceed
                if (not good_read) and (not bad_read):
                    if not bad_finished:
                        bad_read = True
                    if not good_finished:
                        good_read = True
                #if good_taskset_level_count == bad_taskset_level_count and good_taskset_level_count == 3:
                #    return
                #good
                if good_read:
                    good_char = good_taskset_file.read(1)
                if good_read and not good_char:
                    print("end of good file")
                    good_finished = True
                    good_read = False
                if good_read:
                    good_taskset += good_char
                    if good_taskset[:5] in start_of_line:
                        good_taskset_amount = 0
                        good_taskset_level_count += 1
                        print('now on good level ',good_taskset_level_count)
                        db.create_tables_for_taskset_size(good_taskset_level_count)
                        good_taskset = ''
                    if good_taskset == end_of_line:
                        print('finished line in good')
                        good_taskset = ''
                        good_read = False
                    if good_char == ')' and len(good_taskset) > 2:
                        #print(good_taskset)
                        try:
                            _, good_tasksetInfo = eval(good_taskset[2:])
                            good_taskset_amount += 1
                            if good_taskset_amount % 1000 == 0:
                                print('processed ', good_taskset_amount, 'good tasksets')
                                db.commit()
                            if len(good_tasksetInfo) == 1:
                                db.add_task_to_db(good_tasksetInfo[0])
                            db.add_taskset_to_db(good_tasksetInfo,good_taskset_level_count)
                            good_taskset = ''
                        except BaseException as b:
                            print('good')
                            print(good_taskset)
                            raise b
                # bad
                if bad_read:
                    bad_char = bad_taskset_file.read(1)
                if bad_read and not bad_char:
                    print("end of bad file")
                    bad_finished = True
                    bad_read = False
                if bad_read:
                    bad_taskset += bad_char
                    if bad_taskset[:5] in start_of_line:
                        bad_taskset_amount = 0
                        bad_taskset_level_count += 1
                        print('now on bad level ', bad_taskset_level_count)
                        db.create_tables_for_taskset_size(bad_taskset_level_count)
                        bad_taskset = ''
                    if bad_taskset == end_of_line:
                        print('finished line in bad')
                        bad_taskset = ''
                        bad_read = False
                    if bad_char == ')' and len(bad_taskset) > 2:
                        try:
                            _, bad_tasksetInfo = eval(bad_taskset[2:])
                            bad_taskset_amount += 1
                            if bad_taskset_amount %1000 == 0:
                                print('processed ',bad_taskset_amount, 'bad tasksets')
                                db.commit()
                            if len(bad_tasksetInfo)==1:
                                db.add_task_to_db(bad_tasksetInfo[0])
                            db.add_taskset_to_db(bad_tasksetInfo,bad_taskset_level_count)
                            bad_taskset = ''
                        except BaseException as b:
                            print('bad')
                            print(bad_taskset)
                            raise b
                            bad_taskset = ''

db_connection = DatabaseConnection(name='./data/test_db')
read_from_old_format(db=db_connection)
print('done')
db_connection.close()
