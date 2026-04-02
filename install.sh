#!/usr/bin/env bash
set -eo pipefail

# ─────────────────────────────────────────────
# AI Agent Report — 설치 스크립트
# macOS bash 3.2+ 호환 (연관 배열 미사용)
# ─────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AI_REPORT_LINK="$HOME/.ai-report"

# 색상
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   🤖 AI Agent Report — 설치 스크립트         ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════╝${NC}"
echo ""

# ─────────────────────────────────────────────
# 1. Python 3 설치 확인
# ─────────────────────────────────────────────

echo -e "${BLUE}[1/5] Python 3 설치 확인${NC}"

PYTHON_CMD=""
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PY_VER="$(python --version 2>&1)"
    if echo "$PY_VER" | grep -q "Python 3"; then
        PYTHON_CMD="python"
    fi
fi

if [ -n "$PYTHON_CMD" ]; then
    PY_VERSION="$($PYTHON_CMD --version 2>&1)"
    echo -e "  ${GREEN}✓${NC} $PY_VERSION 감지됨"
else
    echo -e "  ${RED}✗${NC} Python 3가 설치되어 있지 않습니다."
    echo ""
    echo -e "  ${YELLOW}Python 3 설치 방법:${NC}"

    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &>/dev/null; then
            echo -e "    ${CYAN}brew install python3${NC}"
            echo ""
            read -p "  Homebrew로 Python 3를 지금 설치하시겠습니까? (y/N): " yn
            case $yn in
                [Yy]* )
                    echo -e "  Python 3 설치 중..."
                    brew install python3
                    if command -v python3 &>/dev/null; then
                        PYTHON_CMD="python3"
                        PY_VERSION="$(python3 --version 2>&1)"
                        echo -e "  ${GREEN}✓${NC} $PY_VERSION 설치 완료!"
                    else
                        echo -e "  ${RED}✗${NC} 설치에 실패했습니다. 수동으로 설치해 주세요."
                        exit 1
                    fi
                    ;;
                * )
                    echo -e "  ${RED}✗${NC} Python 3가 필요합니다. 설치 후 다시 실행해 주세요."
                    exit 1
                    ;;
            esac
        else
            echo -e "    방법 1: ${CYAN}https://www.python.org/downloads/${NC} 에서 다운로드"
            echo -e "    방법 2: Homebrew 설치 후 ${CYAN}brew install python3${NC}"
            echo -e "            Homebrew 설치: ${CYAN}/bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"${NC}"
            echo ""
            echo -e "  ${RED}✗${NC} Python 3 설치 후 다시 실행해 주세요."
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        echo -e "    Ubuntu/Debian: ${CYAN}sudo apt install python3${NC}"
        echo -e "    CentOS/RHEL:   ${CYAN}sudo yum install python3${NC}"
        echo -e "    Arch:          ${CYAN}sudo pacman -S python${NC}"
        echo ""
        read -p "  자동 설치를 시도하시겠습니까? (y/N): " yn
        case $yn in
            [Yy]* )
                if command -v apt &>/dev/null; then
                    sudo apt update && sudo apt install -y python3
                elif command -v yum &>/dev/null; then
                    sudo yum install -y python3
                elif command -v pacman &>/dev/null; then
                    sudo pacman -S --noconfirm python
                else
                    echo -e "  ${RED}✗${NC} 패키지 매니저를 찾을 수 없습니다. 수동으로 설치해 주세요."
                    exit 1
                fi
                if command -v python3 &>/dev/null; then
                    PYTHON_CMD="python3"
                    PY_VERSION="$(python3 --version 2>&1)"
                    echo -e "  ${GREEN}✓${NC} $PY_VERSION 설치 완료!"
                else
                    echo -e "  ${RED}✗${NC} 설치에 실패했습니다. 수동으로 설치해 주세요."
                    exit 1
                fi
                ;;
            * )
                echo -e "  ${RED}✗${NC} Python 3가 필요합니다. 설치 후 다시 실행해 주세요."
                exit 1
                ;;
        esac
    else
        echo -e "    ${CYAN}https://www.python.org/downloads/${NC} 에서 다운로드"
        echo ""
        echo -e "  ${RED}✗${NC} Python 3 설치 후 다시 실행해 주세요."
        exit 1
    fi
fi

echo ""

# ─────────────────────────────────────────────
# 2. 프로젝트 연결 설정
# ─────────────────────────────────────────────

echo -e "${BLUE}[2/5] 프로젝트 연결 설정${NC}"

if [ -L "$AI_REPORT_LINK" ]; then
    EXISTING_TARGET="$(readlink "$AI_REPORT_LINK")"
    if [ "$EXISTING_TARGET" = "$SCRIPT_DIR" ]; then
        echo -e "  ${GREEN}✓${NC} 이미 올바르게 연결됨"
    else
        echo -e "  ${YELLOW}⚠${NC} 기존 연결이 다른 경로를 가리키고 있습니다."
        read -p "  현재 프로젝트로 교체하시겠습니까? (y/N): " yn
        case $yn in
            [Yy]* )
                rm "$AI_REPORT_LINK"
                ln -s "$SCRIPT_DIR" "$AI_REPORT_LINK"
                echo -e "  ${GREEN}✓${NC} 프로젝트 연결 교체 완료"
                ;;
            * )
                echo -e "  ${YELLOW}⚠${NC} 기존 연결 유지"
                ;;
        esac
    fi
elif [ -d "$AI_REPORT_LINK" ]; then
    echo -e "  ${YELLOW}⚠${NC} 이전 설치 흔적이 남아 있습니다."
    read -p "  정리하고 새로 연결하시겠습니까? (y/N): " yn
    case $yn in
        [Yy]* )
            rm -rf "$AI_REPORT_LINK"
            ln -s "$SCRIPT_DIR" "$AI_REPORT_LINK"
            echo -e "  ${GREEN}✓${NC} 프로젝트 연결 완료"
            ;;
        * )
            echo -e "  ${RED}✗${NC} 설치 중단. 이전 설치를 먼저 정리해 주세요."
            exit 1
            ;;
    esac
else
    ln -s "$SCRIPT_DIR" "$AI_REPORT_LINK"
    echo -e "  ${GREEN}✓${NC} 프로젝트 연결 완료"
fi

mkdir -p "$SCRIPT_DIR/업무보고"

# 양식 파일 읽기 전용 보호
if [ -f "$SCRIPT_DIR/.data/업무보고서_양식.md" ]; then
    chmod 444 "$SCRIPT_DIR/.data/업무보고서_양식.md"
fi

echo ""

# ─────────────────────────────────────────────
# 3. 에이전트 감지 (macOS bash 3.2 호환)
# ─────────────────────────────────────────────

echo -e "${BLUE}[3/5] AI 에이전트 감지${NC}"

# 에이전트 정보: name|detect_dir|skill_path|detect_cmd
AGENTS=(
    "GitHub Copilot|$HOME/.copilot|$HOME/.copilot/skills|"
    "Antigravity (Gemini)|$HOME/.gemini/antigravity|$HOME/.gemini/antigravity/skills|"
    "Cursor|$HOME/.cursor|$HOME/.cursor/skills-cursor|"
    "GPT Codex|$HOME/.codex|$HOME/.codex/skills|codex"
    "Claude Code|$HOME/.claude|$HOME/.claude/skills|claude"
)

DETECTED_INDICES=()

for i in "${!AGENTS[@]}"; do
    IFS='|' read -r name detect_dir skill_path detect_cmd <<< "${AGENTS[$i]}"
    detected=false

    if [ -d "$detect_dir" ]; then
        detected=true
    fi

    if [ -n "$detect_cmd" ] && command -v "$detect_cmd" &>/dev/null; then
        detected=true
    fi

    if $detected; then
        DETECTED_INDICES+=("$i")
        echo -e "  ${GREEN}✓${NC} ${name}"
    else
        echo -e "  ${RED}✗${NC} ${name} — 미감지"
    fi
done

echo ""

if [ ${#DETECTED_INDICES[@]} -eq 0 ]; then
    echo -e "${YELLOW}⚠ 감지된 에이전트가 없습니다.${NC}"
    echo "  에이전트를 설치한 후 install.sh를 다시 실행하면 스킬이 자동 설치됩니다."
    echo ""
else
    echo -e "감지된 에이전트: ${GREEN}${#DETECTED_INDICES[@]}개${NC}"
    echo ""
fi

# ─────────────────────────────────────────────
# 4. 에이전트 스킬 설치
# ─────────────────────────────────────────────

echo -e "${BLUE}[4/5] 에이전트 스킬 설치${NC}"

INSTALLED_COUNT=0

for i in "${DETECTED_INDICES[@]}"; do
    IFS='|' read -r name detect_dir skill_path detect_cmd <<< "${AGENTS[$i]}"
    skill_dir="$skill_path/AI_Report"

    if [ ! -d "$skill_path" ]; then
        mkdir -p "$skill_path"
    fi

    mkdir -p "$skill_dir"
    cp "$SCRIPT_DIR/AI_Report/SKILL.md" "$skill_dir/SKILL.md"

    echo -e "  ${GREEN}✓${NC} ${name} — 스킬 설치 완료"
    INSTALLED_COUNT=$((INSTALLED_COUNT + 1))
done

if [ $INSTALLED_COUNT -eq 0 ]; then
    echo -e "  ${YELLOW}⚠${NC} 스킬 설치 건너뜀 (감지된 에이전트 없음)"
fi

echo ""

# ─────────────────────────────────────────────
# 5. VSCode Copilot 로그 설정 확인
# ─────────────────────────────────────────────

# VSCode settings.json 경로 (macOS / Linux)
if [[ "$OSTYPE" == "darwin"* ]]; then
    VSCODE_SETTINGS="$HOME/Library/Application Support/Code/User/settings.json"
else
    VSCODE_SETTINGS="$HOME/.config/Code/User/settings.json"
fi

if [ -f "$VSCODE_SETTINGS" ]; then
    echo -e "${BLUE}[5/5] VSCode Copilot 로그 설정 확인${NC}"

    # Python으로 안전하게 JSON 편집
    SETTING_KEY="github.copilot-chat.debug.saveConversationLog"

    HAS_SETTING=$($PYTHON_CMD -c "
import json, sys
try:
    with open('''$VSCODE_SETTINGS''', 'r') as f:
        s = json.load(f)
    print('yes' if s.get('$SETTING_KEY') == True else 'no')
except:
    print('error')
" 2>/dev/null)

    if [ "$HAS_SETTING" = "yes" ]; then
        echo -e "  ${GREEN}✓${NC} VSCode Copilot 대화 로그 저장 — 이미 활성화됨"
    elif [ "$HAS_SETTING" = "no" ]; then
        $PYTHON_CMD -c "
import json
with open('''$VSCODE_SETTINGS''', 'r') as f:
    s = json.load(f)
s['$SETTING_KEY'] = True
with open('''$VSCODE_SETTINGS''', 'w') as f:
    json.dump(s, f, indent=4, ensure_ascii=False)
" 2>/dev/null

        if [ $? -eq 0 ]; then
            echo -e "  ${GREEN}✓${NC} VSCode Copilot 대화 로그 저장 — 설정 자동 추가 완료"
            echo -e "    ${CYAN}$SETTING_KEY: true${NC}"
        else
            echo -e "  ${YELLOW}⚠${NC} VSCode settings.json 수정 실패 — 수동으로 추가해 주세요:"
            echo -e "    ${CYAN}\"$SETTING_KEY\": true${NC}"
        fi
    else
        echo -e "  ${YELLOW}⚠${NC} VSCode settings.json 읽기 실패 — 수동으로 추가해 주세요:"
        echo -e "    ${CYAN}\"$SETTING_KEY\": true${NC}"
    fi
    echo ""
fi

# ─────────────────────────────────────────────
# 완료
# ─────────────────────────────────────────────

echo -e "${GREEN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   ✅ 설치 완료!                              ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  보고서 출력 경로 : ${CYAN}~/.ai-report/업무보고/YYYY-MM-DD_AI업무보고서.md${NC}"
echo -e "  스킬 설치 에이전트 : ${CYAN}${INSTALLED_COUNT}개${NC}"
echo ""
echo -e "${BLUE}사용법:${NC}"
echo "  AI 에이전트 내에서 아래와 같이 요청하세요:"
echo ""
echo "    /AI업무보고 오늘자 보고서 작성해줘"
echo "    /AI업무보고 2026-04-02 보고서 작성해줘"
echo ""
echo -e "${YELLOW}💡 새 에이전트를 추가 설치하면 install.sh를 다시 실행하세요.${NC}"
echo ""


