#!/usr/bin/env bash
set -euo pipefail

# ─────────────────────────────────────────────
# AI Agent Report — 제거 스크립트
# ─────────────────────────────────────────────

AI_REPORT_LINK="$HOME/.ai-report"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   🗑️  AI Agent Report — 제거 스크립트         ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════╝${NC}"
echo ""

# ─────────────────────────────────────────────
# 1. 에이전트 스킬 제거
# ─────────────────────────────────────────────

echo -e "${BLUE}[1/2] 에이전트 스킬 제거${NC}"

declare -A SKILL_DIRS=(
    ["GitHub Copilot"]="$HOME/.copilot/skills/AI_Report"
    ["Antigravity (Gemini)"]="$HOME/.gemini/antigravity/skills/AI_Report"
    ["Cursor"]="$HOME/.cursor/skills-cursor/AI_Report"
    ["GPT Codex"]="$HOME/.codex/skills/AI_Report"
    ["Claude Code"]="$HOME/.claude/skills/AI_Report"
)

for agent_name in "${!SKILL_DIRS[@]}"; do
    skill_dir="${SKILL_DIRS[$agent_name]}"
    if [ -d "$skill_dir" ]; then
        rm -rf "$skill_dir"
        echo -e "  ${GREEN}✓${NC} $agent_name: $skill_dir 제거됨"
    else
        echo -e "  ${YELLOW}-${NC} $agent_name: 스킬 없음 (건너뜀)"
    fi
done

echo ""

# ─────────────────────────────────────────────
# 2. 심볼릭 링크 제거
# ─────────────────────────────────────────────

echo -e "${BLUE}[2/2] ~/.ai-report 심볼릭 링크 제거${NC}"

if [ -L "$AI_REPORT_LINK" ]; then
    TARGET="$(readlink "$AI_REPORT_LINK")"
    rm "$AI_REPORT_LINK"
    echo -e "  ${GREEN}✓${NC} 심볼릭 링크 제거: ~/.ai-report → $TARGET"
elif [ -d "$AI_REPORT_LINK" ]; then
    echo -e "  ${YELLOW}⚠${NC} ~/.ai-report가 실제 디렉토리입니다. 수동으로 제거하세요."
else
    echo -e "  ${YELLOW}-${NC} ~/.ai-report 없음 (건너뜀)"
fi

echo ""
echo -e "${GREEN}✅ 제거 완료!${NC}"
echo -e "  클론된 저장소는 삭제되지 않았습니다. 필요 시 수동으로 삭제하세요."
echo ""

