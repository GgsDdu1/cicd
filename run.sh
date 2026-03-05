#!/bin/bash
set -e
# 安装volc
echo y | sh -c "$(curl -fsSL https://ml-platform-public-examples-cn-beijing.tos-cn-beijing.volces.com/cli-binary/install.sh)" && export PATH=$HOME/.volc/bin:$PATH
# 检查是否安装成功
output=$(volc version 2>/dev/null)
if [ $? -eq 0 ] && [ -n "$output" ]; then
    echo "✅ volc CLI is installed, version: $output"
else
    echo "❌ volc CLI check failed."
    exit 1
fi

# 更新配置模板
sed -i.bak \
    -e "s/^access_key_id[[:space:]]*=.*/access_key_id     = $VOLC_ACCESS_KEY/" \
    -e "s/^secret_access_key[[:space:]]*=.*/secret_access_key = $VOLC_SECRET_KEY/" \
    .github/config/volc/credentials
sed -i.bak 's/^\(region[[:space:]]*=[[:space:]]*\).*/\1'"$REGION"'/' .github/config/volc/config


# 存放至~/.volc/备用
cp .github/config/volc/credentials .github/config/volc/config  ~/.volc/

task_name=kairos-ci-$CI_COMMIT_SHORT_SHA

# submit任务
volc ml_task submit --conf .github/commons/huoshan-mltask.yaml --task_name $task_name

# while 循环判断任务是否完成
export https_proxy=http://sensecabin:MkV4WhSv3R@10.119.176.202:3128
export http_proxy=http://sensecabin:MkV4WhSv3R@10.119.176.202:3128
git clone --depth 1  -c http.proxy=http://代理服务器:端口 -c https.proxy=http://代理服务器:端口 <仓库URL>
git clone --depth 1 https://github.com/kairos-agi/kairos-sensenova.git kairos-sensenova
cd kairos-sensenova
git fetch --depth 1 origin <commit-id>  # 获取指定 commit（及其必要历史）
git checkout <commit-id>

volc ml_task logs --task t-20260304153259-48whx -i worker-0 -f

STATUS=$(volc ml_task get --id $TASK_ID --output json | jq -r '.[0].Status')

volc ml_task cancel --id t-20260304160336-mjw4d

#1111