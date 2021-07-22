#!/usr/bin/env python3

"""
Written by jdreal.
Github: 


"""

import time


def task_check(task):
    task_done = False
    while not task_done:
        if task.info.state == "success":
            taskStatus = 'OK'
            return taskStatus, task.info.result

        # if task.info.state == "running":
        #     time.sleep(0.35)
        #     continue

        if task.info.state == "error":
            taskStatus = 'Failed'
            return taskStatus, task.info.error
