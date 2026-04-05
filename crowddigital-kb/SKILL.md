---
name: crowddigital-kb
description: 众数信科内部知识库查询技能。当用户提到众数、CrowdDigital、众数信科、公司战略、商业计划、研发计划、公司知识库、内部知识、公司文档等关键词，或需要查询公司内部相关信息时，使用此技能。无论用户是否明确说"知识库"，只要涉及公司内部知识、业务规划、技术规划、组织信息等内容，都应优先使用此技能从知识库中搜索。
---

# 众数信科知识库

## 概述

此技能管理众数信科（CrowdDigital）的内部知识库。知识库通过 git 管理，托管在 `git@git.zhongshu.tech`。技能负责下载/更新知识库、维护索引、并搜索相关内容。

**本地存储:** `~/workspace/crowddigital-kb`

**索引文件:** `@~/workspace/crowddigital-kb/index.md`

## 已注册知识库

| 知识库 | 仓库路径 | 说明 |
|--------|---------|------|
| 商业计划 | `strategy-docs/business-plan` | 公司商业计划相关知识 |
| 研发计划 | `strategy-docs/development-plan` | 研发规划、技术路线相关知识 |

> 后续添加新知识库时，更新此表格，并更新下方"同步知识库"中的仓库列表。

## 核心流程

### 1. 同步知识库

当用户需要查询公司知识，或首次使用本技能时，确保知识库已下载到本地。

**检查本地状态:**
```bash
ls ~/workspace/crowddigital-kb/
```

**克隆知识库**（如果目录不存在）:
```bash
mkdir -p ~/workspace/crowddigital-kb
cd ~/workspace/crowddigital-kb
git clone git@git.zhongshu.tech:strategy-docs/business-plan.git business-plan
git clone git@git.zhongshu.tech:strategy-docs/development-plan.git development-plan
```

**更新知识库**（如果已存在）:
```bash
cd ~/workspace/crowddigital-kb/business-plan && git pull
cd ~/workspace/crowddigital-kb/development-plan && git pull
```

**同步后必须更新 index.md** — 见下方"维护索引"章节。

### 2. 维护索引

每次 clone 或 pull 知识库后，更新 `~/workspace/crowddigital-kb/index.md`。

**索引文件格式:**
```markdown
# 众数信科知识库索引

> 最后更新: <YYYY-MM-DD HH:MM>

## 知识库列表

### 商业计划 (business-plan)
简要描述该知识库的内容和用途。

**目录结构:**
<通过 tree 或 ls 命令生成的文件树>

### 研发计划 (development-plan)
简要描述该知识库的内容和用途。

**目录结构:**
<通过 tree 或 ls 命令生成的文件树>
```

**生成目录结构:**
```bash
cd ~/workspace/crowddigital-kb/business-plan
tree -L 3 --dirsfirst
# 如果 tree 不可用，使用 find . -maxdepth 3 | head -50

cd ~/workspace/crowddigital-kb/development-plan
tree -L 3 --dirsfirst
```

根据目录结构和文件内容为每个知识库编写简要描述，让索引文件本身就是一个有用的导航工具。

### 3. 搜索知识

当用户提问时，按以下步骤搜索：

1. **读取索引** — 先查看 `@~/workspace/crowddigital-kb/index.md`，确定哪些知识库可能相关
2. **定位文件** — 使用 Glob 和 Grep 在相关知识库中搜索关键词
3. **阅读内容** — 使用 Read 工具读取匹配的文件
4. **综合回答** — 基于知识库内容回答用户问题，注明信息来源

**搜索示例:**
```bash
# 按文件名搜索
find ~/workspace/crowddigital-kb/business-plan -name "*.md" | xargs grep -l "关键词"

# 按内容搜索
grep -r "关键词" ~/workspace/crowddigital-kb/ --include="*.md"
```

优先使用 Glob 和 Grep 工具而非 bash 命令来搜索文件。

### 4. 添加新知识库

当需要添加新的知识库时：

1. 确认仓库路径（格式: `<group>/<repo>`）
2. 克隆到 `~/workspace/crowddigital-kb/<repo>/`
3. 更新本 SKILL.md 中的"已注册知识库"表格
4. 更新 `index.md` 索引文件

## 工作流程

```
用户查询公司相关信息
    │
    ├─→ 检查 index.md 是否存在
    │   ├─→ 不存在: 同步所有知识库 → 生成 index.md
    │   └─→ 存在: 阅读 index.md 确定相关知识库
    │
    ├─→ 在相关知识库中搜索
    │   ├─→ 找到匹配内容 → 阅读并回答
    │   └─→ 未找到 → 询问用户是否需要更新知识库（git pull）
    │       ├─→ 更新后重新搜索
    │       └─→ 仍无结果 → 告知用户知识库中未找到相关内容
    │
    └─→ 如果需要新知识库 → 引导添加
```

## 注意事项

- **优先本地搜索** — 先查 index.md 判断范围，再精准搜索，避免全量扫描
- **保持索引更新** — 每次 clone 或 pull 后必须更新 index.md
- **注明来源** — 回答时引用具体的文件路径，方便用户追溯
- **git 配置** — 确保 SSH key 已配置，可访问 `git@git.zhongshu.tech`
- **目录不存在时** — 如果 `~/workspace/crowddigital-kb` 不存在，先创建目录再克隆
