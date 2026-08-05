#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

# 기존 인스턴스 종료
pkill -f "python.*main.py" 2>/dev/null || true
sleep 0.3

if [ ! -d ".venv" ]; then
    echo "가상환경 생성 중..."
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install -q -r requirements.txt
echo "실행: $(python -c 'import sys; print(sys.executable)')"
python main.py
