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
            return task.info.result

        if task.info.state == "running":
            time.sleep(0.35)

        if task.info.state == "error":
            print("发生错误：", task.info.error)
            task_done = True
