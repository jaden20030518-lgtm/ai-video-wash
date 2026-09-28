#!/bin/bash
# 一键洗AI标签 - 双击运行,弹出文件选择框
# 依赖 ffmpeg(macOS 终端执行一次: brew install ffmpeg)
cd "$(dirname "$0")" || exit 1

if ! command -v ffmpeg >/dev/null 2>&1; then
    osascript -e 'display alert "缺少 ffmpeg" message "请先在终端执行一次: brew install ffmpeg" as critical'
    exit 1
fi

FILES=$(osascript <<'EOF'
set fl to choose file with prompt "选择要洗AI标签的视频(可多选)" with multiple selections allowed
set out to ""
repeat with f in fl
    set out to out & POSIX path of f & linefeed
end repeat
return out
EOF
) || exit 0

# 统一转为脚本参数
ARGS=()
while IFS= read -r f; do
    [ -n "$f" ] && ARGS+=("$f")
done <<< "$FILES"

python3 "$(dirname "$0")/wash_ai.py" "${ARGS[@]}" 2>&1 | tee /tmp/wash_ai_last.log
RESULT=${PIPESTATUS[0]}

if [ "$RESULT" -eq 0 ]; then
    osascript -e "display alert \"完成 ✅\" message \"已生成 _clean.mp4,位置见终端/日志。$(grep -c '✅' /tmp/wash_ai_last.log) 个处理成功\""
else
    osascript -e 'display alert "处理失败" message "详情见 /tmp/wash_ai_last.log" as critical'
fi
