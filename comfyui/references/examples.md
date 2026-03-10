# ComfyUI 技能使用示例

本文档提供 ComfyUI 图片生成技能的各种使用示例。

## 目录

- [环境准备](#环境准备)
- [文本生成图片](#文本生成图片)
- [图片编辑](#图片编辑)
- [图片放大](#图片放大)
- [图片扩展](#图片扩展)
- [ControlNet 预处理](#controlnet-预处理)
- [高级用法](#高级用法)

---

## 环境准备

### 设置环境变量

```bash
# Linux/macOS
export COMFYUI_API_SERVER="http://172.16.2.68:18000"
export COMFYUI_API_TOKEN="your_api_token_here"

# 验证设置
echo "Server: ${COMFYUI_API_SERVER:-未设置}"
echo "Token: ${COMFYUI_API_TOKEN:+已设置}"
```

### 检查服务状态

```bash
curl "$COMFYUI_API_SERVER/health"
curl "$COMFYUI_API_SERVER/comfyui/status" \
  -H "Authorization: Bearer $COMFYUI_API_TOKEN"
```

---

## 文本生成图片

### 示例 1: 基础人像生成

**用户请求**: "生成一张亚洲女孩的照片，长发，穿蓝色卫衣"

**执行步骤**:

1. 构造提示词（转换为英文）:
   ```
   young Asian woman, long black hair, wearing light blue hoodie,
   smiling, standing, outdoor, natural lighting,
   medium shot, front view, masterpiece, best quality, ultra detailed
   ```

2. 调用 API:
   ```bash
   curl -X POST "$COMFYUI_API_SERVER/execute/text-to-image/run?stream=true" \
     -H "Authorization: Bearer $COMFYUI_API_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "prompt": "young Asian woman, long black hair, wearing light blue hoodie, smiling, standing, outdoor, natural lighting, medium shot, front view, masterpiece, best quality, ultra detailed",
       "width": 1200,
       "height": 1600,
       "steps": 9
     }'
   ```

3. 下载图片:
   ```bash
   # 使用返回的 task_id
   curl "$COMFYUI_API_SERVER/download/{task_id}/0" \
     -H "Authorization: Bearer $COMFYUI_API_TOKEN" \
     -o asian_girl_portrait.png
   ```

### 示例 2: 风景照生成

**用户请求**: "生成一张美丽的风景照，雪山和草地"

**提示词**:
```
beautiful mountain landscape, snow-capped peaks, green valley,
clear blue sky, fluffy white clouds, peaceful atmosphere,
wide angle shot, natural lighting, masterpiece, best quality, ultra detailed
```

**API 调用**:
```bash
curl -X POST "$COMFYUI_API_SERVER/execute/text-to-image/run" \
  -H "Authorization: Bearer $COMFYUI_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "beautiful mountain landscape, snow-capped peaks, green valley, clear blue sky, fluffy white clouds, peaceful atmosphere, wide angle shot, natural lighting, masterpiece, best quality, ultra detailed",
    "width": 1600,
    "height": 1200,
    "steps": 9
  }'
```

### 示例 3: 使用辅助脚本

```bash
python scripts/text_to_image.py \
  "一位美丽的女孩，长发飘飘，穿着白色连衣裙" \
  --width 1200 --height 1600 \
  --output beauty_portrait.png
```

---

## 图片编辑

### 示例 1: 更改发色

**用户请求**: "把这张照片里的女孩头发改成红色"

**执行步骤**:

1. 编码输入图片:
   ```bash
   IMAGE_BASE64=$(base64 -i input.jpg | tr -d '\n')
   ```

2. 调用 API:
   ```bash
   curl -X POST "$COMFYUI_API_SERVER/execute/image-edit/run" \
     -H "Authorization: Bearer $COMFYUI_API_TOKEN" \
     -H "Content-Type: application/json" \
     -d "{
       \"image_base64\": \"$IMAGE_BASE64\",
       \"prompt\": \"change hair color to red\",
       \"steps\": 8
     }"
   ```

### 示例 2: 添加配饰

**用户请求**: "给照片里的人戴上一顶红色的帽子"

**提示词**:
```
add a red hat on the head
```

### 示例 3: 使用辅助脚本

```bash
python scripts/edit_image.py \
  --input portrait.jpg \
  --prompt "change hair color to blonde" \
  --output blonde_hair.jpg
```

---

## 图片放大

### 示例 1: 基础放大

**用户请求**: "把这张图片放大 2 倍"

**执行步骤**:

1. 编码输入图片:
   ```bash
   IMAGE_BASE64=$(base64 -i small_image.jpg | tr -d '\n')
   ```

2. 调用 API:
   ```bash
   curl -X POST "$COMFYUI_API_SERVER/execute/upscale/run" \
     -H "Authorization: Bearer $COMFYUI_API_TOKEN" \
     -H "Content-Type: application/json" \
     -d "{
       \"image_base64\": \"$IMAGE_BASE64\",
       \"side_length\": 2880,
       \"steps\": 4
     }"
   ```

### 示例 2: 带细节增强的放大

**用户请求**: "放大这张图片，并增强细节"

**请求参数**:
```json
{
  "image_base64": "...",
  "side_length": 3000,
  "prompt": "enhance details, sharpen edges, improve texture quality",
  "denoise": 0.35
}
```

### 示例 3: 使用辅助脚本

```bash
python scripts/upscale_image.py \
  --input small.jpg \
  --side-length 3000 \
  --denoise 0.35 \
  --output large.jpg
```

---

## 图片扩展

### 示例 1: 向四周扩展

**用户请求**: "把这张照片向四周各扩展 300 像素，变成户外森林场景"

**请求参数**:
```json
{
  "image_base64": "...",
  "prompt": "expand into outdoor forest scene, trees and natural environment",
  "left": 300,
  "right": 300,
  "top": 300,
  "bottom": 300,
  "feathering": 150,
  "steps": 25
}
```

### 示例 2: 单方向扩展

**用户请求**: "只向右扩展，添加城市天际线"

**请求参数**:
```json
{
  "image_base64": "...",
  "prompt": "city skyline, modern buildings, urban landscape",
  "left": 0,
  "right": 500,
  "top": 0,
  "bottom": 0,
  "feathering": 100
}
```

### 示例 3: 使用辅助脚本

```bash
python scripts/expand_image.py \
  --input photo.jpg \
  --prompt "expand into beautiful beach scene, ocean and sand" \
  --left 200 --right 200 --top 0 --bottom 0 \
  --feathering 100 \
  --output expanded.jpg
```

---

## ControlNet 预处理

### 示例 1: 生成 OpenPose 姿态图

**用户请求**: "把这张照片转换成 OpenPose 姿态图"

**请求参数**:
```json
{
  "image_base64": "...",
  "preprocessor": "OpenposePreprocessor",
  "resolution": 1024
}
```

### 示例 2: 生成深度图

**用户请求**: "生成这张照片的深度图"

**请求参数**:
```json
{
  "image_base64": "...",
  "preprocessor": "DepthPreprocessor",
  "resolution": 1024
}
```

### 示例 3: 可用的预处理器

| 预处理器 | 说明 | 输出示例 |
|---------|------|---------|
| `OpenposePreprocessor` | 人体姿态骨架图 | 骨架线条图 |
| `DepthPreprocessor` | 深度图 | 灰度深度图 |
| `CannyPreprocessor` | Canny 边缘检测 | 边缘线条图 |
| `LineArtPreprocessor` | 线稿 | 黑白线稿 |
| `MLSDPreprocessor` | 直线检测 | 直线结构图 |

---

## 高级用法

### 批量生成

一次生成多张相似图片：

```bash
curl -X POST "$COMFYUI_API_SERVER/execute/text-to-image/run" \
  -H "Authorization: Bearer $COMFYUI_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "beautiful portrait of a young woman",
    "batch_size": 4,
    "seed": 12345
  }'
```

下载所有生成的图片：
```bash
curl "$COMFYUI_API_SERVER/download/{task_id}/0" -H "Authorization: Bearer $COMFYUI_API_TOKEN" -o img_0.png
curl "$COMFYUI_API_SERVER/download/{task_id}/1" -H "Authorization: Bearer $COMFYUI_API_TOKEN" -o img_1.png
curl "$COMFYUI_API_SERVER/download/{task_id}/2" -H "Authorization: Bearer $COMFYUI_API_TOKEN" -o img_2.png
curl "$COMFYUI_API_SERVER/download/{task_id}/3" -H "Authorization: Bearer $COMFYUI_API_TOKEN" -o img_3.png
```

### 使用固定种子复现结果

```bash
# 第一次生成
curl -X POST "$COMFYUI_API_SERVER/execute/text-to-image/run" \
  -H "Authorization: Bearer $COMFYUI_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a beautiful landscape", "seed": 999999}'

# 第二次使用相同种子，会得到相同结果
curl -X POST "$COMFYUI_API_SERVER/execute/text-to-image/run" \
  -H "Authorization: Bearer $COMFYUI_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a beautiful landscape", "seed": 999999}'
```

### 流式监控进度

使用 SSE 流式返回实时进度：

```bash
curl -N "$COMFYUI_API_SERVER/execute/text-to-image/run?stream=true" \
  -H "Authorization: Bearer $COMFYUI_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a complex scene", "steps": 50}'
```

输出示例：
```
data: {"status": "processing", "progress": 0.1, "message": "Starting..."}

data: {"status": "processing", "progress": 0.5, "message": "Generating..."}

data: {"status": "completed", "task_id": "abc123", "message": "Done!"}
```

---

## 常见问题

### Q: 如何将中文描述转换为英文？

**方法 1**: 使用参考文档中的词汇表手动转换

**方法 2**: 使用辅助脚本
```bash
python scripts/generate_prompt.py "一位美丽的亚洲女孩，长发飘逸"
```

**方法 3**: 使用翻译工具（如 Google Translate）然后调整

### Q: 生成质量不好怎么办？

1. **增加采样步数**: 将 `steps` 从 9 增加到 15-20
2. **添加质量词**: 确保提示词结尾有 `masterpiece, best quality`
3. **添加负向提示词**: 使用 `negative_prompt` 排除不需要的内容
4. **调整图片尺寸**: 某些尺寸效果更好

### Q: 如何让人物更自然？

1. 使用具体详细的描述
2. 添加合理的动作和表情
3. 指定合适的光线和环境
4. 使用写实风格：`realistic style, high quality photography`

### Q: API 返回错误怎么办？

1. 检查环境变量是否正确设置
2. 验证 API token 是否有效
3. 确认工作流 ID 和参数是否正确
4. 查看 API 返回的具体错误信息

---

## 完整工作流示例

### 场景：制作产品宣传图

**需求**: 为一款护肤产品生成宣传图

**步骤**:

1. 生成产品背景图
   ```bash
   curl -X POST "$COMFYUI_API_SERVER/execute/text-to-image/run" \
     -H "Authorization: Bearer $COMFYUI_API_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "prompt": "elegant minimalist bathroom background, soft natural lighting, clean white surfaces, luxury spa atmosphere, wide angle shot, masterpiece, best quality",
       "width": 1920,
       "height": 1080
     }'
   ```

2. 下载背景图
   ```bash
   curl "$COMFYUI_API_SERVER/download/{task_id}/0" \
     -H "Authorization: Bearer $COMFYUI_API_TOKEN" \
     -o background.png
   ```

3. （可选）使用其他工具将产品图合成到背景上

---

## 脚本快速参考

| 脚本 | 功能 | 基本用法 |
|------|------|---------|
| `text_to_image.py` | 文本生成图片 | `python scripts/text_to_image.py "提示词"` |
| `edit_image.py` | 编辑图片 | `python scripts/edit_image.py --input 图片.jpg --prompt "编辑指令"` |
| `upscale_image.py` | 放大图片 | `python scripts/upscale_image.py --input 图片.jpg --side-length 3000` |
| `expand_image.py` | 扩展图片 | `python scripts/expand_image.py --input 图片.jpg --prompt "扩展描述"` |
| `generate_prompt.py` | 生成提示词 | `python scripts/generate_prompt.py "中文描述"` |
