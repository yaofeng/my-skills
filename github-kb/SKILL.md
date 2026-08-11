---
name: github-kb
description: 管理本地GitHub知识库,搜索GitHub仓库、issue和PR。当用户提到github、repo、repository、仓库,或要求下载/搜索GitHub内容时使用此技能。此技能处理所有GitHub相关的查询和仓库管理操作。知识库目录采用 `owner/repo` 两层结构存储。
---

# GitHub 知识库

## 概述

此技能管理一个本地GitHub知识库,并提供GitHub搜索功能。它维护已下载仓库的索引目录,并可以使用`gh` CLI工具搜索GitHub上的issue、PR和仓库。

**知识库位置:** `~/workspace/github-kb`

**目录结构:** 所有仓库以 `owner/repo` 两层结构存储,例如 `QwenLM/Qwen3-ASR`(克隆时必须显式指定目标目录)

**仓库索引:** 通过 `@~/workspace/github-kb/index.md` 引用 - 包含所有已下载仓库的一句话摘要

## 核心功能

### 1. 仓库搜索和访问

当用户提到任何GitHub仓库名称或询问某个仓库时:

1. **首先检查本地知识库:**
   - 阅读 `@~/workspace/github-kb/index.md` 查看仓库是否已下载
   - 如果找到,探索本地副本以回答用户的问题
   - 使用 `Glob` 和 `Read` 工具在仓库内搜索

2. **如果本地未找到:**
   - 使用 `gh repo view <owner/repo>` 验证仓库是否存在
   - 询问用户是否要将其下载到知识库

### 2. 下载仓库

当用户请求下载仓库时:

1. **确认 gh CLI 可用:**
   ```bash
   gh auth status
   ```
   - 若未登录,提示用户先执行 `gh auth login`

2. **确保知识库目录存在(首次使用自动初始化):**
   ```bash
   mkdir -p ~/workspace/github-kb
   ```
   - 默认路径为 `~/workspace/github-kb`;若用户指定了其他路径,更新本SKILL.md中的路径

3. **克隆仓库(保持 `owner/repo` 两层目录结构):**
   ```bash
   cd ~/workspace/github-kb
   gh repo clone <owner/repo> <owner>/<repo>
   # 或: git clone https://github.com/<owner>/<repo>.git <owner>/<repo>
   ```
   - **必须**显式指定目标目录 `<owner>/<repo>`,因为 `gh repo clone`/`git clone` 默认只创建 `<repo>` 单层目录,不会自动生成 owner 层
   - 克隆后验证结果:`ls -la ~/workspace/github-kb/<owner>/<repo>`

4. **更新index.md索引:**
   - 若 `~/workspace/github-kb/index.md` 不存在,先创建索引骨架(标题、仓库列表表格、"最后更新"时间戳)
   - 为新仓库添加一个条目,使用 `owner/repo` 格式的链接
   - 摘要应该描述仓库的功能
   - 更新"最后更新"时间戳

**条目格式示例:**
```markdown
| [QwenLM/Qwen3-ASR](./QwenLM/Qwen3-ASR) | Qwen3 ASR - 自动语音识别模型 |
```

### 3. GitHub搜索

使用 `gh` 命令搜索GitHub信息:

**搜索仓库:**
```bash
gh search repos <query> --limit 10
```

**搜索issue:**
```bash
gh search issues <query> --limit 20
```

**搜索拉取请求:**
```bash
gh search prs <query> --limit 20
```

**搜索代码:**
```bash
gh search code <query> --limit 20
```

**查看仓库详情:**
```bash
gh repo view <owner/repo>
```

**查看仓库中的issue/PR:**
```bash
gh issue list --repo <owner/repo> --limit 20
gh pr list --repo <owner/repo> --limit 20
```

**查看特定issue/PR:**
```bash
gh issue view <number> --repo <owner/repo>
gh pr view <number> --repo <owner/repo>
```

### 4. 回答问题

当用户询问GitHub相关内容时:

1. **分析查询** - 是否涉及:
   - 用户提到的特定仓库?
   - 通用GitHub搜索(issue、PR、仓库)?
   - 仓库内的代码?

2. **选择方法:**
   - **本地仓库** → 在 `~/workspace/github-kb/<owner>/<repo>/` 中搜索
   - **GitHub搜索** → 使用适当的 `gh` 命令
   - **两者结合** → 先检查本地,然后回退到GitHub搜索

3. **提供全面的回答**,包括:
   - 问题的直接答案
   - 相关issue/PR/仓库的链接
   - 有帮助的代码片段
   - 仓库文档的上下文

## 工作流程

```
用户提到GitHub/repo/仓库?
    │
    ├─→ 是: 检查 @~/workspace/github-kb/index.md
    │       │
    │       ├─→ 本地找到仓库?
    │       │   ├─→ 是: 探索本地副本,回答问题
    │       │   └─→ 否: 使用gh命令搜索GitHub
    │       │            └─→ 询问用户是否要下载
    │       │
    │       └─→ 用户想下载?
    │           ├─→ 是: gh repo clone → 更新index.md
    │           └─→ 否: 仅使用gh搜索命令
    │
    └─→ 否: 仅在出现GitHub上下文时使用此技能
```

## 重要说明

- **始终先检查本地索引** - 这比搜索GitHub更快,且用户已经精选了这些仓库
- **保持index.md更新** - 每个下载的仓库都应该有一句话摘要
- **使用@引用** - 使用 `@~/workspace/github-kb/index.md` 引用CLAUDE.md文件,以便在需要时加载
- **主动帮助** - 如果本地搜索失败,主动提供搜索GitHub的建议
- **目录结构** - 仓库一律按 `owner/repo` 两层结构存储,克隆时显式指定目标目录;若用户自定义了知识库路径,同步更新本SKILL.md

## 可用工具

- **gh CLI** - 用于所有GitHub API交互(搜索、查看、克隆;克隆前确认已 `gh auth login`)
- **Glob** - 在本地仓库中查找文件 (`**/*.py`, `**/README.md` 等)
- **Grep** - 在本地仓库中搜索内容
- **Read** - 从本地仓库读取特定文件
- **mcp__zread__*** - 如果可用,用于在线读取GitHub仓库的MCP工具
