#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Merge the English LaTeX source (source/) and its in-place Chinese translation
(source-cn/) into a single bilingual main.tex: for each top-level content unit
(paragraph, heading, figure, list...) the English text comes first, the Chinese
text right after it, interleaved until the end of the paper.

This script is the implementation backing "任务四：输出中英双语 PDF" in the
arxiv SKILL.md. It performs block-level alignment of the two files, then pairs
them unit by unit. The default styling keeps the Chinese translation visually
distinct (grey, ~0.9x relative size) while the English body/headings use the
fonts passed on the command line.

Usage:
  merge_bilingual.py <en_main.tex> <cn_main.tex> [--out merged-main.tex]
                     [--cn-font "PingFang SC"] [--cn-color 7A7A7A]
                     [--en-font Inter] [--heading-font Helvetica]
                     [--margin 0.7in]

Notes / pitfalls encoded here (learned from 2607.15495-GlobalWorkspace):
  - caption arguments must NOT contain \\par (natbib's \\NR@gettitle fails);
    use \\newline{} instead.
  - a size command directly followed by a letter (\\footnotesize The ...) is
    re-parsed as an undefined control sequence by hyperref bookmarks; isolate
    with {} or use \\texorpdfstring.
  - CJKutf8 \\begin{CJK} wrappers and \\fontencoding{T2A} escapes from the
    pdfLaTeX original are stripped/rewritten for XeLaTeX.
  - display formulas ($$..$$) appear once (English side); inline math stays in
    both language copies.
  - all width=\\textwidth figures get height=0.72\\textheight,keepaspectratio;
    figures whose bilingual caption exceeds the thresholds get scaled down and
    \\footnotesize/\\scriptsize captions to avoid "Float too large".
  - template \\AtBeginDocument \\newgeometry overrides preamble \\geometry;
    apply \\newgeometry right after \\begin{document}.
"""
import re
import argparse
import os

BLOCK_ENVS = {"figure", "figure*", "table", "table*", "equation", "equation*",
              "align", "align*", "gather", "gather*", "multline", "multline*",
              "itemize", "enumerate", "abstract", "algorithm", "algorithm*",
              "theorem", "lemma", "lstlisting", "promptblock", "codeblock",
              "verbatim"}
SEC_CMDS = ("\\section", "\\subsection", "\\subsubsection", "\\paragraph",
            "\\subparagraph")


# ---------------------------------------------------------------- lexer/blocks
def expand_inputs(lines, base_dir):
    """Recursively inline \\input{...} / \\include{...} into the top-level file.

    Only whole-line input commands are expanded (relative to base_dir, the
    directory of the file being expanded).  Files that cannot be resolved are
    left untouched so that single-file projects are unaffected.
    """
    out = []
    for ln in lines:
        m = re.match(r"^\s*\\(?:input|include)\{([^}]+)\}\s*$", ln)
        if m:
            rel = m.group(1)
            path = os.path.join(base_dir, rel)
            if not os.path.exists(path) and not path.endswith(".tex"):
                path = path + ".tex"
            if os.path.exists(path):
                with open(path, encoding="utf-8") as f:
                    sub = f.read().splitlines()
                out.extend(expand_inputs(sub, os.path.dirname(path)))
                continue
        out.append(ln)
    return out


def find_nested_arg(s, cmd):
    """Find the first \\cmd{...} anywhere in s (cross-line safe).

    Returns (content, s_with_that_command_removed) or (None, s) if absent.
    """
    idx = s.find("\\" + cmd + "{")
    if idx < 0:
        return None, s
    j = s.index("{", idx)
    content, end = extract_arg(s, j)
    return content, s[:idx] + s[end:]


def ttype(line):
    s = line.strip()
    if not s:
        return "blank"
    for cmd in SEC_CMDS:
        if s.startswith(cmd):
            return "sec"
    if s.startswith("\\title"):
        return "title"
    if s.startswith("\\maketitle"):
        return "maketitle"
    m = re.match(r"\\begin\{([^}]+)\}", s)
    if m:
        return "begin:" + m.group(1)
    m = re.match(r"\\end\{([^}]+)\}", s)
    if m:
        return "end:" + m.group(1)
    return "text"


def split_blocks(lines):
    """Split into top-level blocks: (kind, [lines])."""
    blocks = []
    i, n = 0, len(lines)
    in_doc = False
    while i < n:
        line, t = lines[i], ttype(lines[i])
        if t == "blank":
            i += 1
            continue
        if not in_doc:
            if t == "title":
                j, buf = i, []
                while j < n:
                    buf.append(lines[j])
                    if lines[j].strip().startswith("\\begin{document}"):
                        in_doc = True
                        j += 1
                        break
                    j += 1
                blocks.append(("title", buf))
                i = j
                continue
            if t == "maketitle":
                blocks.append(("maketitle", [line]))
                i += 1
                continue
            if line.strip().startswith("\\begin{document}"):
                in_doc = True
                blocks.append(("begin{document}", [line]))
                i += 1
                continue
            i += 1
            continue
        if t == "sec":
            blocks.append(("sec", [line]))
            i += 1
            continue
        if t.startswith("begin:"):
            env = t.split(":", 1)[1]
            if env in BLOCK_ENVS:
                # Collect until the *matching* \end{env} of this block, tracking
                # nesting depth so a same-named nested environment (e.g. an
                # enumerate inside an enumerate, as in NeurIPS checklists) does
                # not prematurely close the outer block.
                j, buf, depth = i, [], 0
                while j < n:
                    buf.append(lines[j])
                    tj = ttype(lines[j])
                    if tj == "begin:" + env:
                        depth += 1
                    elif tj == "end:" + env:
                        depth -= 1
                        if depth <= 0:
                            j += 1
                            break
                    j += 1
                blocks.append(("env:" + env, buf))
                i = j
                continue
        buf = []
        while i < n:
            ln, tt = lines[i], ttype(lines[i])
            if tt == "blank":
                break
            if tt == "sec":
                break
            if tt.startswith("begin:") and tt.split(":", 1)[1] in BLOCK_ENVS:
                break
            buf.append(ln)
            i += 1
        if buf:
            blocks.append(("para", buf))
    return blocks


# ------------------------------------------------------------ helpers
def extract_arg(s, idx):
    """s[idx] must be '{'. Return (content, end_index_after_)."""
    depth, j = 0, idx
    while j < len(s):
        if s[j] == "{":
            depth += 1
        elif s[j] == "}":
            depth -= 1
            if depth == 0:
                return s[idx + 1:j], j + 1
        j += 1
    raise ValueError("unbalanced braces: " + s[max(0, idx - 30):idx + 60])


def find_command_arg(s, cmd):
    assert s.startswith(cmd), s[:40]
    i = s.index("{")
    content, end = extract_arg(s, i)
    return content, s[end:]


def extract_label(arg):
    m = re.match(r"\\label\{([^}]*)\}\s*(.*)", arg, re.S)
    if m:
        return "\\label{" + m.group(1) + "}", m.group(2)
    return "", arg


def strip_display_math(text):
    """Remove $$...$$ display formulas from the CN copy (EN side keeps them)."""
    return re.sub(r"\$\$.*?\$\$", "", text, flags=re.S)


def fix_en_legacy(text):
    """Strip pdfLaTeX CJKutf8 wrappers and rewrite T2A Cyrillic to \\cyr{}."""
    text = re.sub(r"\\begin\{CJK\*?\}\{[^}]*\}\{[^}]*\}", "", text)
    text = re.sub(r"\\end\{CJK\*?\}", "", text)
    text = re.sub(r"\{\\fontencoding\{T2A\}\\selectfont\s*([^{}]*)\}",
                  r"\\cyr{\1}", text)
    return text


def set_cjk_font(preamble, cmd, font, color):
    """Replace \\setCJK*{old} (with or without options) by the chosen font."""
    pattern = re.compile(r"\\%s(?:\[[^\]]*\])?\{[^}]*\}" % cmd)
    if color:
        repl = "\\%s[Color=%s]{%s}" % (cmd, color, font)
    else:
        repl = "\\%s{%s}" % (cmd, font)
    # use a lambda so repl is inserted literally (no regex-template escaping)
    return pattern.sub(lambda m: repl, preamble, count=1)


# ------------------------------------------------------------ merge driver
def merge(en_path, cn_path, out_path, cfg):
    en_lines = open(en_path, encoding="utf-8").read().splitlines()
    cn_lines = open(cn_path, encoding="utf-8").read().splitlines()
    en_lines = expand_inputs(en_lines, os.path.dirname(en_path))
    cn_lines = expand_inputs(cn_lines, os.path.dirname(cn_path))
    en = split_blocks(en_lines)
    cn = split_blocks(cn_lines)
    assert len(en) == len(cn), "block counts differ: EN=%d CN=%d" % (len(en), len(cn))
    assert [b[0] for b in en] == [b[0] for b in cn], "block type sequences differ"

    ti = next(i for i, l in enumerate(cn_lines) if l.strip().startswith("\\title"))
    preamble_text = "\n".join(cn_lines[:ti])
    preamble_text = set_cjk_font(preamble_text, "setCJKmainfont", cfg.cn_font, cfg.cn_color)
    preamble_text = set_cjk_font(preamble_text, "setCJKsansfont", cfg.cn_font, cfg.cn_color)
    preamble_text = set_cjk_font(preamble_text, "setCJKmonofont", cfg.cn_mono_font, cfg.cn_color)

    out = []
    out.append(preamble_text)
    out.append("")
    if cfg.en_font:
        out.append("\\setmainfont{%s}" % cfg.en_font)
    if cfg.heading_font:
        out.append("\\usepackage{sectsty}")
        out.append("\\newfontfamily\\headingfont{%s}" % cfg.heading_font)
        out.append("\\allsectionsfont{\\headingfont}")
    out.append("")
    out.append("% Make font-size commands safe inside PDF bookmarks.")
    disabled = ("\\let\\footnotesize\\relax\\let\\scriptsize\\relax\\let\\small\\relax"
                "\\let\\newline\\relax\\let\\zhstyle\\relax")
    if cfg.heading_font:
        disabled += "\\let\\headingfont\\relax"
    out.append("\\pdfstringdefDisableCommands{%s}" % disabled)
    out.append("")
    # zhstyle: grey + 0.9x relative size for every character of a Chinese unit.
    rgb = tuple(int(cfg.cn_color[i:i + 2], 16) for i in (0, 2, 4))
    out.append("\\definecolor{zhgray}{RGB}{%d,%d,%d}" % rgb)
    out.append("\\makeatletter")
    out.append("\\newcommand{\\zhstyle}{\\color{zhgray}\\fontsize{\\dimexpr\\f@size pt * 9 / 10\\relax}{\\dimexpr\\baselineskip * 9 / 10\\relax}\\selectfont}")
    out.append("\\makeatother")
    out.append("\\newenvironment{zh}{\\zhstyle}{}")
    out.append("")
    out.append("% --- Readability tuning: relaxed line spacing + block separation ---")
    out.append("\\linespread{1.25}")
    out.append("\\setlength{\\parskip}{0.5em plus 0.15em minus 0.1em}")
    out.append("\\setlength{\\parindent}{0pt}")
    out.append("")

    # title block
    en_title = "\n".join(en[0][1])
    cn_title = "\n".join(cn[0][1])
    en_t_arg, _ = find_command_arg(en_title.strip(), "\\title")
    cn_t_arg, _ = find_command_arg(cn_title.strip(), "\\title")
    heading = "\\headingfont " if cfg.heading_font else ""
    out.append("\\title{%s%s\\\\[2pt] \\texorpdfstring{\\zhstyle}{}%s}"
               % (heading, fix_en_legacy(en_t_arg), cn_t_arg))
    author_part = en_title.split("\\author", 1)
    if len(author_part) > 1:
        # keep the EN side of author/affiliation/contribution/date blocks and
        # pull the \\abstract{...} command out so it can be merged bilingually
        author_tail = author_part[1].rsplit("\n\\begin{document}", 1)[0].strip()
        en_abs, author_tail = find_nested_arg(author_tail, "abstract")
        cn_abs, _ = find_nested_arg(cn_title, "abstract")
        out.append("\\author" + author_tail)
        if en_abs is not None and cn_abs is not None:
            out.append("")
            out.append("\\abstract{%s\\par \\begin{zh}%s\\end{zh}}"
                       % (fix_en_legacy(en_abs.strip()),
                          strip_display_math(cn_abs.strip())))
    out.append("\\begin{document}")
    if cfg.margin:
        out.append("\\newgeometry{margin=%s,headheight=12pt,headsep=25pt,footskip=30pt}"
                   % cfg.margin)
    out.append("")

    # Chinese counterpart of a pending inline paragraph heading, drained into
    # the start of the next Chinese body block so the EN heading is followed
    # directly by EN body text (e.g. "Data Format." -> EN paragraph, not the
    # Chinese heading).
    pending_cn_head = None

    for eb, cb in zip(en[1:], cn[1:]):
        kind = eb[0]
        if pending_cn_head is not None and kind != "para":
            # next unit is not body text: emit the deferred Chinese heading on
            # its own so it is never lost
            out.append("\\begin{zh}")
            out.append(pending_cn_head)
            out.append("\\end{zh}")
            out.append("")
            pending_cn_head = None
        if kind in ("maketitle", "begin{document}", "title"):
            continue
        if kind == "env:abstract":
            ebody = re.sub(r"\\begin\{abstract\}|\\end\{abstract\}", "",
                           "\n".join(eb[1]))
            cbody = strip_display_math(re.sub(r"\\begin\{abstract\}|\\end\{abstract\}",
                                              "", "\n".join(cb[1])))
            out.append("\\begin{abstract}")
            out.append(fix_en_legacy(ebody.strip()))
            out.append("\\par")
            out.append("\\begin{zh}")
            out.append(cbody.strip())
            out.append("\\end{zh}")
            out.append("\\end{abstract}")
            out.append("")
        elif kind == "sec":
            el, cl = eb[1][0], cb[1][0]
            for cmd in SEC_CMDS:
                if el.startswith(cmd):
                    e_arg, rest = find_command_arg(el.strip(), cmd)
                    c_arg, _ = find_command_arg(cl.strip(), cmd)
                    if cmd in ("\\paragraph", "\\subparagraph"):
                        # inline paragraph heading: keep EN heading on its own so
                        # it flows directly into the EN body below, and defer the
                        # CN heading onto the opening of the Chinese body block.
                        out.append("%s{%s}%s" % (cmd, fix_en_legacy(e_arg), rest))
                        pending_cn_head = "%s{%s}" % (cmd, c_arg)
                        is_inline_head = True
                    else:
                        out.append("%s{%s\\newline \\texorpdfstring{\\zhstyle}{}%s}%s"
                                   % (cmd, fix_en_legacy(e_arg), c_arg, rest))
                        is_inline_head = False
                    break
            if not is_inline_head:
                out.append("")
        elif kind == "para":
            et, ct = "\n".join(eb[1]), "\n".join(cb[1])
            if et.strip() == "\\maketitle":
                out.append("\\maketitle")
                out.append("")
                continue
            if et.strip() == ct.strip():
                # identical on both sides (e.g. a bare control line): if a CN
                # inline heading is pending, attach it here so it is not lost
                if pending_cn_head is not None:
                    out.append("\\begin{zh}")
                    out.append(pending_cn_head)
                    out.append("\\end{zh}")
                    out.append("")
                    pending_cn_head = None
                out.append(et.strip())
                out.append("")
            else:
                out.append(fix_en_legacy(et).rstrip())
                out.append("")
                out.append("\\begin{zh}")
                if pending_cn_head is not None:
                    out.append(pending_cn_head)
                    pending_cn_head = None
                out.append(strip_display_math(ct).rstrip())
                out.append("\\end{zh}")
                out.append("")
        elif kind in ("env:figure", "env:figure*"):
            elines = list(eb[1])
            cap_start = next((k for k, l in enumerate(elines)
                              if l.strip().startswith("\\caption{")), None)
            if cap_start is not None:
                # caption may span several lines: extract on the joined text
                cap_text = "\n".join(elines[cap_start:])
                cap_arg, after = extract_arg(cap_text, cap_text.index("{"))
                label, e_cap = extract_label(cap_arg)
                ccap_text = "\n".join(cb[1])
                cidx = ccap_text.find("\\caption{")
                c_arg, _ = extract_arg(ccap_text, cidx + len("\\caption"))
                _, c_cap2 = extract_label(c_arg)
                e_clean = fix_en_legacy(e_cap.strip())
                cap_len = len(e_clean) + len(c_cap2.strip())
                scale, fsize = "", ""
                if cap_len > 1350:
                    scale, fsize = "0.5", "\\scriptsize"
                elif cap_len > 900:
                    scale, fsize = "0.85", "\\footnotesize"
                for kk, ll in enumerate(elines):
                    if "width=\\textwidth" in ll:
                        if scale:
                            elines[kk] = ll.replace(
                                "width=\\textwidth",
                                "width=%s\\textwidth,height=0.72\\textheight,keepaspectratio" % scale)
                        else:
                            elines[kk] = ll.replace(
                                "width=\\textwidth",
                                "width=\\textwidth,height=0.72\\textheight,keepaspectratio")
                if fsize:
                    merged = "\\caption{%s%s{}%s\\newline{} \\texorpdfstring{\\zhstyle}{}%s}" \
                             % (label, fsize, e_clean, c_cap2.strip())
                else:
                    merged = "\\caption{%s%s\\newline{} \\texorpdfstring{\\zhstyle}{}%s}" \
                             % (label, e_clean, c_cap2.strip())
                # locate the line holding the caption's closing brace on the
                # ORIGINAL lines (before merged is written to cap_start)
                depth, started, close_line = 0, False, None
                for k in range(cap_start, len(elines)):
                    for ch in elines[k]:
                        if ch == "{":
                            depth += 1
                            started = True
                        elif ch == "}":
                            depth -= 1
                            if started and depth == 0:
                                close_line = k
                                break
                    if close_line is not None:
                        break
                elines[cap_start] = merged
                if close_line is not None and close_line > cap_start:
                    del elines[cap_start + 1: close_line + 1]
            out.append("\n".join(elines))
            out.append("")
        elif kind in ("env:equation", "env:equation*", "env:align", "env:align*",
                      "env:gather", "env:gather*", "env:multline", "env:multline*"):
            # display math appears once (English side is identical to CN side)
            out.append("\n".join(eb[1]))
            out.append("")
        elif kind in ("env:table", "env:table*"):
            elines = list(eb[1])
            cap_start = next((k for k, l in enumerate(elines)
                              if l.strip().startswith("\\caption{")), None)
            if cap_start is not None:
                cap_text = "\n".join(elines[cap_start:])
                cap_arg, after = extract_arg(cap_text, cap_text.index("{"))
                label, e_cap = extract_label(cap_arg)
                ccap_text = "\n".join(cb[1])
                cidx = ccap_text.find("\\caption{")
                c_arg, _ = extract_arg(ccap_text, cidx + len("\\caption"))
                _, c_cap2 = extract_label(c_arg)
                merged = "\\caption{%s%s\\newline{} \\texorpdfstring{\\zhstyle}{}%s}" \
                         % (label, fix_en_legacy(e_cap.strip()), c_cap2.strip())
                # locate the line holding the caption's closing brace on the
                # ORIGINAL lines (before merged is written to cap_start)
                depth, started, close_line = 0, False, None
                for k in range(cap_start, len(elines)):
                    for ch in elines[k]:
                        if ch == "{":
                            depth += 1
                            started = True
                        elif ch == "}":
                            depth -= 1
                            if started and depth == 0:
                                close_line = k
                                break
                    if close_line is not None:
                        break
                elines[cap_start] = merged
                if close_line is not None and close_line > cap_start:
                    del elines[cap_start + 1: close_line + 1]
            out.append("\n".join(elines))
            out.append("")
        elif kind == "env:itemize":
            ei = [l for l in eb[1] if l.strip().startswith("\\item")]
            ci = [l for l in cb[1] if l.strip().startswith("\\item")]
            assert len(ei) == len(ci), "itemize item counts differ"
            out.append("\\begin{itemize}")
            for e, c in zip(ei, ci):
                out.append("    \\item %s" % e.strip()[len("\\item"):].strip())
                out.append("    \\item \\begin{zh}%s\\end{zh}"
                           % c.strip()[len("\\item"):].strip())
            out.append("\\end{itemize}")
            out.append("")
        elif kind in ("env:lstlisting", "env:codeblock"):
            out.append("\n".join(eb[1]))
            out.append("")
        else:
            raise ValueError("unhandled block kind: " + kind)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print("written", out_path)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("en_main", help="English main.tex path (source/)")
    ap.add_argument("cn_main", help="Chinese main.tex path (source-cn/)")
    ap.add_argument("--out", default="merged-main.tex")
    ap.add_argument("--cn-font", default="PingFang SC")
    ap.add_argument("--cn-mono-font", default="Arial Unicode MS")
    ap.add_argument("--cn-color", default="7A7A7A")
    ap.add_argument("--en-font", default="Inter")
    ap.add_argument("--heading-font", default="Helvetica")
    ap.add_argument("--margin", default="0.7in")
    cfg = ap.parse_args()
    merge(cfg.en_main, cfg.cn_main, cfg.out, cfg)


if __name__ == "__main__":
    main()
