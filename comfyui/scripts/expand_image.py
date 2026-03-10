#!/usr/bin/env python3
"""
图片外绘扩展命令行工具

使用示例:
    python expand_image.py --input photo.jpg --prompt "扩展为森林场景"
    python expand_image.py photo.jpg "扩展成海滩" --left 300 --right 300
"""

import argparse
import base64
import os
import sys
import requests


def main():
    parser = argparse.ArgumentParser(description='使用 ComfyUI API 扩展图片')
    parser.add_argument('input', help='输入图片路径')
    parser.add_argument('prompt', help='扩展内容描述')
    parser.add_argument('--left', type=int, default=200, help='左侧扩展像素（默认：200）')
    parser.add_argument('--right', type=int, default=200, help='右侧扩展像素（默认：200）')
    parser.add_argument('--top', type=int, default=200, help='顶部扩展像素（默认：200）')
    parser.add_argument('--bottom', type=int, default=200, help='底部扩展像素（默认：200）')
    parser.add_argument('--feathering', type=int, default=100, help='边缘羽化像素（默认：100）')
    parser.add_argument('--steps', type=int, default=25, help='采样步数（默认：25）')
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

    print(f"🖼️  扩展描述: {args.prompt}")
    print(f"📐 扩展尺寸: 左{args.left} 右{args.right} 上{args.top} 下{args.bottom}px")

    # 构造请求
    inputs = {
        "image_base64": image_base64,
        "prompt": args.prompt,
        "left": args.left,
        "right": args.right,
        "top": args.top,
        "bottom": args.bottom,
        "feathering": args.feathering,
        "steps": args.steps,
        "cfg": args.cfg
    }

    if args.seed is not None:
        inputs["seed"] = args.seed

    # 执行工作流
    print(f"🚀 正在扩展图片...")
    response = requests.post(
        f"{args.api_server}/execute/image-expend/run?stream=true",
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
    output_path = args.output or f"expanded_{task_id}.png"
    print(f"📥 正在下载扩展后的图片...")
    img_response = requests.get(
        f"{args.api_server}/download/{task_id}/0",
        headers=headers
    )
    img_response.raise_for_status()

    with open(output_path, "wb") as f:
        f.write(img_response.content)

    print(f"💾 扩展后的图片已保存到: {output_path}")


if __name__ == "__main__":
    main()
