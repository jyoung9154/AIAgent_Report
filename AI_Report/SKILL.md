---
name: AI업무보고
description: "'/AI업무보고 오늘자 보고서 작성해줘' 요청 시 Copilot+Antigravity+Cursor+GPT Codex+Claude Code 세션 히스토리를 통합 파싱하여 AI 업무보고서를 자동 생성/병합하는 스킬입니다."
---

# AI업무보고 (통합 스킬)

> **이 파일은 포인터 파일입니다. 실제 스킬 정의는 아래 절대경로를 참조하세요.**

## 통합 스킬 파일 위치

```
~/.ai-report/SKILL.md
```

이 스킬이 트리거되면 반드시 위 파일(`~/.ai-report/SKILL.md`)을 `read_file`로 읽고 그 내용의 절차를 따를 것.

## 통합 파서 스크립트

```bash
python3 ~/.ai-report/parse_sessions.py --date {날짜} --summary
python3 ~/.ai-report/parse_sessions.py --date {날짜}
python3 ~/.ai-report/parse_sessions.py --date {날짜} --source copilot
python3 ~/.ai-report/parse_sessions.py --date {날짜} --source vscode
python3 ~/.ai-report/parse_sessions.py --date {날짜} --source antigravity
python3 ~/.ai-report/parse_sessions.py --date {날짜} --source cursor
python3 ~/.ai-report/parse_sessions.py --date {날짜} --source codex
python3 ~/.ai-report/parse_sessions.py --date {날짜} --source claude
```

## 양식 파일

```
~/.ai-report/.data/업무보고서_양식.md
```

## 빠른 실행 요약

1. `read_file ~/.ai-report/SKILL.md` — 통합 스킬 전체 절차 확인
2. `read_file ~/.ai-report/.data/업무보고서_양식.md` — 양식 파일 확인
3. `run_in_terminal: python3 ~/.ai-report/parse_sessions.py --date {날짜} --summary` — 요약 파싱
4. `run_in_terminal: python3 ~/.ai-report/parse_sessions.py --date {날짜}` — 상세 파싱
5. 보고서 작성 및 저장
