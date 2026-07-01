---
name: arxiv
description: 下载、翻译、分析 arXiv 论文，构建本地论文资料库。涵盖 LaTeX 源码提取、全文中译、图/表/公式/引用处理、术语统一、KaTeX 兼容性检查。适用于用户要求"翻译 arXiv 论文"或"完整翻译第X章"的场景。
---

# arXiv 论文翻译技能

## 工作目录与文件规范

### 目录结构
```
<project-root>/
├── source/                              # LaTeX 源码
│   ├── index.md                         # 论文索引
│   └── <arXiv编号>-<技术简称>/           # 单篇论文目录
├── translation/                         # 翻译产物
│   └── <arXiv编号>-<技术简称>.md         # 单篇完整翻译
└── summary/                             # 论文分析报告
    └── <论文标题>-<日期>.md
```

### 名称规范
- **子目录**: `2606.02800-Cosmos3`（arXiv编号-技术简称，技术简称如 Cosmos3、TrAISformer）
- **索引中的摘要字段**：题目、arXiv 编号、目录、作者、机构、发表时间、关键字、核心贡献、摘要、代码仓库、创建日期
- **翻译文件**: `2606.02800-Cosmos3.md`

---

## 翻译流程

### 前提
- 来源论文已下载到 `source/<arXiv编号>-<技术简称>/` 目录中
- `source/index.md` 中已存在该论文的条目

### 翻译规则

#### 章节标题
- `\section{...}` → `## X 中文标题`
- `\subsection{...}` → `### X.X 中文标题`  
- `\subsubsection{...}` → `#### X.X.X 中文标题`
- `\paragraph{...}` → `**中文标题**`
- 移除所有 `\label{...}`

#### 公式
- `\begin{equation}...\end{equation}` → `$$...$$`
- `\begin{equation*}...\end{equation*}` → `$$...$$`
- `\begin{aligned}...\end{aligned}` 等保持 `$$...$$` 内
- 内联公式保留 `$...$`
- **自定义命令必须展开为 KaTeX 兼容命令**（见下方"自定义命令处理"）

#### 图/表
- `\begin{figure}...\end{figure}` → 转为 Markdown 引用块格式：
  ```
  ---
  
  **图X：标题。** 标题内容...
  
  ---
  ```
- `\begin{table}...\end{table}` → 转换为 Markdown 表格，保留标题
- 图/表编号从 1 开始计，在全文中全局递增
- 多个 `\includegraphics` 合并为同一图

#### 引用
- `\citep{key}` → `[key]`
- `\citet{key}` → `name et al.`
- `\citep{key1,key2}` → `[key1, key2]`
- `\ref{fig:xxx}` → `图X`（用实际编号）
- `\ref{tab:xxx}` → `表X`（用实际编号）
- `\ref{sec:xxx}` → `第X节`
- `\ref{eq:xxx}` → `公式X`
- `\cref{...}` / `\Cref{...}` → 同上（判断前缀决定图/表/节/公式）
- 移除 `\label{...}`

#### 列表
- `\begin{itemize}...\end{itemize}` → 移除，转为 `- ` 列表
- `\item` → `- `
- `\begin{enumerate}...\end{enumerate}` → 移除，转为 `1. ` 列表
- 嵌套列表保留缩进

#### 算法
- `\begin{algorithm}...\end{algorithm}` → 代码块或文本描述格式
- 保留算法标题和步骤

#### 特殊符号
- `\cmark` → `✓`
- `\xmark` → `✗`
- `\texttt{...}` → `` `<...>` ``
- `\textbf{...}` → `**...**`
- `\textit{...}` → `*...*`
- `\footnote{...}` → 注：...
- `\makecell{...}` → 合并为同一单元格文本

#### 表格元素
- `\toprule`, `\midrule`, `\bottomrule` → 替换为 Markdown 表头分隔符 `---|---`
- `\cmidrule`, `\cline` → 移除
- `\multirow`, `\multicolumn` → 在 Markdown 中展平为独立单元格
- `\resizebox` → 移除
- `\begin{threeparttable}...\end{threeparttable}` → 移除

---

### 自定义命令处理

论文常定义自己的 LaTeX 命令（`\newcommand`）。这些在 Markdown/KaTeX 中无法识别，必须展开：

1. **在源码中查找定义**：
   ```bash
   grep 'newcommand\|DeclareMathOperator\|def' common.tex | head -20
   ```

2. **常见替换模式**：
   - `\vect{#1}` = `\boldsymbol{\mathrm{#1}}`
   - `\rvv{text}` = 移除外层包裹，保留内部文本
   - 其他自定义命令类似展开

3. **用 Python 脚本批量替换**：
   ```python
   content = content.replace('\vect{x}', '\\boldsymbol{\\mathrm{x}}')
   content = re.sub(r'\\rvv\{([^}]*)\}', r'\1', content)
   ```

4. **检查所有数学模式中的命令**：提取 `$...$` 和 `$$...$$` 中的 `\command{` 模式，对照 KaTeX 支持列表验证。

---

### 引用编号策略

由于论文中引用是 `\ref{fig:xxx}` 形式，翻译时需要人工映射编号：

1. 统计源码中 `\begin{figure}` 出现的顺序（全局）
2. 统计 `\begin{table}` 出现的顺序  
3. 在翻译中替换为 `图1`、`图2`...`表1`、`表2`...

**验证**：翻译完成后统计所有 `图\d+`、`表\d+`，确保最大编号与图/表总数一致。

---

### 术语一致性

在翻译文件开头维护术语对照表：
```
### 术语对照

| 原文 | 翻译 |
|------|------|
| Physical AI | Physical AI（物理世界人工智能） |
| Reasoner | 推理器 |
| Generator | 生成器 |
```

翻译过程中遇到新的技术术语时追加到该表中。

---

### 后处理：KaTeX 兼容性检查

翻译完成后执行以下检查：

```python
import re

# 1. 检查残留 LaTeX 命令
for cmd in ['citep', 'citet', 'label', 'cref', 'texttt']:
    if re.findall(r'\\' + cmd + '{', content):
        print(f"Remaining: \\{cmd}{{...}}")

# 2. 提取所有数学模式中的 \command{...}，验证 KaTeX 支持
math_cmds = set()
for m in re.finditer(r'\$[^$]*\$', content):
    for cmd in re.finditer(r'\\([a-zA-Z]+)\{', m.group()):
        math_cmds.add(cmd.group(1))

# 对照 KaTeX 安全命令列表
katex_safe = {'mathrm', 'mathbf', 'mathbb', 'boldsymbol', 'text', ...}
unknown = math_cmds - katex_safe
if unknown:
    print(f"Unknown: {unknown}")
```

---

### 分节翻译策略

对于长论文（>200 行 LaTeX），可采用子代理并行翻译：

```
1. 阅读论文结构（section/subsection 分布）
2. 按章节分组源文件
3. 并行分发到子代理（每个子代理翻译 2-3 章）
4. 合并子代理输出，统一检查术语一致性和引用编号
```

---

### 保存位置

完整翻译文件保存到 `translation/<arXiv编号>-<技术简称>.md`。