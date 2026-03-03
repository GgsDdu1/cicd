#!/usr/bin/env python3
"""
update_yaml.py - 将代理地址，commit_id（通过参数传入）注入 YAML 的 Envs，并将 cmd.sh 内容设为 Entrypoint

用法:
    python update_yaml.py --yaml-file <yaml_path> --cmd-file <cmd_path> \
                          [--http-proxy <HTTP_PROXY>] [--https-proxy <HTTPS_PROXY>] \
                          [--commit-id <COMMIT_ID>] \
                          [--output-file <output_path>]
"""

import sys
import argparse
import subprocess

# 尝试导入 PyYAML，若失败则自动安装
try:
    import yaml
except ImportError:
    print("PyYAML not found, installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyyaml"])
    import yaml


def update_yaml(yaml_path, cmd_path, http_proxy, https_proxy, commit_id, output_path=None):
    """主逻辑：读取 YAML，修改 Envs 和 Entrypoint，写入文件"""
    # 1. 读取 YAML 模板
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # 确保 Envs 字段存在且为列表
    if "Envs" not in data or data["Envs"] is None:
        data["Envs"] = []

    # 2. 构建代理列表（仅当参数非空时添加）
    envs = []
    if http_proxy:
        envs.append({"Name": "http_proxy", "Value": http_proxy})
    if https_proxy:
        envs.append({"Name": "https_proxy", "Value": https_proxy})
    if commit_id:
        envs.append({"Name": "commit_id", "Value": commit_id})

    for env in envs:
        data["Envs"] = [e for e in data["Envs"] if e.get("Name") != env["Name"]]
    data["Envs"].extend(envs)

    # 3. 读取 cmd.sh 内容，作为 Entrypoint
    with open(cmd_path, "r", encoding="utf-8") as f:
        cmd_content = f.read()

    data["Entrypoint"] = cmd_content

    # 4. 写入新的 YAML
    output_path = output_path or yaml_path  # 默认覆盖原文件
    with open(output_path, "w", encoding="utf-8") as f:
        # 使用 safe_dump，保持字段顺序（Python 3.7+ 字典有序）
        yaml.safe_dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print(f"✅ YAML 文件已更新: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="更新 YAML 文件：注入代理和 Entrypoint")
    parser.add_argument("--yaml-file", required=True, help="输入的 YAML 模板路径")
    parser.add_argument("--cmd-file", required=True, help="cmd.sh 文件路径")
    parser.add_argument("--http-proxy", help="HTTP 代理地址（如 http://proxy.example.com:8080）")
    parser.add_argument("--https-proxy", help="HTTPS 代理地址")
    parser.add_argument("--commit-id", help="git 本次提交commit id")
    parser.add_argument("--output-file", help="输出 YAML 路径（默认覆盖输入文件）")
    args = parser.parse_args()

    update_yaml(
        yaml_path=args.yaml_file,
        cmd_path=args.cmd_file,
        http_proxy=args.http_proxy,
        https_proxy=args.https_proxy,
        commit_id = args.commit_id,
        output_path=args.output_file,
    )


if __name__ == "__main__":
    main()