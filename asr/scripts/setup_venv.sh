#!/usr/bin/env bash
# 校验并创建 asr 技能所需的 Python 虚拟环境（默认 ~/.venv/funasr，可用 VENV_DIR 覆盖）。
# 本机有 uv 时优先使用 uv 管理虚拟环境；没有 uv 则降级为 python3 -m venv + pip。
# 幂等：环境已存在且依赖完整则直接跳过。
set -euo pipefail

VENV_DIR="${VENV_DIR:-$HOME/.venv/funasr}"
PY="$VENV_DIR/bin/python"

# 依赖列表（pip 包名）
DEPS=(torch funasr librosa soundfile tqdm python-dotenv)

echo "==> 校验虚拟环境: $VENV_DIR"

venv_ok() {
  [ -x "$PY" ] && "$PY" -c "import funasr, torch, librosa, soundfile, tqdm, dotenv" >/dev/null 2>&1
}

# 已有且依赖完整 → 直接跳过
if venv_ok; then
  echo "虚拟环境已存在且依赖完整 ✓"
  "$PY" -c "import torch; print('  torch', torch.__version__, '| CUDA 可用:', torch.cuda.is_available())"
  exit 0
fi

# 确定工具链：优先 uv，否则降级为传统方式
if command -v uv >/dev/null 2>&1; then
  TOOL="uv"
  UV_VER="$(uv --version 2>/dev/null | awk '{print $2}')"
  echo "==> 检测到 uv（$UV_VER），使用 uv 管理虚拟环境"
else
  TOOL="legacy"
  command -v python3 >/dev/null 2>&1 || {
    echo "✗ 未找到 python3，请先安装 python3（建议 >= 3.10）"
    exit 1
  }
  echo "==> 未检测到 uv，降级为传统方式（python3 -m venv + pip）"
fi

# 创建虚拟环境（不存在时）
if [ -x "$PY" ]; then
  echo "虚拟环境已存在，但依赖不完整，将补装依赖..."
else
  echo "未找到虚拟环境，开始创建..."
  case "$TOOL" in
    uv)
      uv venv "$VENV_DIR"
      ;;
    *)
      python3 -m venv "$VENV_DIR"
      ;;
  esac
  echo "虚拟环境已创建: $VENV_DIR"
fi

# 安装依赖
echo "==> 安装依赖"
case "$TOOL" in
  uv)
    uv pip install --python "$PY" "${DEPS[@]}"
    ;;
  *)
    "$PY" -m pip install --upgrade pip
    "$PY" -m pip install "${DEPS[@]}"
    ;;
esac

echo "✓ 虚拟环境就绪: $PY"
"$PY" -c "import funasr, torch; print('  funasr OK | torch', torch.__version__, '| CUDA 可用:', torch.cuda.is_available())"
