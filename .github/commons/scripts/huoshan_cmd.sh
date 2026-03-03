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
bash examples/inference.sh

