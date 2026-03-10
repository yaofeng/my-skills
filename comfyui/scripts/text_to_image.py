#!/usr/bin/env python3
"""
文本生成图片命令行工具

使用示例:
    python text_to_image.py "一位美丽的女孩，长发飘逸" --width 1200 --height 1600
    python text_to_image.py "beautiful landscape" --output landscape.png
"""

import argparse
import os
import sys
import requests

# 添加 scripts 目录到路径以导入本地模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from prompt_generator import PromptGenerator


def main():
    parser = argparse.ArgumentParser(description='使用 ComfyUI API 生成图片')
    parser.add_argument('description', help='图片描述（中文或英文）')
    parser.add_argument('--width', type=int, default=1200, help='图片宽度（默认：1200）')
    parser.add_argument('--height', type=int, default=1600, help='图片高度（默认：1600）')
    parser.add_argument('--steps', type=int, default=9, help='采样步数（默认：9）')
    parser.add_argument('--seed', type=int, help='随机种子（用于复现结果）')
    parser.add_argument('--batch-size', type=int, default=1, help='批量生成数量（默认：1）')
    parser.add_argument('--output', '-o', help='输出文件路径（默认：自动生成）')
    parser.add_argument('--api-server', default=os.environ.get('COMFYUI_API_SERVER', 'http://172.16.2.68:18000'),
                       help='API 服务器地址')
    parser.add_argument('--api-token', default=os.environ.get('COMFYUI_API_TOKEN'),
                       help='API 认证令牌')

    args = parser.parse_args()

    # 检查 API token
    if not args.api_token:
        print("错误: 未设置 API token。请设置 COMFYUI_API_TOKEN 环境变量或使用 --api-token 参数。")
        sys.exit(1)

    headers = {"Authorization": f"Bearer {args.api_token}"}

    # 判断是否是人物类
    person_keywords = ["人", "女孩", "少年", "少女", "男人", "女人", "人物", "角色", "模特"]
    is_person = any(keyword in args.description for keyword in person_keywords)

    # 生成提示词
    print(f"📝 描述: {args.description}")
    positive, negative = PromptGenerator.from_description(args.description, is_person=is_person)
    print(f"✨ 正向提示词: {positive[:100]}...")

    # 构造请求
    inputs = {
        "prompt": positive,
        "width": args.width,
        "height": args.height,
        "batch_size": args.batch_size,
        "steps": args.steps
    }

    if negative:
        inputs["negative_prompt"] = negative
    if args.seed is not None:
        inputs["seed"] = args.seed

    # 执行工作流
    print(f"🚀 正在生成图片...")
    response = requests.post(
        f"{args.api_server}/execute/text-to-image/run?stream=true",
        headers=headers,
        json=inputs
    )
    response.raise_for_status()
    result = response.json()

    task_id = result.get("task_id")
    if not task_id:
        print("❌ 错误: 未获得 task_id")
        sys.exit(1)

    print(f"✅ 任务已提交，ID: {task_id}")

    # 下载图片
    for i in range(args.batch_size):
        if args.batch_size > 1:
            output_path = args.output or f"generated_{task_id}_{i}.png"
        else:
            output_path = args.output or f"generated_{task_id}.png"

        print(f"📥 正在下载图片 {i+1}/{args.batch_size}...")
        img_response = requests.get(
            f"{args.api_server}/download/{task_id}/{i}",
            headers=headers
        )
        img_response.raise_for_status()

        with open(output_path, "wb") as f:
            f.write(img_response.content)

        print(f"💾 图片已保存到: {output_path}")


if __name__ == "__main__":
    main()
