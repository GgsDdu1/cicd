#!/bin/bash
set -e
export http_proxy
export https_proxy

echo "commit_id: $commit_id"
git clone --depth 1 https://github.com/GgsDdu1/cicd.git /root/code/kairos-sensenova
# git clone --depth 1 https://github.com/kairos-agi/kairos-sensenova.git /root/code/kairos-sensenova
cd /root/code/kairos-sensenova
git fetch --depth 1 origin $commit_id  # 获取指定 commit（及其必要历史）
git checkout $commit_id
ls -alh
# 测试运行的命令
echo "Run cmd: {$case_cmd}"
$case_cmd
ls output -alh

# 产物上传
# download ads-cli
wget https://quark.aoss.cn-sh-01.sensecoreapi-oss.cn/ads-cli/release/v1.10.0/ads-cli
chmod +x ads-cli
mv ads-cli /usr/bin/
remote_endpoint="kairos-ci.aoss.cn-sh-01b.sensecoreapi-oss.cn"
ads-cli cp output/* s3://$ak:$sk@$remote_endpoint/$remote_dir
echo "Upload output to $remote_dir..."
