#!/usr/bin/env python3
"""
통합 AI 업무보고 세션 파서
GitHub Copilot JetBrains (JSONL) + GitHub Copilot VSCode (JSONL)
+ Antigravity (brain artifacts) + Cursor (agent-transcripts JSONL)
+ GPT Codex (Responses API JSONL) + Claude Code (session JSONL) 세션을 모두 파싱하여
업무보고서 작성에 필요한 구조화된 데이터를 JSON으로 출력한다.

Usage:
    python3 parse_sessions.py                              # 오늘 날짜, 전체 에이전트
    python3 parse_sessions.py --date 2026-03-31            # 특정 날짜
    python3 parse_sessions.py --source copilot             # Copilot (JetBrains)만
    python3 parse_sessions.py --source vscode              # Copilot (VSCode)만
    python3 parse_sessions.py --source antigravity         # Antigravity만
    python3 parse_sessions.py --source cursor              # Cursor만
    python3 parse_sessions.py --source codex               # GPT Codex만
    python3 parse_sessions.py --source claude              # Claude Code만
    python3 parse_sessions.py --verbose                    # 전체 응답 포함
    python3 parse_sessions.py --summary                    # 요약만
    python3 parse_sessions.py --discover                   # 에이전트 데이터 구조 탐색
"""

import os
import sys
import json
import glob
import re
import argparse
import urllib.parse
from datetime import datetime, timezone, timedelta
from pathlib import Path

# UTC+9 (KST)
KST = timezone(timedelta(hours=9))

# ─────────────────────────────────────────────
# 공통 유틸리티
# ─────────────────────────────────────────────

def utc_to_kst(ts_str: str) -> str:
    """ISO 8601 UTC 타임스탬프를 KST 로컬 시간 문자열로 변환"""
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        kst_dt = dt.astimezone(KST)
        return kst_dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return ts_str[:19] if ts_str else ""


def utc_to_kst_date(ts_str: str) -> str:
    """ISO 8601 UTC 타임스탬프에서 KST 날짜(YYYY-MM-DD)만 추출"""
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        kst_dt = dt.astimezone(KST)
        return kst_dt.strftime("%Y-%m-%d")
    except Exception:
        return ts_str[:10] if ts_str else ""


# ─────────────────────────────────────────────
# GitHub Copilot JSONL 파서
# ─────────────────────────────────────────────

def extract_text_from_content(content) -> str:
    """assistant.message content 필드에서 텍스트 추출 (list/str 모두 처리)"""
    if isinstance(content, str):
        try:
            parsed = json.loads(content)
            if isinstance(parsed, list):
                texts = []
                for item in parsed:
                    if item.get("role") == "assistant":
                        text = item.get("content", "")
                        if isinstance(text, str) and text.strip():
                            texts.append(text.strip())
                return "\n".join(texts)
        except Exception:
            pass
        return content.strip()
    elif isinstance(content, list):
        texts = []
        for item in content:
            if isinstance(item, dict) and item.get("role") == "assistant":
                text = item.get("content", "")
                if isinstance(text, str) and text.strip():
                    texts.append(text.strip())
        return "\n".join(texts)
    return str(content)


def parse_copilot_session(session_dir: str, target_date: str, verbose: bool = False) -> dict | None:
    """Copilot 세션 디렉토리를 파싱하여 구조화된 dict 반환"""
    session_id = os.path.basename(session_dir)
    partitions = sorted(glob.glob(os.path.join(session_dir, "partition-*.jsonl")))
    if not partitions:
        return None

    # 첫 번째 파티션의 첫 줄에서 날짜 확인
    try:
        with open(partitions[0], encoding="utf-8") as fp:
            first_line = fp.readline().strip()
            if not first_line:
                return None
            first_obj = json.loads(first_line)
            ts = first_obj.get("timestamp", "")
            ts_date = utc_to_kst_date(ts)
            if ts_date != target_date:
                return None
    except Exception:
        return None

    # 모든 파티션 이벤트 수집
    events = []
    for partition_file in partitions:
        try:
            with open(partition_file, encoding="utf-8") as fp:
                for line in fp:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        events.append(json.loads(line))
                    except Exception:
                        pass
        except Exception:
            pass

    # 이벤트를 턴(Turn) 단위로 그룹핑
    turns = []
    current_user_msg = None
    tool_calls_in_turn = []
    files_modified = []

    for ev in events:
        ev_type = ev.get("type", "")
        data = ev.get("data", {})
        ts_kst = utc_to_kst(ev.get("timestamp", ""))

        if ev_type == "user.message":
            current_user_msg = {
                "timestamp": ts_kst,
                "content": data.get("content", ""),
                "turn_id": data.get("turnId", ""),
            }
            tool_calls_in_turn = []
            files_modified = []

        elif ev_type == "tool.execution_start":
            tool_name = data.get("toolName", "") or data.get("name", "")
            tool_args = data.get("arguments", data.get("input", {}))
            tool_calls_in_turn.append({
                "tool": tool_name,
                "args": tool_args,
            })
            FILE_WRITE_TOOLS = (
                "replace_string_in_file",
                "insert_edit_into_file",
                "create_file",
            )
            if tool_name in FILE_WRITE_TOOLS:
                fp_val = ""
                if isinstance(tool_args, dict):
                    fp_val = (tool_args.get("filePath", "")
                              or tool_args.get("file_path", ""))
                if fp_val:
                    files_modified.append({"tool": tool_name, "file": fp_val})

        elif ev_type == "assistant.message":
            content = data.get("content", "")
            text = extract_text_from_content(content)

            if current_user_msg:
                turns.append({
                    "user_timestamp": current_user_msg["timestamp"],
                    "user_message": current_user_msg["content"],
                    "assistant_response": text if verbose else text[:500],
                    "tools_used": list({t["tool"] for t in tool_calls_in_turn if t.get("tool")}),
                    "files_modified": list({f["file"] for f in files_modified}),
                })
                current_user_msg = None
                tool_calls_in_turn = []
                files_modified = []

    if not turns:
        return None

    all_files = []
    all_tools = []
    for t in turns:
        all_files.extend(t["files_modified"])
        all_tools.extend(t["tools_used"])

    return {
        "agent": "copilot",
        "agent_label": "GitHub Copilot",
        "ide": "JetBrains-IC",
        "session_id": session_id,
        "date": target_date,
        "start_time": turns[0]["user_timestamp"] if turns else "",
        "end_time": turns[-1]["user_timestamp"] if turns else "",
        "turn_count": len(turns),
        "files_modified": list(dict.fromkeys(all_files)),
        "tools_used": list(dict.fromkeys(all_tools)),
        "turns": turns,
    }


def find_copilot_sessions(target_date: str, verbose: bool = False) -> list:
    """Copilot 세션 파싱"""
    jb_dir = os.path.expanduser("~/.copilot/jb")
    if not os.path.isdir(jb_dir):
        return []

    results = []
    for entry in os.listdir(jb_dir):
        session_dir = os.path.join(jb_dir, entry)
        if not os.path.isdir(session_dir):
            continue
        parsed = parse_copilot_session(session_dir, target_date, verbose=verbose)
        if parsed:
            results.append(parsed)

    results.sort(key=lambda x: x["start_time"])
    return results


# ─────────────────────────────────────────────
# GitHub Copilot (VSCode) JSONL 파서
# ─────────────────────────────────────────────

def _get_vscode_workspace_storage_dir() -> str:
    """VSCode workspaceStorage 경로 반환 (macOS / Linux)"""
    import sys
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/Application Support/Code/User/workspaceStorage")
    else:
        return os.path.expanduser("~/.config/Code/User/workspaceStorage")


def parse_vscode_copilot_session(jsonl_path: str, target_date: str, verbose: bool = False) -> dict | None:
    """VSCode Copilot 단일 JSONL 파일을 파싱하여 구조화된 dict 반환.
    JetBrains Copilot과 동일한 이벤트 형식(user.message, assistant.message, tool.execution_start)을 사용."""
    session_id = os.path.splitext(os.path.basename(jsonl_path))[0]

    try:
        with open(jsonl_path, encoding="utf-8") as fp:
            first_line = fp.readline().strip()
            if not first_line:
                return None
            first_obj = json.loads(first_line)
            ts = first_obj.get("timestamp", "")
            if not ts:
                return None
            ts_date = utc_to_kst_date(ts)
            if ts_date != target_date:
                return None
    except Exception:
        return None

    # 전체 이벤트 수집
    events = []
    try:
        with open(jsonl_path, encoding="utf-8") as fp:
            for line in fp:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except Exception:
                    pass
    except Exception:
        return None

    # 턴 그룹핑 (JetBrains 파서와 동일 로직)
    turns = []
    current_user_msg = None
    tool_calls_in_turn = []
    files_modified = []

    for ev in events:
        ev_type = ev.get("type", "")
        data = ev.get("data", {})
        ts_kst = utc_to_kst(ev.get("timestamp", ""))

        if ev_type == "user.message":
            current_user_msg = {
                "timestamp": ts_kst,
                "content": data.get("content", ""),
                "turn_id": data.get("turnId", ""),
            }
            tool_calls_in_turn = []
            files_modified = []

        elif ev_type == "tool.execution_start":
            tool_name = data.get("toolName", "") or data.get("name", "")
            tool_args = data.get("arguments", data.get("input", {}))
            tool_calls_in_turn.append({"tool": tool_name, "args": tool_args})
            FILE_WRITE_TOOLS = (
                "replace_string_in_file", "insert_edit_into_file", "create_file",
            )
            if tool_name in FILE_WRITE_TOOLS:
                fp_val = ""
                if isinstance(tool_args, dict):
                    fp_val = tool_args.get("filePath", "") or tool_args.get("file_path", "")
                if fp_val:
                    files_modified.append({"tool": tool_name, "file": fp_val})

        elif ev_type == "assistant.message":
            content = data.get("content", "")
            text = extract_text_from_content(content)

            if current_user_msg:
                turns.append({
                    "user_timestamp": current_user_msg["timestamp"],
                    "user_message": current_user_msg["content"],
                    "assistant_response": text if verbose else text[:500],
                    "tools_used": list({t["tool"] for t in tool_calls_in_turn if t.get("tool")}),
                    "files_modified": list({f["file"] for f in files_modified}),
                })
                current_user_msg = None
                tool_calls_in_turn = []
                files_modified = []

    if not turns:
        return None

    all_files = []
    all_tools = []
    for t in turns:
        all_files.extend(t["files_modified"])
        all_tools.extend(t["tools_used"])

    return {
        "agent": "vscode_copilot",
        "agent_label": "GitHub Copilot (VSCode)",
        "ide": "VSCode",
        "session_id": session_id,
        "date": target_date,
        "start_time": turns[0]["user_timestamp"] if turns else "",
        "end_time": turns[-1]["user_timestamp"] if turns else "",
        "turn_count": len(turns),
        "files_modified": list(dict.fromkeys(all_files)),
        "tools_used": list(dict.fromkeys(all_tools)),
        "turns": turns,
    }


def find_vscode_copilot_sessions(target_date: str, verbose: bool = False) -> list:
    """VSCode Copilot chatSessions 파싱"""
    ws_dir = _get_vscode_workspace_storage_dir()
    if not os.path.isdir(ws_dir):
        return []

    results = []
    for ws_hash in os.listdir(ws_dir):
        chat_dir = os.path.join(ws_dir, ws_hash, "chatSessions")
        if not os.path.isdir(chat_dir):
            continue
        for fname in os.listdir(chat_dir):
            if not fname.endswith(".jsonl"):
                continue
            jsonl_path = os.path.join(chat_dir, fname)
            parsed = parse_vscode_copilot_session(jsonl_path, target_date, verbose=verbose)
            if parsed:
                results.append(parsed)

    results.sort(key=lambda x: x["start_time"])
    return results


# ─────────────────────────────────────────────
# Antigravity Brain Artifacts 파서
# ─────────────────────────────────────────────

def parse_antigravity_session(session_dir: str, target_date: str, verbose: bool = False) -> dict | None:
    """
    Antigravity brain 세션 디렉토리를 파싱.
    metadata.json 파일의 updatedAt 필드로 날짜 필터링.
    walkthrough.md, task.md, implementation_plan.md 아티팩트에서 정보 추출.
    """
    session_id = os.path.basename(session_dir)

    # metadata.json 파일 수집
    metadata_files = glob.glob(os.path.join(session_dir, "*.metadata.json"))
    if not metadata_files:
        return None

    # 이 세션의 아티팩트 중 target_date에 업데이트된 것이 있는지 확인
    has_today_activity = False
    artifacts = []
    earliest_time = None
    latest_time = None

    for mf in metadata_files:
        try:
            with open(mf, encoding="utf-8") as fp:
                meta = json.load(fp)
        except Exception:
            continue

        updated_at = meta.get("updatedAt", "")
        updated_date = utc_to_kst_date(updated_at)
        updated_time = utc_to_kst(updated_at)

        if updated_date != target_date:
            continue

        has_today_activity = True

        # 시간 범위 추적
        if earliest_time is None or updated_time < earliest_time:
            earliest_time = updated_time
        if latest_time is None or updated_time > latest_time:
            latest_time = updated_time

        # 대응하는 아티팩트 파일 읽기
        artifact_file = mf.replace(".metadata.json", "")
        artifact_name = os.path.basename(artifact_file)
        # URL 인코딩된 한글 파일명 디코딩
        decoded_name = urllib.parse.unquote(artifact_name)

        content = ""
        if os.path.isfile(artifact_file):
            try:
                with open(artifact_file, encoding="utf-8") as fp:
                    content = fp.read()
            except Exception:
                pass

        artifacts.append({
            "name": decoded_name,
            "type": meta.get("artifactType", ""),
            "summary": meta.get("summary", ""),
            "updated_at": updated_time,
            "content": content if verbose else content[:500],
            "version": meta.get("version", ""),
        })

    if not has_today_activity:
        return None

    # 핵심 아티팩트 추출 (walkthrough, task, implementation_plan)
    walkthrough = ""
    task = ""
    impl_plan = ""
    files_mentioned = []

    for art in artifacts:
        name_lower = art["name"].lower()
        if name_lower == "walkthrough.md":
            walkthrough = art.get("content", "")
        elif name_lower == "task.md":
            task = art.get("content", "")
        elif name_lower == "implementation_plan.md":
            impl_plan = art.get("content", "")

    # 아티팩트 내용에서 파일 경로 추출 (file:// 링크)
    all_content = walkthrough + task + impl_plan
    file_links = re.findall(r'file:///[^\s\)]+', all_content)
    for fl in file_links:
        path = fl.replace("file://", "")
        files_mentioned.append(path)

    # turns 구성 — Antigravity는 대화 로그가 protobuf라 직접 파싱 불가
    # 아티팩트 기반으로 pseudo-turn 생성
    turns = []
    for art in artifacts:
        artifact_type_map = {
            "ARTIFACT_TYPE_WALKTHROUGH": "walkthrough",
            "ARTIFACT_TYPE_TASK": "task",
            "ARTIFACT_TYPE_IMPLEMENTATION_PLAN": "implementation_plan",
            "ARTIFACT_TYPE_OTHER": "other",
        }
        turns.append({
            "user_timestamp": art["updated_at"],
            "user_message": f"[Antigravity Artifact] {art['name']}",
            "assistant_response": art["summary"],
            "artifact_type": artifact_type_map.get(art["type"], art["type"]),
            "artifact_content": art["content"],
            "tools_used": [],
            "files_modified": [],
        })

    # 도구 사용 추론 (walkthrough/implementation_plan 내용 기반)
    tools_inferred = []
    if "수정" in all_content or "Modify" in all_content:
        tools_inferred.append("replace_file_content")
    if "view_file" in all_content or "view_file" in all_content.lower():
        tools_inferred.append("view_file")
    if "run_command" in all_content or "grep" in all_content:
        tools_inferred.append("run_command")

    return {
        "agent": "antigravity",
        "agent_label": "Antigravity (Gemini)",
        "ide": "Antigravity",
        "session_id": session_id,
        "date": target_date,
        "start_time": earliest_time or "",
        "end_time": latest_time or "",
        "turn_count": len(turns),
        "files_modified": list(dict.fromkeys(files_mentioned)),
        "tools_used": tools_inferred,
        "turns": turns,
        "artifacts": artifacts,
        "walkthrough": walkthrough,
        "task": task,
        "implementation_plan": impl_plan,
    }


def find_antigravity_sessions(target_date: str, verbose: bool = False) -> list:
    """Antigravity brain 세션 파싱"""
    brain_dir = os.path.expanduser("~/.gemini/antigravity/brain")
    if not os.path.isdir(brain_dir):
        return []

    results = []
    for entry in os.listdir(brain_dir):
        session_dir = os.path.join(brain_dir, entry)
        if not os.path.isdir(session_dir):
            continue
        # 숨김 디렉토리나 temp 제외
        if entry.startswith(".") or entry.startswith("temp"):
            continue
        parsed = parse_antigravity_session(session_dir, target_date, verbose=verbose)
        if parsed:
            results.append(parsed)

    results.sort(key=lambda x: x["start_time"])
    return results


# ─────────────────────────────────────────────
# Cursor Agent Transcripts 파서
# ─────────────────────────────────────────────

def _extract_cursor_text(content_items) -> str:
    """Cursor content items 리스트에서 텍스트 추출"""
    if isinstance(content_items, str):
        return content_items.strip()
    texts = []
    if isinstance(content_items, list):
        for item in content_items:
            if isinstance(item, dict) and item.get("type") == "text":
                texts.append(item.get("text", ""))
    return "\n".join(texts).strip()


def _clean_cursor_user_message(text: str) -> str:
    """Cursor user 메시지에서 메타 태그 제거"""
    # <manually_attached_skills>...</manually_attached_skills> 블록 제거
    text = re.sub(r'<manually_attached_skills>.*?</manually_attached_skills>\s*',
                  '', text, flags=re.DOTALL).strip()
    # <user_query>...</user_query> 래핑 제거
    m = re.search(r'<user_query>\s*(.*?)\s*</user_query>', text, re.DOTALL)
    if m:
        text = m.group(1).strip()
    # @ 파일 참조 앞의 경로 정리 (Cursor는 @path/file.java 형태로 파일 참조)
    return text


def _extract_file_refs_from_text(text: str) -> list:
    """assistant 응답 텍스트에서 파일 경로 참조를 추출"""
    file_exts = r'\.(java|js|jsx|ts|tsx|xml|yml|yaml|py|md|json|css|html|properties|gradle|sql)'
    refs = []
    # 백틱 내 파일 경로: `path/to/File.java`
    for m in re.finditer(r'`([^`\n]*?' + file_exts + r')`', text):
        refs.append(m.group(1))
    # 마크다운 링크 내 파일 경로: [text](/path/to/file.java)
    for m in re.finditer(r'\]\((/[^\)]*?' + file_exts + r')\)', text):
        refs.append(m.group(1))
    return list(dict.fromkeys(refs))  # 중복 제거, 순서 유지


def parse_cursor_session(jsonl_file: str, target_date: str, project_name: str,
                         session_id: str, verbose: bool = False) -> dict | None:
    """
    Cursor agent-transcripts JSONL 파일을 파싱.
    Cursor JSONL은 이벤트 내에 타임스탬프가 없으므로 파일의 mtime/birthtime으로 날짜 판별.
    구조: 한 줄 = {role: "user"|"assistant", message: {content: [{type: "text", text: "..."}]}}
    한 user 메시지에 여러 assistant 이벤트가 연속될 수 있으므로 병합 처리.
    """
    try:
        stat = os.stat(jsonl_file)
        file_dt = datetime.fromtimestamp(stat.st_mtime, tz=KST)
        file_date = file_dt.strftime("%Y-%m-%d")
        file_time = file_dt.strftime("%Y-%m-%d %H:%M:%S")

        # macOS에서 생성시간은 st_birthtime, 없으면 mtime 사용
        birthtime = getattr(stat, "st_birthtime", stat.st_mtime)
        birth_dt = datetime.fromtimestamp(birthtime, tz=KST)
        birth_date = birth_dt.strftime("%Y-%m-%d")
        start_time = birth_dt.strftime("%Y-%m-%d %H:%M:%S")

        # 파일 수정일(mtime) 또는 생성일(birthtime) 기준으로 날짜 필터링
        if file_date != target_date and birth_date != target_date:
            return None
    except Exception:
        return None

    # JSONL 파싱
    events = []
    with open(jsonl_file, encoding="utf-8") as fp:
        for line in fp:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except Exception:
                pass

    if not events:
        return None

    # 턴(Turn) 구성 — user → assistant(N개 연속) 쌍으로 그룹핑
    turns = []
    current_user = None
    current_assistant_parts = []

    def _flush_turn():
        """현재 축적된 user+assistant 쌍을 turn으로 저장"""
        nonlocal current_user, current_assistant_parts
        if current_user is not None and current_assistant_parts:
            full_assistant = "\n".join(current_assistant_parts).strip()
            file_refs = _extract_file_refs_from_text(full_assistant)
            turns.append({
                "user_timestamp": start_time if not turns else file_time,
                "user_message": current_user,
                "assistant_response": full_assistant if verbose else full_assistant[:500],
                "tools_used": [],
                "files_modified": file_refs,
            })
        current_user = None
        current_assistant_parts = []

    for ev in events:
        role = ev.get("role", "")
        content_items = ev.get("message", {}).get("content", [])

        if role == "user":
            # 이전 턴 flush
            _flush_turn()
            raw = _extract_cursor_text(content_items)
            current_user = _clean_cursor_user_message(raw)
            current_assistant_parts = []

        elif role == "assistant":
            text = _extract_cursor_text(content_items)
            if text:
                if current_user is not None:
                    # 현재 user에 대한 assistant 응답 축적
                    current_assistant_parts.append(text)
                elif turns:
                    # user 없이 assistant만 온 경우 → 이전 턴에 append
                    prev = turns[-1]
                    prev_full = prev["assistant_response"] + "\n" + text
                    prev["assistant_response"] = prev_full if verbose else prev_full[:500]
                    prev["files_modified"] = _extract_file_refs_from_text(prev_full)

    # 마지막 턴 flush
    _flush_turn()

    if not turns:
        return None

    all_files = []
    for t in turns:
        all_files.extend(t["files_modified"])

    return {
        "agent": "cursor",
        "agent_label": "Cursor",
        "ide": "Cursor",
        "session_id": session_id,
        "project": project_name,
        "date": target_date,
        "start_time": start_time,
        "end_time": file_time,
        "turn_count": len(turns),
        "files_modified": list(dict.fromkeys(all_files)),
        "tools_used": [],
        "turns": turns,
    }


def find_cursor_sessions(target_date: str, verbose: bool = False) -> list:
    """Cursor agent-transcripts 세션 파싱.
    경로 패턴: ~/.cursor/projects/{project_folder}/agent-transcripts/{session_id}/{session_id}.jsonl
    project_folder는 경로를 '-'으로 인코딩한 형태 (예: Users-jaeyoung-Project-anti)
    """
    cursor_projects_dir = os.path.expanduser("~/.cursor/projects")
    if not os.path.isdir(cursor_projects_dir):
        return []

    results = []
    for proj_entry in os.listdir(cursor_projects_dir):
        proj_path = os.path.join(cursor_projects_dir, proj_entry)
        transcripts_dir = os.path.join(proj_path, "agent-transcripts")
        if not os.path.isdir(transcripts_dir):
            continue

        # 프로젝트 폴더 이름에서 실제 프로젝트명 추정
        # Users-jaeyoung-Project-anti → Project-anti
        # Users-sysypark-amaranth10-mailProject → amaranth10-mailProject
        project_name = proj_entry
        m = re.match(r'^Users-[^-]+-(.+)$', proj_entry)
        if m:
            project_name = m.group(1)

        for sess_entry in os.listdir(transcripts_dir):
            sess_dir = os.path.join(transcripts_dir, sess_entry)
            if not os.path.isdir(sess_dir):
                continue
            jsonl_file = os.path.join(sess_dir, sess_entry + ".jsonl")
            if not os.path.isfile(jsonl_file):
                continue

            parsed = parse_cursor_session(
                jsonl_file, target_date, project_name, sess_entry, verbose=verbose
            )
            if parsed:
                results.append(parsed)

    results.sort(key=lambda x: x["start_time"])
    return results


# ─────────────────────────────────────────────
# GPT Codex (Codex CLI) 파서
# ─────────────────────────────────────────────

def _codex_extract_text(payload) -> str:
    """Codex payload에서 텍스트 추출."""
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, dict):
        # user_message / event_msg payload
        text = payload.get("text", "") or payload.get("message", "") or payload.get("content", "")
        if isinstance(text, str):
            return text.strip()
        if isinstance(text, list):
            parts = []
            for item in text:
                if isinstance(item, dict):
                    t = item.get("text", "") or item.get("output", "")
                    if t:
                        parts.append(t.strip())
                elif isinstance(item, str):
                    parts.append(item.strip())
            return "\n".join(parts).strip()
    if isinstance(payload, list):
        parts = []
        for item in payload:
            if isinstance(item, dict):
                t = item.get("text", "") or item.get("output", "")
                if t:
                    parts.append(t.strip())
            elif isinstance(item, str):
                parts.append(item.strip())
        return "\n".join(parts).strip()
    return str(payload)


def parse_codex_session(jsonl_path: str, target_date: str, verbose: bool = False) -> dict | None:
    """
    GPT Codex 세션 JSONL 파일을 파싱.
    실제 구조:
      ~/.codex/sessions/YYYY/MM/DD/rollout-YYYY-MM-DDTHH-MM-SS-<uuid>.jsonl

    JSONL 각 줄: {"timestamp":"...","type":"...","payload":{...}}
    이벤트 타입:
      - session_meta: 세션 메타데이터 (id, cwd, cli_version 등)
      - user_message: 사용자 입력
      - event_msg: 에이전트 응답 및 추론
      - function_call: 도구 실행 (shell, 파일 읽기/쓰기 등)
      - token_count: 토큰 사용량 통계
    """
    fname = os.path.basename(jsonl_path)
    # rollout-YYYY-MM-DDTHH-MM-SS-<uuid>.jsonl 에서 uuid 부분을 session_id로 사용
    session_id = fname.replace("rollout-", "").replace(".jsonl", "")

    # 이벤트 파싱
    events = []
    try:
        with open(jsonl_path, encoding="utf-8") as fp:
            for line in fp:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except Exception:
                    pass
    except Exception:
        return None

    if not events:
        return None

    # 날짜 판별: timestamp 필드 사용
    def _get_ts(ev):
        ts = ev.get("timestamp", "")
        if ts:
            return utc_to_kst_date(ts), utc_to_kst(ts)
        return "", ""

    first_date, _ = _get_ts(events[0])
    if not first_date:
        # 파일명에서 날짜 추출 시도: rollout-YYYY-MM-DD...
        m = re.match(r"rollout-(\d{4}-\d{2}-\d{2})", fname)
        if m:
            first_date = m.group(1)
        else:
            return None

    if first_date != target_date:
        return None

    # session_meta에서 세션 정보 추출
    session_meta = {}
    for ev in events:
        if ev.get("type") == "session_meta":
            session_meta = ev.get("payload", {})
            break

    # 턴 구성
    turns = []
    current_user_msg = None
    tool_calls_in_turn = []
    files_modified = []

    for ev in events:
        ev_type = ev.get("type", "")
        payload = ev.get("payload", {})
        _, ts_kst = _get_ts(ev)

        if ev_type == "user_message":
            content = _codex_extract_text(payload)
            current_user_msg = {
                "timestamp": ts_kst,
                "content": content,
            }
            tool_calls_in_turn = []
            files_modified = []

        elif ev_type == "function_call":
            fn_name = ""
            fn_args = {}
            if isinstance(payload, dict):
                fn_name = payload.get("name", "") or payload.get("tool", "")
                fn_args_raw = payload.get("arguments", payload.get("args", "{}"))
                try:
                    fn_args = json.loads(fn_args_raw) if isinstance(fn_args_raw, str) else fn_args_raw
                except Exception:
                    fn_args = {"raw": fn_args_raw}
            tool_calls_in_turn.append({"tool": fn_name, "args": fn_args})

            # 파일 수정 추적
            FILE_WRITE_TOOLS = ("write", "create", "edit", "patch", "apply_diff",
                                "replace_string_in_file", "insert_edit_into_file", "create_file",
                                "write_to_file", "exec_command")
            if fn_name in FILE_WRITE_TOOLS:
                fp_val = ""
                if isinstance(fn_args, dict):
                    fp_val = (fn_args.get("file_path", "") or fn_args.get("filePath", "")
                              or fn_args.get("path", "") or fn_args.get("filename", ""))
                if fp_val:
                    files_modified.append(fp_val)

        elif ev_type == "event_msg":
            # 에이전트 응답 — 턴 완료
            content = _codex_extract_text(payload)
            if current_user_msg:
                turns.append({
                    "user_timestamp": current_user_msg["timestamp"],
                    "user_message": current_user_msg["content"],
                    "assistant_response": content if verbose else content[:500],
                    "tools_used": list({t["tool"] for t in tool_calls_in_turn if t.get("tool")}),
                    "files_modified": list(dict.fromkeys(files_modified)),
                })
                current_user_msg = None
                tool_calls_in_turn = []
                files_modified = []

    # flush: user_message 후 event_msg 없이 끝난 경우
    if current_user_msg and tool_calls_in_turn:
        turns.append({
            "user_timestamp": current_user_msg["timestamp"],
            "user_message": current_user_msg["content"],
            "assistant_response": "",
            "tools_used": list({t["tool"] for t in tool_calls_in_turn if t.get("tool")}),
            "files_modified": list(dict.fromkeys(files_modified)),
        })

    if not turns:
        return None

    all_files = []
    all_tools = []
    for t in turns:
        all_files.extend(t["files_modified"])
        all_tools.extend(t["tools_used"])

    return {
        "agent": "codex",
        "agent_label": "GPT Codex",
        "ide": "Terminal (Codex CLI)",
        "session_id": session_id,
        "date": target_date,
        "start_time": turns[0]["user_timestamp"] if turns else "",
        "end_time": turns[-1]["user_timestamp"] if turns else "",
        "turn_count": len(turns),
        "files_modified": list(dict.fromkeys(all_files)),
        "tools_used": list(dict.fromkeys(all_tools)),
        "turns": turns,
        "cwd": session_meta.get("cwd", ""),
        "cli_version": session_meta.get("cli_version", ""),
    }


def find_codex_sessions(target_date: str, verbose: bool = False) -> list:
    """GPT Codex 세션 파싱.
    경로: ~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl
    날짜 디렉토리 구조를 따라 target_date에 해당하는 폴더를 직접 탐색한다.
    """
    sessions_base = os.path.expanduser("~/.codex/sessions")
    if not os.path.isdir(sessions_base):
        return []

    # target_date = "YYYY-MM-DD" → YYYY/MM/DD 디렉토리
    parts = target_date.split("-")
    if len(parts) != 3:
        return []

    date_dir = os.path.join(sessions_base, parts[0], parts[1], parts[2])

    results = []
    if os.path.isdir(date_dir):
        for fname in os.listdir(date_dir):
            if not fname.endswith(".jsonl"):
                continue
            jsonl_path = os.path.join(date_dir, fname)
            parsed = parse_codex_session(jsonl_path, target_date, verbose=verbose)
            if parsed:
                results.append(parsed)

    results.sort(key=lambda x: x["start_time"])
    return results


# ─────────────────────────────────────────────
# Claude Code 세션 파서
# ─────────────────────────────────────────────

def parse_claude_session(jsonl_file: str, target_date: str, project_name: str,
                         session_id: str, verbose: bool = False) -> dict | None:
    """
    Claude Code 세션 JSONL 파일을 파싱.
    경로: ~/.claude/projects/{project-hash}/sessions/{session_id}.jsonl

    JSONL 형식 (Claude Code 공식):
      {"type":"summary","summary":"이전 대화 요약","timestamp":"2026-04-02T01:00:00.000Z"}
      {"type":"human","message":{"role":"human","content":"요청 내용"},"timestamp":"2026-04-02T01:01:00.000Z"}
      {"type":"assistant","message":{"role":"assistant","content":[{"type":"text","text":"응답"},{"type":"tool_use","id":"xxx","name":"Read","input":{"file_path":"/path"}}]},"timestamp":"..."}
      {"type":"tool_result","tool_use_id":"xxx","content":"결과 내용","timestamp":"..."}
    """
    # 날짜 필터링: 파일 mtime 또는 내부 timestamp 기반
    try:
        stat = os.stat(jsonl_file)
        file_dt = datetime.fromtimestamp(stat.st_mtime, tz=KST)
        file_date = file_dt.strftime("%Y-%m-%d")
        file_time = file_dt.strftime("%Y-%m-%d %H:%M:%S")

        birthtime = getattr(stat, "st_birthtime", stat.st_mtime)
        birth_dt = datetime.fromtimestamp(birthtime, tz=KST)
        birth_date = birth_dt.strftime("%Y-%m-%d")
        start_time = birth_dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return None

    # 이벤트 파싱
    events = []
    try:
        with open(jsonl_file, encoding="utf-8") as fp:
            for line in fp:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except Exception:
                    pass
    except Exception:
        return None

    if not events:
        return None

    # 이벤트 내 timestamp로 날짜 확인
    has_target_date = False
    for ev in events:
        ts = ev.get("timestamp", "")
        if ts and utc_to_kst_date(ts) == target_date:
            has_target_date = True
            break

    # 이벤트 내 timestamp가 없으면 파일 날짜로 폴백
    if not has_target_date:
        if file_date != target_date and birth_date != target_date:
            return None

    # 턴 구성 — human → assistant(+tool_use) → tool_result 쌍
    turns = []
    current_human = None
    current_assistant_parts = []
    current_tools = []
    current_files = []

    def _flush_claude_turn():
        nonlocal current_human, current_assistant_parts, current_tools, current_files
        if current_human is not None and current_assistant_parts:
            full_assistant = "\n".join(current_assistant_parts).strip()
            turns.append({
                "user_timestamp": current_human.get("timestamp", start_time),
                "user_message": current_human.get("content", ""),
                "assistant_response": full_assistant if verbose else full_assistant[:500],
                "tools_used": list(dict.fromkeys(current_tools)),
                "files_modified": list(dict.fromkeys(current_files)),
            })
        current_human = None
        current_assistant_parts = []
        current_tools = []
        current_files = []

    for ev in events:
        ev_type = ev.get("type", "")
        ts = ev.get("timestamp", "")
        ts_kst = utc_to_kst(ts) if ts else ""

        if ev_type == "human":
            _flush_claude_turn()
            msg = ev.get("message", {})
            content = msg.get("content", "")
            if isinstance(content, list):
                content = "\n".join(
                    item.get("text", "") for item in content
                    if isinstance(item, dict) and item.get("type") == "text"
                ).strip()
            current_human = {
                "timestamp": ts_kst or start_time,
                "content": content if isinstance(content, str) else str(content),
            }
            current_assistant_parts = []
            current_tools = []
            current_files = []

        elif ev_type == "assistant":
            msg = ev.get("message", {})
            content = msg.get("content", [])
            if isinstance(content, str):
                current_assistant_parts.append(content.strip())
            elif isinstance(content, list):
                for item in content:
                    if not isinstance(item, dict):
                        continue
                    if item.get("type") == "text":
                        text = item.get("text", "").strip()
                        if text:
                            current_assistant_parts.append(text)
                    elif item.get("type") == "tool_use":
                        tool_name = item.get("name", "")
                        tool_input = item.get("input", {})
                        if tool_name:
                            current_tools.append(tool_name)
                        # 파일 수정 추적
                        WRITE_TOOLS = ("Write", "Edit", "MultiEdit", "write", "edit",
                                       "create_file", "replace_string_in_file",
                                       "insert_edit_into_file")
                        READ_TOOLS = ("Read", "read", "read_file", "view_file")
                        if tool_name in WRITE_TOOLS:
                            fp_val = ""
                            if isinstance(tool_input, dict):
                                fp_val = (tool_input.get("file_path", "")
                                          or tool_input.get("filePath", "")
                                          or tool_input.get("path", ""))
                            if fp_val:
                                current_files.append(fp_val)
                        if tool_name == "Bash" or tool_name == "bash":
                            current_tools.append("Bash")

        elif ev_type == "tool_result":
            # tool_result는 추가 컨텍스트용, 턴 구성에 직접 영향 없음
            pass

        elif ev_type == "summary":
            # 세션 요약, 무시
            pass

    # 마지막 턴 flush
    _flush_claude_turn()

    if not turns:
        return None

    all_files = []
    all_tools = []
    for t in turns:
        all_files.extend(t["files_modified"])
        all_tools.extend(t["tools_used"])

    # start/end 시간: 이벤트 timestamp 또는 파일 시간 폴백
    actual_start = turns[0]["user_timestamp"] if turns else start_time
    actual_end = turns[-1]["user_timestamp"] if turns else file_time

    return {
        "agent": "claude",
        "agent_label": "Claude Code",
        "ide": "Terminal (Claude Code)",
        "session_id": session_id,
        "project": project_name,
        "date": target_date,
        "start_time": actual_start,
        "end_time": actual_end,
        "turn_count": len(turns),
        "files_modified": list(dict.fromkeys(all_files)),
        "tools_used": list(dict.fromkeys(all_tools)),
        "turns": turns,
    }


def find_claude_sessions(target_date: str, verbose: bool = False) -> list:
    """Claude Code 세션 파싱.
    경로: ~/.claude/projects/{project-hash}/sessions/{session_id}.jsonl
    """
    projects_dir = os.path.expanduser("~/.claude/projects")
    if not os.path.isdir(projects_dir):
        return []

    results = []
    for proj_entry in os.listdir(projects_dir):
        proj_path = os.path.join(projects_dir, proj_entry)
        sessions_dir = os.path.join(proj_path, "sessions")
        if not os.path.isdir(sessions_dir):
            continue

        # 프로젝트 이름 추정: 해시 폴더명에서 settings.json 참조
        project_name = proj_entry
        settings_file = os.path.join(proj_path, "settings.json")
        if os.path.isfile(settings_file):
            try:
                with open(settings_file, encoding="utf-8") as fp:
                    settings = json.load(fp)
                    project_name = settings.get("projectName", proj_entry)
            except Exception:
                pass

        for sess_file in os.listdir(sessions_dir):
            if not sess_file.endswith(".jsonl"):
                continue
            jsonl_path = os.path.join(sessions_dir, sess_file)
            sess_id = sess_file.replace(".jsonl", "")

            parsed = parse_claude_session(
                jsonl_path, target_date, project_name, sess_id, verbose=verbose
            )
            if parsed:
                results.append(parsed)

    results.sort(key=lambda x: x["start_time"])
    return results


# ─────────────────────────────────────────────
# 데이터 구조 탐색 (--discover)
# ─────────────────────────────────────────────

def discover_agent_data():
    """각 에이전트의 데이터 디렉토리 구조를 탐색하여 보여준다."""
    agents = [
        {
            "name": "GitHub Copilot (JetBrains)",
            "base": "~/.copilot/jb",
            "description": "JSONL 대화 이벤트 로그 (partition-*.jsonl)",
        },
        {
            "name": "GitHub Copilot (VSCode)",
            "base": _get_vscode_workspace_storage_dir(),
            "description": "chatSessions JSONL 대화 로그 (saveConversationLog 설정 필요)",
            "raw_path": True,
        },
        {
            "name": "Antigravity (Gemini)",
            "base": "~/.gemini/antigravity/brain",
            "description": "Brain artifacts (metadata.json + walkthrough.md/task.md)",
        },
        {
            "name": "Cursor",
            "base": "~/.cursor/projects",
            "description": "agent-transcripts JSONL 대화 로그",
        },
        {
            "name": "GPT Codex",
            "base": "~/.codex/sessions",
            "description": "날짜별 디렉토리 (YYYY/MM/DD/rollout-*.jsonl)",
        },
        {
            "name": "Claude Code",
            "base": "~/.claude/projects",
            "description": "프로젝트별 세션 JSONL",
        },
    ]

    result = {"agents": []}
    for agent in agents:
        base_path = agent["base"] if agent.get("raw_path") else os.path.expanduser(agent["base"])
        info = {
            "name": agent["name"],
            "base_path": base_path,
            "description": agent["description"],
            "exists": os.path.isdir(base_path),
            "contents": [],
        }
        if info["exists"]:
            try:
                entries = sorted(os.listdir(base_path))[:10]
                for e in entries:
                    full = os.path.join(base_path, e)
                    if os.path.isdir(full):
                        sub_entries = os.listdir(full)[:5]
                        info["contents"].append({
                            "name": e + "/",
                            "children": sub_entries,
                        })
                    else:
                        info["contents"].append({"name": e})
            except Exception:
                pass
        result["agents"].append(info)

    print(json.dumps(result, ensure_ascii=False, indent=2))


# ─────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="통합 AI 업무보고 세션 파서 (Copilot + Antigravity + Cursor + GPT Codex + Claude Code)"
    )
    parser.add_argument(
        "--date",
        default=datetime.now(KST).strftime("%Y-%m-%d"),
        help="파싱 대상 날짜 (YYYY-MM-DD). 기본값: 오늘(KST)",
    )
    parser.add_argument(
        "--source",
        choices=["all", "copilot", "vscode", "antigravity", "cursor", "codex", "claude"],
        default="all",
        help="파싱 대상 에이전트 (기본: all)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="assistant 응답/아티팩트 전체 포함 (기본: 500자 요약)",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="세션 목록 요약만 출력 (turns 제외)",
    )
    parser.add_argument(
        "--discover",
        action="store_true",
        help="각 에이전트의 데이터 디렉토리 구조를 탐색하여 표시",
    )
    args = parser.parse_args()

    # --discover 모드
    if args.discover:
        discover_agent_data()
        return

    all_sessions = []

    # Copilot (JetBrains) 세션 수집
    if args.source in ("all", "copilot"):
        copilot_sessions = find_copilot_sessions(args.date, verbose=args.verbose)
        all_sessions.extend(copilot_sessions)

    # Copilot (VSCode) 세션 수집
    if args.source in ("all", "vscode"):
        vscode_sessions = find_vscode_copilot_sessions(args.date, verbose=args.verbose)
        all_sessions.extend(vscode_sessions)

    # Antigravity 세션 수집
    if args.source in ("all", "antigravity"):
        anti_sessions = find_antigravity_sessions(args.date, verbose=args.verbose)
        all_sessions.extend(anti_sessions)

    # Cursor 세션 수집
    if args.source in ("all", "cursor"):
        cursor_sessions = find_cursor_sessions(args.date, verbose=args.verbose)
        all_sessions.extend(cursor_sessions)

    # GPT Codex 세션 수집
    if args.source in ("all", "codex"):
        codex_sessions = find_codex_sessions(args.date, verbose=args.verbose)
        all_sessions.extend(codex_sessions)

    # Claude Code 세션 수집
    if args.source in ("all", "claude"):
        claude_sessions = find_claude_sessions(args.date, verbose=args.verbose)
        all_sessions.extend(claude_sessions)

    if not all_sessions:
        print(json.dumps({
            "date": args.date,
            "session_count": 0,
            "copilot_sessions": 0,
            "vscode_copilot_sessions": 0,
            "antigravity_sessions": 0,
            "cursor_sessions": 0,
            "codex_sessions": 0,
            "claude_sessions": 0,
            "sessions": [],
            "message": f"{args.date} 날짜의 AI 세션이 없습니다."
        }, ensure_ascii=False, indent=2))
        return

    # 에이전트별 카운트
    copilot_count = sum(1 for s in all_sessions if s["agent"] == "copilot")
    vscode_copilot_count = sum(1 for s in all_sessions if s["agent"] == "vscode_copilot")
    antigravity_count = sum(1 for s in all_sessions if s["agent"] == "antigravity")
    cursor_count = sum(1 for s in all_sessions if s["agent"] == "cursor")
    codex_count = sum(1 for s in all_sessions if s["agent"] == "codex")
    claude_count = sum(1 for s in all_sessions if s["agent"] == "claude")

    # 전체 수정 파일
    all_files = []
    for s in all_sessions:
        all_files.extend(s.get("files_modified", []))

    output = {
        "date": args.date,
        "session_count": len(all_sessions),
        "copilot_sessions": copilot_count,
        "vscode_copilot_sessions": vscode_copilot_count,
        "antigravity_sessions": antigravity_count,
        "cursor_sessions": cursor_count,
        "codex_sessions": codex_count,
        "claude_sessions": claude_count,
        "total_turns": sum(s["turn_count"] for s in all_sessions),
        "total_files_modified": list(dict.fromkeys(all_files)),
        "sessions": [],
    }

    for s in all_sessions:
        if args.summary:
            session_summary = {
                "agent": s["agent"],
                "agent_label": s["agent_label"],
                "session_id": s["session_id"],
                "start_time": s["start_time"],
                "end_time": s["end_time"],
                "turn_count": s["turn_count"],
                "files_modified": s["files_modified"],
                "tools_used": s["tools_used"],
            }
            # Copilot/VSCode/Cursor/Codex/Claude는 첫 user_message, Antigravity는 walkthrough summary
            if s["agent"] in ("copilot", "vscode_copilot", "cursor", "codex", "claude") and s.get("turns"):
                session_summary["first_message"] = s["turns"][0]["user_message"][:200]
                if s["agent"] in ("cursor", "claude"):
                    session_summary["project"] = s.get("project", "")
            elif s["agent"] == "antigravity":
                session_summary["walkthrough_summary"] = s.get("walkthrough", "")[:200]
                session_summary["task_summary"] = s.get("task", "")[:200]
            output["sessions"].append(session_summary)
        else:
            output["sessions"].append(s)

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

