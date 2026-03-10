# ComfyUI Workflow API 指南

本文档详细说明 ComfyUI Workflow API 的使用方法。

## API 基础信息

- **Base URL**: 从环境变量 `COMFYUI_API_SERVER` 读取（默认：`http://172.16.2.68:18000`）
- **认证方式**: Bearer Token，从环境变量 `COMFYUI_API_TOKEN` 读取
- **响应格式**: JSON

## 通用请求格式

所有请求都需要携带认证头：

```bash
curl "$COMFYUI_API_SERVER/{endpoint}" \
  -H "Authorization: Bearer $COMFYUI_API_TOKEN"
```

---

## API 端点

### 1. 列出工作流

获取所有可用的工作流列表。

**端点**: `GET /workflows`

**请求示例**:
```bash
curl "$COMFYUI_API_SERVER/workflows" \
  -H "Authorization: Bearer $COMFYUI_API_TOKEN"
```

**响应示例**:
```json
{
  "workflows": [
    {
      "id": "text-to-image",
      "description": "基于 Z-Image 模型的文本生成图片工作流"
    },
    {
      "id": "image-edit",
      "description": "基于 Qwen-Image-Edit 模型的图片编辑工作流"
    }
  ]
}
```

---

### 2. 获取工作流详情

获取指定工作流的输入输出参数定义。

**端点**: `GET /workflows/{workflow_id}`

**参数**:
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| workflow_id | string | 是 | 工作流 ID |

**请求示例**:
```bash
curl "$COMFYUI_API_SERVER/workflows/text-to-image" \
  -H "Authorization: Bearer $COMFYUI_API_TOKEN"
```

**响应示例**:
```json
{
  "id": "text-to-image",
  "description": "基于 Z-Image 模型的文本生成图片工作流",
  "inputs": [
    {
      "name": "prompt",
      "type": "string",
      "required": true,
      "description": "正向提示词"
    },
    {
      "name": "width",
      "type": "integer",
      "required": false,
      "default": 1200,
      "min": 64,
      "max": 4096,
      "description": "生成图像的宽度"
    }
  ],
  "outputs": [
    {
      "name": "image",
      "type": "image",
      "description": "生成的图片文件"
    }
  ]
}
```

**重要**: 每次执行工作流前都应该重新获取工作流定义，因为参数可能会更新。

---

### 3. 执行工作流

执行指定的工作流并传递输入参数。

**端点**: `POST /execute/{workflow_id}/run`

**查询参数**:
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| stream | boolean | 否 | 是否使用 SSE 流式返回进度，默认 true |

**请求体**: JSON 对象，包含工作流输入参数

**请求示例**:
```bash
curl -X POST "$COMFYUI_API_SERVER/execute/text-to-image/run?stream=true" \
  -H "Authorization: Bearer $COMFYUI_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "a beautiful landscape",
    "width": 1200,
    "height": 1600,
    "steps": 9
  }'
```

**响应示例**:
```json
{
  "task_id": "abc123def456",
  "status": "pending",
  "message": "Task submitted successfully"
}
```

**stream=true 时的响应**:
使用 Server-Sent Events (SSE) 格式，实时返回进度：
```
data: {"status": "processing", "progress": 0.5}

data: {"status": "completed", "task_id": "abc123def456"}
```

---

### 4. 下载生成的文件

下载工作流执行生成的图片文件。

**端点**: `GET /download/{task_id}/{asset_index}`

**参数**:
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| task_id | string | 是 | 任务 ID |
| asset_index | integer | 是 | 资源索引（从 0 开始） |

**请求示例**:
```bash
curl "$COMFYUI_API_SERVER/download/abc123def456/0" \
  -H "Authorization: Bearer $COMFYUI_API_TOKEN" \
  -o output.png
```

**响应**: 图片文件二进制数据

**批量下载**:
如果 `batch_size > 1`，需要下载多个索引：
```bash
# 下载第一张
curl "$COMFYUI_API_SERVER/download/{task_id}/0" \
  -H "Authorization: Bearer $COMFYUI_API_TOKEN" -o image_0.png

# 下载第二张
curl "$COMFYUI_API_SERVER/download/{task_id}/1" \
  -H "Authorization: Bearer $COMFYUI_API_TOKEN" -o image_1.png
```

---

### 5. 获取任务资产信息

查询指定任务生成的所有资产信息。

**端点**: `GET /storage/task/{task_id}`

**参数**:
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| task_id | string | 是 | 任务 ID |

**请求示例**:
```bash
curl "$COMFYUI_API_SERVER/storage/task/abc123def456" \
  -H "Authorization: Bearer $COMFYUI_API_TOKEN"
```

**响应示例**:
```json
{
  "task_id": "abc123def456",
  "status": "completed",
  "assets": [
    {
      "index": 0,
      "type": "image",
      "filename": "output_0.png",
      "size": 2048576
    },
    {
      "index": 1,
      "type": "image",
      "filename": "output_1.png",
      "size": 2048576
    }
  ]
}
```

---

### 6. 列出所有资产

列出所有任务的资产（从 index.yaml 获取）。

**端点**: `GET /storage/list`

**请求示例**:
```bash
curl "$COMFYUI_API_SERVER/storage/list" \
  -H "Authorization: Bearer $COMFYUI_API_TOKEN"
```

---

### 7. 健康检查

检查 API 服务是否正常运行。

**端点**: `GET /health`

**请求示例**:
```bash
curl "$COMFYUI_API_SERVER/health"
```

**响应示例**:
```json
{
  "status": "healthy"
}
```

---

### 8. 检查 ComfyUI 服务状态

检查后端 ComfyUI 服务的连接状态。

**端点**: `GET /comfyui/status`

**请求示例**:
```bash
curl "$COMFYUI_API_SERVER/comfyui/status" \
  -H "Authorization: Bearer $COMFYUI_API_TOKEN"
```

---

## 工作流参数详解

### text-to-image

| 参数 | 类型 | 必需 | 默认值 | 范围 | 说明 |
|------|------|------|--------|------|------|
| prompt | string | 是 | - | - | 正向提示词 |
| negative_prompt | string | 否 | - | - | 负向提示词 |
| width | integer | 否 | 1200 | 64-4096 | 图片宽度 |
| height | integer | 否 | 1600 | 64-4096 | 图片高度 |
| batch_size | integer | 否 | 1 | 1-6 | 批量生成数量 |
| seed | integer | 否 | 随机 | 0-2^53 | 随机种子 |
| steps | integer | 否 | 9 | 1-100 | 采样步数 |

### image-edit

| 参数 | 类型 | 必需 | 默认值 | 范围 | 说明 |
|------|------|------|--------|------|------|
| image_base64 | string | 是 | - | - | 图片的 Base64 编码 |
| prompt | string | 是 | - | - | 编辑指令 |
| width | integer | 否 | 1200 | 64-4096 | 输出宽度 |
| height | integer | 否 | 1600 | 64-4096 | 输出高度 |
| batch_size | integer | 否 | 1 | 1-6 | 批量数量 |
| seed | integer | 否 | 随机 | 0-2^53 | 随机种子 |
| steps | integer | 否 | 8 | 1-50 | 采样步数 |
| cfg | float | 否 | 1.0 | 0-20 | CFG 引导系数 |

### upscale

| 参数 | 类型 | 必需 | 默认值 | 范围 | 说明 |
|------|------|------|--------|------|------|
| image_base64 | string | 是 | - | - | 图片的 Base64 编码 |
| prompt | string | 否 | - | - | 增强细节的提示词 |
| side_length | integer | 否 | 2880 | 1024-8192 | 目标边长 |
| seed | integer | 否 | 随机 | 0-2^53 | 随机种子 |
| steps | integer | 否 | 4 | 2-8 | 采样步数 |
| denoise | float | 否 | 0.3 | 0.1-0.4 | 去噪强度 |

### image-expend

| 参数 | 类型 | 必需 | 默认值 | 范围 | 说明 |
|------|------|------|--------|------|------|
| image_base64 | string | 是 | - | - | 图片的 Base64 编码 |
| prompt | string | 是 | - | - | 扩展内容描述 |
| left | integer | 否 | 200 | 0-2000 | 左侧扩展像素 |
| top | integer | 否 | 200 | 0-2000 | 顶部扩展像素 |
| right | integer | 否 | 200 | 0-2000 | 右侧扩展像素 |
| bottom | integer | 否 | 200 | 0-2000 | 底部扩展像素 |
| feathering | integer | 否 | 100 | 0-500 | 边缘羽化像素 |
| seed | integer | 否 | 0 | 0-2^53 | 随机种子 |
| steps | integer | 否 | 25 | 1-100 | 采样步数 |
| cfg | float | 否 | 1.0 | 0-20 | CFG 系数 |

### controlnet-preprocess

| 参数 | 类型 | 必需 | 默认值 | 范围 | 说明 |
|------|------|------|--------|------|------|
| image_base64 | string | 是 | - | - | 图片的 Base64 编码 |
| preprocessor | string | 否 | OpenposePreprocessor | - | 预处理器类型 |
| resolution | integer | 否 | 1024 | 64-4096 | 输出分辨率 |

**可用的预处理器**:
- `OpenposePreprocessor` - OpenPose 姿态图
- `DepthPreprocessor` - 深度图
- `CannyPreprocessor` - Canny 边缘检测
- `LineArtPreprocessor` - 线稿
- `MLSDPreprocessor` - 直线检测

---

## 图片编码

将图片文件编码为 Base64：

```bash
# Linux/macOS
base64 -i input.jpg | tr -d '\n' > base64.txt

# Python
python3 -c "import base64; print(base64.b64encode(open('input.jpg', 'rb').read()).decode())"
```

---

## 错误处理

### HTTP 状态码

| 状态码 | 说明 | 处理方法 |
|--------|------|----------|
| 200 | 成功 | 继续处理 |
| 400 | 请求参数错误 | 检查参数格式和范围 |
| 401 | 认证失败 | 检查 API token |
| 404 | 资源不存在 | 检查工作流 ID 或 task_id |
| 500 | 服务器错误 | 稍后重试 |
| 503 | 服务不可用 | ComfyUI 后端可能未运行 |

### 错误响应示例

```json
{
  "detail": [
    {
      "loc": ["body", "width"],
      "msg": "ensure this value is greater than 64",
      "type": "value_error.number.not_gt"
    }
  ]
}
```

---

## Python 使用示例

### 基础客户端

```python
import os
import requests
import base64

class ComfyUIClient:
    def __init__(self):
        self.api_server = os.environ.get("COMFYUI_API_SERVER", "http://172.16.2.68:18000")
        self.api_token = os.environ.get("COMFYUI_API_TOKEN", "")
        self.headers = {"Authorization": f"Bearer {self.api_token}"}

    def text_to_image(self, prompt, width=1200, height=1600):
        response = requests.post(
            f"{self.api_server}/execute/text-to-image/run",
            headers=self.headers,
            json={"prompt": prompt, "width": width, "height": height}
        )
        task_id = response.json()["task_id"]

        # 下载图片
        img_response = requests.get(
            f"{self.api_server}/download/{task_id}/0",
            headers=self.headers
        )
        with open("output.png", "wb") as f:
            f.write(img_response.content)

        return "output.png"
```

### 使用方法

```python
client = ComfyUIClient()
client.text_to_image("a beautiful landscape, masterpiece, best quality")
```
