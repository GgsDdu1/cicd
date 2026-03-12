#!/bin/bash
set -e
set -o pipefail  # 确保管道中前面的命令失败会导致整体失败

export http_proxy
export https_proxy

# 定义产物上传函数
upload_artifacts() {
    local src_dir="$1"
    echo "Running upload_artifacts hook..."
    if [ -z "$ak" ] || [ -z "$sk" ] || [ -z "$remote_dir" ]; then
        echo "Error: Missing required environment variables for upload (ak, sk, remote_dir)" >&2
        return 1
    fi

    if ! command -v ads-cli &> /dev/null; then
        echo "Downloading ads-cli..."
        wget -q https://quark.aoss.cn-sh-01.sensecoreapi-oss.cn/ads-cli/release/v1.10.0/ads-cli
        chmod +x ads-cli
        mv ads-cli /usr/bin/
    fi

    remote_endpoint="white-bucket.aoss.cn-sh-01b.sensecoreapi-oss.cn"
    ads-cli -q cp "$src_dir" "s3://${ak}:${sk}@${remote_endpoint}/${remote_dir}" || echo "Upload failed but continuing"
    echo "Upload $src_dir to ${remote_dir}..."
}

log_path="/root/run.log"
# 设置退出钩子：脚本正常结束或异常退出时执行上传，上传运行日志
trap "upload_artifacts \"${log_path}\"" EXIT
touch "$log_path"

# 业务逻辑块，输出同时显示在终端并写入 run.log
{
    ln -sf /data_tmp/data /data
    source /data/caohelei/myenv/bin/activate
    echo "commit_id: $commit_id"
    git clone --depth 1 https://github.com/GgsDdu1/cicd.git /root/code/kairos-sensenova
    # git clone --depth 1 https://github.com/kairos-agi/kairos-sensenova.git /root/code/kairos-sensenova
    cd /root/code/kairos-sensenova
    git fetch --depth 1 origin "$commit_id"
    git checkout "$commit_id"
    ls -alh
    echo "Run cmd: $case_cmd"
    $case_cmd
    ls output -alh
} 2>&1 | tee "$log_path"

# 如果业务逻辑块成功（脚本未提前退出），则上传 output 产物
upload_artifacts "output/*/*"