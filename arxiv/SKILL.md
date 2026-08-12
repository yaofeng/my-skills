---
name: arxiv
description: 下载、翻译、分析 arXiv 论文，构建本地论文资料库。翻译任务指基于 source 原始 LaTeX 源码进行保留原始格式的原地中文翻译并输出到 source-cn，专业术语默认采用“中文（English）”保留英文原文；生成 Markdown 任务指基于 source-cn 已翻译源码生成 translation 下的 Markdown 文档；编译 PDF 任务指根据 source 或 source-cn 中的 LaTeX 工程编译生成 PDF，中文 PDF 需采用适合屏幕阅读的字体与行距优化方案。
---

# arXiv 论文翻译技能

## 工作目录与文件规范

### 目录结构
```
<project-root>/
├── source/                              # 原始 LaTeX 源码
│   ├── index.md                         # 论文索引
│   └── <arXiv编号>-<技术简称>/           # 单篇原始论文目录
├── source-cn/                           # 原地中文翻译后的 LaTeX 源码
│   └── <arXiv编号>-<技术简称>/           # 与 source 同名、同结构的中文源码目录
├── translation/                         # 从 source-cn 生成的产物
│   ├── <arXiv编号>-<技术简称>.md         # 单篇完整 Markdown 译文
│   └── <arXiv编号>-<技术简称>.pdf        # 从 source-cn 编译的中文 PDF（与 Markdown 同名）
└── summary/                             # 论文分析报告
    └── <论文标题>-<日期>.md
```

### 名称规范
- **子目录**: `2606.02800-Cosmos3`（arXiv编号-技术简称，技术简称如 Cosmos3、TrAISformer）
- **索引中的摘要字段**：题目、arXiv 编号、目录、作者、机构、发表时间、关键字、核心贡献、摘要、代码仓库、创建日期
- **中文源码目录**: `source-cn/2606.02800-Cosmos3/`
- **Markdown 文件**: `translation/2606.02800-Cosmos3.md`
- **PDF 文件**: `translation/2606.02800-Cosmos3.pdf`（与 Markdown 文件同名同目录）

---

## 任务路由

### 术语约定

- 用户说“翻译”“完整翻译”“全文翻译”“翻译第 X 章”时，默认执行 **任务一：翻译（source → source-cn 原地翻译）**。
- 所有中文翻译任务默认保留专业术语的英文原文，使用“中文译名（English original）”形式；即使用户没有特别说明，也要遵守本规则。
- 用户说“生成 Markdown”“导出 Markdown”“生成 translation 文档”时，执行 **任务二：生成 Markdown（source-cn → translation）**。
- 用户说“编译 PDF”“生成 PDF”“重新编译”“渲染 PDF”时，执行 **任务三：编译 PDF（source/source-cn → PDF）**。
- 不要把“翻译”“生成 Markdown”和“编译 PDF”混为同一个动作：翻译阶段只产出保留原始 LaTeX 结构的中文源码；Markdown 阶段只从已经翻译好的 `source-cn/` 读取内容并导出 Markdown；编译 PDF 阶段只基于已有 `source/` 或 `source-cn/` LaTeX 工程生成 PDF。
- 如果用户同时要求“翻译并生成 Markdown”，先完成任务一并通过结构覆盖检查，再执行任务二。
- 如果用户同时要求“翻译并编译 PDF”，先完成任务一并通过结构覆盖检查，再执行任务三；中文 PDF 优先从 `source-cn/<paper>/` 编译，编译验证后最终 PDF 复制到 `translation/<arXiv编号>-<技术简称>.pdf`。

---

## 任务一：翻译（source → source-cn 原地翻译）

### 前提

- 来源论文已下载到 `source/<arXiv编号>-<技术简称>/` 目录中。
- `source/index.md` 中已存在该论文的条目。

### 输出位置

- 中文 LaTeX 源码必须保存到 `source-cn/<arXiv编号>-<技术简称>/`。
- `source-cn/<paper>/` 必须与 `source/<paper>/` 保持同名子目录和主要文件结构。
- 默认不在翻译阶段写 `translation/<paper>.md`；除非用户同时要求生成 Markdown。

### 原地翻译原则

翻译任务是在原始 LaTeX 源码中进行“原地翻译”，目标是让中文 PDF 尽可能保持原文 PDF 的版式和结构。必须遵守：

- 先完整复制 `source/<paper>/` 到 `source-cn/<paper>/`，再在副本上修改；不得改动 `source/<paper>/` 原文。
- 保留原始 `.tex` 文件拆分、`\input` / `\include` 顺序、class、bst、bib、图片目录、宏定义和模板文件。
- 保留原始 LaTeX 环境与排版结构，包括 `figure`、`wrapfigure`、`table`、`table*`、`threeparttable`、`tabular`、`tabularx`、`longtable`、`equation`、`align`、`algorithm`、`itemize`、`enumerate`、脚注、引用和 label。
- 只翻译自然语言内容：标题、摘要、正文段落、图注、表注、列表项、算法说明、脚注、附录文字、必要的表格文本。
- 数学公式、数值、表格数据、引用 key、label key、图片路径和代码片段保持不变；模型名、基准名、专有名词及专业术语按下述英文保留规则处理。
- 不要把 LaTeX 表格改成 Markdown 表格；不要把图片改成 Markdown 图片；不要重排 figure/table；不要删除原始浮动体。
- 中文源码建议使用 XeLaTeX 编译：必要时在主文件加入 `\usepackage{ctex}`，并把 `00README.json` 的 compiler 更新为 `xelatex`。
- 如果当前环境没有 TeX 引擎，只生成可编译的 `source-cn` 源码并明确报告未能编译；不要用重排版 PDF 冒充原始模板编译结果。

### 专业术语英文保留规则

专业术语的英文原文能消除译名歧义，也便于读者检索相关文献。翻译标题、摘要、正文、图注、表注、列表、算法、脚注和附录时遵守：

- 专业术语首次出现时，默认写成“中文译名（English original）”，例如“注意力残差（Attention Residuals）”“流水线并行（pipeline parallelism）”。括号内保留原文术语，不使用自行改写的英文回译。
- 带缩写的术语写成“中文译名（English Full Name，ACRONYM）”，例如“大语言模型（Large Language Model，LLM）”。原文只给缩写且无法可靠确认全称时，不猜测扩写；保留原缩写并在必要时给出中文说明。
- 同一术语在同一章节或紧邻段落中重复出现时，可只使用中文译名或通行缩写，避免括号过密；在标题、摘要、图表、算法等可独立阅读的位置，或相隔较远重新出现时，优先再次给出中英对照。
- 同一术语全篇使用一致的中文译名和英文大小写。不要在不同章节中随意切换译法，也不要把同一英文术语改写成多个中文近义词。
- 模型名、数据集名、评测基准名、产品名、机构名、代码标识符、API 名和变量名通常直接保留原文，不强行翻译；若确需解释，采用“中文说明（原文名称）”。
- 数学公式、代码、引用 key、label key、文件路径和命令中的英文不做术语括注或翻译。
- 对没有公认中文译名、硬译会降低准确性的术语，可保留英文作为正文名称，并在首次出现时补充中文释义；不要为了机械满足格式而创造未经采用的中文术语。
- 交付前抽查各章节高频术语的首次出现，确认括号中包含准确英文原文，并检查译名、缩写和英文大小写的一致性。

### 原地翻译覆盖清单

在翻译前展开主文件中的 `\input` / `\include`，按真实阅读顺序统计并记录：

- `.tex` 文件列表与章节顺序；
- section、subsection、subsubsection、paragraph 数；
- 非空正文段落数；
- equation/align 等公式环境数；
- figure、wrapfigure、table、table*、algorithm 数；
- `\includegraphics` 路径；
- itemize/enumerate 条目数；
- footnote 数；
- bibliography 条目数。

完成后必须对比 `source/<paper>/` 与 `source-cn/<paper>/`：主要结构计数应一致；如果必须改变结构，需说明原因。

### 翻译后的编译提示

翻译任务完成后，如果用户同时要求编译，或需要验证中文源码是否可用，转入 **任务三：编译 PDF**。如果当前环境没有 TeX 引擎，只生成可编译的 `source-cn` 源码并明确报告未能编译；不要用重排版 PDF 冒充原始模板编译结果。

---

## 任务二：生成 Markdown（source-cn → translation）

### 前提
- 中文源码已存在于 `source-cn/<arXiv编号>-<技术简称>/` 目录中。
- 原始论文资源仍存在于 `source/<arXiv编号>-<技术简称>/` 目录中，用于 Markdown 图片链接。
- `source/index.md` 中已存在该论文的条目。

### “生成 Markdown”的交付契约

当用户要求“生成 Markdown”或在完成原地翻译后继续要求导出 Markdown 时，目标是基于 `source-cn/<paper>/` 忠实生成可阅读 Markdown，而不是总结论文。Markdown 必须满足：

- 原文每个非空正文段落都有语义等价的译文；保留原始段落边界，除非中文表达确有必要拆分。
- 保留 `source-cn` 中的中英术语对照形式；不得在导出 Markdown 时删除专业术语括号中的英文原文。
- 不得把多个原文段落合并成摘要、要点或概括，也不得用综合评价替代原文。
- 保留动机、解释、限定条件、转折、因果链、实现细节、实验目的和局限性；看似重复不构成省略理由。
- 每个公式、图注、表注、脚注、列表项、算法步骤、附录和参考文献都有对应内容。
- 每个 `figure` 除中文图注外，还必须用 Markdown 图片语法直接引用 `source/<paper>/` 目录中的原文图片资源，确保译文可直接预览图片；若原始资源是 PDF，必须先在 `source/<paper>/` 对应目录生成同名 PNG，再在 Markdown 中引用该 PNG。不要引用 `source-cn/<paper>/` 中的图片。
- 表格保留全部数据行、数据列和数值；不得只摘录最佳值或核心指标。
- 算法保留输入、输出、初始化、每一步操作和注释；不得改写为高层步骤摘要。
- 如果受上下文、时间或源文件缺失限制而无法完成，明确报告“部分 Markdown”，不得声称完整 Markdown 已经生成。

“覆盖了主要观点”不等于“完成了 Markdown 译文”。Markdown 文件与分析文件必须隔离：`translation/` 保存忠实 Markdown 译文，压缩、重组、评分和批判只写入 `summary/`。

### 生成 Markdown 前建立覆盖清单

在生成 Markdown 前，先展开 `source-cn/<paper>/<main>.tex` 中的 `\\input` / `\\include`，确定真实阅读顺序，并按 section/subsection 统计：

- 非空正文段落数；
- section、subsection、subsubsection、paragraph 数；
- 公式环境及公式组数；
- figure、table、algorithm 数；
- figure 中 `\includegraphics` 引用的图片资源路径；
- algorithmic 步骤数；
- itemize、enumerate 条目数；
- footnote 数；
- bibliography 条目数。

为内容单元赋予稳定标识，例如 `S3.2-P01`（3.2 节第 1 个正文段落）、`S3.2-E01`（第 1 组公式）、`S3.2-A01-L03`（算法 1 第 3 步）。生成 Markdown 时逐项勾销。只有该节所有单元都有对应 Markdown 内容后，才能把该节标为完成。

对 LaTeX 环境中的换行要谨慎：源码行数不是段落数。以空行、章节命令和块级环境边界识别段落，不能按固定行数截断段落、公式、表格或算法。

### 禁止摘要化

生成 Markdown 时，以下做法均视为内容缺失：

- 用“作者提出……结果表明……”替代完整论证；
- 将多个原文段落压成一个总结段落；
- 删除看似次要或重复的解释、比较、限定条件；
- 把算法代码改写成较少的概括步骤；
- 用“其余配置同上”替代原表中真实存在的数据；
- 只保留表格最优值、均值或主要指标；
- 先写全篇摘要式译文，再依赖后处理零散补齐。

若用户只要求摘要、综述或评价，才允许压缩内容，并应保存到 `summary/` 而非冒充完整 Markdown 译文。

### Markdown 生成规则

#### 章节标题
- `\title{...}` → `# 中文标题`（一级标题，论文标题）
- `\begin{abstract}...\end{abstract}` → 移除环境标记，在内容前加 `**摘要**` 标记行
- `\section{...}` → `## X 中文标题`
- `\subsection{...}` → `### X.X 中文标题`  
- `\subsubsection{...}` → `#### X.X.X 中文标题`
- `\paragraph{...}` → `**中文标题**`
- 移除所有 `\label{...}`
- **必须**生成一级标题（`#`），不得遗漏论文标题

#### 公式
- `\begin{equation}...\end{equation}` → `$$...$$`
- `\begin{equation*}...\end{equation*}` → `$$...$$`
- `\begin{align}...\end{align}`、`\begin{align*}...\end{align*}` → `$$...$$`
- `\begin{gather}...\end{gather}`、`\begin{multline}...\end{multline}` → `$$...$$`
- `\begin{aligned}...\end{aligned}` 等保持 `$$...$$` 内
- `\[...\]` → `$$...$$`
- `\(...\)` → `$...$`
- 内联公式保留 `$...$`
- **自定义命令必须展开为 KaTeX 兼容命令**（见下方"自定义命令处理"）
- **严禁**在正则替换中将 `$$` 替换为数字或其他字符串。处理数学公式时，必须先提取保护 `$...$` 和 `$$...$$` 块，再做其他文本替换，最后还原数学块。错误的替换会导致公式无法渲染。

#### 图/表
- `\begin{figure}...\end{figure}` → 转为 Markdown 引用块格式：
  ```
  ---
  
  ![图X](../source/<arXiv编号>-<技术简称>/figures/<图片文件>.png)
  
  **图X：标题。** 标题内容...
  
  ---
  ```
- `\begin{table}...\end{table}` → 转换为 Markdown 表格，保留标题，并像图片一样在表格块前后加入分割线：
  ```
  ---
  
  **表X：标题。** 标题内容...
  
  | 列1 | 列2 |
  |-----|-----|
  | ... | ... |
  
  ---
  ```
- 图/表编号从 1 开始计，在全文中全局递增
- 多个 `\includegraphics` 合并为同一图
- 如果多个图表块相邻，或表格块紧邻图片块，只保留一条共享分割线；不得出现连续重复的分割线，例如 `---` 空行后紧接另一个 `---`。
- 图片链接必须直接指向源码目录中的图片资源，**必须使用相对路径**（例如 `../source/2605.00809-GenLIP/figures/fig1.png`），不得使用绝对路径；如果一张图包含多个 `\includegraphics`，按原文顺序在同一图注前逐个插入 Markdown 图片引用。
- 图片 alt 文本应使用图注摘要（例如 `![Qwen-VLA 概述](...)`），不得仅用 `![图](...)`。
- 生成后**必须验证所有图片链接的目标文件存在**；不存在时报告缺失项。
- 若原始图片是 PDF，先在 PDF 所在目录生成同名 PNG（例如 `foo.pdf` → `foo.png`），再在 Markdown 中引用生成的 PNG；保留原始 PDF 文件，不要删除或替换上游资源。
- 推荐转换命令：`pdftoppm -png -singlefile source/<paper>/figures/foo.pdf source/<paper>/figures/foo`。若 `pdftoppm` 不可用，可使用系统等价工具，但输出文件仍必须是同目录、同名 `.png`。

#### 引用
- `\citep{key}` → `[key]`
- `\citet{key}` → `name et al.`
- `\citep{key1,key2}` → `[key1, key2]`
- `\ref{fig:xxx}` → `图X`（用实际编号）
- `\ref{tab:xxx}` → `表X`（用实际编号）
- `\ref{sec:xxx}` → `「章节标题」`（用实际章节中文标题，因为 Markdown 无节号）
- `\ref{eq:xxx}` → `公式X`
- `\cref{...}` / `\Cref{...}` → 同上（判断前缀决定图/表/节/公式）
- **波浪号+引用组合**：`~\ref{fig:xxx}` 和 `~\cref{fig:xxx}` 中的 `~` 必须与 `\ref`/`\cref` 一起替换为 `图X`，**不得**只剥离 `\ref` 而留下孤立 `~` 或空格。常见错误模式：`表~\ref{tab:data}` 被错误转换为 `表 ` （编号丢失），正确结果应为 `表 1`。
- **引用替换后不得留下孤立空格**：替换完成后检查 `图 ` / `表 ` 后跟标点或空行而非数字的模式。
- 移除 `\label{...}`

#### 列表
- `\begin{itemize}...\end{itemize}` → 移除，转为 `- ` 列表
- `\item` → `- `
- `\begin{enumerate}...\end{enumerate}` → 移除，转为 `1. ` 列表
- 嵌套列表保留缩进（2 空格 per level）

#### 行首空格处理
- Markdown 中 **4 个及以上行首空格会触发代码块渲染**，导致正文显示为等宽字体代码块。
- 所有正文行、段落、列表项**不得有行首空格**（数学块 `$$` 内部除外）。
- 列表项统一从行首开始（`- item`），嵌套列表用 2 空格缩进。
- LaTeX 源码中的缩进（如 `\item` 前的空格、段落前的空格）在转换为 Markdown 时**必须去除**。
- 后处理脚本必须检测并清除行首空格（数学块 `$$` 内部除外）。

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
- `\textsc{...}` → `*...*`（小型大写字母转为斜体）
- `\textlangle` → `⟨`
- `\textrangle` → `⟩`
- `\textbackslash` → `\`
- `\textbar` → `|`
- `\textgreater` → `>`
- `\textless` → `<`
- `\_` → `_`（文本模式中的转义下划线）
- `\{` → `{`、`\}` → `}`（文本模式中的转义花括号）
- `\,` → 空格（文本模式中）；数学模式中保留
- `\;` → 空格（文本模式中）；数学模式中保留
- `\!` → 移除（文本模式中）；数学模式中保留
- `\:` → 空格（文本模式中）；数学模式中保留
- `\quad` → 空格（文本模式中）；数学模式中保留
- `\qquad` → 空格（文本模式中）；数学模式中保留
- `\newline` → `<br>`（表格单元格内换行）
- `\noindent` → 移除
- `\ldots` / `\dots` → `...`
- `~`（波浪号/不间断空格）→ 空格（文本模式中，非引用连接符场景）
- `\underline{...}` → `**...**`（表格中）或 `*...*`（正文中）

#### 表格元素
- `\toprule`, `\midrule`, `\bottomrule` → 替换为 Markdown 表头分隔符 `---|---`
- `\cmidrule(lr){2-4}` 等 → **完整移除**，正则模式 `\\cmidrule\([^)]*\)\{[^}]*\}` 全部替换为空。**不得**残留 `\cmidrule` 或部分匹配如 `\cmidrule(lr){2-4**`。
- `\cline{...}` → 移除
- `\multirow{n}{*}{text}` → 展平为 `text`（放在对应行对应列）
- `\multicolumn{n}{c}{text}` → 展平为 `text`（放在对应列位置，占用 n 列）
- `\resizebox{...}{...}{...}` → 移除前两个参数，保留第三个参数（表格内容）
- `\begin{threeparttable}...\end{threeparttable}` → 移除
- `\begin{tabularx}{\textwidth}{...}...\end{tabularx}` → 转为普通 Markdown 表格（如作者列表）
- 转换后**必须验证每行列数一致**：用 Python 脚本检查每个 Markdown 表格中所有 `|` 分隔的列数相同。列数不一致会导致表格渲染错乱。
- 嵌套 `\multicolumn`/`\multirow` 展平后，需重新对齐列数，确保表头行与数据行列数匹配。

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
2. 记录每个 figure 中 `\includegraphics{...}` 的资源路径，并映射到对应图号
3. 统计 `\begin{table}` 出现的顺序  
4. 在翻译中替换为 `图1`、`图2`...`表1`、`表2`...

**图表标题也必须带编号**：图注和表注本身也必须使用编号，即 `**图 1：...**` 而非 `**图：...**`。标题编号和正文引用编号必须来自同一映射表，确保一致。

**注意嵌套 `\input`**：统计图表顺序时必须递归展开所有 `\input`/`\include`，因为图表环境可能定义在被嵌套引入的文件中。只展开一层会遗漏嵌套文件中的图表，导致编号映射错误。

**验证**：翻译完成后统计所有 `图\d+`、`表\d+`，确保最大编号与图/表总数一致；同时检查所有 Markdown 图片链接的目标文件存在，且图号与原始 figure 顺序一致。Markdown 图片链接不应指向 `.pdf`；PDF 原图必须已转换为 `source/<paper>/` 同目录同名 `.png` 后再引用。

---

### 术语一致性

在翻译文件开头维护术语对照表：
```
### 术语对照

| 原文 | 翻译 |
|------|------|
| Physical AI | 物理世界人工智能（Physical AI） |
| Reasoner | 推理器（Reasoner） |
| Generator | 生成器（Generator） |
```

生成 Markdown 过程中遇到新的技术术语时追加到该表中。术语表与正文统一采用“中文译名（English original）”；模型名、数据集名、基准名等无需强制改写为中文。

---

### 后处理：完整性验证

Markdown 生成完成后，**必须运行后处理验证脚本** `scripts/md_postcheck.py`，对生成的 Markdown 文件进行全面的自动化检查：

```bash
python3 <skill_dir>/scripts/md_postcheck.py <markdown_file> [--source-dir <source-cn目录>] [--figures-dir <source图片目录>]
```

脚本检查以下项目，按严重程度分类为 ERROR（必须修复）和 WARNING（建议修复）：

**ERROR 级检查**：
1. **数学分隔符完整性**：`$$` 出现次数为偶数；检测纯数字行（可能是 `$$` 被错误替换为数字的损坏分隔符）
2. **行首空格检测**：数学块 `$$` 外的行不得有行首空格（4+ 空格触发代码块渲染）
3. **LaTeX 残留命令检测**：检查文本模式中残留的 LaTeX 命令，包括但不限于：`\textlangle`、`\textrangle`、`\textbackslash`、`\textbar`、`\textgreater`、`\textless`、`\_`（文本模式）、`\{`、`\}`、`\,`（文本模式）、`\;`（文本模式）、`\!`（文本模式）、`\newline`、`\noindent`、`\textsc{`、`\underline{`、`\cmidrule`、`\multicolumn`、`\multirow`、`\tabularx`、`\begin{`、`\end{`、`\input{`、`\label{`、`\bibliography`、`\appendix`、`\citep{`、`\citet{`、`\cref{`、`\ref{`、`\texttt{`、`\textbf{`、`\textit{`、`\emph{`
4. **表格列数一致性**：每个 Markdown 表格中所有行的列数必须一致
5. **引用断链检测**：`图 ` / `表 ` 后跟空格、标点或行尾而非数字的模式（引用编号丢失）
6. **论文标题存在**：检测一级标题 `# ` 是否存在
7. **图片路径有效性**：所有 `![...](path)` 的目标文件是否存在（需要 `--figures-dir` 参数）

**WARNING 级检查**：
8. **图表标题编号完整性**：`图：` / `表：` 标题缺少编号（应为 `图 N：` / `表 N：`）
9. **图表编号一致性**：标题中的编号与正文引用编号是否匹配
10. **摘要标记存在**：检测 `**摘要**` 标记是否存在
11. **图片 alt 文本**：`![图](...)` 使用了无意义的 alt 文本
12. **KaTeX 兼容性**：提取数学模式中的 `\command{...}`，对照 KaTeX 支持列表验证

脚本退出码：有 ERROR 时返回 1，仅有 WARNING 时返回 0。**有 ERROR 时不得向用户报告"完整 Markdown"。**

---

### 分节生成 Markdown 策略

对于长论文（>200 行 LaTeX），按章节分批处理，但每个章节内部仍须逐段生成 Markdown：

1. 阅读并展开论文结构，建立全篇覆盖清单。
2. 按完整 section/subsection 分组，不在段落或环境中间切分。
3. 依照原始顺序处理“正文段落—公式—图表—算法—列表”。
4. 每完成一个内容单元，就在覆盖清单中标记对应关系。
5. 逐节检查段落、公式、图表和算法步骤数量，再进入下一节。
6. 合并后统一术语、引用和编号，但不得在润色时合并或删减原文内容。

若允许使用子代理，可按章节并行生成 Markdown，但必须向每个子代理提供该节完整 `source-cn` 源码和内容单元清单。主代理合并时必须自行进行覆盖审计，不能仅相信子代理的“已完成”声明。

---

## 任务三：编译 PDF（source/source-cn → PDF）

### 触发条件

当用户要求“编译 PDF”“生成 PDF”“重新编译”“渲染 PDF”“把源码编译出来”时，执行本任务。目标是使用论文目录中的 LaTeX 工程生成 PDF，而不是重新排版或用脚本仿制 PDF。

### 输入目录选择

- 编译原文 PDF：优先使用 `source/<arXiv编号>-<技术简称>/`。
- 编译中文 PDF：优先使用 `source-cn/<arXiv编号>-<技术简称>/`。
- 如果用户没有指定中文或原文：
  - 已存在 `source-cn/<paper>/` 且用户上下文在中文翻译任务后，默认编译中文 PDF；
  - 否则编译 `source/<paper>/` 中的原文 PDF。
- 编译前先读取 `00README.json`；如果其中声明了主文件、编译器或 TeX Live 版本，优先遵循。
- 若没有 `00README.json`，通过 `latexmkrc`、`\documentclass`、主 `.tex` 文件、`\input` / `\include` 关系判断主文件。常见主文件名包括 `main.tex`、`paper.tex`、`BAAI-TechReport.tex`。

### 输出位置

- PDF 先输出到被编译的源码目录中（用于编译验证），例如：
  - `source/<paper>/<main>.pdf`
  - `source-cn/<paper>/<main>.pdf`
- **编译验证通过后，必须将最终 PDF 复制一份到 `translation/<arXiv编号>-<技术简称>.pdf`**，与同名的 Markdown 译文保持一致。
- 不要把 `.aux`、`.log`、`.out`、`.bbl`、`.blg`、`.fls`、`.fdb_latexmk` 等 LaTeX 中间产物作为交付内容；如果仓库需要保持清洁，完成验证后可清理中间产物，但不要删除源码、图片、bib、bst、cls 或最终 PDF。

### 编译命令

优先使用 `latexmk`，让其自动处理多轮编译和参考文献：

```sh
latexmk -xelatex -interaction=nonstopmode <main>.tex
```

如果 `latexmk` 不可用，按显式轮次执行：

```sh
xelatex -interaction=nonstopmode <main>.tex
bibtex <main>
xelatex -interaction=nonstopmode <main>.tex
xelatex -interaction=nonstopmode <main>.tex
```

对于明确要求 `pdflatex`、`lualatex`、`biber` 或特定构建命令的论文，以 `00README.json`、`latexmkrc` 或论文源码说明为准。

### 中文 PDF 字体优化方案

编译 `source-cn/<paper>/` 时，目标是让中文 PDF 既保持原文版式，又适合屏幕阅读。优先使用 XeLaTeX，并在主文件中采用以下策略：

- 使用 `ctex` / `xeCJK` 支持中文，不使用 pdfLaTeX 强行编译中文。
- 字体优先级：
  - 屏幕阅读版：中文主字体优先选 `Heiti SC`、`PingFang SC`、`Noto Sans CJK SC`、`Source Han Sans SC` 等无衬线字体，粗体更清晰；
  - 原文论文风格版：若用户要求更接近传统论文，可选 `Songti SC`、`SimSun`、`Noto Serif CJK SC`、`Source Han Serif SC`；
  - 字体必须先通过实际编译验证。若 `PingFang SC` 的 TTC 映射导致 `fontspec` / `xeCJK` 错误，回退到 `Heiti SC` 或其他稳定字体。
- 推荐屏幕阅读参数：
  - 正文字号约 `9.8pt` 到 `10.2pt`；
  - 正文行高约 `13.5pt` 到 `14.5pt`，或 `\linespread{1.15}` 到 `\linespread{1.22}`；
  - 段间距约 `0.35\baselineskip` 到 `0.5\baselineskip`，避免行距放大后段落过散；
  - 摘要可使用 `10.2pt / 13.2pt` 左右，避免首页过度拥挤。
- 粗体优化：
  - 优先使用字体自带粗体或较重字重；
  - 如果伪粗体 `FakeBold` 触发 `xeCJK` 字形边界错误，不要继续使用，改用稳定的黑体类字体；
  - 粗体必须在正文、列表、图注中肉眼可辨。
- 保留原文图表、页眉、边距和浮动体结构；字体优化不得重排为全新版式。

示例配置，可按本机字体可用性调整：

```tex
\usepackage[fontset=none]{ctex}
\setCJKmainfont{Heiti SC}
\setCJKsansfont{Heiti SC}
\setCJKmonofont{Arial Unicode MS}
\linespread{1.18}
\AtBeginDocument{%
  \renewcommand\normalsize{\fontsize{9.8}{13.8}\selectfont}%
  \normalsize
}
```

如果追求传统论文观感，可改用：

```tex
\usepackage[fontset=none]{ctex}
\setCJKmainfont{Songti SC}
\setCJKsansfont{Heiti SC}
\setCJKmonofont{Arial Unicode MS}
\linespread{1.15}
```

### 编译验证

编译后必须验证：

- 命令退出码为 0，或日志中没有致命错误且 PDF 已正确生成；优先追求退出码为 0。
- `rg -n '^!|Undefined control sequence|LaTeX Error|Package .* Error|fontspec Error|Missing character|undefined references|undefined citations|Rerun' <main>.log` 不应出现未解释的严重问题。
- 使用 `pdfinfo` 或等价工具确认页数、纸张尺寸和输出文件。
- 渲染抽查至少首页、正文方法页、实验表格页、附录页和参考文献页，确认：
  - 中文不乱码；
  - 字号和行距适合阅读；
  - 粗体可辨；
  - 图表未大面积错位或溢出；
  - 页眉、页脚、引用和参考文献正常。
- 若字体调整导致页数变化，需要在交付中说明；为了屏幕阅读放大行距导致页数增加是可接受的。

### 失败处理

- 如果缺少 TeX 引擎或宏包，报告缺失项和已尝试的命令。
- 如果中文字体不可用，列出已测试字体，并回退到可编译字体。
- 如果原始工程本身无法编译，不要伪造 PDF；保留源码并说明阻塞点。
- 如果只生成了部分 PDF 或存在严重排版问题，明确标注为“编译未通过验收”，不要声称完成。

---

## 完整性验收门禁

KaTeX 和残留命令检查只能证明格式基本可用，不能证明内容完整。交付前必须额外完成以下验收。

### 结构覆盖

- `source-cn` 与 Markdown 的章节、子章节和显式 paragraph 覆盖一致。
- 公式组、图、表、算法、列表项、脚注和参考文献数量一致。
- 每个图都有对应 Markdown 图片引用，且链接到 `source/<paper>/` 目录中的真实图片资源；PDF 原图必须已在 `source/<paper>/` 同目录生成同名 PNG，Markdown 引用 PNG。
- 每个算法的步骤数量一致。
- 每张表的数据行、数据列和单元格内容均已保留。
- 每个表格块前后都有 Markdown 分割线，并且全文不存在连续重复的分割线。
- 图表编号全局连续，并与 label 映射一致。

### 逐节段落覆盖

为每个 section/subsection 生成内部审计表：

```markdown
| 章节 | 源文正文段落 | 已翻译段落 | 公式 | 图/表 | 算法步骤 | 未覆盖单元 |
|------|--------------|------------|------|-------|----------|------------|
| 3.2  | 5            | 5          | 5    | 0     | 7        | 无         |
```

Markdown 段落数量不要求机械地与源文一模一样，因为中文可能需要拆句；但每个 `source-cn` 段落必须能明确映射到一个或多个 Markdown 段落。任何 `source-cn` 段落映射不到 Markdown 时，验收失败。

### 压缩预警

出现以下信号时，暂停交付并逐句复核相关章节：

- 多个原文段落只对应一个短译文段落；
- 算法步骤数、列表项数或表格单元格数减少；
- 源文有完整的动机—方法—解释链，译文只剩方法结论；
- 源文中的 `however`、`because`、`therefore`、`crucially`、`in contrast` 等关系没有对应表达；
- 某节译文规模异常小于相邻、相似长度章节。

字符或词数比例只能用于触发复核，不能单独证明完整或不完整；中文通常比英文紧凑。

### 高风险章节人工回查

至少逐句回查以下部分：

- 方法章节及所有算法；
- 实验设置和训练协议；
- 消融实验的解释段落；
- Discussion、Limitations 和 Conclusion；
- 附录中的训练配置与实现细节。

### 完成条件

只有同时满足以下条件，才能向用户报告”Markdown 已完整生成”：

1. 覆盖清单没有未翻译单元。
2. 所有章节逐段完成，没有摘要式替代。
3. 公式、图、表、算法、列表、脚注、附录和参考文献全部处理。
4. 表格完整保留所有数据，算法完整保留所有步骤。
5. 所有图均已通过 Markdown 图片语法引用 `source/<paper>/` 中的图片资源，且链接路径存在；不得在 Markdown 中直接引用 PDF 图片，PDF 原图需先转换为同目录同名 PNG。
6. 所有表格块前后都有分割线，且没有连续重复的分割线。
7. 引用映射、KaTeX 兼容性和残留 LaTeX 命令检查通过。
8. 高风险章节人工回查未发现段落合并、信息删减或因果链丢失。
9. 数学分隔符 `$$` 完整，无被数字或其他字符串替代的损坏分隔符。
10. 无行首空格导致代码块渲染（数学块 `$$` 内部除外）。
11. 图表标题带编号（`图 N：` / `表 N：`），且与正文引用编号一致。
12. 所有 LaTeX 文本命令已转换（`\textlangle`、`\_`、`\,`、`\newline`、`\textsc`、`\underline`、`\cmidrule` 等）。
13. 论文一级标题（`\title`）已转换为 `#` 标题，摘要已有 `**摘要**` 标记。
14. 后处理验证脚本 `scripts/md_postcheck.py` 运行通过（无 ERROR）。
15. 专业术语首次出现已按“中文（English）”保留英文原文，缩写、译名和英文大小写在全文中一致。

任一条件不满足时，报告当前进度和未完成章节，使用”部分 Markdown”而不是”完整 Markdown”。

---

### 保存位置

- Markdown 文件保存到 `translation/<arXiv编号>-<技术简称>.md`。注意：该文件必须基于 `source-cn/<paper>/` 已翻译源码生成；Markdown 图片链接必须直接指向 `../source/<paper>/...` 下的原文 PNG 资源。
- PDF 文件保存到 `translation/<arXiv编号>-<技术简称>.pdf`，与 Markdown 文件同名同目录，便于对照查阅。
