#!/usr/bin/env python3
"""
Volcano Engine ML Task 管理脚本
功能：
- 提交任务前，检查是否存在同名且运行中的任务，若有则取消。
- 提交任务，获取 Task ID。
- 将TASK_ID写入文件task_id.txt中
- 等待任务进入 Running 状态（超时控制）。
- 实时流式输出日志（带重试，处理命令 panic）。
- 任务结束后检查最终状态，成功则退出 0，否则退出 1。
环境变量：
  TASK_NAME          : 任务名称
  TASK_CONFIG_FILE: 任务配置文件路径
  PENDDING_TIME_OUT    : 等待 Running 的超时时间（秒，默认 1800）
  INTERVAL           : 状态检查间隔（秒，默认 30）
"""

import os
import sys
import time
import json
import subprocess
import signal
def run_cmd(cmd, check=True, capture_output=True):
    """执行命令，返回输出或抛出异常"""
    result = subprocess.run(cmd, shell=True, capture_output=capture_output, text=True)
    if check and result.returncode != 0:
        print(f"Command failed: {cmd}\nSTDERR: {result.stderr}")
        sys.exit(result.returncode)
    return result

def run_cmd_live(cmd):
    """实时输出命令的标准输出，返回进程对象"""
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    for line in process.stdout:
        print(line, end='')
    process.wait()
    return process.returncode

def get_task_status(task_id):
    """获取任务状态，返回状态字符串，失败时返回 None"""
    try:
        result = run_cmd(f"volc ml_task get --id {task_id} --output json", check=True)
        data = json.loads(result.stdout)
        return data[0]['Status'] if isinstance(data, list) else data.get('Status')
    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"Warning: Failed to get task status: {e}")
        return None

def cancel_task(task_id):
    """取消任务"""
    print(f"Cancelling existing task {task_id}...")
    run_cmd(f"volc ml_task cancel --id {task_id}", check=False)

def submit_task(config_file, task_name):
    """提交任务，返回 task_id"""
    print(f"Submitting task with name: {task_name}")
    result = run_cmd(f"volc ml_task submit --conf {config_file} --task_name {task_name} --output json")
    data = json.loads(result.stdout)
    task_id = data.get('Id')
    if not task_id:
        print(f"Failed to get task ID from output: {result.stdout}")
        sys.exit(1)
    print(f"Task submitted, ID: {task_id}")
    return task_id

def wait_for_running(task_id, timeout, interval):
    """等待任务进入 Running 状态，超时或失败则退出"""
    start_time = time.time()
    while True:
        elapsed = time.time() - start_time
        if elapsed > timeout:
            print(f"⏰ Timeout reached after {timeout}s. Task did not become Running.")
            sys.exit(1)

        status = get_task_status(task_id)
        if status is None:
            # 获取失败，继续等待
            time.sleep(interval)
            continue

        print(f"Current status: {status}")

        if status == "Running":
            print("✅ Task is now Running.")
            break
        elif status in ("Killing", "Failed", "Killed", "Exception"):
            print(f"❌ Task failed with status: {status}")
            sys.exit(1)
        else:
            print(f"Waiting... next check in {interval}s")
            time.sleep(interval)

def wait_for_completion(task_id, interval):
    """等待任务进入终态，返回最终状态"""
    while True:
        status = get_task_status(task_id)
        if status is None:
            # 获取失败，继续等待
            time.sleep(interval)
            continue

        print(f"Current status: {status}")

        # 终态判断：Success, Failed, Killed, Exception, Killing? Killing是过渡状态，可能最终变为Killed。
        if status in ("Success", "Failed", "Killed", "Exception"):
            return status
        elif status == "Killing":
            # Killing可能很快变成Killed，继续等待
            pass
        # 其他状态继续等待
        time.sleep(interval)

def fetch_logs_on_failure(task_id):
    """如果任务失败，获取并打印日志"""
    print("Fetching logs due to task failure...")
    cmd = f"volc ml_task logs --task {task_id} -i worker-0"
    try:
        # 使用 run_cmd_live 实时输出，或一次性获取
        # 这里使用 run_cmd_live 以便实时看到日志
        run_cmd_live(cmd)
    except Exception as e:
        print(f"Failed to fetch logs: {e}")

def write_taskid_to_file(task_id, file_path):
    with open(file_path, "w") as f:
        f.write(task_id)
    print(f"已将task_id:{task_id}成功写入文件{file_path}")

def main():
    
    # 读取环境变量
    task_name = os.environ.get('TASK_NAME')
    config_file = os.environ.get('TASK_CONFIG_FILE')
    timeout = int(os.environ.get('PENDDING_TIME_OUT', 1800))
    interval = int(os.environ.get('INTERVAL', 30))
    taskid_file = os.environ.get('TASKID_FILE')

    if not task_name or not config_file:
        print("Error: TASK_NAME and TASK_CONFIG_FILE must be set.")
        sys.exit(1)

    # 1. 检查并取消已存在的同名运行中任务
    print(f"Checking for existing tasks with name: {task_name}")
    result = run_cmd(f"volc ml_task list --output json", check=True)
    tasks = json.loads(result.stdout)
    running_tasks = [t for t in tasks if t.get('JobName') == task_name and t.get('Status') in ('Running', 'Initialized', 'Queue', 'Staging')]
    for t in running_tasks:
        cancel_task(t['JobId'])

    # 2. 提交新任务
    task_id = submit_task(config_file, task_name)
    write_taskid_to_file(task_id, taskid_file)

    # 3. 等待 Running
    wait_for_running(task_id, timeout, interval)

    # 4. 等待任务完成
    final_status = wait_for_completion(task_id, interval)

    # 5. 根据最终状态处理
    if final_status == "Success":
        print("✅ Task succeeded!")
        sys.exit(0)
    else:
        # 失败，获取日志
        fetch_logs_on_failure(task_id)
        print(f"❌ Task failed! status: {final_status}")
        sys.exit(1)

if __name__ == "__main__":
    main()