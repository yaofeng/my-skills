---
name: comfyui
description: 图片生成、编辑和处理技能。当用户要求生成图片、编辑图片、放大图片、图片扩展、AI 绘画、Stable Diffusion、文生图、图生图，或任何图像处理/创建任务时，使用此技能。即使没有明确提及 ComfyUI，只要是图片生成/编辑/处理需求，都应该触发此技能。
compatibility: 需要 COMFYUI_API_SERVER 和 COMFYUI_API_TOKEN 环境变量
---

# ComfyUI 图片生成技能

基于 ComfyUI Workflow API 的智能图片生成、编辑和处理技能。

## 环境变量

使用此技能前，确保已设置以下环境变量：

- `COMFYUI_API_SERVER`: API 服务器地址（如：`http://172.16.2.68:18000`）
- `COMFYUI_API_TOKEN`: API 认证令牌

检查环境变量：
```bash
echo "Server: ${COMFYUI_API_SERVER:-未设置}"
echo "Token: ${COMFYUI_API_TOKEN:+已设置}"
```

## 可用工作流

| 工作流 ID | 功能描述 | 使用场景 |
|-----------|----------|----------|
| `text-to-image` | 文本生成图片 | 用户说"生成"、"画"、"创建"图片 |
| `image-edit` | 根据指令编辑图片 | 用户说"编辑"、"修改"、"把这张图..." |
| `upscale` | 高清放大图片 | 用户说"放大"、"高清"、"提高分辨率" |
| `image-expend` | 图片外绘扩展 | 用户说"扩展"、"扩充"、"向外延伸" |
| `controlnet-preprocess` | ControlNet 预处理 | 用户需要姿态图、深度图等 |

## 工作流程

### 步骤 1：确定用户需求

根据用户的描述确定使用哪个工作流：

**生成新图片** → `text-to-image`
```
用户说："画一个女孩"、"生成风景图"、"创建头像"
```

**编辑现有图片** → `image-edit`
```
用户说："把她的头发改成红色"、"去掉背景"、"添加帽子"
```

**放大图片** → `upscale`
```
用户说："放大到2倍"、"提高分辨率"、"变清晰点"
```

**扩展图片** → `image-expend`
```
用户说："向右扩展"、"扩充背景"、"外绘"
```

### 步骤 2：获取工作流参数

通过 API 获取工作流的输入参数：
```bash
curl "$COMFYUI_API_SERVER/workflows/{workflow_id}" \
  -H "Authorization: Bearer $COMFYUI_API_TOKEN"
```

**重要**：每次执行前都应该获取最新的工作流参数定义，因为 API 可能会更新。

### 步骤 3：构造提示词

**基本原则**：
- 使用英文描述（模型对英文支持最好）
- 具体描述细节，避免模糊词汇
- 按照逻辑顺序编写
- 结尾添加质量增强词（`masterpiece, best quality`）

**人物类提示词结构**：
1. 人物特征：年龄、性别、身材、相貌
2. 人物服饰：服装、鞋袜、饰品
3. 表情/动作：表情、姿态、动作
4. 环境/背景：场景、时间、天气
5. 画面构图：拍摄角度、光线、色调
6. 艺术风格：风格类型、质量增强

**示例**：
```
用户说："一位年轻的亚洲女孩，黑色长发，身穿浅蓝色连帽卫衣，站在学校操场上"

转换为：
Character Features: Young Asian girl, approximately 16-18 years old, with a slender and well-proportioned figure, moderate height; delicate and soft facial features, fair and smooth skin, refined and three-dimensional facial features, naturally arched eyebrows, round and bright eyes; long black hair that is smooth and flowing, healthy and glossy texture, waist-length, naturally slightly curled at the ends, with some strands gently brushing against her shoulders.

Character Clothing: Wearing a light blue hooded sweatshirt made of soft and skin-friendly fabric, with a loose and casual fit, the hood naturally draped behind her back, decorated with simple small white letter prints on the chest; paired with dark gray slim-fit jogger pants with tapered cuffs; wearing pure white athletic sneakers with neatly tied laces, paired with light gray cotton ankle socks; wearing a slim black sports wristband on her wrist, small silver hoop earrings on her earlobes, overall look is simple and youthful.

Expression/Actions: Wearing a natural sweet smile, with corners of the mouth slightly upturned, clear and bright eyes, gazing gently toward the camera; standing naturally upright, weight slightly shifted to the right leg, relaxed and comfortable posture; hands casually tucked into the front pocket of the hoodie, shoulders relaxed and lowered; head slightly tilted to the left, hair gently brushing against her cheeks with the breeze, overall presenting a youthful and energetic static standing pose.

Environment/Background: School playground scene, red rubber running track curving around green artificial turf, track lines clearly visible; background features beige school buildings, blue basketball hoops, silver flagpoles and other iconic campus facilities; neatly planted roadside trees along the playground edge with lush green leaves; clear blue sky with a few fluffy white clouds, bright and transparent sunlight.

Composition: Medium portrait composition, character positioned at the left golden ratio point; shooting angle is eye-level with a slightly low angle to enhance the youthful vitality; shallow depth of field effect with moderately blurred background buildings and track to highlight the subject; color palette dominated by fresh and bright light blue and white tones, with playground red and green colors as soft accents; natural lighting from the front side, soft and even afternoon sunlight, delicate light and shadow transitions on the character's face; overall atmosphere is sunny, fresh, and full of youthful campus vibes.

Art Style: Realistic photography style, pursuing commercial-grade portrait quality; sharp and clear image with accurate and natural color reproduction; incorporating fresh and dreamy visual aesthetics with rich and soft lighting layers; post-processing focuses on preserving skin texture and environmental details, highlighting the harmony between character expression and campus atmosphere, overall presenting a cinematic youthful portrait effect.
```

### 步骤 4：执行工作流

调用执行 API：
```bash
curl -X POST "$COMFYUI_API_SERVER/execute/{workflow_id}/run?stream=true" \
  -H "Authorization: Bearer $COMFYUI_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"参数名": "参数值", ...}'
```

**注意**：
- 图片参数需要 Base64 编码
- 使用 `stream=true` 获取实时进度
- 保存返回的 `task_id` 用于后续下载

### 步骤 5：下载生成的图片

使用 task_id 下载结果：
```bash
curl "$COMFYUI_API_SERVER/download/{task_id}/0" \
  -H "Authorization: Bearer $COMFYUI_API_TOKEN" \
  -o output.png
```

如果批量生成（batch_size > 1），需要下载多个索引（0, 1, 2, ...）

## 使用辅助脚本

技能提供了辅助脚本来简化操作：

### 生成图片
```bash
python scripts/text_to_image.py \
  "一位美丽的亚洲女孩，长发飘飘" \
  --width 1200 --height 1600 \
  --output girl.png
```

### 编辑图片
```bash
python scripts/edit_image.py \
  --input photo.jpg \
  --prompt "把头发改成红色" \
  --output edited.png
```

### 放大图片
```bash
python scripts/upscale_image.py \
  --input photo.jpg \
  --side-length 3000 \
  --output upscaled.png
```

### 扩展图片
```bash
python scripts/expand_image.py \
  --input photo.jpg \
  --prompt "扩展为户外森林场景" \
  --left 300 --right 300 --top 200 --bottom 200 \
  --output expanded.png
```

## 常用参数说明

### text-to-image 参数
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| prompt | string | 是 | 正向提示词（英文） |
| negative_prompt | string | 否 | 负向提示词 |
| width | integer | 否 | 宽度，默认 1200 |
| height | integer | 否 | 高度，默认 1600 |
| batch_size | integer | 否 | 生成数量，默认 1，最大 6 |
| seed | integer | 否 | 随机种子，用于复现 |
| steps | integer | 否 | 采样步数，默认 9 |

### upscale 参数
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| image_base64 | string | 是 | 图片的 Base64 编码 |
| side_length | integer | 否 | 目标边长，默认 2880 |
| prompt | string | 否 | 增强细节的提示词 |
| steps | integer | 否 | 采样步数，默认 4 |
| denoise | float | 否 | 去噪强度，默认 0.3 |

### image-edit 参数
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| image_base64 | string | 是 | 图片的 Base64 编码 |
| prompt | string | 是 | 编辑指令 |
| width | integer | 否 | 输出宽度，默认 1200 |
| height | integer | 否 | 输出高度，默认 1600 |
| cfg | float | 否 | CFG 系数，默认 1 |

## 错误处理

### API 请求失败
- 检查环境变量是否正确设置
- 验证 API token 是否有效
- 确认网络连接正常

### task_id 未返回
- 检查请求参数是否符合工作流定义
- 查看错误消息了解具体原因

### 下载失败
- 确认任务已完成（可能需要等待）
- 检查 task_id 是否正确
- 验证 asset_index 是否在有效范围内

## 输出格式

生成的图片应该：
1. 保存到用户指定的路径或默认位置
2. 使用有意义的文件名（如 `portrait_asian_girl.png`）
3. 告知用户保存位置
4. 如果是批量生成，列出所有文件路径

## 示例对话

**用户**："帮我生成一张图片，一位年轻的亚洲女孩，长发，穿着蓝色卫衣"

**你应该**：
1. 确定使用 `text-to-image` 工作流
2. 将中文描述转换为英文提示词：
   ```
   young Asian woman, long black hair, wearing light blue hoodie,
   standing, outdoor, natural lighting, medium shot, masterpiece, best quality
   ```
3. 构造 API 请求并执行
4. 下载生成的图片
5. 告诉用户图片保存位置

**用户**："把这张照片放大，要高清的"

**你应该**：
1. 确定使用 `upscale` 工作流
2. 将用户提供的图片编码为 Base64
3. 调用 API 执行放大
4. 下载并保存高清图片
5. 告诉用户新图片的尺寸和保存位置

## 参考文档

- [API 文档](./references/api-guide.md) - API 接口详细说明
- [示例集合](./references/examples.md) - 更多使用示例
