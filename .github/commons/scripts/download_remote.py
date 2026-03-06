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


def main():
    
    # 读取环境变量
    remote_dir = os.environ.get('REMOTE_DIR')
    ak = os.environ.get('AOSS_AK')
    sk = os.environ.get('AOSS_SK')
    case_type= os.environ.get("CASE_TYPE")
    remote_endpoint = "kairos-ci.aoss.cn-sh-01b.sensecoreapi-oss.cn"
    run_cmd(f"mkdir output || true && ads-cli cp s3://{ak}:{sk}@{remote_endpoint}/{remote_dir}/{case_type} ./output")
    

if __name__ == "__main__":
    main()