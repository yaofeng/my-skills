#!/usr/bin/env python3
"""
合并两个 ASR 识别结果并过滤无语意噪声。

本脚本做"机械"层面的合并与过滤：
- 对齐两个 SRT（相同的 VAD 分段，一一对应）
- 逐对选择更合理的文本（优先包含日文语素且具备句子结构的输出）
- 过滤无语意内容（呻吟、笑声、单字、纯标点、纯英文语气词、无关语言等）
- 折叠过长重复字符、清理渗入的无关语言噪声

注意：具体内容层面的"上下文推理纠错 / 综合分析纠错"由 Claude 依据两个
原始 SRT 完成。本脚本只作为精准识别时的一个预过滤辅助。

用法:
  python merge_srt.py <文件1> <文件2> -o <输出.srt>
  python merge_srt.py --stem <文件名stem> --workspace <工作目录> -o <输出.srt>
"""

import argparse
import os
import re
import sys
from collections import Counter

DEFAULT_WORKSPACE = os.environ.get("ASR_WORKSPACE", os.getcwd())


# ─────────────────────────────────────────────────────────────
# 1. 时间戳处理
# ─────────────────────────────────────────────────────────────

def ts_to_ms(ts: str) -> int:
    """将时间戳字符串转换为总毫秒数。"""
    ts = ts.strip().replace(",", ".")
    m = re.match(r"(\d+):(\d+):(\d+)(?:\.(\d+))?", ts)
    if not m:
        return 0
    h, mi, s = int(m.group(1)), int(m.group(2)), int(m.group(3))
    ms_str = m.group(4) or "0"
    ms_str = ms_str.ljust(3, "0")[:3]
    return h * 3600000 + mi * 60000 + s * 1000 + int(ms_str)


def ms_to_ts(ms: int) -> str:
    """将毫秒转换为 HH:MM:SS,mmm 格式。"""
    h = ms // 3600000
    ms %= 3600000
    mi = ms // 60000
    ms %= 60000
    s = ms // 1000
    ms %= 1000
    return f"{h:02d}:{mi:02d}:{s:02d},{ms:03d}"


# ─────────────────────────────────────────────────────────────
# 2. SRT 解析
# ─────────────────────────────────────────────────────────────

def parse_srt(path: str):
    """解析 SRT 文件 → (start_ms, end_ms, start_ts_str, end_ts_str, text) 列表。"""
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    content = content.replace("\r\n", "\n").replace("\r", "\n")
    blocks = re.split(r"\n{2,}", content.strip())

    ts_re = re.compile(
        r"(\d{1,2}:\d{1,2}:\d{1,2}[,.]?\d*)\s*-->\s*(\d{1,2}:\d{1,2}:\d{1,2}[,.]?\d*)"
    )

    entries = []
    for block in blocks:
        lines = [l for l in block.split("\n") if l.strip()]
        if len(lines) < 2:
            continue

        ts_idx = None
        for i, line in enumerate(lines):
            if ts_re.search(line):
                ts_idx = i
                break
        if ts_idx is None:
            continue

        m = ts_re.search(lines[ts_idx])
        start_raw, end_raw = m.group(1), m.group(2)
        start_ms = ts_to_ms(start_raw)
        end_ms = ts_to_ms(end_raw)

        text = "\n".join(lines[ts_idx + 1:]).strip()
        entries.append((start_ms, end_ms, start_raw, end_raw, text))

    return entries


# ─────────────────────────────────────────────────────────────
# 3. 字符 / 语言检测
# ─────────────────────────────────────────────────────────────

HIRAGANA_RE = re.compile(r"[ぁ-ん]")
KATAKANA_RE = re.compile(r"[ァ-ン]")
JP_RE = re.compile(r"[ぁ-んァ-ン]")
CJK_RE = re.compile(r"[一-鿿]")
HANGUL_RE = re.compile(r"[가-힯ᄀ-ᇿ㄰-㆏]")
LATIN_RE = re.compile(r"[a-zA-Z]")

# 单独出现的汉语语助词，常作为 ASR 噪声渗入其他语言文本
CHINESE_NOISE_CHARS = set(
    "啊嗯爸呢吗吧呀哦哎呃呗哇哩噜咪嗒啵嘞哔"
    "这那什么没们个时出会也对说过还进远连选"
    "鱼大东怎了"
)


def has_japanese(text: str) -> bool:
    return bool(JP_RE.search(text))


def has_hangul(text: str) -> bool:
    return bool(HANGUL_RE.search(text))


def compact(text: str) -> str:
    """去掉空白与标点，仅保留内容字符。"""
    return re.sub(r"[\s\.\,\!\?\'\"\(\)\[\]\{\}\<\>\\/\-\~\:；：。、，！？…—–　\-〿＀-￯♪]+", "", text)


# ─────────────────────────────────────────────────────────────
# 4. 噪声检测
# ─────────────────────────────────────────────────────────────

# 仅核心呻吟音（元音 + ん + 促音）
MOAN_CHARS = set("あいうえおんっアイウエオンッ")
# 扩展的气声呻吟字符（用于短条目的宽松检查）
BREAT_CHARS = set("あいうえおんっはひふハヒファィゥェォッ")
# 笑声字符
LAUGH_CHARS = set("ふはひフハヒ")
# 需丢弃的英文语气词/噪声词
EN_NOISE = {
    "okay", "ok", "yeah", "yes", "oh", "uh", "um", "hmm", "huh", "ah", "eh",
    "mm", "mmm", "ya", "ye", "yo", "ha", "he", "hi", "ho", "hey", "no", "nah",
    "wow", "ow", "woo", "ooh", "aah", "mhm",
    "the", "a", "an", "is", "it", "so", "but", "and", "my", "me", "we",
    "he", "she", "they", "you", "i",
    "thank", "thanks", "please", "sorry", "hello", "bye", "goodbye",
    "don", "know", "right", "like", "just", "cause", "because",
    "what", "where", "when", "how", "who", "why",
    "can", "will", "would", "should", "could", "cannot",
    "this", "that", "here", "there", "now", "then",
    "go", "got", "get", "do", "did", "have", "has", "had",
    "hat", "look", "young", "sony", "whether", "dad", "cat",
    "nana", "run", "sun", "fun",
}


def is_pure_chinese(text: str) -> bool:
    """判断文本是否为不含日文假名的纯中文（日文语境下多为 ASR 噪声）。"""
    if not text.strip():
        return True
    if has_japanese(text):
        return False
    comp = compact(text)
    if not comp:
        return True
    if CJK_RE.search(text):
        return True
    cn_count = sum(1 for ch in comp if ch in CHINESE_NOISE_CHARS)
    if cn_count > 0 and cn_count / len(comp) > 0.5:
        return True
    return False


def is_noise(text: str) -> bool:
    """判断文本是否为应丢弃的无语意噪声。"""
    if not text or not text.strip():
        return True

    clean = text.strip()
    comp = compact(clean)

    if not comp:
        return True

    # 过短（≤2 字符）
    if len(comp) <= 2:
        return True

    # 纯韩文（韩语误识）
    if has_hangul(text) and not has_japanese(text) and not CJK_RE.search(text):
        return True

    # 纯中文（无假名）
    if is_pure_chinese(text):
        return True

    # 纯英文（无任何日文/中文）
    if LATIN_RE.search(text) and not has_japanese(text) and not CJK_RE.search(text):
        return True

    # 日文文本内嵌的英文噪声词
    if has_japanese(text):
        eng_words = [w.lower() for w in re.findall(r'[a-zA-Z]+', text)]
        if eng_words and all(w in EN_NOISE for w in eng_words):
            jp_part = re.sub(r'[a-zA-Z\s\.\,\'\"]+', '', text).strip()
            if len(compact(jp_part)) <= 2:
                return True

    # 纯呻吟：只含核心呻吟字符
    if all(ch in MOAN_CHARS for ch in comp):
        return True

    # 纯笑声模式
    if all(ch in LAUGH_CHARS for ch in comp):
        return True

    # 重复单字模式：>70% 为同一字符
    if len(comp) >= 3:
        c = Counter(comp)
        most_common_count = c.most_common(1)[0][1]
        if most_common_count / len(comp) > 0.7:
            return True

    # 重复 2 字符模式（bigram）
    if len(comp) >= 6:
        bigrams = [comp[i:i+2] for i in range(len(comp)-1)]
        if bigrams:
            bg_counter = Counter(bigrams)
            most_common_bg = bg_counter.most_common(1)[0][1]
            if most_common_bg / len(bigrams) > 0.6:
                return True

    # 重复 3 字符模式（trigram）
    if len(comp) >= 9:
        trigrams = [comp[i:i+3] for i in range(len(comp)-2)]
        if trigrams:
            tg_counter = Counter(trigrams)
            most_common_tg = tg_counter.most_common(1)[0][1]
            if most_common_tg / len(trigrams) > 0.5:
                return True

    # 短条目（≤5 字符）全部由气声字符构成
    if len(comp) <= 5 and all(ch in BREAT_CHARS for ch in comp):
        return True

    # 中短条目（≤8 字符）≥80% 为气声字符
    if len(comp) <= 8:
        moan_count = sum(1 for ch in comp if ch in BREAT_CHARS)
        if moan_count / len(comp) >= 0.8:
            return True

    # 带标点的短重复模式，如 "あっ、あっ、あっ"
    parts = re.split(r'[、，。\.\s]+', clean)
    parts = [p for p in parts if p.strip()]
    if len(parts) >= 3:
        part_counter = Counter(parts)
        most_common_part = part_counter.most_common(1)[0][1]
        if most_common_part / len(parts) > 0.6:
            repeated_part = part_counter.most_common(1)[0][0]
            if len(compact(repeated_part)) <= 3:
                return True

    return False


# ─────────────────────────────────────────────────────────────
# 5. 文本选择
# ─────────────────────────────────────────────────────────────

def jp_content_ratio(text: str) -> float:
    """计算日文字符（假名+汉字）占内容字符的比例。"""
    comp = compact(text)
    if not comp:
        return 0.0
    jp_count = sum(1 for ch in comp if is_jp_char(ch))
    return jp_count / len(comp)


def is_jp_char(ch: str) -> bool:
    """判断字符是否为日文（平假名、片假名或汉字）。"""
    return bool(HIRAGANA_RE.match(ch) or KATAKANA_RE.match(ch) or CJK_RE.match(ch))


# 日文句子助词——自然日文文本的强指标
SENTENCE_PARTICLES = set('がのをにはへでとからよりもってばたらなるましょ')


def has_sentence_structure(text: str) -> bool:
    """判断文本是否具备日文句子结构（助词、动词词尾等）。"""
    comp = compact(text)
    if len(comp) < 4:
        return False
    particle_count = sum(1 for ch in comp if ch in SENTENCE_PARTICLES)
    return particle_count >= 2


def pick_text(text1: str, text2: str) -> str | None:
    """返回更优的文本；两者都是噪声时返回 None。

    策略：
    - 文件 2（Fun-ASR-Nano）常产出更完整的日文，但有时掺入中文/英文噪声。
    - 文件 2 日文占比高（>60%）且具备句子结构时优先。
    - 文件 2 含噪声/乱码时用文件 1。
    - 两者均有效时，优先选择更完整自然的那个。
    """
    t1_has_jp = has_japanese(text1)
    t2_has_jp = has_japanese(text2)
    t1_noise = is_noise(text1)
    t2_noise = is_noise(text2)

    if t1_noise and t2_noise:
        return None

    if t1_noise and not t2_noise:
        return text2
    if not t1_noise and t2_noise:
        return text1

    t2_jp_ratio = jp_content_ratio(text2)
    t1_jp_ratio = jp_content_ratio(text1)

    t2_has_structure = has_sentence_structure(text2)
    t1_has_structure = has_sentence_structure(text1)

    if t2_jp_ratio > 0.60 and t2_has_structure:
        return text2

    if t1_has_structure and (not t2_has_structure or t2_jp_ratio <= 0.60):
        return text1

    if t2_jp_ratio <= 0.60 and t1_has_jp:
        return text1

    if t1_has_jp:
        return text1
    if t2_has_jp:
        return text2

    return None


# ─────────────────────────────────────────────────────────────
# 6. 机械纠错（噪声清理，不包含具体内容纠错）
# ─────────────────────────────────────────────────────────────

def fold_long_repeats(text: str) -> str:
    """将连续 4+ 个相同假名字符折叠为 3 个。"""
    result = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        j = i + 1
        while j < n and text[j] == ch:
            j += 1
        run = j - i
        if run > 3 and (HIRAGANA_RE.match(ch) or KATAKANA_RE.match(ch)):
            result.append(ch * 3)
        else:
            result.append(text[i:j])
        i = j
    return "".join(result)


def fold_pattern_repeats(text: str, max_repeat: int = 3) -> str:
    """折叠重复的 2 字符模式（如 はぁはぁはぁ…、そうそうそうそう…）。"""

    def fold_2char(m):
        pattern = m.group(1)
        return pattern * max_repeat

    return re.sub(r'(..)\1{2,}', fold_2char, text)


def remove_chinese_noise_chars(text: str) -> str:
    """移除渗入日文文本的单个汉语噪声字。"""
    if has_japanese(text):
        for ch in CHINESE_NOISE_CHARS:
            text = text.replace(ch, '')
    return text


# 渗入的汉语/英文噪声短语
CHINESE_NOISE_PHRASES = [
    "没关系，没关系", "没关系", "我的妈呀", "我的姑娘",
    "啊，救命啊", "救命啊", "我爱过你", "嗯，嗯，嗯", "嗯，嗯",
    "嗯", "呃，呃", "呃", "哈哈", "哎",
    "啊，没有了", "没有了", "打开空调", "公主",
    "我我我我", "谁加你了", "骗你的", "没有哦", "哥哥", "爸爸", "妈妈",
    "可以", "对吧",
]


def clean_leaked_noise(text: str) -> str:
    """清理渗入文本的中文/英文噪声。"""
    if has_japanese(text):
        for phrase in CHINESE_NOISE_PHRASES:
            text = text.replace(phrase, "")
        text = remove_chinese_noise_chars(text)
        en_words_to_remove = sorted(EN_NOISE, key=len, reverse=True)
        for word in en_words_to_remove:
            text = re.sub(rf"\b{re.escape(word)}\b", "", text, flags=re.IGNORECASE)
    else:
        for ch in CHINESE_NOISE_CHARS:
            text = text.replace(ch, '')
    return text.strip()


def correct_text(text: str) -> str:
    """应用机械纠错（折叠重复 + 清理噪声）。"""
    text = fold_long_repeats(text)
    text = fold_pattern_repeats(text)
    text = clean_leaked_noise(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    text = text.strip()
    return text


# ─────────────────────────────────────────────────────────────
# 7. 主合并
# ─────────────────────────────────────────────────────────────

def merge_srt(path1: str, path2: str, out_path: str):
    print(f"Parsing {path1} ...")
    entries1 = parse_srt(path1)
    print(f"  → {len(entries1)} entries")

    print(f"Parsing {path2} ...")
    entries2 = parse_srt(path2)
    print(f"  → {len(entries2)} entries")

    n = min(len(entries1), len(entries2))
    if len(entries1) != len(entries2):
        print(f"  WARNING: mismatched entry counts; using first {n}")

    kept = []
    discarded = 0
    from1 = 0
    from2 = 0

    for i in range(n):
        _, _, start_raw, end_raw, text1 = entries1[i]
        _, _, _, _, text2 = entries2[i]

        chosen = pick_text(text1, text2)
        if chosen is None:
            discarded += 1
            continue

        if chosen == text1:
            from1 += 1
        else:
            from2 += 1

        corrected = correct_text(chosen)

        if not corrected or is_noise(corrected):
            discarded += 1
            continue

        comp = compact(corrected)
        if len(comp) <= 2:
            discarded += 1
            continue

        kept.append((start_raw, end_raw, corrected))

    lines = []
    for idx, (start_raw, end_raw, text) in enumerate(kept, start=1):
        start_norm = ms_to_ts(ts_to_ms(start_raw))
        end_norm = ms_to_ts(ts_to_ms(end_raw))
        lines.append(f"{idx}\n{start_norm} --> {end_norm}\n{text}\n")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n{'='*60}")
    print(f"DONE!")
    print(f"  Original file 1 entries : {len(entries1)}")
    print(f"  Original file 2 entries : {len(entries2)}")
    print(f"  Entries from file 1     : {from1}")
    print(f"  Entries from file 2     : {from2}")
    print(f"  Entries discarded (noise): {discarded}")
    print(f"  Entries in output       : {len(kept)}")
    print(f"  Written to              : {out_path}")
    print(f"{'='*60}")


def parse_args():
    parser = argparse.ArgumentParser(description="合并两个 ASR 的 SRT 并过滤噪声")
    parser.add_argument("file1", nargs="?", help="第一个 SRT（SenseVoiceSmall 输出）")
    parser.add_argument("file2", nargs="?", help="第二个 SRT（Fun-ASR-Nano 输出）")
    parser.add_argument("-o", "--output", help="输出 SRT 路径")
    parser.add_argument("--stem", help="音频文件名 stem，自动定位 srt/<stem>_1.srt 与 srt/<stem>_2.srt")
    parser.add_argument("--workspace", default=DEFAULT_WORKSPACE,
                        help="工作目录，默认当前工作目录（可用 ASR_WORKSPACE 环境变量覆盖）")
    return parser.parse_args()


def main():
    args = parse_args()

    if args.stem:
        srt_dir = os.path.join(args.workspace, "srt")
        file1 = os.path.join(srt_dir, f"{args.stem}_1.srt")
        file2 = os.path.join(srt_dir, f"{args.stem}_2.srt")
        output = args.output or os.path.join(srt_dir, f"{args.stem}.pre.srt")
    else:
        if not args.file1 or not args.file2:
            print("错误：需要提供两个 SRT 文件路径，或用 --stem 自动定位。")
            sys.exit(1)
        file1, file2 = args.file1, args.file2
        output = args.output or "merged.srt"

    for p in (file1, file2):
        if not os.path.exists(p):
            print(f"错误：找不到文件 {p}")
            sys.exit(1)

    merge_srt(file1, file2, output)


if __name__ == "__main__":
    main()
