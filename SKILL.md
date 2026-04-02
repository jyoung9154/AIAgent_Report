---
name: AI업무보고
description: "'/AI업무보고 오늘자 보고서 작성해줘' 또는 '/AI업무보고 YYYY-MM-DD 보고서 작성해줘' 요청 시 GitHub Copilot (JetBrains / VSCode) + Antigravity + Cursor + GPT Codex + Claude Code 여섯 에이전트의 세션 히스토리를 통합 파싱하여 날짜별 AI 업무보고서를 자동 생성하거나 기존 파일에 병합하는 스킬입니다."
risk: low
source: internal
date_added: '2026-03-31'
---

# AI 업무보고서 통합 자동 생성 스킬

## 개요

이 스킬은 **GitHub Copilot**(JetBrains IDE), **GitHub Copilot**(VSCode), **Antigravity**(Gemini), **Cursor**, **GPT Codex**(터미널), **Claude Code**(터미널) 여섯 에이전트의 세션 데이터를 통합 파싱하여, 날짜별 AI 업무보고서를 **자동 생성** 또는 **기존 파일에 병합**한다.

- **Copilot 데이터 (JetBrains)**: `~/.copilot/jb/{session_id}/partition-{n}.jsonl` (JSONL 대화 로그)
- **Copilot 데이터 (VSCode)**: `~/Library/Application Support/Code/User/workspaceStorage/{hash}/chatSessions/{session_id}.jsonl` (JSONL 대화 로그, `saveConversationLog` 설정 필요)
- **Antigravity 데이터**: `~/.gemini/antigravity/brain/{session_id}/` (brain 아티팩트 — walkthrough.md, task.md, implementation_plan.md, metadata.json)
- **Cursor 데이터**: `~/.cursor/projects/{project_folder}/agent-transcripts/{session_id}/{session_id}.jsonl` (JSONL 대화 로그, 파일 mtime 기반 날짜 판별)
- **GPT Codex 데이터**: `~/.codex/sessions/YYYY/MM/DD/rollout-YYYY-MM-DDTHH-MM-SS-<uuid>.jsonl` (JSONL — 각 줄 `{timestamp, type, payload}`, 이벤트 타입: `session_meta`, `user_message`, `event_msg`, `function_call`, `token_count`)
- **Claude Code 데이터**: `~/.claude/projects/{project-hash}/sessions/{session_id}.jsonl` (대화 턴 JSONL — tool_use 이벤트 포함, timestamp ISO 8601 기반 날짜 판별)

> **⚠️ 이 스킬은 절대경로 기반이므로 어느 에이전트에서든 동일하게 사용 가능하다.**

---

## ⭐ 핵심 원칙

1. **반드시 양식 파일을 먼저 읽는다** — 추정이나 기억에 의존하지 않고 실제 양식 파일 내용을 기반으로 작성
2. **반드시 파서를 실행하여 대화 로그를 수집한다** — 오늘자 세션에서 실제로 수행한 작업만 기재 (추측/할루시네이션 금지)
3. **경로 표기 규칙을 준수한다** — 모든 파일 경로는 `프로젝트 - 파일명` 형식 사용 (로컬 절대경로 사용 금지)
4. **각 항목을 최소 기준 이상으로 상세히 작성한다** — 양식 내 `> 작성방법` 지시를 반드시 따름
5. **여섯 에이전트의 작업을 하나의 보고서로 통합한다** — 에이전트별로 분리하지 않고 요청 단위로 통합
6. **이전 보고서를 반드시 확인한다** — 같은 파일/기능이 이전 날짜에도 작업된 경우, 연속 개발 타임라인을 추적하여 "기타" 섹션에 기재
7. **아래 "작성 품질 기준"의 최소 분량과 패턴을 반드시 지킨다** — 가이드의 황금 예시를 참고하여 동일한 깊이로 작성

---

## 트리거 패턴

아래 요청 패턴 중 하나가 감지되면 이 스킬을 실행한다.

| 요청 패턴 | 설명 |
|---|---|
| `/AI업무보고 오늘자 보고서 작성해줘` | 오늘 날짜(KST) 세션 기반 보고서 생성 |
| `/AI업무보고 YYYY-MM-DD 보고서 작성해줘` | 특정 날짜 세션 기반 보고서 생성 |
| `오늘 AI 업무보고서 작성해줘` | 오늘 날짜 보고서 생성 (동의어) |
| `AI 업무보고 [날짜]` | 날짜 지정 보고서 생성 |
| `업무보고서 병합해줘` | Antigravity 보고서 텍스트를 기존 파일에 병합 |

---

## 📂 공유 파일 경로 (절대경로)

| 파일 | 절대경로 |
|---|---|
| **통합 파서 스크립트** | `~/.ai-report/parse_sessions.py` |
| **양식 파일** | `~/.ai-report/.data/업무보고서_양식.md` |
| **이 스킬 파일** | `~/.ai-report/SKILL.md` |

---

## 📂 보고서 출력 경로

```
~/.ai-report/업무보고/YYYY-MM-DD_AI업무보고서.md
```

- `YYYY-MM-DD`는 작성 당일 날짜로 대체 (현재 시간 기준)
- 동일 날짜 파일이 이미 존재하면 병합 규칙에 따라 기존 내용에 추가

---

## 🔄 실행 절차 (Step-by-Step)

### STEP 1 — 날짜 결정

- 요청에 날짜(YYYY-MM-DD)가 명시되어 있으면 해당 날짜 사용
- 없으면 오늘 날짜(KST) 자동 사용

### STEP 2 — 양식 파일 읽기

```bash
# Copilot 에이전트의 경우
read_file ~/.ai-report/.data/업무보고서_양식.md

# Antigravity 에이전트의 경우
view_file ~/.ai-report/.data/업무보고서_양식.md
```

전체 섹션 구조와 각 항목의 `> 작성방법` 지시를 숙지한다.

### STEP 3 — 통합 파서 실행

터미널에서 아래 명령을 실행하여 **여섯 에이전트의 세션 데이터를 동시에** 파싱한다.

```bash
# 요약 모드 (빠른 전체 파악 — 먼저 실행)
python3 ~/.ai-report/parse_sessions.py --date {날짜} --summary

# 상세 모드 (turns 전체 포함 — 보고서 작성 시 사용)
python3 ~/.ai-report/parse_sessions.py --date {날짜}

# 특정 에이전트만 파싱
python3 ~/.ai-report/parse_sessions.py --date {날짜} --source copilot
python3 ~/.ai-report/parse_sessions.py --date {날짜} --source vscode
python3 ~/.ai-report/parse_sessions.py --date {날짜} --source antigravity
python3 ~/.ai-report/parse_sessions.py --date {날짜} --source cursor
python3 ~/.ai-report/parse_sessions.py --date {날짜} --source codex
python3 ~/.ai-report/parse_sessions.py --date {날짜} --source claude

# 데이터 구조 탐색 (에이전트 설치 확인용)
python3 ~/.ai-report/parse_sessions.py --discover
```

#### 파서 출력 JSON 구조

```json
{
  "date": "2026-03-31",
  "session_count": 7,
  "copilot_sessions": 3,
  "vscode_copilot_sessions": 1,
  "antigravity_sessions": 1,
  "cursor_sessions": 1,
  "codex_sessions": 1,
  "claude_sessions": 1,
  "total_turns": 40,
  "total_files_modified": ["경로1", "경로2"],
  "sessions": [
    {
      "agent": "copilot",
      "agent_label": "GitHub Copilot",
      "ide": "JetBrains-IC",
      "session_id": "...",
      "start_time": "2026-03-31 09:42:42",
      "end_time": "2026-03-31 15:29:26",
      "turn_count": 12,
      "files_modified": ["경로1"],
      "tools_used": ["replace_string_in_file", "read_file"],
      "turns": [
        {
          "user_timestamp": "2026-03-31 10:39:50",
          "user_message": "사용자 요청 내용",
          "assistant_response": "AI 응답 요약",
          "tools_used": ["read_file"],
          "files_modified": ["경로1"]
        }
      ]
    },
    {
      "agent": "antigravity",
      "agent_label": "Antigravity (Gemini)",
      "ide": "Antigravity",
      "session_id": "...",
      "start_time": "2026-03-31 14:37:10",
      "end_time": "2026-03-31 14:37:43",
      "turn_count": 3,
      "files_modified": ["/경로/파일.js"],
      "tools_used": ["replace_file_content", "view_file"],
      "artifacts": ["..."],
      "walkthrough": "...",
      "task": "...",
      "implementation_plan": "..."
    },
    {
      "agent": "cursor",
      "agent_label": "Cursor",
      "ide": "Cursor",
      "session_id": "...",
      "project": "amaranth10-mailProject",
      "start_time": "2026-03-31 17:41:43",
      "end_time": "2026-03-31 17:41:43",
      "turn_count": 9,
      "files_modified": ["파일명.java"],
      "tools_used": [],
      "turns": [
        {
          "user_timestamp": "...",
          "user_message": "사용자 요청 내용",
          "assistant_response": "AI 응답 요약",
          "tools_used": [],
          "files_modified": ["파일명.java"]
        }
      ]
    },
    {
      "agent": "codex",
      "agent_label": "GPT Codex",
      "ide": "Terminal (Codex CLI)",
      "session_id": "...",
      "start_time": "2026-03-31 18:00:00",
      "end_time": "2026-03-31 18:30:00",
      "turn_count": 5,
      "files_modified": ["경로/파일.py"],
      "tools_used": ["shell", "write"],
      "turns": [
        {
          "user_timestamp": "2026-03-31 18:00:00",
          "user_message": "사용자 요청 내용",
          "assistant_response": "AI 응답 요약",
          "tools_used": ["shell"],
          "files_modified": ["경로/파일.py"]
        }
      ]
    },
    {
      "agent": "claude",
      "agent_label": "Claude Code",
      "ide": "Terminal (Claude Code)",
      "session_id": "...",
      "project": "프로젝트명",
      "start_time": "2026-03-31 19:00:00",
      "end_time": "2026-03-31 19:45:00",
      "turn_count": 6,
      "files_modified": ["경로/파일.java"],
      "tools_used": ["Read", "Write", "Bash"],
      "turns": [
        {
          "user_timestamp": "2026-03-31 19:00:00",
          "user_message": "사용자 요청 내용",
          "assistant_response": "AI 응답 요약",
          "tools_used": ["Read", "Write"],
          "files_modified": ["경로/파일.java"]
        }
      ]
    }
  ]
}
```

> **Cursor 세션 특이사항:**
> - Cursor JSONL은 이벤트 내에 타임스탬프 필드가 없으므로 `start_time`은 파일 birthtime, `end_time`은 파일 mtime 기준이다.
> - `tools_used`는 항상 빈 배열 — Cursor JSONL에는 tool_call 타입이 포함되지 않으며, 도구 사용 정보는 assistant 텍스트에서만 추론 가능하다.
> - `files_modified`는 assistant 응답 텍스트 내 백틱(`` ` ``)이나 마크다운 링크에서 파일 경로를 정규식으로 추출한 결과다.
> - `project` 필드가 추가로 포함된다 — Cursor 프로젝트 폴더명에서 추정한 프로젝트명.

> **GPT Codex 세션 특이사항:**
> - 경로가 날짜별 디렉토리 구조: `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`
> - 각 줄은 `{timestamp, type, payload}` 형태의 JSON 객체.
> - `session_meta` (첫 줄): 세션 id, cwd, cli_version, model_provider 등 초기 설정.
> - `user_message`: 사용자 프롬프트 입력.
> - `event_msg`: 에이전트 응답 및 추론(Reasoning) 텍스트.
> - `function_call`: 셸 명령어(`exec_command`), 파일 읽기/쓰기, MCP 외부 툴 호출 등 도구 실행 내역.
> - `token_count`: 각 턴 완료 시 입력/출력/추론 토큰 사용량 통계.

> **Claude Code 세션 특이사항:**
> - `timestamp`는 ISO 8601 UTC 형식 — KST 변환하여 날짜 판별.
> - `assistant` 이벤트의 `content` 배열 내에 `tool_use` 항목이 포함됨 (name: `Read`, `Write`, `Edit`, `Bash` 등).
> - `project` 필드가 포함된다 — settings.json의 projectName 또는 프로젝트 해시 폴더명.

### STEP 3.5 — 이전 보고서 확인 (개발 타임라인 추적) ⭐ 필수

오늘 작업한 파일/기능이 이전에도 작업된 적 있는지 확인하기 위해 **이전 보고서 파일을 반드시 읽는다.**

```bash
# 업무보고 폴더 내 기존 보고서 목록 확인
ls ~/.ai-report/업무보고/*.md 2>/dev/null
```

1. **최근 5일분 보고서를 읽는다** (있는 만큼만)
2. 각 보고서에서 **오늘 수정한 파일/기능과 동일한 파일명 또는 기능명**이 언급된 항목을 추출한다
3. **이전 보고서가 실제로 존재하고, 동일 파일/기능이 명확히 기재되어 있는 경우에만** "기타" 섹션에 아래 형식으로 기재한다:

```
{기능명} 연속 개발 타임라인: MM-DD(핵심작업 요약) → MM-DD(핵심작업 요약) → 오늘 MM-DD(오늘 핵심작업 요약) 순으로 연속 개발됨.
```

> **⚠️ 절대 추정 금지** — 이전 보고서를 실제로 읽어서 확인한 사실만 적시할 것. "아마 ~했을 것이다", "~로 추정된다" 같은 표현 절대 사용 금지.
>
> **이전 보고서가 없거나, 해당 파일/기능이 이전 보고서에 언급되지 않은 경우**: 타임라인 항목 자체를 생략한다. "해당 없음"도 쓰지 않는다.

### STEP 3-1 — Antigravity 보강 (선택 — 파서 데이터가 부족한 경우)

Antigravity 세션은 protobuf 대화 로그를 직접 파싱할 수 없으므로, brain 아티팩트만으로 정보가 부족할 경우 아래를 추가로 확인한다.

```bash
# Antigravity 세션의 아티팩트 목록 확인
ls ~/.gemini/antigravity/brain/{session_id}/

# walkthrough.md 상세 내용
cat ~/.gemini/antigravity/brain/{session_id}/walkthrough.md

# task.md 상세 내용
cat ~/.gemini/antigravity/brain/{session_id}/task.md

# implementation_plan.md 상세 내용
cat ~/.gemini/antigravity/brain/{session_id}/implementation_plan.md
```

또는 사용자가 **Antigravity 보고서 텍스트를 직접 붙여넣기**한 경우 해당 텍스트를 파싱하여 보고서에 통합한다.

### STEP 4 — 기존 보고서 파일 확인

```bash
ls ~/.ai-report/업무보고/{날짜}_AI업무보고서.md 2>/dev/null && echo EXISTS || echo NEW
```

- **EXISTS**: 기존 파일에 새 요청 항목만 추가(병합)
- **NEW**: 아래 템플릿으로 신규 파일 생성

### STEP 5 — 보고서 내용 작성

파서가 반환한 `sessions` 배열을 분석하여 아래 규칙으로 보고서 항목을 구성한다.

#### 5-1. 에이전트 통합 기준

| 조건 | 처리 방법 |
|---|---|
| Copilot만 사용 | `보고자 (IDE)` = `JetBrains-IC`, `AI 에이전트` = `GitHub Copilot` |
| Copilot (VSCode)만 사용 | `보고자 (IDE)` = `VSCode`, `AI 에이전트` = `GitHub Copilot` |
| Antigravity만 사용 | `보고자 (IDE)` = `Antigravity`, `AI 에이전트` = `Gemini` |
| Cursor만 사용 | `보고자 (IDE)` = `Cursor`, `AI 에이전트` = `Cursor` |
| GPT Codex만 사용 | `보고자 (IDE)` = `Terminal (Codex CLI)`, `AI 에이전트` = `GPT Codex` |
| Claude Code만 사용 | `보고자 (IDE)` = `Terminal (Claude Code)`, `AI 에이전트` = `Claude Code` |
| **복수 에이전트 사용** | `보고자 (IDE)` = 사용된 에이전트 `/`로 구분 (예: `JetBrains-IC / Antigravity / Terminal (Claude Code)`), 세션 ID도 구분, 총 요청 건수는 합산 |

#### 5-2. 요청 항목 분류 기준

| turns 내용 | 분류 방법 |
|---|---|
| 하나의 큰 작업을 여러 turn으로 반복 수정한 경우 | 하나의 요청 항목으로 묶기 |
| 완전히 다른 주제/파일을 다룬 경우 | 별도 요청 항목으로 분리 |
| **Copilot 작업과 Antigravity 작업이 같은 주제인 경우** | 하나의 요청 항목으로 합치되, 양쪽 에이전트 사용 내역을 모두 기술 |
| 보고서 작성/병합 요청 | 작성 및 병합은 요청 항목에서 제외 |

#### 5-3. AI 의사결정 근거 작성 기준

- **Copilot**: `assistant_response`에서 "왜 이 방법을 선택했는지" 핵심 이유 추출
- **Antigravity**: `walkthrough.md`, `implementation_plan.md` 내용에서 결정 사항 추출
- **Cursor**: `assistant_response`에서 결정 사항 추출 (Copilot과 동일 방식, 단 tool_call 정보는 없으므로 텍스트 기반으로만 추론)
- **GPT Codex**: `assistant_response`에서 결정 사항 추출, `function_call` 이벤트의 `name`/`arguments`로 도구 사용 맥락 파악
- **Claude Code**: `assistant_response`에서 결정 사항 추출, `tool_use` 항목의 `name`/`input`으로 도구 사용 맥락 파악
- 코드 변경이 있었다면 어떤 문제를 어떻게 해결했는지 1~3가지로 정리
- 근거가 불분명하면 `tools_used`와 `files_modified` 기반으로 추론

#### 5-4. 산출물 목록 작성 기준

- `files_modified`에 있는 파일을 기준으로 작성
- 도구별 작업 유형 매핑:

| 도구 (Copilot) | 도구 (Antigravity) | 도구 (Cursor) | 도구 (GPT Codex) | 도구 (Claude Code) | 작업 유형 |
|---|---|---|---|---|---|
| `replace_string_in_file` | `replace_file_content` / `multi_replace_file_content` | — (텍스트에서 추론) | `apply_diff` / `edit` | `Edit` / `MultiEdit` | 수정 |
| `insert_edit_into_file` | — | — | `patch` | — | 수정 |
| `create_file` | `write_to_file` | — | `write` / `create` | `Write` | 생성 |
| `run_in_terminal` (rm/delete) | `run_command` (rm/delete) | — | `shell` (rm/delete) | `Bash` (rm/delete) | 삭제 |

> **Cursor 산출물 판별**: Cursor는 tool_call 데이터가 없으므로, `files_modified`(텍스트 추출)와 `assistant_response` 내용을 참조하여 작업 유형(생성/수정/삭제)을 추론한다.
>
> **GPT Codex 산출물 판별**: `function_call` 이벤트의 `name` 필드와 `arguments` 내 `file_path`/`path`로 파일과 작업 유형을 판별한다.
>
> **Claude Code 산출물 판별**: `tool_use` 항목의 `name` 필드와 `input` 내 `file_path`/`path`로 파일과 작업 유형을 판별한다.

### STEP 6 — 경로 표기 규칙 준수 확인 (필수 검토)

작성 완료 후 아래 경로 표기 규칙을 전수 점검한다.

#### ⚠️ 경로 표기 규칙

| ❌ 잘못된 표기 | ✅ 올바른 표기 |
|---|---|
| `~/A10/Back/amaranth10-mail/src/.../SettingServiceImpl.java` | `amaranth10-mail - SettingServiceImpl.java` |
| `~/Project-anti/klago-ui-mail-micro/src/.../UDAP010_Re.js` | `klago-ui-mail-micro - UDAP010_Re.js` |
| `amaranth10-mailbox/src/main/java/.../MailListServiceImpl.java` | `amaranth10-mailbox - MailListServiceImpl.java` |

**형식**: `{프로젝트명} - {파일명}` (경로 없이 프로젝트와 파일명만)

### STEP 7 — 파일 저장

```
~/.ai-report/업무보고/{날짜}_AI업무보고서.md
```

- 날짜를 현재 날짜로 치환
- 기존 파일이 있으면 병합 규칙에 따라 처리

---

## 보고서 파일 템플릿

> **작성 규칙**: 요청별 상세의 항목 번호는 파일에 이미 존재하는 마지막 번호 이후부터 이어서 부여한다. 새 파일이면 1번부터 시작.

```markdown
# AI 에이전트 업무보고서

> **파일 경로**: `~/.ai-report/업무보고/{날짜}_AI업무보고서.md`

---

## 요약 (Summary)

> ⭐ 여기에 3문장 이상으로 오늘의 핵심 작업 흐름을 시간순으로 서술할 것.
> 황금 예시 참조: "오늘은 ~에 ~가 ~를 수행하였고, ~에서는 ~를 ~하였다. ~에는 ~가 추가되었다."

| 항목 | 내용 |
|---|---|
| 보고일 | {날짜} |
| 보고자 (IDE) | JetBrains-IC / Antigravity / Cursor |
| 프로젝트 | {프로젝트명 — 복수 프로젝트면 슬래시 구분} |
| AI 에이전트 | GitHub Copilot / Gemini / Cursor |
| 모델 버전 | Auto |
| 사용 인터페이스 | JetBrains-IC / Antigravity / Cursor |
| 세션 / 대화 ID | {Copilot session_id 목록} / {Antigravity session_id 목록} / {Cursor session_id 목록} |
| 총 요청 건수 | {N}건 (Copilot {N}건 + Antigravity {N}건 + Cursor {N}건) |
| 총 산출물 | 파일 {N}개 (수정 {N}개, 생성 {N}개, 삭제 {N}개) |
| 총 소요 시간 | {첫 turn 시작} ~ {마지막 turn 종료} |
| 기존 대비 절감 | 추정 절감 시간 (직접 구현 시 예상 시간 기반) |

---

## 요청 목록

| # | 요청 제목 | 에이전트 | 결과 | 산출물 수 |
|---|---|---|---|---|
| 1 | {요청 제목} | Copilot | ✅ 완료 | {N}개 |
| 2 | {요청 제목} | Antigravity | ✅ 완료 | {N}개 |
| 3 | {요청 제목} | Copilot + Antigravity | ✅ 완료 | {N}개 |

---

## 요청별 상세

(양식 파일의 1-1 ~ 1-10 구조를 그대로 따름)

---

## 다음 세션 인계 메모
## 프롬프트 회고
## 기타
- {기타 특이사항 또는 없음}
```

---

## 기존 파일 병합 규칙

기존 보고서 파일이 있는 경우 아래 규칙을 따른다.

1. **요약 섹션** — `보고자 (IDE)`, `AI 에이전트`, `세션 / 대화 ID`, `총 요청 건수`, `총 산출물`, `총 소요 시간`, `기존 대비 절감` 수치를 재계산하여 업데이트
2. **요청 목록 테이블** — 마지막 번호 이후에 새 행 추가
3. **요청별 상세** — 기존 마지막 요청 상세 이후에 새 요청 상세 추가
4. **다음 세션 인계 메모** — 완료/미완료 항목을 기존 내용에 누적 추가
5. **프롬프트 회고** — 새로운 Keep/Improve 항목을 기존 내용에 추가
6. **기타** — 새로운 내용을 기존 내용에 추가

> ⚠️ **절대 기존 내용을 삭제하거나 요약하지 말 것** — 누적 보고서이므로 이전 항목은 그대로 유지한다.

---

## 직접 병합 모드 (Antigravity 텍스트 붙여넣기)

사용자가 Antigravity에서 작성한 보고서 텍스트를 **직접 메시지로 붙여넣기**한 경우:

1. 붙여넣은 텍스트에서 요청 목록, 요청별 상세, 인계 메모 등을 파싱
2. 기존 Copilot 보고서에 병합 규칙에 따라 추가
3. 요약 섹션의 메타 정보(보고자, 에이전트, 세션ID, 건수, 산출물, 시간)를 통합 재계산

---

## 🚫 절대 금지 사항

- **실제로 수행하지 않은 작업의 기재** — 오늘 세션에서 확인된 내용만 기록
- **로컬 절대 경로 사용** — `~/...` 형태 금지, `프로젝트 - 파일명` 형식 사용
- **"정상 동작 확인"만으로 검증 결과 마무리** — 검증 방법, 범위, 결과를 구체적으로 기술
- **"확인 필요"같은 모호한 후속 조치** — 누가, 언제, 무엇을 할지 명확히 작성
- **양식 없이 임의 형식 사용** — 반드시 양식 파일을 읽고 준수
- **기존 보고서 내용 삭제/요약** — 병합 시 이전 항목은 그대로 유지

---

## ✍️ 작성 품질 기준 (Golden Example)

> **⭐ 이 섹션은 가장 중요하다.** 아래 최소 분량 기준과 황금 예시를 반드시 따라야 한다. 모델 크기에 관계없이 이 기준을 충족하면 고품질 보고서가 된다.

### 항목별 최소 분량 기준

| 항목 | 최소 기준 | 금지 |
|---|---|---|
| **요약 (Summary)** 상단 설명 | 3문장 이상, 시간순으로 오늘 핵심 작업 흐름 서술 | "작업을 수행했다" 같은 1줄 요약 |
| **1-1. 요청 배경 및 목적** | 배경/목적/해결문제 각 2문장 이상 (총 6문장+) | "요청에 따라 작업함" |
| **1-2. 프롬프트 요약** | 핵심 지시 내용 2문장+, 제공 컨텍스트 구체 나열, 반복 수정 횟수+이유 | "요청했다"로 끝남 |
| **1-3. AI 의사결정 근거** | 최소 2개 결정사항, 각각 [선택한 방법] — [이유] 형식 | 근거 없이 결과만 기술 |
| **1-4. 사용한 도구/명령어** | 테이블 2행 이상, 각 행에 도구명+목적 | 빈 테이블 |
| **1-5. 주요 작업 내역** | 번호 목록 3단계 이상, 각 단계 "무엇을 → 어떻게 → 결과" | 1줄 나열 |
| **1-7. 산출물 목록** | 수정/생성/삭제된 파일 전수 기재 | 일부 생략 |
| **1-8. 검증 결과** | 검증 방법+결과+할루시네이션 여부+수정 내역 4항목 모두 기재 | "정상 확인" 1줄 |
| **1-9. 기대 효과 및 한계** | 기대 효과 2개+, 한계 1개+ (수치/시나리오 포함) | "빨라진다" |
| **1-10. 후속 조치** | 테이블 1행 이상, 담당자+기한 명시 | "확인 필요" |
| **다음 세션 인계 메모** | 완료/미완료/주의사항/관련파일 4항목 모두 기재 | 1줄 요약 |
| **프롬프트 회고** | Keep 1개+, Improve 1개+ | 생략 |
| **기타 — 연속 개발 타임라인** | 이전 보고서에 동일 파일/기능이 실제 기재된 경우에만 작성, 없으면 항목 자체 생략 | 추정, "아마 ~했을 것이다" |

### 황금 예시 (이 패턴을 그대로 따라할 것)

아래는 실제 보고서에서 발췌한 **좋은 예시**이다. 각 항목을 이 수준으로 작성해야 한다.

#### 예시: 요약 (Summary) 상단 설명

```
> 오늘은 03-27에 초기 구현된 반송메일 분석 기능의 품질을 높이는 작업들이 집중적으로 이루어졌다.
> 오전에 Antigravity가 반송메일 프로젝트 전 과정의 종합 보고서 6종을 작성하였고,
> 오전~오후 Copilot 세션에서는 AI 호출 유틸리티를 공통 메서드(AIResponseUtil.call_GPT,
> RagServiceImpl.mail048A01)로 통합하고, 반송 분석 UI를 별도 패널 방식에서 ContentsComponent
> 인라인 자동 표시 방식으로 전면 전환하였다. 저녁에는 BounceServiceImpl 전체에 중학생도 이해하는
> 수준의 한국어 주석이 추가되었다.
```

✅ **좋은 이유**: 시간순으로 에이전트별 핵심 작업을 나열, 구체적인 클래스/메서드명 언급, 변경의 맥락("품질을 높이는 작업") 설명.

#### 예시: 1-1. 요청 배경 및 목적

```
- [배경] `BounceServiceImpl`에서 AI를 호출하는 `callBounceAI` 메서드와 RAG 등록을 처리하는
  `bounceRagRegist` 메서드가 각각 별도의 저수준 API 호출 로직을 직접 구현하고 있었다.
  프로젝트에는 이미 공통 유틸리티 메서드(`AIResponseUtil.call_GPT`, `RagServiceImpl.mail048A01`)가
  존재하였으나 반송 서비스에서는 사용하지 않고 있었다.
- [목적] 중복된 AI/RAG 호출 로직을 공통 유틸리티 메서드로 대체하여 코드 일관성을 높이고,
  유틸리티 메서드 개선 시 일괄 반영되는 구조로 전환한다.
- [해결하려는 문제] `callBounceAI`가 `AIResponseUtil.call_GPT`를 사용하지 않고 별도 HTTP 호출
  로직을 구현하여 유틸리티 개선 사항이 반영되지 않는 문제.
```

✅ **좋은 이유**: 배경에서 현재 상태("별도 구현 중")를 구체적으로 설명, 목적에서 기대 결과("일괄 반영 구조")를 명확히 기술, 해결 문제에서 무엇이 문제인지 한 문장으로 명확히 정리.

#### 예시: 1-3. AI 의사결정 근거

```
- [결정 사항 1]: `bounceRagRegist` 수정 불가 판단 후 즉시 재확인 — 처음에는 `bounceRagRegist`가
  호출하는 API(`/05` RAG 등록)와 `AIResponseUtil.call_GPT`가 호출하는 API(`/oai001A04` GPT 채팅)가
  다르므로 수정 불가로 판단했으나, 사용자가 `RagServiceImpl.mail048A01`을 제시하여 해당 메서드
  시그니처 확인 후 통합 가능함을 재확인. 이후 즉시 수정 진행.
- [결정 사항 2]: `callBounceAI`에서 `AIResponseUtil` import 추가 및 기존 저수준 HTTP 호출 코드를
  단일 메서드 호출로 교체 — 기존 로직의 파라미터(requestInfo, prompt, systemPrompt)를 그대로
  유지하여 호출 인터페이스 변경 없이 내부 구현만 교체.
```

✅ **좋은 이유**: 각 결정에 대해 "무엇을 선택했고 왜 그렇게 했는지"가 명확. 초기 판단 오류도 솔직히 기록하여 의사결정 과정이 투명.

#### 예시: 1-5. 주요 작업 내역

```
1. **현행 코드 분석**: `callBounceAI`의 기존 HTTP 호출 방식과 `AIResponseUtil.call_GPT` 시그니처 대조 → import 추가 및 메서드 교체 설계
2. **callBounceAI 수정**: `AIResponseUtil` import 추가 → 기존 저수준 호출 코드를 `AIResponseUtil.call_GPT(requestInfo, prompt, systemPrompt)` 단일 호출로 교체
3. **bounceRagRegist 수정 가능성 검토**: RAG API 엔드포인트 차이로 초기 불가 판단 → 사용자 제시 `mail048A01` 확인 후 `mailSeq`, `ragId`, `category` 파라미터 매핑하여 수정 완료
4. **컴파일 검증**: `get_errors`로 import 및 메서드 시그니처 오류 없음 확인
```

✅ **좋은 이유**: 각 단계마다 "무엇을 → 어떻게 → 결과"가 모두 포함. 단순 나열이 아닌 흐름이 보이는 구조.

#### 예시: 기타 — 연속 개발 타임라인

```
- **반송메일 기능 연속 개발 타임라인**: 03-27(설계+초기구현) → 03-30(AI 유틸 통합, UI 전환, 주석) 순으로 연속 개발됨.
```

✅ **좋은 이유**: 이전 보고서를 읽어서 동일 기능의 작업 흐름을 날짜별로 추적. 보고받는 사람이 전체 개발 맥락을 한눈에 파악 가능.

---

## 📋 체크리스트 (작성 완료 전 확인)

- [ ] 양식 파일(`~/.ai-report/.data/업무보고서_양식.md`) 읽음
- [ ] 통합 파서 실행 (`python3 ~/.ai-report/parse_sessions.py --date {날짜}`)
- [ ] **이전 보고서 확인 완료** (최근 5일분, 연속 개발 타임라인 추출)
- [ ] Copilot 세션 데이터 확인 완료
- [ ] Antigravity 세션 데이터 확인 완료 (brain 아티팩트 또는 사용자 붙여넣기)
- [ ] Cursor 세션 데이터 확인 완료 (agent-transcripts JSONL)
- [ ] GPT Codex 세션 데이터 확인 완료 (Responses API JSONL)
- [ ] Claude Code 세션 데이터 확인 완료 (session JSONL)
- [ ] 요청 건수 === 요청별 상세 블록 수
- [ ] 모든 파일 경로가 `프로젝트 - 파일명` 형식
- [ ] 1-1(배경/목적) 각 항목 2문장 이상
- [ ] 1-3(의사결정 근거) 최소 2개 이상 기술
- [ ] 1-5(주요 작업 내역) 3단계 이상, 각 단계 "무엇을 → 어떻게 → 결과"
- [ ] 1-8(검증 결과) "정상 동작 확인" 한 줄로 끝내지 않음
- [ ] 1-9(기대 효과) 수치/시나리오 포함
- [ ] 1-10(후속 조치) 담당자 + 기한 명시
- [ ] 다음 세션 인계 메모 4항목 (완료/미완료/주의사항/관련파일) 모두 작성
- [ ] 프롬프트 회고 (Keep + Improve) 작성 완료
- [ ] **기타 — 연속 개발 타임라인**: 이전 보고서에 동일 파일/기능이 실제로 기재된 경우에만 작성 (없으면 생략)
- [ ] **황금 예시 수준의 품질 확인** (위 "작성 품질 기준" 최소 분량 충족 여부)
- [ ] 파일 저장 완료

---

## 주의사항

- **절대 요약 금지**: 요청 항목, 산출물, 도구 사용 내역 등은 절대 생략 없이 전체 기록
- **파일 수정 시 포맷 유지**: 기존 파일에 추가할 때 들여쓰기/줄바꿈 스타일 그대로 유지
- **세션 ID 기록**: 보고서 헤더의 세션/대화 ID에 실제 session_id를 모두 기록 (Copilot, Antigravity, Cursor, GPT Codex, Claude Code 구분 표기)
- **시간 표기**: KST 기준으로 표기
- **미완료 항목 처리**: turns에서 오류가 발생했거나 해결되지 않은 항목도 보고서에 포함하고 상태를 "❌ 미완료" 또는 "⚠️ 진행 중"으로 표기
- **파서 스크립트 오류 시**: 직접 `~/.copilot/jb/`, `~/Library/Application Support/Code/User/workspaceStorage/*/chatSessions/`, `~/.gemini/antigravity/brain/`, `~/.cursor/projects/`, `~/.codex/sessions/`, `~/.claude/projects/` 하위를 순회하여 해당 날짜의 파일을 읽고 동일한 방식으로 파싱

