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

def main():
    
    # 读取环境变量
    remote_dir = os.environ.get('REMOTE_DIR')
    ak = os.environ.get('AOSS_AK')
    sk = os.environ.get('AOSS_SK')
    case_type= os.environ.get("CASE_TYPE")
    remote_endpoint = "white-bucket.aoss.cn-sh-01b.sensecoreapi-oss.cn"
    if remote_dir.endswith("/"):
        remote_dir = remote_dir[:-1]
    run_cmd("wget https://quark.aoss.cn-sh-01.sensecoreapi-oss.cn/ads-cli/release/v1.10.0/ads-cli")
    run_cmd("chmod +x ads-cli")
    run_cmd(f"mkdir output || true && ./ads-cli -q cp s3://{ak}:{sk}@{remote_endpoint}/{remote_dir}/{case_type} ./output")
    

if __name__ == "__main__":
    main()