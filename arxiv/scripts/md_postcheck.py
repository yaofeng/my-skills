#!/usr/bin/env python3
"""
arxiv 技能 Markdown 后处理验证脚本

检查生成的 Markdown 文件是否存在以下问题：
  ERROR 级：
    1. 数学分隔符完整性（$$ 偶数，无数字替代）
    2. 行首空格检测（数学块外）
    3. LaTeX 残留命令检测（文本模式）
    4. 表格列数一致性
    5. 引用断链检测（图 / 表 后无编号）
    6. 论文标题存在（一级标题 #）
    7. 图片路径有效性
  WARNING 级：
    8. 图表标题编号完整性
    9. 图表编号一致性
   10. 摘要标记存在
   11. 图片 alt 文本质量
   12. KaTeX 兼容性

用法：
  python3 md_postcheck.py <markdown_file> [--source-dir <dir>] [--figures-dir <dir>]

退出码：有 ERROR 返回 1，仅有 WARNING 返回 0。
"""

import argparse
import os
import re
import sys
from pathlib import Path


# ── ANSI 颜色 ──────────────────────────────────────────────
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RESET = "\033[0m"
BOLD = "\033[1m"


def fmt_error(msg):
    return f"{RED}ERROR{RESET} {msg}"

def fmt_warning(msg):
    return f"{YELLOW}WARNING{RESET} {msg}"

def fmt_ok(msg):
    return f"{GREEN}OK{RESET} {msg}"


# ── 数学块追踪 ─────────────────────────────────────────────

def get_math_block_lines(lines):
    """返回在 $$...$$ 数学块内部的行号集合（0-based）。"""
    in_math = False
    math_lines = set()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "$$":
            math_lines.add(i)
            in_math = not in_math
        elif in_math:
            math_lines.add(i)
    return math_lines


def strip_inline_math(text):
    """移除 $...$ 和 $$...$$ 内容，用于检查文本模式残留。"""
    text = re.sub(r"\$\$.*?\$\$", "", text, flags=re.DOTALL)
    text = re.sub(r"\$[^$]+\$", "", text)
    return text


# ── 检查项 ─────────────────────────────────────────────────

def check_math_delimiters(lines, errors):
    """检查 1: 数学分隔符完整性。"""
    # 统计 $$ 出现次数
    dd_count = sum(1 for line in lines if line.strip() == "$$")
    if dd_count % 2 != 0:
        errors.append(f"数学分隔符 `$$` 出现 {dd_count} 次（奇数），数学块未正确闭合。")

    # 检测纯数字行（可能是 $$ 被替换为数字）
    for i, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r"^\d{4,6}$", stripped):
            errors.append(
                f"第 {i+1} 行: 疑似 `$$` 被错误替换为数字 `{stripped}`。"
                f"请检查数学公式分隔符是否损坏。"
            )


def check_leading_spaces(lines, errors, warnings):
    """检查 2: 行首空格检测。"""
    math_lines = get_math_block_lines(lines)
    count = 0
    for i, line in enumerate(lines):
        if i in math_lines:
            continue
        stripped = line.rstrip("\n")
        if stripped and stripped != stripped.lstrip():
            count += 1
            if count <= 5:
                errors.append(
                    f"第 {i+1} 行: 行首有空格（{len(stripped) - len(stripped.lstrip())} 个），"
                    f"可能导致代码块渲染: {stripped[:80]}..."
                )
    if count > 5:
        errors.append(f"共 {count} 行有行首空格（仅显示前 5 个）。")


def check_latex_remnants(lines, errors, warnings):
    """检查 3: LaTeX 残留命令检测（文本模式）。"""
    math_lines = get_math_block_lines(lines)

    # 文本模式中不应出现的 LaTeX 命令
    text_latex_cmds = [
        # 引用/标签
        r"\\citep\{", r"\\citet\{", r"\\cite\{", r"\\cref\{", r"\\Cref\{",
        r"\\ref\{", r"\\label\{", r"\\bibliography", r"\\appendix",
        # 文本格式
        r"\\texttt\{", r"\\textbf\{", r"\\textit\{", r"\\emph\{",
        r"\\textsc\{", r"\\underline\{",
        # 特殊符号
        r"\\textlangle", r"\\textrangle", r"\\textbackslash",
        r"\\textbar", r"\\textgreater", r"\\textless",
        # 转义字符（文本模式）
        r"\\_(?=[a-zA-Z])",  # \_ 后跟字母（如 chunk\_size）
        r"\\\{", r"\\\}",
        # 间距命令（文本模式）
        r"\\,(?!\d)", r"\\;", r"\\!", r"\\:", r"\\quad", r"\\qquad",
        # 结构命令
        r"\\newline", r"\\noindent", r"\\ldots", r"\\dots",
        # 表格命令
        r"\\cmidrule", r"\\multicolumn", r"\\multirow", r"\\tabularx",
        # 环境
        r"\\begin\{", r"\\end\{", r"\\input\{", r"\\include\{",
    ]

    for i, line in enumerate(lines):
        if i in math_lines:
            continue
        clean = strip_inline_math(line)
        for pat in text_latex_cmds:
            matches = re.findall(pat, clean)
            if matches:
                cmd_desc = matches[0] if len(matches) == 1 else f"{matches[0]} 等 {len(matches)} 处"
                errors.append(
                    f"第 {i+1} 行: 文本模式残留 LaTeX 命令 `{cmd_desc}`: "
                    f"{line.rstrip()[:80]}..."
                )


def check_table_columns(lines, errors, warnings):
    """检查 4: 表格列数一致性。"""
    in_table = False
    table_start = 0
    header_cols = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            cols = stripped.count("|") - 1
            if not in_table:
                in_table = True
                table_start = i + 1
                header_cols = cols
            else:
                if not stripped.startswith("|---") and cols != header_cols:
                    errors.append(
                        f"第 {i+1} 行: 表格列数不匹配（期望 {header_cols} 列，"
                        f"实际 {cols} 列），表格起始行 {table_start}: "
                        f"{stripped[:80]}..."
                    )
        else:
            if in_table and not stripped.startswith("|---"):
                in_table = False


def check_dangling_refs(lines, errors, warnings):
    """检查 5: 引用断链检测。"""
    # 检测 "图 " / "表 " 后跟空格、标点或行尾而非数字
    for i, line in enumerate(lines):
        # 图 后面应该跟数字，如 "图 3"
        if re.search(r"[图表] (?![0-9])", line):
            # 排除标题行中的 "图表" 或 "图表号" 等非引用
            if not line.strip().startswith("**图") and not line.strip().startswith("**表"):
                match = re.search(r"[图表] (?![0-9])", line)
                if match:
                    errors.append(
                        f"第 {i+1} 行: 引用断链，`{match.group()}`后缺少编号: "
                        f"{line.rstrip()[:80]}..."
                    )


def check_title(lines, errors, warnings):
    """检查 6: 论文标题存在。"""
    has_h1 = any(line.strip().startswith("# ") for line in lines)
    if not has_h1:
        errors.append("缺少一级标题 `#`（论文标题 \\title 未转换）。")


def check_image_paths(lines, errors, warnings, figures_dir):
    """检查 7: 图片路径有效性。"""
    img_pattern = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
    found = False
    for i, line in enumerate(lines):
        for m in img_pattern.finditer(line):
            found = True
            alt = m.group(1)
            path = m.group(2)
            if figures_dir:
                # 尝试解析相对路径
                full_path = os.path.join(figures_dir, os.path.basename(path))
                # 也尝试从 figures_dir 的父目录解析
                alt_path = os.path.join(os.path.dirname(figures_dir), path.lstrip("../"))
                if not os.path.exists(full_path) and not os.path.exists(alt_path):
                    if not os.path.isabs(path):
                        # 尝试直接相对于 figures_dir 的上级
                        try_path = os.path.join(figures_dir, "..", path)
                        if not os.path.exists(try_path):
                            errors.append(
                                f"第 {i+1} 行: 图片路径不存在: `{path}`"
                            )
                    elif not os.path.exists(path):
                        errors.append(
                            f"第 {i+1} 行: 图片路径不存在: `{path}`"
                        )

            # 检查是否为绝对路径
            if os.path.isabs(path):
                warnings.append(
                    f"第 {i+1} 行: 图片使用了绝对路径 `{path}`，建议使用相对路径。"
                )

            # 检查是否引用 PDF
            if path.lower().endswith(".pdf"):
                errors.append(
                    f"第 {i+1} 行: 图片引用了 PDF `{path}`，应转换为同名 PNG。"
                )

    if not found:
        warnings.append("未找到任何 Markdown 图片引用。")


def check_caption_numbers(lines, errors, warnings):
    """检查 8: 图表标题编号完整性。"""
    # 检测 **图： 或 **表： 缺少编号
    for i, line in enumerate(lines):
        stripped = line.strip()
        # **图：...  缺少编号
        if re.match(r"^\*\*图：", stripped) or re.match(r"^\*\*表：", stripped):
            warnings.append(
                f"第 {i+1} 行: 图表标题缺少编号（`图：` 应为 `图 N：`）: "
                f"{stripped[:60]}..."
            )
        # **表：**...  也缺少编号
        if re.match(r"^\*\*表：\*\*", stripped):
            warnings.append(
                f"第 {i+1} 行: 表格标题缺少编号: {stripped[:60]}..."
            )


def check_caption_ref_consistency(lines, errors, warnings):
    """检查 9: 图表编号一致性。"""
    # 提取标题中的编号
    caption_fig_nums = set()
    caption_tab_nums = set()
    for line in lines:
        for m in re.finditer(r"\*\*图 (\d+)[:：]", line):
            caption_fig_nums.add(int(m.group(1)))
        for m in re.finditer(r"\*\*表 (\d+)[:：]", line):
            caption_tab_nums.add(int(m.group(1)))

    # 提取正文引用中的编号
    ref_fig_nums = set()
    ref_tab_nums = set()
    for line in lines:
        for m in re.finditer(r"图 (\d+)", line):
            ref_fig_nums.add(int(m.group(1)))
        for m in re.finditer(r"表 (\d+)", line):
            ref_tab_nums.add(int(m.group(1)))

    # 检查正文引用了但标题中没有的编号
    missing_figs = ref_fig_nums - caption_fig_nums
    missing_tabs = ref_tab_nums - caption_tab_nums
    if missing_figs:
        warnings.append(
            f"正文引用了图编号 {sorted(missing_figs)}，但对应图标题中未找到这些编号。"
        )
    if missing_tabs:
        warnings.append(
            f"正文引用了表编号 {sorted(missing_tabs)}，但对应表标题中未找到这些编号。"
        )


def check_abstract(lines, errors, warnings):
    """检查 10: 摘要标记存在。"""
    has_abstract = any("摘要" in line for line in lines[:50])
    if not has_abstract:
        warnings.append("未在前 50 行找到 `摘要` 标记（\\begin{abstract} 可能未转换）。")


def check_image_alt(lines, errors, warnings):
    """检查 11: 图片 alt 文本质量。"""
    img_pattern = re.compile(r"!\[([^\]]*)\]\(")
    for i, line in enumerate(lines):
        for m in img_pattern.finditer(line):
            alt = m.group(1)
            if alt in ("图", "图。", "", "image", "img"):
                warnings.append(
                    f"第 {i+1} 行: 图片 alt 文本 `{alt}` 无意义，"
                    f"建议使用图注摘要。"
                )


def check_katex_compatibility(lines, errors, warnings):
    """检查 12: KaTeX 兼容性。"""
    katex_safe = {
        "mathrm", "mathbf", "mathbb", "boldsymbol", "text", "mathcal",
        "mathfrak", "mathscr", "mathsf", "mathtt", "bm", "vec", "hat",
        "tilde", "bar", "dot", "ddot", "overline", "underline", "frac",
        "sqrt", "sum", "prod", "int", "oint", "lim", "log", "ln", "exp",
        "sin", "cos", "tan", "min", "max", "inf", "sup", "det", "dim",
        "arg", "deg", "gcd", "ker", "Pr", "in", "notin", "subset", "supset",
        "subseteq", "supseteq", "cup", "cap", "setminus", "emptyset",
        "varnothing", "forall", "exists", "nabla", "partial", "infty",
        "to", "rightarrow", "leftarrow", "Rightarrow", "Leftarrow",
        "leftrightarrow", "Leftrightarrow", "mapsto", "hookrightarrow",
        "leq", "geq", "neq", "approx", "sim", "simeq", "cong", "equiv",
        "propto", "perp", "parallel", "cdot", "times", "div", "pm", "mp",
        "oplus", "otimes", "odot", "ell", "Re", "Im", "aleph", "hbar",
        "angle", "langle", "rangle", "lceil", "rceil", "lfloor", "rfloor",
        "big", "Big", "bigg", "Bigg", "bigl", "bigr", "Bigl", "Bigr",
        "left", "right", "displaystyle", "textstyle", "scriptstyle",
        "binom", "choose", "stackrel", "overset", "underset", "substack",
        "begin", "end", "array", "aligned", "align", "cases", "matrix",
        "pmatrix", "bmatrix", "vmatrix", "Vmatrix", "color", "textcolor",
        "cancel", "bcancel", "xcancel", "boxed", "mathring", "accentset",
        "breve", "check", "grave", "ddot", "dot", "widehat", "widetilde",
        "operatorname", "DeclareMathOperator", "space", "thinspace",
        "medspace", "thickspace", "negthinspace", "negmedspace",
        "negthickspace", "colon", "backslash", "vert", "Vert", "uparrow",
        "downarrow", "Uparrow", "Downarrow", "updownarrow", "Updownarrow",
        "nearrow", "searrow", "nwarrow", "swarrow", "Rrightarrow",
        "Lleftarrow", "rightleftharpoons", "rightleftarrows",
        # 希腊字母（KaTeX 完整支持）
        "alpha", "beta", "gamma", "delta", "epsilon", "varepsilon",
        "zeta", "eta", "theta", "vartheta", "iota", "kappa", "lambda",
        "mu", "nu", "xi", "pi", "varpi", "rho", "varrho", "sigma",
        "varsigma", "tau", "upsilon", "phi", "varphi", "chi", "psi",
        "omega", "Gamma", "Delta", "Theta", "Lambda", "Xi", "Pi",
        "Sigma", "Upsilon", "Phi", "Psi", "Omega",
        # 其他常用数学符号
        "mid", "nmid", "vdash", "dashv", "models", "therefore",
        "because", "square", "blacksquare", "triangle", "blacktriangle",
        "diamond", "lozenge", "star", "ast", "dagger", "ddagger",
        "bullet", "circ", "bullet", "ldotp", "cdotp", "prime",
        "backprime", "flat", "natural", "sharp", "checkmark",
        "dots", "cdots", "vdots", "ddots", "ldots", "adots",
        "mathstrut", "nolimits", "limits", "norm", "abs",
        "textwidth", "columnwidth", "linewidth",
    }

    content = "".join(lines)
    math_cmds = set()
    # 提取 $$...$$ 中的命令
    for m in re.finditer(r"\$\$(.*?)\$\$", content, re.DOTALL):
        for cmd in re.finditer(r"\\([a-zA-Z]+)", m.group(1)):
            math_cmds.add(cmd.group(1))
    # 提取 $...$ 中的命令
    for m in re.finditer(r"\$([^$]+)\$", content):
        for cmd in re.finditer(r"\\([a-zA-Z]+)", m.group(1)):
            math_cmds.add(cmd.group(1))

    unknown = math_cmds - katex_safe
    if unknown:
        warnings.append(
            f"数学模式中可能不被 KaTeX 支持的命令: {sorted(unknown)}"
        )


# ── 主入口 ─────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="arxiv 技能 Markdown 后处理验证脚本"
    )
    parser.add_argument("markdown_file", help="待检查的 Markdown 文件路径")
    parser.add_argument(
        "--source-dir", default=None,
        help="source-cn 源码目录（用于解析图片相对路径）"
    )
    parser.add_argument(
        "--figures-dir", default=None,
        help="source 图片目录（用于验证图片文件存在性）"
    )
    args = parser.parse_args()

    md_path = Path(args.markdown_file)
    if not md_path.exists():
        print(fmt_error(f"文件不存在: {md_path}"))
        return 1

    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
    lines = content.split("\n")

    errors = []
    warnings = []

    # ERROR 级检查
    check_math_delimiters(lines, errors)
    check_leading_spaces(lines, errors, warnings)
    check_latex_remnants(lines, errors, warnings)
    check_table_columns(lines, errors, warnings)
    check_dangling_refs(lines, errors, warnings)
    check_title(lines, errors, warnings)
    check_image_paths(lines, errors, warnings, args.figures_dir)

    # WARNING 级检查
    check_caption_numbers(lines, errors, warnings)
    check_caption_ref_consistency(lines, errors, warnings)
    check_abstract(lines, errors, warnings)
    check_image_alt(lines, errors, warnings)
    check_katex_compatibility(lines, errors, warnings)

    # 输出结果
    print(f"\n{BOLD}检查文件: {md_path}{RESET}")
    print(f"总行数: {len(lines)}\n")

    if errors:
        print(f"{BOLD}── ERROR（必须修复）──{RESET}")
        for e in errors:
            print(f"  {fmt_error(e)}")
        print()

    if warnings:
        print(f"{BOLD}── WARNING（建议修复）──{RESET}")
        for w in warnings:
            print(f"  {fmt_warning(w)}")
        print()

    if not errors and not warnings:
        print(f"{fmt_ok('所有检查通过！')}")
    elif not errors:
        print(f"{fmt_ok(f'无 ERROR，{len(warnings)} 个 WARNING。')}")

    # 汇总
    print(f"\n{BOLD}汇总: {len(errors)} ERROR, {len(warnings)} WARNING{RESET}")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
