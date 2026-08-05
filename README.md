# InputWizard

키보드 단축키·마우스 스크롤·한영키를 사용하기 어려울 때 사용하는 **떠 있는 보조 입력 버튼** 유틸리티입니다.

배경 없이 화면 위에 플로팅되며, 드래그로 위치를 자유롭게 이동할 수 있습니다.

---

## 버튼 구성

```
┌───┬──┐
│한영│ ↑│
├───┤  │
│복사│  │
├───┤  │
│붙기│ ↓│
└───┴──┘
```

| 위치 | 버튼 | 기능 |
|------|------|------|
| 좌 상단 | 한/영 | 한영 입력 전환 (OS별 자동 처리) |
| 좌 중단 | 복사 | 현재 선택 영역 복사 (Ctrl/Cmd+C) |
| 좌 하단 | 붙여넣기 | 커서 위치에 붙여넣기 (Ctrl/Cmd+V) |
| 우 상단 | ↑ | 포커스 영역 위로 스크롤 |
| 우 하단 | ↓ | 포커스 영역 아래로 스크롤 |

---

## 설치

### 요구 사항
- Python 3.10 이상
- PySide6
- pynput

```bash
git clone https://github.com/progh2/inputwizard.git
cd inputwizard
pip install -r requirements.txt
python main.py
```

### Linux 추가 설정

X11 환경에서 한/영 전환에 `xdotool`이 필요합니다.

```bash
sudo apt install xdotool
```

Wayland 환경에서는 `ydotool`을 설치하고 서비스를 활성화하세요.

```bash
sudo apt install ydotool
sudo systemctl enable --now ydotoold
```

---

## 사용 방법

1. `python main.py` 로 실행
2. 창을 드래그하여 원하는 위치로 이동
3. 버튼을 클릭하여 입력 동작 수행
4. 우클릭 메뉴에서 스크롤 강도 조절 및 종료

창의 위치는 자동으로 저장되어 다음 실행 시 복원됩니다.

---

## OS별 한/영 전환 방식

| OS | 방식 |
|----|------|
| Windows | 가상 키 `VK_HANGUL (0x15)` 이벤트 전송 |
| macOS | 입력 소스 전환 (`Ctrl+Space` 또는 시스템 API) |
| Linux (X11) | `xdotool key hangul` |
| Linux (Wayland) | `ydotool key 0x90` |

---

## 개발

```bash
# 가상환경 생성 및 의존성 설치
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 실행
python main.py
```

### 프로젝트 구조 (예정)

```
inputwizard/
├── main.py               # 진입점
├── src/
│   ├── ui/
│   │   ├── main_window.py    # 플로팅 창 및 버튼 레이아웃
│   │   └── styles.py         # 버튼 스타일
│   ├── actions/
│   │   ├── scroll.py         # 스크롤 이벤트 주입
│   │   ├── clipboard.py      # 복사/붙여넣기
│   │   └── ime.py            # 한/영 전환 (OS별)
│   └── config.py             # 설정 로드/저장
├── requirements.txt
├── PRD.md
└── README.md
```

---

## 라이선스

MIT License

---

## 기여

이슈 및 PR은 언제나 환영합니다.  
[Issues](https://github.com/progh2/inputwizard/issues) · [PRD](./PRD.md)
