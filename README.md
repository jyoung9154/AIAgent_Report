# 🤖 AI Agent Report — 통합 AI 업무보고서 자동 생성기

> **GitHub Copilot (JetBrains / VSCode) · Antigravity (Gemini) · Cursor · GPT Codex · Claude Code** 6개 AI 에이전트의 세션 히스토리를 통합 파싱하여, 날짜별 업무보고서를 자동 생성합니다.

---

## ✨ 주요 기능

| 기능 | 설명 |
|---|---|
| **6-에이전트 통합 파싱** | Copilot (JetBrains + VSCode), Antigravity, Cursor, GPT Codex, Claude Code 세션 데이터를 한번에 파싱 |
| **업무보고서 자동 생성** | 양식 기반으로 요청별 상세, 산출물, 검증 결과 등을 자동 작성 |
| **기존 보고서 병합** | 같은 날짜 보고서가 있으면 새 항목만 추가 |
| **에이전트 스킬 자동 설치** | 감지된 에이전트에 스킬을 자동 설치하여 자연어 트리거 사용 가능 |
| **VSCode 로그 자동 활성화** | VSCode 감지 시 Copilot 대화 로그 저장 설정을 자동으로 추가 |

---

## 📦 설치

### 1. 저장소 클론

```bash
git clone https://github.com/{your-username}/AIAgent_Report.git ~/AIAgent_Report
cd ~/AIAgent_Report
```

### 2. 설치 스크립트 실행

```bash
chmod +x install.sh
./install.sh
```

설치 스크립트가 자동으로:
1. **Python 3** 설치 여부를 확인합니다 (미설치 시 설치를 안내합니다)
2. 사용 중인 **AI 에이전트를 자동 감지**합니다
3. 감지된 에이전트의 스킬 디렉토리에 `AI_Report` 스킬을 설치합니다
4. 프로젝트 연결 설정을 완료합니다
5. **VSCode** 감지 시 Copilot 대화 로그 저장 설정을 자동으로 추가합니다

> 💡 **새 에이전트를 추가 설치했나요?**
> GPT Codex, Claude Code 등 새로운 에이전트를 나중에 설치했다면, `./install.sh`를 **다시 실행**하면 해당 에이전트에도 스킬이 자동으로 설치됩니다.

---

## 🚀 사용법

설치 후 각 AI 에이전트 내에서 아래와 같이 **자연어로 요청**하면 자동으로 보고서가 생성됩니다:

```
/AI업무보고 오늘자 보고서 작성해줘
/AI업무보고 2026-04-02 보고서 작성해줘
```

### 지원 에이전트

| 에이전트 | IDE / 환경 |
|---|---|
| **GitHub Copilot** | JetBrains IDE (IntelliJ, WebStorm 등) · VSCode (대화 로그 저장 설정 자동 활성화) |
| **Antigravity (Gemini)** | Antigravity IDE |
| **Cursor** | Cursor IDE |
| **GPT Codex** | 터미널 (Codex CLI) |
| **Claude Code** | 터미널 (Claude Code CLI) |

### 보고서 출력 경로

```
~/.ai-report/업무보고/YYYY-MM-DD_AI업무보고서.md
```

---

## 🗑️ 제거

```bash
./uninstall.sh
```

모든 에이전트에서 `AI_Report` 스킬을 제거하고 프로젝트 연결을 해제합니다.
클론된 저장소 자체는 삭제하지 않습니다.

---

## 📁 프로젝트 구조

```
AIAgent_Report/
├── README.md                 # 이 파일
├── install.sh                # 설치 스크립트
├── uninstall.sh              # 제거 스크립트
├── .gitignore
├── parse_sessions.py         # 6-에이전트 통합 파서
├── SKILL.md                  # 통합 스킬 정의 (에이전트가 읽는 절차서)
├── .data/                    # (숨김) 양식 파일 등 내부 데이터
│   └── 업무보고서_양식.md      # 보고서 양식 템플릿 (읽기 전용)
├── AI_Report/                # 에이전트 스킬 폴더 (설치 시 복사됨)
│   └── SKILL.md              # 포인터 파일
└── 업무보고/                  # 보고서 출력 디렉토리
```

---

## 📋 요구 사항

- **Python 3.9+** (설치 스크립트가 자동 확인 및 설치 안내)
- **macOS / Linux** (Windows는 미테스트)
- 지원 에이전트 중 1개 이상 설치되어 있어야 합니다

---

## 📄 라이선스

MIT License

