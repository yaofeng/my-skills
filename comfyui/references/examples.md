# ComfyUI 技能使用示例

本文档提供 ComfyUI 图片生成技能的各种使用示例。

## 环境准备

### 验证环境变量

```bash
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

**用户请求**: "一位年轻的亚洲女孩，黑色长发，身穿浅蓝色连帽卫衣，站在学校操场上"

**执行步骤**:

1. 构造提示词（转换为英文）:
    ```
    Character Features: Young Asian girl, 16-18 years old, slender figure, fair skin, delicate features, round bright eyes; long, smooth black hair reaching the waist with slightly curled ends.
    Character Clothing: Light blue loose hoodie with white lettering, hood down; dark gray joggers; white sneakers with light gray socks. Accessories include a black wristband and small silver hoop earrings. Simple, youthful style.
    Expression/Actions: Sweet natural smile, looking at the camera. Standing relaxed with weight on the right leg, hands in hoodie pockets, shoulders down. Head slightly tilted left, hair brushing cheeks. Youthful standing pose.
    Environment/Background: School playground with a red running track and green turf. Background includes beige school buildings, basketball hoops, and trees. Clear blue sky with clouds, bright sunlight.
    Composition: Medium shot, subject at left golden ratio. Slightly low eye-level angle. Shallow depth of field blurring the background. Bright palette of light blue and white with red/green accents. Soft natural side lighting. Sunny, fresh, youthful campus atmosphere.
    Art Style: Realistic photography, commercial quality. Sharp, clear, natural colors. Fresh and dreamy aesthetics with soft lighting. Cinematic youthful portrait effect.
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

### Q: 图片 base64 导致参数过长如何解决？

1. 将参数写入临时文件 /tmp/comfyui-args-xxxx.json
2. curl 通过 `-d @/tmp/tmp/comfyui-args-xxxx.json` 进行请求发送

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
