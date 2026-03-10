#!/usr/bin/env python3
"""
图片编辑命令行工具

使用示例:
    python edit_image.py --input photo.jpg --prompt "change hair color to red"
    python edit_image.py photo.jpg "给人物戴上帽子" --output edited.png
"""

import argparse
import base64
import os
import sys
import requests


def main():
    parser = argparse.ArgumentParser(description='使用 ComfyUI API 编辑图片')
    parser.add_argument('input', help='输入图片路径')
    parser.add_argument('prompt', help='编辑指令')
    parser.add_argument('--width', type=int, default=1200, help='输出图片宽度（默认：1200）')
    parser.add_argument('--height', type=int, default=1600, help='输出图片高度（默认：1600）')
    parser.add_argument('--steps', type=int, default=8, help='采样步数（默认：8）')
    parser.add_argument('--cfg', type=float, default=1.0, help='CFG 系数（默认：1.0）')
    parser.add_argument('--seed', type=int, help='随机种子')
    parser.add_argument('--output', '-o', help='输出文件路径（默认：自动生成）')
    parser.add_argument('--api-server', default=os.environ.get('COMFYUI_API_SERVER', 'http://172.16.2.68:18000'),
                       help='API 服务器地址')
    parser.add_argument('--api-token', default=os.environ.get('COMFYUI_API_TOKEN'),
                       help='API 认证令牌')

    args = parser.parse_args()

    # 检查输入文件
    if not os.path.exists(args.input):
        print(f"❌ 错误: 输入文件不存在: {args.input}")
        sys.exit(1)

    # 检查 API token
    if not args.api_token:
        print("错误: 未设置 API token。请设置 COMFYUI_API_TOKEN 环境变量或使用 --api-token 参数。")
        sys.exit(1)

    headers = {"Authorization": f"Bearer {args.api_token}"}

    # 编码图片
    print(f"📸 读取图片: {args.input}")
    with open(args.input, "rb") as f:
        image_base64 = base64.b64encode(f.read()).decode("utf-8")

    print(f"✏️  编辑指令: {args.prompt}")

    # 构造请求
    inputs = {
        "image_base64": image_base64,
        "prompt": args.prompt,
        "width": args.width,
        "height": args.height,
        "steps": args.steps,
        "cfg": args.cfg
    }

    if args.seed is not None:
        inputs["seed"] = args.seed

    # 执行工作流
    print(f"🚀 正在编辑图片...")
    response = requests.post(
        f"{args.api_server}/execute/image-edit/run?stream=true",
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
    output_path = args.output or f"edited_{task_id}.png"
    print(f"📥 正在下载编辑后的图片...")
    img_response = requests.get(
        f"{args.api_server}/download/{task_id}/0",
        headers=headers
    )
    img_response.raise_for_status()

    with open(output_path, "wb") as f:
        f.write(img_response.content)

    print(f"💾 编辑后的图片已保存到: {output_path}")


if __name__ == "__main__":
    main()
