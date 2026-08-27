#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extended bilingual merge for papers whose chapters live in \\input files
(extends merge_bilingual.py). Recursively expands \\input/\\include of both the
English and Chinese main.tex, then performs block-level interleaving so that
every content unit appears English-first, Chinese-after.

Additional coverage over merge_bilingual.py:
  - recursive \\input / \\include expansion (chapters/ split projects)
  - env:equation / align / gather / multline -> output once (English side)
  - env:table / table* -> English table body kept, every \\caption merged to
    EN + Chinese (paired by occurrence order with the CN side; identical
    captions such as subtable short labels are emitted once)
  - env:promptbox / codeblock / lstlisting -> output once (English side)
  - preamble: CJKutf8 commented out, xeCJK + \\setCJKmainfont/sansfont/monofont
    injected (source is pdfLaTeX with no CJK font commands)
"""
import re
import os
import argparse
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from merge_bilingual import (ttype, split_blocks, extract_arg,
                             find_command_arg, extract_label, strip_display_math,
                             fix_en_legacy, set_cjk_font, BLOCK_ENVS)

BLOCK_ENVS = set(BLOCK_ENVS) | {"promptbox"}
MATH_ENVS = {"equation", "equation*", "align", "align*", "gather", "gather*",
             "multline", "multline*"}
CODE_ENVS = {"lstlisting", "codeblock", "verbatim", "promptbox"}


# ------------------------------------------------------------ \\input expansion
def expand_inputs(text, base_dir, depth=0, seen=None):
    """Inline \\input{path} / \\include{path} recursively.

    The LaTeX path is relative to the main file directory; '.tex' is optional.
    Unresolvable files are left as-is (with a warning), so the output remains
    compilable in the worst case.
    """
    if depth > 8 or seen is None:
        seen = set()
    pattern = re.compile(r"\\(?:input|include)\{([^}]+)\}")
    def repl(m):
        rel = m.group(1).strip()
        cand = rel if rel.endswith(".tex") else rel + ".tex"
        path = os.path.normpath(os.path.join(base_dir, cand))
        key = os.path.abspath(path)
        if key in seen:
            return "% Inline \\input{%s} skipped (cycle/duplicate)" % rel
        if not os.path.exists(path):
            print("WARN: cannot expand \\input{%s} (missing %s); kept as-is"
                  % (rel, path))
            return m.group(0)
        seen.add(key)
        with open(path, encoding="utf-8") as f:
            sub = f.read()
        inlined = expand_inputs(sub, os.path.dirname(path), depth + 1, seen)
        return "\n" + inlined.rstrip("\n") + "\n"
    return pattern.sub(repl, text)


def balanced_braces(s):
    depth = 0
    for ch in s:
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth < 0:
                return False
    return depth == 0


def fold_multiline_captions(lines):
    """Collapse \\caption{...} spanning several lines into a single line."""
    out = []
    i, n = 0, len(lines)
    while i < n:
        s = lines[i].strip()
        if s.startswith("\\caption{") and not balanced_braces(s):
            buf = lines[i]
            j = i + 1
            while j < n and not balanced_braces(buf):
                buf += "\n" + lines[j]
                j += 1
            out.append(buf)
            i = j
        else:
            out.append(lines[i])
            i += 1
    return out


def strip_comment_lines(s):
    return "\n".join(l for l in s.split("\n") if not l.strip().startswith("%"))


def merged_caption(e_cap, c_cap):
    """Build a bilingual caption; identical captions are emitted once.
    Comment lines inside \\caption arguments are dropped (they would silently
    comment out the rest of the caption in LaTeX)."""
    e = fix_en_legacy(strip_comment_lines(e_cap).strip())
    c = strip_comment_lines(c_cap).strip()
    if e == c:
        return e
    return "%s\\newline{} \\texorpdfstring{\\zhstyle}{}%s" % (e, c)


# ------------------------------------------------------------ merge driver
def merge(en_path, cn_path, out_path, cfg):
    en_raw = open(en_path, encoding="utf-8").read()
    cn_raw = open(cn_path, encoding="utf-8").read()
    en_dir, cn_dir = os.path.dirname(en_path), os.path.dirname(cn_path)

    en_text = expand_inputs(en_raw, en_dir)
    cn_text = expand_inputs(cn_raw, cn_dir)

    en = split_blocks(en_text.splitlines())
    cn = split_blocks(cn_text.splitlines())
    assert len(en) == len(cn), "block counts differ: EN=%d CN=%d" % (len(en), len(cn))
    en_kinds = [b[0] for b in en]
    cn_kinds = [b[0] for b in cn]
    for i, (ek, ck) in enumerate(zip(en_kinds, cn_kinds)):
        assert ek == ck, "block %d kind mismatch: EN=%s CN=%s" % (i, ek, ck)

    ti = next(i for i, l in enumerate(cn_text.splitlines())
              if l.strip().startswith("\\title"))
    preamble_text = "\n".join(cn_text.splitlines()[:ti])
    preamble_text = set_cjk_font(preamble_text, "setCJKmainfont", cfg.cn_font, cfg.cn_color)
    preamble_text = set_cjk_font(preamble_text, "setCJKsansfont", cfg.cn_font, cfg.cn_color)
    preamble_text = set_cjk_font(preamble_text, "setCJKmonofont", cfg.cn_mono_font, cfg.cn_color)
    # pdfLaTeX CJKutf8 is replaced by xeCJK under XeLaTeX.
    preamble_text = re.sub(r"(?m)^\\usepackage\{CJKutf8\}$",
                           lambda m: "% \\usepackage{CJKutf8}  % disabled for XeLaTeX",
                           preamble_text)
    # Source has no CJK font commands (pdfLaTeX); inject xeCJK + fonts.
    if not re.search(r"\\usepackage\{xeCJK\}|\\usepackage\[[^\]]*\]\{ctex\}", preamble_text):
        preamble_text += ("\n%% ---- bilingual CJK setup (injected) ----\n"
                          "\\usepackage{xeCJK}\n"
                          "\\setCJKmainfont[Color=%s]{%s}\n"
                          "\\setCJKsansfont[Color=%s]{%s}\n"
                          "\\setCJKmonofont[Color=%s]{%s}\n"
                          "%% ---- end ----" % (cfg.cn_color, cfg.cn_font,
                                                cfg.cn_color, cfg.cn_font,
                                                cfg.cn_color, cfg.cn_mono_font))

    out = []
    out.append(preamble_text)
    out.append("")
    if cfg.en_font:
        out.append("\\setmainfont{%s}" % cfg.en_font)
    if cfg.heading_font:
        out.append("\\usepackage{sectsty}")
        out.append("\\newfontfamily\\headingfont{%s}" % cfg.heading_font)
        out.append("\\allsectionsfont{\\headingfont}")
    # Paragraph-level headings: if the source writes \\paragraph{...} as its
    # own line/paragraph (heading followed by a blank line before body text),
    # render it as a block heading so the bilingual heading (EN \\newline CN)
    # stays on its own lines instead of run-in merging with following body
    # text. For genuinely run-in headings (body text on the same line) we do
    # NOT inject this, so the heading keeps hugging its body text.
    para_block_needed = bool(re.search(r"\\paragraph\{[^}]*\}\s*(\n\s*)?\n\s*\n|\\subparagraph\{[^}]*\}\s*(\n\s*)?\n\s*\n",
                                       en_text + cn_text))
    if para_block_needed:
        out.append("\\renewcommand{\\paragraph}[1]{\\par\\vspace{1.2ex}\\noindent{\\normalsize\\bfseries #1}\\par\\nopagebreak}")
        out.append("\\renewcommand{\\subparagraph}[1]{\\par\\vspace{1.2ex}\\noindent{\\normalsize\\bfseries #1}\\par\\nopagebreak}")
    out.append("")
    out.append("% Make font-size commands safe inside PDF bookmarks.")
    disabled = ("\\let\\footnotesize\\relax\\let\\scriptsize\\relax\\let\\small\\relax"
                "\\let\\newline\\relax\\let\\zhstyle\\relax")
    if cfg.heading_font:
        disabled += "\\let\\headingfont\\relax"
    out.append("\\pdfstringdefDisableCommands{%s}" % disabled)
    out.append("")
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
        out.append("\\author" + author_part[1].rsplit("\n\\begin{document}", 1)[0].strip())
    out.append("\\begin{document}")
    if cfg.margin:
        out.append("\\newgeometry{margin=%s,headheight=12pt,headsep=25pt,footskip=30pt}"
                   % cfg.margin)
    out.append("")

    for eb, cb in zip(en[1:], cn[1:]):
        kind = eb[0]
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
            for cmd in ("\\section", "\\subsection", "\\subsubsection",
                        "\\paragraph", "\\subparagraph"):
                if el.startswith(cmd):
                    e_arg, rest = find_command_arg(el.strip(), cmd)
                    c_arg, _ = find_command_arg(cl.strip(), cmd)
                    out.append("%s{%s\\newline \\texorpdfstring{\\zhstyle}{}%s}%s"
                               % (cmd, fix_en_legacy(e_arg), c_arg, rest))
                    break
            out.append("")
        elif kind == "para":
            et, ct = "\n".join(eb[1]), "\n".join(cb[1])
            if et.strip() == "\\maketitle":
                out.append("\\maketitle")
                out.append("")
                continue
            if et.strip() == ct.strip():
                out.append(et.strip())
                out.append("")
            else:
                out.append(fix_en_legacy(et).rstrip())
                out.append("")
                out.append("\\begin{zh}")
                # labels are already defined on the English side; drop them in
                # the Chinese copy to avoid multiply-defined-label warnings
                ct_clean = re.sub(r"\\label\{[^}]*\}", "", ct)
                out.append(strip_display_math(ct_clean).rstrip())
                out.append("\\end{zh}")
                out.append("")
        elif kind in ("env:figure", "env:figure*"):
            elines = fold_multiline_captions(list(eb[1]))
            cbl = fold_multiline_captions(list(cb[1]))
            for k, l in enumerate(elines):
                if l.strip().startswith("\\caption{"):
                    cap_arg, _ = find_command_arg(l.strip(), "\\caption")
                    label, e_cap = extract_label(cap_arg)
                    cl = next(l for l in cbl if l.strip().startswith("\\caption{"))
                    c_cap, _ = find_command_arg(cl.strip(), "\\caption")
                    _, c_cap2 = extract_label(c_cap)
                    elines[k] = "\\caption{%s%s}" % (label,
                                                     merged_caption(e_cap, c_cap2))
                    break
            out.append("\n".join(elines))
            out.append("")
        elif kind in ("env:table", "env:table*"):
            elines = fold_multiline_captions(list(eb[1]))
            cbl = fold_multiline_captions(list(cb[1]))
            c_caps = [l for l in cbl if l.strip().startswith("\\caption{")]
            ci = 0
            for k, l in enumerate(elines):
                if l.strip().startswith("\\caption{"):
                    cap_arg, _ = find_command_arg(l.strip(), "\\caption")
                    label, e_cap = extract_label(cap_arg)
                    if ci < len(c_caps):
                        c_cap, _ = find_command_arg(c_caps[ci].strip(), "\\caption")
                        _, c_cap2 = extract_label(c_cap)
                        ci += 1
                    else:
                        c_cap2 = ""
                    elines[k] = "\\caption{%s%s}" % (label,
                                                     merged_caption(e_cap, c_cap2))
            # keep large tables from overflowing when captions grow
            cap_total = sum(len(l) for l in elines if l.strip().startswith("\\caption{"))
            if cap_total > 1000:
                elines = [l.replace("\\begin{tabular", "\\resizebox{\\linewidth}{!}{\\begin{tabular")
                          if l.strip().startswith("\\begin{tabular")
                          else l.replace("}\n\\end{tabular}", "}\\end{tabular}")
                          for l in elines]
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
        elif kind == "env:enumerate":
            ei = [l for l in eb[1] if l.strip().startswith("\\item")]
            ci = [l for l in cb[1] if l.strip().startswith("\\item")]
            assert len(ei) == len(ci), "enumerate item counts differ"
            out.append("\\begin{enumerate}")
            for e, c in zip(ei, ci):
                out.append("    \\item %s" % e.strip()[len("\\item"):].strip())
                out.append("    \\item \\begin{zh}%s\\end{zh}"
                           % c.strip()[len("\\item"):].strip())
            out.append("\\end{enumerate}")
            out.append("")
        elif kind.startswith("env:") and kind[4:] in MATH_ENVS:
            # display math is identical in both languages: keep English once
            out.append("\n".join(eb[1]))
            out.append("")
        elif kind.startswith("env:") and kind[4:] in CODE_ENVS:
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
    ap.add_argument("--out", default="merged-bilingual-main.tex")
    ap.add_argument("--cn-font", default="PingFang SC")
    ap.add_argument("--cn-mono-font", default="PingFang SC")
    ap.add_argument("--cn-color", default="7A7A7A")
    ap.add_argument("--en-font", default="Inter")
    ap.add_argument("--heading-font", default="Helvetica")
    ap.add_argument("--margin", default="0.7in")
    cfg = ap.parse_args()
    merge(cfg.en_main, cfg.cn_main, cfg.out, cfg)


if __name__ == "__main__":
    main()