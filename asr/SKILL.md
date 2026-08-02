---
name: asr
description: 从音频/视频生成 SRT 字幕（语音识别 + 自动纠错，分普通/精准两档）、将非中文内容翻译为中文、并以 Markdown 总结内容。当用户要求转录音频、语音识别、生成字幕、创建 SRT 文件、翻译字幕或总结视频内容时使用此技能。
---

# SRT 字幕工作流（语音识别 / 翻译 / 总结）

本技能处理三个任务：
1. **语音识别**（含自动纠错，分普通 / 精准两档）
2. **内容翻译**（非中文 → 中文，语意翻译）
3. **内容总结**（Markdown 中文输出，按内容种类选择策略）

## 技能包结构

```
<skill-path>
├── SKILL.md              # 本文件
└── scripts/
    ├── setup_venv.sh     # 虚拟环境校验 / 创建脚本
    ├── asr.py            # ASR 转录脚本（FunASR，单/双模型）
    └── merge_srt.py      # SRT 合并 + 噪声过滤（精准识别可选辅助）
```

**路径约定**（本文所有命令中的占位符含义，请勿写入具体路径）：
- `<skill-path>`：本技能包目录（`scripts/` 的上一级），即 Agent 加载本技能时所在位置。
- `<current-workspace>`：当前项目工作目录（运行技能时所在目录），含下列子目录：
  - `audio/`   输入的音频/视频文件
  - `srt/`     生成的 SRT 文件
  - `summary/` 内容总结（.md）
  - `tmp/`     临时处理文件
- `<venv-path>`：技能使用的 Python 虚拟环境，默认 `~/.venv/funasr`，可用环境变量 `VENV_DIR` 覆盖（见 setup_venv.sh）。

## 步骤 0：环境准备（每次执行任务前必须先完成）

### 0.1 校验虚拟环境

本技能的 Python 脚本运行于独立虚拟环境 `<venv-path>`。执行前**必须**先运行 `scripts/setup_venv.sh` 完成环境准备：

```bash
bash <skill-path>/scripts/setup_venv.sh
```

该脚本是幂等的，会自动处理三种情况：
- 虚拟环境**存在且依赖完整** → 直接通过，跳过。
- 虚拟环境**存在但依赖缺失** → 只补装缺失依赖。
- 虚拟环境**不存在** → 创建并安装依赖。

**工具链选择（uv 优先）：**
- 本机有 `uv`（`command -v uv`）→ 使用 `uv venv` 创建、`uv pip install` 安装。
- 本机没有 `uv` → 降级为传统方式：`python3 -m venv` 创建 + `pip install`。

脚本执行成功后输出 CUDA 可用性，再进入下一步设备选择。

### 0.2 校验 GPU 与选择设备

优先使用本机 GPU 推理：

```bash
<venv-path>/bin/python -c "import torch; print('CUDA 可用' if torch.cuda.is_available() else '无 GPU')"
```

- **有 GPU**：使用 `--device cuda:0`（多卡时用 `nvidia-smi` 确认编号）。
- **无 GPU**：**告知用户**当前没有可用 GPU，并**询问**是否改用 CPU 推理（`--device cpu`）。用户确认前不要擅自继续。

## 任务 1：语音识别（含自动纠错）

识别分**普通**与**精准**两个等级。默认使用**普通**；用户要求更高质量时使用**精准**。

| 等级 | ASR 模型 | 纠错方式 | 适用场景 |
|------|----------|----------|----------|
| 普通 | SenseVoiceSmall（单模型） | 依据上下文推理纠错 | 快速、一般需求 |
| 精准 | SenseVoiceSmall + Fun-ASR-Nano（`both`，双模型） | 综合两个识别结果分析纠错 | 对质量要求高 |

### 普通识别流程

1. 运行 ASR（设备按 0.2 选择）：

   ```bash
   <venv-path>/bin/python <skill-path>/scripts/asr.py \
     -i <input-audio-file> \
     --asr-model SenseVoiceSmall -l <language> --device cuda:0
   ```

   → 输出 `srt/<stem>_1.srt`

2. 读取 `_1.srt` 全部内容，**依据上下文推理**逐条纠错，生成 `srt/<stem>.srt`：
   - 结合前后条目语境修正 ASR 误识（同音字、错别字、人名、术语）。
   - **过滤无语意内容**：噪声、呻吟（あ/い/う/え/お 等重复）、笑声、单字或极短片段、纯标点、纯英文语气词（okay/yeah/oh/uh 等）、渗入的无关语言。
   - 折叠过长重复字符（如 あああああ → あああ）。
3. 重新编号条目（从 1 开始），时间戳使用标准化 `HH:MM:SS,mmm` 格式。

### 精准识别流程

1. 运行 ASR 双模型（设备按 0.2 选择）：

   ```bash
   <venv-path>/bin/python <skill-path>/scripts/asr.py \
     -i <input-audio-file> \
     --asr-model both -l <language> --device cuda:0
   ```

   → 输出 `srt/<stem>_1.srt`（SenseVoiceSmall）与 `srt/<stem>_2.srt`（Fun-ASR-Nano）

2. （可选）先用 `merge_srt.py` 做机械合并与噪声预过滤，得到初步结果，便于后续对照：

   ```bash
   <venv-path>/bin/python <skill-path>/scripts/merge_srt.py \
     --stem <stem> --workspace <current-workspace>
   ```

   → 输出 `srt/<stem>.pre.srt`

3. 读取**两个原始 SRT**（以及初步合并结果），**综合两个识别结果**分析纠错，生成 `srt/<stem>.srt`：
   - 逐条对比两个模型输出：**二者一致处可信度高**，直接采纳；不一致时结合上下文判断哪个更合理。
   - 融合互补信息：一个模型漏掉/误识的内容，用另一个模型的正确部分补全。
   - 同样执行：过滤无语意内容（噪声、呻吟、笑声等）、修正常见误识、折叠过长重复、重编号、标准时间戳。

### 参数说明（asr.py）

- `-i / --input-audio`：音频文件路径；省略则显示 `audio/` 目录的交互菜单。
- `-l / --language`：`auto`、`zn`、`en`、`yue`、`ja`（默认）、`ko`、`nospeech`。
- `--asr-model`：`SenseVoiceSmall`、`Fun-ASR-Nano` 或 `both`。
- `--device`：`auto`（默认，自动检测 GPU）、`cuda:0`、`cuda:1`、`cpu`。
- `--batch-size`：ASR 批处理大小（默认 10）；显存充足可调大加速。
- `--workspace`：工作目录。

### 完成确认

完成后简要报告：各原始文件条目数、合并后条目数、作为噪声丢弃的条目数。

## 任务 2：内容翻译（非中文 → 中文）

读取纠错后的 `srt/<stem>.srt`，生成中文版本 `srt/<stem>.cn.srt`。

- 仅当内容为非中文时翻译；若已是中文则直接复制即可。
- **语意翻译，非逐字翻译**。在整句语意不变的前提下，**通顺、简洁**是最重要的：
  - 去除无意义的填充词、重复、口头禅。
  - 中文读起来自然流畅，不像机器翻译。

**处理流程：**
1. 读取完整纠错 SRT。
2. 逐条将文本翻译为自然中文，保持相邻条目间的对话上下文连贯。
3. 写入 `srt/<stem>.cn.srt`，保持**完全相同的时间戳与条目编号**，只替换文本。

## 任务 3：内容总结（Markdown 中文输出）

读取**纠错后的** `srt/<stem>.srt`（注意：总结的是识别结果原文，**不是**翻译后的内容），用中文总结，保存到 `summary/<stem>.md`。

**根据识别内容的种类采用不同总结策略：**

- **影片类**：按**场景**总结。识别场景转换点，每个场景给出描述性小标题 + 时间范围，记录该场景的关键情节、对话、动作与叙事发展。
- **新闻类**：按**地区 / 时间**归纳总结。以发生地区或时间顺序组织，突出事件要素（何时、何地、何事、何结果）。
- **技术类**：从**技术角度**总结，并给出**综合性评价**。提炼核心观点、技术要点、方法与结论，评价其价值、局限与适用性。
- **其他内容**：自动选择最合适的方式（对话类按话题、解说类按逻辑主线等）。

**通用要求：**
- 全部使用中文撰写。
- 顶部包含一段简要的**内容概述**。
- 结构清晰，使用 Markdown 标题层级（如 `## 第N章`、`### N.M 小节`）。

## 通用指南

- **文件名 stem**：来自输入音频文件名（如 `xxx_001.mp4` → stem `xxx_001`）。
- **Python 路径**：运行 `asr.py` / `merge_srt.py` 时始终使用 `<venv-path>/bin/python`，不要用系统 python。
- **默认语言**：先识别一小段进行语言判断，除非用户另行指定。
- **设备**：GPU 优先；无 GPU 时先告知用户并询问是否使用 CPU。
- **询问用户**：用户未指定音频文件时，列出 `audio/` 目录中的可用文件帮助选择。
- **进度报告**：ASR 步骤耗时较长，在每个阶段告知用户当前进展。
- 同时请求多个任务时按序执行：识别 → 翻译 → 总结。每个步骤依赖上一步的输出。
