#!/usr/bin/env python3
"""
图片放大命令行工具

使用示例:
    python upscale_image.py --input photo.jpg --side-length 3000
    python upscale_image.py photo.jpg -o large.png --denoise 0.35
"""

import argparse
import base64
import os
import sys
import requests


def main():
    parser = argparse.ArgumentParser(description='使用 ComfyUI API 高清放大图片')
    parser.add_argument('input', help='输入图片路径')
    parser.add_argument('--side-length', type=int, default=2880, help='目标边长（默认：2880）')
    parser.add_argument('--prompt', help='增强细节的提示词（可选）')
    parser.add_argument('--steps', type=int, default=4, help='采样步数（默认：4，范围2-8）')
    parser.add_argument('--denoise', type=float, default=0.3, help='去噪强度（默认：0.3，范围0.1-0.4）')
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

    print(f"🔍 放大到边长: {args.side_length}px")

    # 构造请求
    inputs = {
        "image_base64": image_base64,
        "side_length": args.side_length,
        "steps": args.steps,
        "denoise": args.denoise
    }

    if args.prompt:
        inputs["prompt"] = args.prompt
        print(f"✨ 增强提示词: {args.prompt}")

    if args.seed is not None:
        inputs["seed"] = args.seed

    # 执行工作流
    print(f"🚀 正在放大图片...")
    response = requests.post(
        f"{args.api_server}/execute/upscale/run?stream=true",
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
    output_path = args.output or f"upscaled_{task_id}.png"
    print(f"📥 正在下载放大后的图片...")
    img_response = requests.get(
        f"{args.api_server}/download/{task_id}/0",
        headers=headers
    )
    img_response.raise_for_status()

    with open(output_path, "wb") as f:
        f.write(img_response.content)

    print(f"💾 放大后的图片已保存到: {output_path}")


if __name__ == "__main__":
    main()
