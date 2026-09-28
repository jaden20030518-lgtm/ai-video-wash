#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
洗AI标签 - 一键去除视频中的AI标识与元数据
用法:
  python3 wash_ai.py 视频1.mp4 视频2.mov ...     # 处理指定文件
  python3 wash_ai.py -f 某个文件夹               # 批量处理文件夹内所有视频
  python3 wash_ai.py -f 某个文件夹 -r            # 递归处理子文件夹
输出:在原文件同目录生成 XXX_clean.mp4
依赖:ffmpeg / ffprobe(macOS 安装: brew install ffmpeg)
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm", ".flv", ".ts", ".m2ts"}

# 剪映等工具写入元数据的常见字段(用于检测,仅提示用)
AI_META_HINTS = ("is_use_ai", "source_type", "quicktime.artwork", "aigc", "ai_")


def die(msg: str) -> None:
    print(f"❌ {msg}")
    sys.exit(1)


def ensure_ffmpeg() -> None:
    if not shutil.which("ffmpeg"):
        die("未找到 ffmpeg。请在终端执行: brew install ffmpeg")


def probe(path: Path) -> dict:
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_format", "-show_streams", str(path)],
        capture_output=True, text=True)
    if r.returncode != 0:
        die(f"无法读取视频: {path}")
    return json.loads(r.stdout)


def detect_ai_meta(info: dict) -> bool:
    """检查元数据里是否残留 AI 相关声明字段"""
    blobs = [json.dumps(info.get("format", {}).get("tags", {}))]
    blobs += [json.dumps(s.get("tags", {})) for s in info.get("streams", [])]
    return any(h.lower() in b.lower() for b in blobs for h in AI_META_HINTS)


def choose_fps(info: dict) -> str | None:
    """帧率策略:保持原帧率;若源是异常的高帧率(如60),降到30"""
    for s in info.get("streams", []):
        if s.get("codec_type") == "video":
            num, _, den = (s.get("avg_frame_rate") or "0/1").partition("/")
            try:
                fps = int(num) / max(int(den or 1), 1)
            except (ValueError, ZeroDivisionError):
                return None
            if fps > 40:
                return "30"
    return None


def wash(src: Path, dst: Path, crf: int = 19) -> None:
    info = probe(src)
    had_ai_meta = detect_ai_meta(info)
    fps = choose_fps(info)

    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(src),
           "-vf", "crop=iw*0.985:ih*0.985,noise=alls=3:allf=t+u",
           "-c:v", "libx264", "-crf", str(crf), "-preset", "slow",
           "-profile:v", "high", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "128k",
           "-map_metadata", "-1", "-fflags", "+bitexact",
           "-flags:v", "+bitexact", "-flags:a", "+bitexact",
           "-movflags", "+faststart"]
    if fps:
        cmd += ["-r", fps]
    cmd.append(str(dst))

    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        die(f"处理失败 {src.name}:\n{r.stderr[-500:]}")

    # 复验
    after = probe(dst)
    if detect_ai_meta(after):
        print(f"⚠️  {dst.name}: 元数据复验仍有可疑字段,请检查")
    fps_txt = f", 帧率 {fps}" if fps else ""
    tag_txt = "检测到AI声明元数据,已清除" if had_ai_meta else "未发现AI声明元数据(已做画面处理)"
    print(f"✅ {src.name} → {dst.name}  [{tag_txt}{fps_txt}]")


def collect(args) -> list[Path]:
    files: list[Path] = []
    for p in args.inputs:
        pp = Path(p).expanduser()
        if pp.is_dir():
            it = pp.rglob("*") if args.recursive else pp.iterdir()
            files += [f for f in it
                      if f.is_file() and f.suffix.lower() in VIDEO_EXTS
                      and "_clean" not in f.stem]
        elif pp.is_file():
            files.append(pp)
        else:
            print(f"⚠️  跳过不存在的路径: {p}")
    if not files:
        die("没有找到可处理的视频文件")
    return sorted(set(files))


def main() -> None:
    ap = argparse.ArgumentParser(description="去除视频AI标识与元数据")
    ap.add_argument("inputs", nargs="*", help="视频文件或文件夹")
    ap.add_argument("-f", "--folder", help="要批量处理的文件夹")
    ap.add_argument("-r", "--recursive", action="store_true", help="递归子文件夹")
    ap.add_argument("-o", "--outdir", help="输出目录(默认输出到原视频旁边)")
    ap.add_argument("-q", "--quality", type=int, default=19, choices=range(14, 26),
                    help="画质 CRF(14=最好,25=较小文件,默认19)")
    args = ap.parse_args()
    if args.folder:
        args.inputs.append(args.folder)

    ensure_ffmpeg()
    files = collect(args)
    print(f"共 {len(files)} 个待处理视频\n")
    ok = 0
    for f in files:
        # 优先用 -o 指定的输出目录;原目录不可写时自动落到当前目录
        base = Path(args.outdir) if args.outdir else f.parent
        if args.outdir:
            base.mkdir(parents=True, exist_ok=True)
        elif not (f.parent.stat().st_mode & 0o200 or os.access(f.parent, os.W_OK)):
            base = Path.cwd()
        dst = base / f"{f.stem}_clean.mp4"
        if dst.exists():
            dst = base / f"{f.stem}_clean_1.mp4"
        try:
            wash(f, dst, args.quality)
            ok += 1
        except SystemExit:
            raise
        except Exception as e:  # 单条失败不影响批量
            print(f"⚠️  跳过 {f.name}: {e}")
    print(f"\n完成:{ok}/{len(files)} 个成功")


if __name__ == "__main__":
    main()
