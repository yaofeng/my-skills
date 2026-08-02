#!/usr/bin/env python3
"""
ASR 转录脚本（基于 FunASR），随 asr 技能打包。

用法:
  <venv-path>/bin/python asr.py -i <音频文件> --asr-model both -l ja --device cuda:0

工作目录（含 audio/、srt/、tmp/ 子目录）默认取当前工作目录，也可用环境变量 ASR_WORKSPACE 或 --workspace 显式指定。
"""

import argparse
import os
import re
import traceback
import uuid

import dotenv
import librosa
import soundfile as sf
from funasr import AutoModel
from tqdm import tqdm

dotenv.load_dotenv(override=True)

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
DEFAULT_WORKSPACE = os.environ.get("ASR_WORKSPACE", os.getcwd())

SAMPLING_RATE = 16000
SUPPORTED_AUDIO_EXTS = {".mp4", ".m4a"}

VAD_MODEL = "fsmn-vad"

# ASR 模型配置：显示名 -> (FunASR model id, SRT 文件名后缀)
ASR_MODELS = {
    "SenseVoiceSmall": ("iic/SenseVoiceSmall", "_1"),
    "Fun-ASR-Nano":    ("FunAudioLLM/Fun-ASR-Nano-2512", "_2"),
}

# VAD 片段前后 padding（让 ASR 有更完整的上下文）
VAD_PAD_BEFORE_SAMPLES = SAMPLING_RATE // 2   # 0.5s
VAD_PAD_AFTER_SAMPLES = SAMPLING_RATE // 10   # 0.1s
MIN_SEGMENT_SAMPLES = SAMPLING_RATE // 2      # 0.5s

DEFAULT_LANGUAGE = "ja"
DEFAULT_BATCH_SIZE = 10

# ---------------------------------------------------------------------------
# 运行时状态
# ---------------------------------------------------------------------------
_models: dict = {}
_workspace: str = DEFAULT_WORKSPACE
_device: str = "cuda:0"


# ---------------------------------------------------------------------------
# 设备解析
# ---------------------------------------------------------------------------
def resolve_device(device_arg):
    """设备解析：auto 时优先 GPU，无 GPU 则回退 CPU 并提示。"""
    if device_arg and device_arg != "auto":
        return device_arg
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda:0"
    except Exception:
        pass
    print("⚠ 未检测到可用 GPU，将使用 CPU 推理（速度较慢）。")
    print("  可显式指定 --device cuda:0 强制使用 GPU，或 --device cpu。")
    return "cpu"


# ---------------------------------------------------------------------------
# 交互选择
# ---------------------------------------------------------------------------
def user_select(items, caption):
    """显示编号菜单并返回所选条目。"""
    print()
    for idx, item in enumerate(items):
        print(f"[{idx}] {item}")
    print("-" * 50)
    return items[int(input(caption))]


def select_audio_file(audio_dir):
    """列出 *audio_dir* 中的音频文件并让用户选择。"""
    audio_files = sorted(
        f for f in os.listdir(audio_dir)
        if os.path.splitext(f)[1] in SUPPORTED_AUDIO_EXTS
    )
    return os.path.join(audio_dir, user_select(audio_files, "请选择音频文件："))


# ---------------------------------------------------------------------------
# 音频 / 模型工具
# ---------------------------------------------------------------------------
def load_audio(audio_file):
    """加载音频并重采样到 SAMPLING_RATE。"""
    return librosa.load(audio_file, sr=SAMPLING_RATE)[0]


def run_vad(audio_file):
    """在 *audio_file* 上运行 FSMN-VAD。

    返回 SAMPLING_RATE 下的 (start_sample, end_sample) 列表。
    """
    if VAD_MODEL not in _models:
        _models[VAD_MODEL] = AutoModel(model=VAD_MODEL, device=_device, disable_update=True)
    timestamps_ms = _models[VAD_MODEL].generate(input=audio_file)[0]["value"]
    return [(s * SAMPLING_RATE // 1000, e * SAMPLING_RATE // 1000) for s, e in timestamps_ms]


def run_asr(audio_arrays, language=DEFAULT_LANGUAGE, model_key=None):
    """对一批音频数组运行 ASR。

    返回每段输入的 {"text": ...} 列表。
    """
    if model_key is None:
        model_key = ASR_MODELS["Fun-ASR-Nano"][0]
    if model_key not in _models:
        _models[model_key] = AutoModel(model=model_key, device=_device, disable_update=True)

    tmp_dir = os.path.join(_workspace, "tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    tmp_files = [os.path.join(tmp_dir, f"{uuid.uuid4()}.wav") for _ in audio_arrays]
    try:
        for arr, path in zip(audio_arrays, tmp_files):
            sf.write(path, arr, SAMPLING_RATE)
        results = _models[model_key].generate(
            input=tmp_files,
            cache={},
            language=language,
            use_itn=True,
            batch_size_s=60,
            merge_vad=True,
            merge_length_s=15,
            disable_pbar=True,
        )
    finally:
        for path in tmp_files:
            if os.path.exists(path):
                os.remove(path)

    return [{"text": re.sub(r"<\|\w+\|>", "", r["text"])} for r in results]


# ---------------------------------------------------------------------------
# SRT 格式化
# ---------------------------------------------------------------------------
def format_srt_time(seconds):
    """将秒格式化为 SRT 时间戳 HH:MM:SS.s。"""
    hour = int(seconds // 3600)
    minute = int((seconds % 3600) // 60)
    second = seconds % 60
    return f"{hour:02d}:{minute:02d}:{second:02.1f}"


def write_srt_entry(f, index, time_from, time_to, text):
    """将单个 SRT 条目写入文件句柄 *f*。"""
    f.write(f"{index}\n")
    f.write(f"{format_srt_time(time_from)} --> {format_srt_time(time_to)}\n")
    f.write(f"{text.strip()}\n\n")


# ---------------------------------------------------------------------------
# 流程工具
# ---------------------------------------------------------------------------
def prepare_segments(speeches, audio_array):
    """为 VAD 片段加 padding 并切出音频数组作为 ASR 输入。"""
    segments = []
    for start, end in speeches:
        start = max(start - VAD_PAD_BEFORE_SAMPLES, 0)
        end = end + VAD_PAD_AFTER_SAMPLES
        segments.append((start, end, audio_array[start:end]))
    return segments


def build_model_list(choice):
    """根据 --asr-model 选择返回 (model_key, suffix) 列表。"""
    if choice == "both":
        return [ASR_MODELS["SenseVoiceSmall"], ASR_MODELS["Fun-ASR-Nano"]]
    return [ASR_MODELS[choice]]


def transcribe_segments(segments, srt_file, model_key, language, batch_size):
    """分批对 *segments* 运行 ASR 并把 SRT 输出写到 *srt_file*。"""
    with open(srt_file, "wt", encoding="utf-8") as f:
        srt_idx = 0
        desc = os.path.basename(model_key)
        for batch_start in tqdm(range(0, len(segments), batch_size), desc=desc):
            batch = segments[batch_start:batch_start + batch_size]
            audio_arrays = [arr for _, _, arr in batch]
            try:
                chunks = run_asr(audio_arrays, language=language, model_key=model_key)
            except Exception:
                print(f"error of asr, batch starting at {batch_start}")
                traceback.print_exc()
                break
            for (speech_start, speech_end, _), chunk in zip(batch, chunks):
                time_offset = speech_start / SAMPLING_RATE
                time_from, time_to = 0.0, (speech_end - speech_start) / SAMPLING_RATE
                if chunk.get("timestamp"):
                    time_from, time_to = chunk["timestamp"]
                if time_from is None or time_to is None:
                    continue
                time_from += time_offset
                time_to += time_offset
                try:
                    srt_idx += 1
                    write_srt_entry(f, srt_idx, time_from, time_to, chunk["text"])
                except Exception:
                    traceback.print_exc()
                    break


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(description="ASR transcription tool")
    parser.add_argument("-i", "--input-audio", default="",
                        help="音频文件路径；为空时展示选择菜单")
    parser.add_argument("-l", "--language", default=DEFAULT_LANGUAGE,
                        help="识别语言（auto/zn/en/yue/ja/ko/nospeech）")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE,
                        help="ASR 批处理大小")
    parser.add_argument("--asr-model", default="both",
                        choices=list(ASR_MODELS.keys()) + ["both"],
                        help="选择 ASR 模型；both 表示两个模型都跑")
    parser.add_argument("--device", default="auto",
                        help="推理设备（auto/cuda:0/cuda:1/cpu）")
    parser.add_argument("--workspace", default=DEFAULT_WORKSPACE,
                        help="工作目录，默认当前工作目录（可用 ASR_WORKSPACE 环境变量覆盖）")
    return parser.parse_args()


def main():
    global _device, _workspace
    args = parse_args()
    _device = resolve_device(args.device)
    _workspace = args.workspace

    audio_dir = os.path.join(_workspace, "audio")
    srt_dir = os.path.join(_workspace, "srt")
    os.makedirs(srt_dir, exist_ok=True)

    audio_file = args.input_audio if args.input_audio else select_audio_file(audio_dir)
    audio_stem = os.path.splitext(os.path.basename(audio_file))[0]

    native_sr = librosa.get_samplerate(audio_file)
    if native_sr != SAMPLING_RATE:
        print(f"⚠ 原始采样率 {native_sr} Hz，将被重采样到 {SAMPLING_RATE} Hz")

    audio_array = load_audio(audio_file)
    speeches = run_vad(audio_file)
    speeches = [(s, e) for s, e in speeches if e - s > MIN_SEGMENT_SAMPLES]
    segments = prepare_segments(speeches, audio_array)

    for model_key, suffix in build_model_list(args.asr_model):
        srt_file = os.path.join(srt_dir, f"{audio_stem}{suffix}.srt")
        print(f"\n>>> 使用模型 {model_key}，输出到 {srt_file}")
        transcribe_segments(segments, srt_file, model_key, args.language, args.batch_size)


if __name__ == "__main__":
    main()
