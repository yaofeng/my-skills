"""
ComfyUI 图片生成技能
支持文本生成图片、图片编辑、放大、外绘扩展等功能
"""

import os
import base64
import json
import requests
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
import re

from prompt_generator import PromptGenerator


class ComfyUIError(Exception):
    """ComfyUI API 错误"""
    pass


class ComfyUIClient:
    """ComfyUI API 客户端"""

    def __init__(self, api_server: Optional[str] = None, api_token: Optional[str] = None):
        """
        初始化客户端

        Args:
            api_server: API 服务器地址，默认从环境变量 COMFYUI_API_SERVER 读取
            api_token: API 认证令牌，默认从环境变量 COMFYUI_API_TOKEN 读取
        """
        self.api_server = api_server or os.environ.get("COMFYUI_API_SERVER", "http://172.16.2.68:18000")
        self.api_token = api_token or os.environ.get("COMFYUI_API_TOKEN", "")

        if not self.api_token:
            raise ComfyUIError("API token not found. Please set COMFYUI_API_TOKEN environment variable.")

        self.headers = {}
        if self.api_token:
            self.headers["Authorization"] = f"Bearer {self.api_token}"

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """发送 HTTP 请求"""
        url = f"{self.api_server}{endpoint}"
        response = requests.request(method, url, headers=self.headers, **kwargs)
        response.raise_for_status()
        return response.json()

    def get_workflows(self) -> List[Dict[str, Any]]:
        """获取工作流列表"""
        return self._request("GET", "/workflows").get("workflows", [])

    def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """获取工作流详细信息"""
        return self._request("GET", f"/workflows/{workflow_id}")

    def execute_workflow(
        self,
        workflow_id: str,
        inputs: Dict[str, Any],
        stream: bool = True
    ) -> Dict[str, Any]:
        """
        执行工作流

        Args:
            workflow_id: 工作流 ID
            inputs: 输入参数
            stream: 是否使用流式返回

        Returns:
            执行结果，包含 task_id
        """
        params = {"stream": stream} if stream else {}
        return self._request("POST", f"/execute/{workflow_id}/run", params=params, json=inputs)

    def download_asset(self, task_id: str, asset_index: int = 0) -> bytes:
        """
        下载生成的资源

        Args:
            task_id: 任务 ID
            asset_index: 资源索引（默认 0）

        Returns:
            文件二进制数据
        """
        url = f"{self.api_server}/download/{task_id}/{asset_index}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.content

    def download_asset_to_file(
        self,
        task_id: str,
        output_path: str,
        asset_index: int = 0
    ) -> str:
        """
        下载资源到文件

        Args:
            task_id: 任务 ID
            output_path: 输出文件路径
            asset_index: 资源索引（默认 0）

        Returns:
            保存的文件路径
        """
        content = self.download_asset(task_id, asset_index)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "wb") as f:
            f.write(content)

        return output_path

    def get_task_assets(self, task_id: str) -> Dict[str, Any]:
        """获取任务资产信息"""
        return self._request("GET", f"/storage/task/{task_id}")

    def list_assets(self) -> List[Dict[str, Any]]:
        """列出所有资产"""
        return self._request("GET", "/storage/list").get("assets", [])

    def health_check(self) -> bool:
        """健康检查"""
        try:
            self._request("GET", "/health")
            return True
        except Exception:
            return False


class ComfyUISkill:
    """ComfyUI 图片生成技能"""

    def __init__(self, api_server: Optional[str] = None, api_token: Optional[str] = None):
        self.client = ComfyUIClient(api_server, api_token)
        self.default_output_dir = Path("./generated_images")
        self.default_output_dir.mkdir(exist_ok=True)

    def _encode_image(self, image_path: str) -> str:
        """将图片文件编码为 Base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _parse_dimensions(self, description: str) -> Tuple[int, int]:
        """从描述中解析图片尺寸"""
        width, height = 1200, 1600  # 默认值

        # 查找尺寸模式
        size_patterns = [
            r'(\d+)\s*[x×]\s*(\d+)',  # 1200x1600
            r'(\d+)\s*by\s*(\d+)',     # 1200 by 1600
            r'width\s*[:：]\s*(\d+)',   # width: 1200
            r'高度\s*[:：]\s*(\d+)',    # 高度: 1600
        ]

        for pattern in size_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                width = int(match.group(1))
                height = int(match.group(2))
                break

        return width, height

    # ============ 文本生成图片 ============

    def text_to_image(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        width: int = 1200,
        height: int = 1600,
        batch_size: int = 1,
        seed: Optional[int] = None,
        steps: int = 9,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        文本生成图片

        Args:
            prompt: 正向提示词
            negative_prompt: 负向提示词
            width: 图片宽度
            height: 图片高度
            batch_size: 批量生成数量
            seed: 随机种子
            steps: 采样步数
            output_path: 输出文件路径（不指定则自动生成）

        Returns:
            包含任务信息和文件路径的字典
        """
        inputs = {
            "prompt": prompt,
            "width": width,
            "height": height,
            "batch_size": batch_size,
            "steps": steps
        }

        if negative_prompt:
            inputs["negative_prompt"] = negative_prompt
        if seed is not None:
            inputs["seed"] = seed

        result = self.client.execute_workflow("text-to-image", inputs)
        task_id = result.get("task_id")

        if not task_id:
            raise ComfyUIError("Failed to get task_id from response")

        # 下载图片
        if output_path is None:
            output_path = str(self.default_output_dir / f"t2i_{task_id}.png")

        downloaded = self.client.download_asset_to_file(task_id, output_path, asset_index=0)

        return {
            "task_id": task_id,
            "file_path": downloaded,
            "workflow": "text-to-image",
            "inputs": inputs
        }

    # ============ 图片编辑 ============

    def edit_image(
        self,
        image_path: str,
        edit_prompt: str,
        width: int = 1200,
        height: int = 1600,
        batch_size: int = 1,
        seed: Optional[int] = None,
        steps: int = 8,
        cfg: float = 1.0,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        编辑图片

        Args:
            image_path: 输入图片路径
            edit_prompt: 编辑指令
            width: 输出图片宽度
            height: 输出图片高度
            batch_size: 批量生成数量
            seed: 随机种子
            steps: 采样步数
            cfg: CFG 引导系数
            output_path: 输出文件路径

        Returns:
            包含任务信息和文件路径的字典
        """
        image_base64 = self._encode_image(image_path)

        inputs = {
            "image_base64": image_base64,
            "prompt": edit_prompt,
            "width": width,
            "height": height,
            "batch_size": batch_size,
            "steps": steps,
            "cfg": cfg
        }

        if seed is not None:
            inputs["seed"] = seed

        result = self.client.execute_workflow("image-edit", inputs)
        task_id = result.get("task_id")

        if not task_id:
            raise ComfyUIError("Failed to get task_id from response")

        if output_path is None:
            output_path = str(self.default_output_dir / f"edit_{task_id}.png")

        downloaded = self.client.download_asset_to_file(task_id, output_path, asset_index=0)

        return {
            "task_id": task_id,
            "file_path": downloaded,
            "workflow": "image-edit",
            "inputs": inputs
        }

    # ============ 图片放大 ============

    def upscale_image(
        self,
        image_path: str,
        side_length: int = 2880,
        prompt: Optional[str] = None,
        seed: Optional[int] = None,
        steps: int = 4,
        denoise: float = 0.3,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        高清放大图片

        Args:
            image_path: 输入图片路径
            side_length: 目标边长（像素）
            prompt: 正向提示词（可选）
            seed: 随机种子
            steps: 采样步数
            denoise: 去噪强度
            output_path: 输出文件路径

        Returns:
            包含任务信息和文件路径的字典
        """
        image_base64 = self._encode_image(image_path)

        inputs = {
            "image_base64": image_base64,
            "side_length": side_length,
            "steps": steps,
            "denoise": denoise
        }

        if prompt:
            inputs["prompt"] = prompt
        if seed is not None:
            inputs["seed"] = seed

        result = self.client.execute_workflow("upscale", inputs)
        task_id = result.get("task_id")

        if not task_id:
            raise ComfyUIError("Failed to get task_id from response")

        if output_path is None:
            output_path = str(self.default_output_dir / f"upscale_{task_id}.png")

        downloaded = self.client.download_asset_to_file(task_id, output_path, asset_index=0)

        return {
            "task_id": task_id,
            "file_path": downloaded,
            "workflow": "upscale",
            "inputs": inputs
        }

    # ============ 图片外绘扩展 ============

    def expand_image(
        self,
        image_path: str,
        prompt: str,
        left: int = 200,
        top: int = 200,
        right: int = 200,
        bottom: int = 200,
        feathering: int = 100,
        seed: Optional[int] = None,
        steps: int = 25,
        cfg: float = 1.0,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        图片外绘扩展

        Args:
            image_path: 输入图片路径
            prompt: 提示词
            left: 左侧扩展像素数
            top: 顶部扩展像素数
            right: 右侧扩展像素数
            bottom: 底部扩展像素数
            feathering: 边缘羽化像素数
            seed: 随机种子
            steps: 采样步数
            cfg: CFG 引导系数
            output_path: 输出文件路径

        Returns:
            包含任务信息和文件路径的字典
        """
        image_base64 = self._encode_image(image_path)

        inputs = {
            "image_base64": image_base64,
            "prompt": prompt,
            "left": left,
            "top": top,
            "right": right,
            "bottom": bottom,
            "feathering": feathering,
            "steps": steps,
            "cfg": cfg
        }

        if seed is not None:
            inputs["seed"] = seed

        result = self.client.execute_workflow("image-expend", inputs)
        task_id = result.get("task_id")

        if not task_id:
            raise ComfyUIError("Failed to get task_id from response")

        if output_path is None:
            output_path = str(self.default_output_dir / f"expand_{task_id}.png")

        downloaded = self.client.download_asset_to_file(task_id, output_path, asset_index=0)

        return {
            "task_id": task_id,
            "file_path": downloaded,
            "workflow": "image-expend",
            "inputs": inputs
        }

    # ============ ControlNet 预处理 ============

    def preprocess_controlnet(
        self,
        image_path: str,
        preprocessor: str = "OpenposePreprocessor",
        resolution: int = 1024,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        ControlNet 预处理

        Args:
            image_path: 输入图片路径
            preprocessor: 预处理器类型
            resolution: 输出分辨率
            output_path: 输出文件路径

        Returns:
            包含任务信息和文件路径的字典
        """
        image_base64 = self._encode_image(image_path)

        inputs = {
            "image_base64": image_base64,
            "preprocessor": preprocessor,
            "resolution": resolution
        }

        result = self.client.execute_workflow("controlnet-preprocess", inputs)
        task_id = result.get("task_id")

        if not task_id:
            raise ComfyUIError("Failed to get task_id from response")

        if output_path is None:
            preprocessor_name = preprocessor.replace("Preprocessor", "").lower()
            output_path = str(self.default_output_dir / f"controlnet_{preprocessor_name}_{task_id}.png")

        downloaded = self.client.download_asset_to_file(task_id, output_path, asset_index=0)

        return {
            "task_id": task_id,
            "file_path": downloaded,
            "workflow": "controlnet-preprocess",
            "inputs": inputs
        }

    # ============ 智能生成接口 ============

    def generate_from_description(
        self,
        description: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        seed: Optional[int] = None,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        从自然语言描述生成图片

        Args:
            description: 图片描述（可以是中文）
            width: 图片宽度
            height: 图片高度
            seed: 随机种子
            output_path: 输出文件路径

        Returns:
            包含任务信息和文件路径的字典
        """
        # 判断是否是人物类
        person_keywords = ["人", "女孩", "少年", "少女", "男人", "女人", "人物", "角色", "模特"]
        is_person = any(keyword in description for keyword in person_keywords)

        # 生成提示词
        positive, negative = PromptGenerator.from_description(description, is_person=is_person)

        # 解析尺寸
        if width is None or height is None:
            parsed_w, parsed_h = self._parse_dimensions(description)
            width = width or parsed_w
            height = height or parsed_h

        return self.text_to_image(
            prompt=positive,
            negative_prompt=negative,
            width=width,
            height=height,
            seed=seed,
            output_path=output_path
        )


# ============ 便捷函数 ============

def create_skill() -> ComfyUISkill:
    """创建技能实例"""
    return ComfyUISkill()


def generate_image(description: str, **kwargs) -> Dict[str, Any]:
    """快速生成图片"""
    skill = create_skill()
    return skill.generate_from_description(description, **kwargs)


def edit_image_from_description(
    image_path: str,
    edit_instruction: str,
    **kwargs
) -> Dict[str, Any]:
    """快速编辑图片"""
    skill = create_skill()
    return skill.edit_image(image_path, edit_instruction, **kwargs)


def upscale_image_file(image_path: str, side_length: int = 2880, **kwargs) -> Dict[str, Any]:
    """快速放大图片"""
    skill = create_skill()
    return skill.upscale_image(image_path, side_length=side_length, **kwargs)


if __name__ == "__main__":
    # 测试代码
    skill = create_skill()

    # 打印可用工作流
    print("Available workflows:")
    for wf in skill.client.get_workflows():
        print(f"  - {wf['id']}: {wf['description']}")
