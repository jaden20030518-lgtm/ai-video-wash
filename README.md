# ai-video-wash

一键去除 AI 视频的生成标识:清除剪映等工具写入的 AI 声明元数据,并对画面做轻度"去 AI 味"处理。

One-click tool to strip AIGC metadata (e.g. CapCut/JianYing's `com.apple.quicktime.artwork` AI flags) from videos and lightly "de-AI" the visuals.

## 功能

- 清除 AI 声明元数据 — 自动检测并清除剪映/CapCut 写入的 `is_use_ai_video_generation`、`source_type` 等声明字段
- 打散画面指纹 — 轻微裁切 1.5%,打破生成模型的统计特征
- 帧率归一 — 60fps 素材自动降到 30fps(主流生成模型输出帧率特征)
- 轻噪点 — 打破过度平滑的 AI 画面质感
- 批量处理 — 支持整个文件夹(含子目录)批量洗标

## 依赖

- Python 3.8+
- ffmpeg / ffprobe(macOS: `brew install ffmpeg`)

## 用法

### 双击版(macOS)

双击 `一键洗AI标签.command`,在弹窗中选择一个或多个视频,处理结果输出到原视频旁边(`xxx_clean.mp4`)。

首次使用需在终端执行一次 `brew install ffmpeg`。

### 命令行

```bash
# 处理单个或多个文件
python3 wash_ai.py 视频1.mov 视频2.mp4

# 批量处理文件夹(递归)
python3 wash_ai.py -f 素材文件夹 -r

# 指定输出目录与画质
python3 wash_ai.py -f 素材文件夹 -o 输出目录 -q 17
```

参数说明:

| 参数 | 说明 |
|------|------|
| `inputs` | 视频文件或文件夹(可多个) |
| `-f, --folder` | 要批量处理的文件夹 |
| `-r, --recursive` | 递归处理子文件夹 |
| `-o, --outdir` | 输出目录(默认输出到原视频旁边) |
| `-q, --quality` | 画质 CRF,14(最好)~ 25(文件更小),默认 19 |

## 注意

- 生成工具的水印是画面内容,本工具无法去除,请导出前确认无水印
- 本工具降低被 AIGC 检测识别的概率,不保证 100% 不被平台判定
- 请遵守平台规则及相关法规,合规使用

## License

MIT
