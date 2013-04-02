#!/usr/bin/python

import math, sys, re, io, copy
import threading, thread
# variables extracted from the input file
num_of_tasks_ = 0
total_time_ = 0
power_list_ = []
EE_or_not_ = False
tasks_ = {}
key_list_ = []
freq_list_ = [1188, 918, 648, 384]
in_scheduler_ = ""
# variables used during computation
sched_list_ = []
result_list_ = []
best_energy_sofar_ = 0

threadlock = threading.Lock()

def non_EE_scheduler_( selection_list_ = [] ):
    global num_of_tasks_, total_time_, freq_list_, tasks_, sched_list_, result_list_, key_list_, in_scheduler_
    if selection_list_ == []:
        print "Error: No frequency selected for each task. return."
        return
    sched_list_ = []
    result_list_ = []
    for i in range(0, total_time_):
        for j in range(0, len(key_list_)):
            key_ = key_list_[j]
            if i%tasks_[key_][0] == 0:
                if sched_list_ == []:
                    if in_scheduler_ == "EDF":
                        # add the new task into the sched_list (key_, time_still_need, deadline_)
                        sched_list_.append( [key_,
                                             tasks_[key_][selection_list_[j]],
                                             (i+tasks_[key_][0])] )
                    elif in_scheduler_ == "RM":
                        # add the new task into the sched_list (key_, time_still_need, period_)
                        sched_list_.append( [key_,
                                             tasks_[key_][selection_list_[j]],
                                             tasks_[key_][0]] )
                    else:
                        print "Error: wrong scheduling scheme. return."
                        return -1
                elif key_ in zip(*sched_list_)[0]:
                    print "Cannot find feasible schedule. %s miss the deadline at time, %d." % (key_, i)
                    result_list_ = []
                    return -1
                else:
                    if in_scheduler_ == "EDF":
                        # add the new task into the sched_list (key_, time_still_need, deadline_)
                        sched_list_.append( [key_,
                                             tasks_[key_][selection_list_[j]],
                                             (i+tasks_[key_][0])] )
                    elif in_scheduler_ == "RM":
                        # add the new task into the sched_list (key_, time_still_need, period_)
                        sched_list_.append( [key_,
                                             tasks_[key_][selection_list_[j]],
                                             tasks_[key_][0]] )
        if sched_list_ != []:
            # find EDF or highest priority
            idx_ = zip( *sched_list_ )[2].index( min(zip(*sched_list_)[2]) )
            sched_list_[idx_][1] -= 1
            # for ease of design and implemenation but not efficiency
            # (current time index, the key, the frequency, the power)
            result_list_.append( [i, sched_list_[idx_][0], freq_list_[0], power_list_[0]] )
            if sched_list_[idx_][1] == 0:
                del sched_list_[idx_]
        else:
            result_list_.append( [i, "IDLE", "IDLE", power_list_[-1]] )
    return sum( zip(*result_list_)[-1] )

def print_result_( ):
    global result_list_
    if result_list_ == []:
        print "Error: result_list_ empty, return."
        return
    else:
        print "<time started>  <task>  <freq> <runtime> <energy>"
        key_ = result_list_[0][1]
        freq_ = result_list_[0][2]
        power_ = result_list_[0][3]
        starttime_ = 0
        final_energy_ = 0.0
        final_idle_ = 0
        for list_ in result_list_:
            if list_[1] == key_:
                continue
            print "%-15s %-7s %-6s %-9s %s" % (starttime_, key_, freq_, (list_[0]-starttime_), (float)(list_[0]-starttime_)*power_/1000)
            if key_ == "IDLE":
                final_idle_ += list_[0]-starttime_
            final_energy_ += ((float)(list_[0]-starttime_)*power_/1000)
            starttime_ = list_[0]
            key_ = list_[1]
            freq_ = list_[2]
            power_ = list_[3]
        # print the last entry
        print "%-15s %-7s %-6s %-9s %s" % (starttime_, key_, freq_, (total_time_-starttime_), (float)(total_time_-starttime_)*power_/1000)
        final_energy_ += ((float)(total_time_-starttime_)*power_/1000)
        if result_list_[-1][1] == "IDLE":
            final_idle_ += total_time_-starttime_
        rate_ = (float)(final_idle_) / (total_time_)* 100
        print "total energy: %s. total execution time: %s. idle time vs time: %s percent" % (final_energy_, total_time_, rate_)
    return

# implement the recursive algorithm
def EE_scheduler_( tmp_sched_list_, last_time_, cur_time_, cur_result_list_ ):
    global total_time_, freq_list_, tasks_, key_list_, in_scheduler_, best_energy_sofar_, result_list_
    # check the arrival of new tasks
    for key_ in key_list_:
        # if a new task arrives during the interval or if it is the beginning timing
        if cur_time_/tasks_[key_][0]-last_time_/tasks_[key_][0] == 1 or cur_time_ == 0:
            if tmp_sched_list_ != [] and key_ in zip(*tmp_sched_list_)[0]:
                print "Cannot find feasible schedule. %s miss the deadline  at time." % key_
                return
            else:
                if in_scheduler_ == "EDF":
                    # add the new task into the sched_list (key_, execution_time_, freq_idx_, deadline_, deadline_)
                    tmp_sched_list_.append( [key_,
                                             -1,
                                             -1,
                                             ((cur_time_/tasks_[key_][0]+1)*tasks_[key_][0]),
                                             (cur_time_/tasks_[key_][0]+1)*tasks_[key_][0]] )
                elif in_scheduler_ == "RM":
                    # add the new task into the sched_list (key_, execution_time_, freq_idx_, deadline_, period_)
                    tmp_sched_list_.append( [key_,
                                             -1,
                                             -1,
                                             ((cur_time_/tasks_[key_][0]+1)*tasks_[key_][0]),
                                             tasks_[key_][0]] )
                else:
                    print "Error: wrong in_scheduler_ scheme."
        # in brute-force optimization, this could happen
        elif cur_time_/tasks_[key_][0]-last_time_/tasks_[key_][0] > 1:
            print "Error: Cannot find feasible schedule. More than one tasks arrival in interval."
            return
    # schedule IDLE
    if tmp_sched_list_ == []:
        # find the time of the next earliest task
        tmp_next_arrival_list_ = []
        for key_ in key_list_:
            tmp_next_arrival_list_.append( (cur_time_/tasks_[key_][0]+1)*tasks_[key_][0] )
        # schedule to the point of next task
        et_ = min( tmp_next_arrival_list_ ) - cur_time_
        if cur_time_+et_ > total_time_:
            cur_result_list_.append( [cur_time_, "IDLE", "IDLE", power_list_[-1], power_list_[-1]*(total_time_-cur_time_)] )
            tmp_energy_sum_ = sum( zip(*cur_result_list_)[-1] )
            # if better than the best schedule so far, update the best schedule
            threadlock.acquire()
            if tmp_energy_sum_ < best_energy_sofar_ or best_energy_sofar_ == 0:
                best_energy_sofar_ = tmp_energy_sum_
                result_list_ = []
                result_list_ = copy.deepcopy( cur_result_list_ )
                threadlock.release()
            else:
                threadlock.release()
        else:
            cur_result_list_.append( [cur_time_, "IDLE", "IDLE", power_list_[-1], power_list_[-1]*et_] )
            # recursively invoke the scheduling function
            EE_scheduler_( tmp_sched_list_, cur_time_, cur_time_+et_, cur_result_list_ )
    # schedule a task
    else:
        # select the task with earliest deadline/highest priority, find the next scheduling point
        idx_ = zip( *tmp_sched_list_ )[-1].index( min(zip(*tmp_sched_list_)[-1]) )
        key_ = tmp_sched_list_[idx_][0]

        # for multiprogramming purpose
        if last_time_ < 0:
            last_time_ *= -1
            # use the specified frequency_ and et_
            et_ = tasks_[key_][last_time_]
            last_time_ = 0
            # if cannot meet deadline, continue
            if cur_time_ + et_ >= tmp_sched_list_[idx_][-2]:
                return
            freq_idx_ = tasks_[key_][1:].index(et_)
            # duplicate a new schedule list and remove the scheduled task
            arg_tmp_sched_list_ = copy.deepcopy( tmp_sched_list_ )
            arg_tmp_sched_list_[idx_][1] = et_
            arg_tmp_sched_list_[idx_][2] = freq_idx_
            # find the next earliest conficting task with higher priority
            greater_deadline_list_ = []
            for tmp_key_ in tasks_.keys():
                # for RM case, find the one with higher priority
                if tmp_key_ != key_ and in_scheduler_ == "RM" and tasks_[tmp_key_][0] < tmp_sched_list_[idx_][-1] and (cur_time_+et_)/tasks_[tmp_key_][0] - (cur_time_/tasks_[tmp_key_][0]) > 0:
                    greater_deadline_list_.append( (key_, (cur_time_/tasks_[tmp_key_][0]+1)*tasks_[tmp_key_][0]) )
                # for EDF case, find the one with eariler deadline
                if tmp_key_ != key_ and in_scheduler_ == "EDF" and ( (cur_time_/tasks_[tmp_key_][0]+2)*tasks_[tmp_key_][0] < tmp_sched_list_[idx_][-1] ) and (cur_time_+et_)/tasks_[tmp_key_][0] - (cur_time_/tasks_[tmp_key_][0]) > 0:
                    greater_deadline_list_.append( (key_, (cur_time_/tasks_[tmp_key_][0]+1)*tasks_[tmp_key_][0]) )
            # if no conficting task, schedule to et_
            if greater_deadline_list_ == []:
                actual_et_ = et_
            # compute the actual scheduling time
            else:
                actual_et_ = (min(zip(*greater_deadline_list_)[1]) - cur_time_)
            # if reach the total time
            if cur_time_+actual_et_ > total_time_:
                cur_result_list_.append( [cur_time_, tmp_sched_list_[idx_][0], freq_list_[freq_idx_], power_list_[freq_idx_], power_list_[freq_idx_]*(total_time_-cur_time_)] )
                tmp_energy_sum_ = sum( zip(*cur_result_list_)[-1] )
                # if better than the best schedule so far, update the best schedule
                threadlock.acquire()
                if tmp_energy_sum_ < best_energy_sofar_ or best_energy_sofar_ == 0:
                    best_energy_sofar_ = tmp_energy_sum_
                    result_list_ = []
                    result_list_ = copy.deepcopy( cur_result_list_ )
                    threadlock.release()
                else:
                    threadlock.release()

            # if not reach the total time, keep scheduling
            else:
                # duplicate and update the result list
                arg_cur_result_list_ = copy.deepcopy( cur_result_list_ )
                arg_cur_result_list_.append( [cur_time_, tmp_sched_list_[idx_][0], freq_list_[freq_idx_], power_list_[freq_idx_], power_list_[freq_idx_]*actual_et_] )
                if actual_et_ == et_:
                    del arg_tmp_sched_list_[idx_]
                else:
                    # if not reach the total time, keep scheduling
                    arg_tmp_sched_list_[idx_][1] = et_ - actual_et_
                # recursively invoke the scheduling function
                EE_scheduler_( arg_tmp_sched_list_, cur_time_, cur_time_+actual_et_, arg_cur_result_list_ )
                arg_cur_result_list_ = []
                arg_tmp_sched_list_ = []

        # if it is an unscheduled task
        elif tmp_sched_list_[idx_][1] == -1:
            # for each frequency, check if the deadline can be met, and recursively invoke the function
            for et_ in tasks_[key_][1:]:
                # if cannot meet deadline, continue
                if cur_time_ + et_ >= tmp_sched_list_[idx_][-2]:
                    continue
                freq_idx_ = tasks_[key_][1:].index(et_)
                # duplicate a new schedule list and remove the scheduled task
                arg_tmp_sched_list_ = copy.deepcopy( tmp_sched_list_ )
                arg_tmp_sched_list_[idx_][1] = et_
                arg_tmp_sched_list_[idx_][2] = freq_idx_
                # find the next earliest conficting task with higher priority
                greater_deadline_list_ = []
                for tmp_key_ in tasks_.keys():
                    # for RM case, find the one with higher priority
                    if tmp_key_ != key_ and in_scheduler_ == "RM" and tasks_[tmp_key_][0] < tmp_sched_list_[idx_][-1] and (cur_time_+et_)/tasks_[tmp_key_][0] - (cur_time_/tasks_[tmp_key_][0]) > 0:
                        greater_deadline_list_.append( (key_, (cur_time_/tasks_[tmp_key_][0]+1)*tasks_[tmp_key_][0]) )
                    # for EDF case, find the one with eariler deadline
                    if tmp_key_ != key_ and in_scheduler_ == "EDF" and ( (cur_time_/tasks_[tmp_key_][0]+2)*tasks_[tmp_key_][0] < tmp_sched_list_[idx_][-1] ) and (cur_time_+et_)/tasks_[tmp_key_][0] - (cur_time_/tasks_[tmp_key_][0]) > 0:
                        greater_deadline_list_.append( (key_, (cur_time_/tasks_[tmp_key_][0]+1)*tasks_[tmp_key_][0]) )
                # if no conficting task, schedule to et_
                if greater_deadline_list_ == []:
                    actual_et_ = et_
                # compute the actual scheduling time
                else:
                    actual_et_ = (min(zip(*greater_deadline_list_)[1]) - cur_time_)
                # if reach the total time
                if cur_time_+actual_et_ > total_time_:
                    cur_result_list_.append( [cur_time_, tmp_sched_list_[idx_][0], freq_list_[freq_idx_], power_list_[freq_idx_], power_list_[freq_idx_]*(total_time_-cur_time_)] )
                    tmp_energy_sum_ = sum( zip(*cur_result_list_)[-1] )
                    # if better than the best schedule so far, update the best schedule
                    threadlock.acquire()
                    if tmp_energy_sum_ < best_energy_sofar_ or best_energy_sofar_ == 0:
                        best_energy_sofar_ = tmp_energy_sum_
                        result_list_ = []
                        result_list_ = copy.deepcopy( cur_result_list_ )
                        threadlock.release()
                    else:
                        threadlock.release()
                # if not reach the total time, keep scheduling
                else:
                    # duplicate and update the result list
                    arg_cur_result_list_ = copy.deepcopy( cur_result_list_ )
                    arg_cur_result_list_.append( [cur_time_, tmp_sched_list_[idx_][0], freq_list_[freq_idx_], power_list_[freq_idx_], power_list_[freq_idx_]*actual_et_] )
                    if actual_et_ == et_:
                        del arg_tmp_sched_list_[idx_]
                    else:
                        # if not reach the total time, keep scheduling
                        arg_tmp_sched_list_[idx_][1] = et_ - actual_et_
                    # recursively invoke the scheduling function
                    EE_scheduler_( arg_tmp_sched_list_, cur_time_, cur_time_+actual_et_, arg_cur_result_list_ )
                    arg_cur_result_list_ = []
                    arg_tmp_sched_list_ = []

        # if it is already scheduled before but not finished
        else:
            et_ = tmp_sched_list_[idx_][1]
            freq_idx_ = tmp_sched_list_[idx_][2]
            # if cannot meet deadline, continue
            if cur_time_ + et_ >= tmp_sched_list_[idx_][-2]:
                return
            # find the next earliest conficting task with higher priority
            greater_deadline_list_ = []
            for tmp_key_ in tasks_.keys():
                # for RM case, find the one with higher priority
                if tmp_key_ != key_ and in_scheduler_ == "RM" and (tasks_[tmp_key_][0] < tmp_sched_list_[idx_][-1]) and (cur_time_+et_)/tasks_[tmp_key_][0] - (cur_time_/tasks_[tmp_key_][0]) > 0:
                    greater_deadline_list_.append( (key_, (cur_time_/tasks_[tmp_key_][0]+1)*tasks_[tmp_key_][0]) )
                # for EDF case, find the one with eariler deadline
                if tmp_key_ != key_ and in_scheduler_ == "EDF" and ( (cur_time_/tasks_[tmp_key_][0]+2)*tasks_[tmp_key_][0] < tmp_sched_list_[idx_][-1] ) and (cur_time_+et_)/tasks_[tmp_key_][0] - (cur_time_/tasks_[tmp_key_][0]) > 0:
                    greater_deadline_list_.append( (key_, (cur_time_/tasks_[tmp_key_][0]+1)*tasks_[tmp_key_][0]) )
            # if no conficting task, schedule to et_
            if greater_deadline_list_ == []:
                actual_et_ = et_
            # compute the actual scheduling time
            else:
                actual_et_ = (min(zip(*greater_deadline_list_)[1]) - cur_time_)
            # if reach the total time
            if cur_time_+actual_et_ > total_time_:
                cur_result_list_.append( [cur_time_, tmp_sched_list_[idx_][0], freq_list_[freq_idx_], power_list_[freq_idx_], power_list_[freq_idx_]*(total_time_-cur_time_)] )
                tmp_energy_sum_ = sum( zip(*cur_result_list_)[-1] )
                # if better than the best schedule so far, update the best schedule
                threadlock.acquire()
                if tmp_energy_sum_ < best_energy_sofar_ or best_energy_sofar_ == 0:
                    best_energy_sofar_ = tmp_energy_sum_
                    result_list_ = []
                    result_list_ = copy.deepcopy( cur_result_list_ )
                    threadlock.release()
                else:
                    threadlock.release()
            # if not reach the total time, keep scheduling
            else:
                cur_result_list_.append( [cur_time_, tmp_sched_list_[idx_][0], freq_list_[freq_idx_], power_list_[freq_idx_], power_list_[freq_idx_]*actual_et_] )
                if actual_et_ == et_:
                    del tmp_sched_list_[idx_]
                else:
                    # if not reach the total time, keep scheduling
                    tmp_sched_list_[idx_][1] = et_ - actual_et_
                # recursively invoke the scheduling function
                EE_scheduler_( tmp_sched_list_, cur_time_, cur_time_+actual_et_, cur_result_list_ )

def main( ):
    global num_of_tasks_, total_time_, power_list_, EE_or_not_, tasks_, key_list_, in_scheduler_
    if len(sys.argv) >= 3:
        filename_ = sys.argv[1]
        in_file_ = open( filename_, 'r' )
        first_line_ = in_file_.readline().split()
        num_of_tasks_ = int(first_line_[0])
        total_time_ = int(first_line_[1])
        power_list_ = map(int, first_line_[2:])
        print "Fisrt line extracted: ",  num_of_tasks_, total_time_, power_list_
        in_scheduler_ = sys.argv[2]
    if len(sys.argv) == 4:
        EE_field_ = sys.argv[3]
        if EE_field_ == "EE":
            EE_or_not_ = True
    for i in range(0, num_of_tasks_):
        line_ = in_file_.readline().split()
        tasks_[line_[0]] = map(int, line_[1:])
        key_list_.append(line_[0])
    if not EE_or_not_ and (in_scheduler_ == "EDF" or "RM"):
        non_EE_scheduler_( [1]*num_of_tasks_ )
    elif EE_or_not_ and (in_scheduler_ == "EDF" or "RM"):
        try:
            # tackle the scheduling problem using 4 threads
            thread1 = myThread(1, "Scheduling Thread-")
            thread2 = myThread(2, "Scheduling Thread-")
            thread3 = myThread(3, "Scheduling Thread-")
            thread4 = myThread(4, "Scheduling Thread-")
            # start the threads
            thread1.start()
            thread2.start()
            thread3.start()
            thread4.start()
            # wait for all threads finishing
            thread1.join()
            thread2.join()
            thread3.join()
            thread4.join()
        except:
            print "Error"
    else:
        print "Error: wrong arguments: %s, %s." % (in_scheduler_, EE_field_)
        return
    
    print_result_()
    print tasks_
    return

class myThread (threading.Thread):
    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
    def run(self):
        print "Starting thread " + self.name, self.threadID
        EE_scheduler_([], -1*self.threadID, 0, [])
        print "Exiting thread " + self.name, self.threadID


if __name__ == "__main__":
    main( )
