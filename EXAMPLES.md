# 使用示例

## 快速开始

### 示例 1: 转换单个视频（默认配置）
```bash
python main.py "video.mp4"
```

### 示例 2: 批量转换（使用 GPU HEVC 编码）
```bash
python main.py "C:\Videos\录播" --config "config/hevc_nvenc.vbr.28.config.yaml"
```

### 示例 3: 提取关键帧（适合静态画面多的视频）
```bash
python main.py "直播录制.mp4" --config "config/keyframe_extract.config.yaml"
```

### 示例 4: 关键帧 + 转换（最大压缩）
```bash
# GPU 版本（推荐，速度快）
python main.py "C:\Videos\录播" --config "config/keyframe_and_convert.config.yaml"

# CPU 版本（通用，速度慢）
python main.py "C:\Videos\录播" --config "config/keyframe_and_convert_cpu.config.yaml"
```

### 示例 5: 命令行覆盖配置文件模式
```bash
# 使用 GPU 编码配置，但改为组合模式
python main.py "video.mp4" --config "config/hevc_nvenc.vbr.28.config.yaml" --mode both
```

## 实际场景

### 场景 1: B站录播压缩
假设你有一个 10GB 的直播录播视频，大部分时间画面静态。

```bash
# 使用组合模式，可能压缩到 500MB 以下
python main.py "录播-20260215.mp4" --config "config/keyframe_and_convert.config.yaml"
```

**效果：**
- 关键帧提取: 10GB → 2GB（保留所有场景变化）
- HEVC 编码: 2GB → 500MB（高效压缩）

### 场景 2: 批量转换教程视频
```bash
# 批量处理目录下所有视频
python main.py "D:\教程视频" --config "config/keyframe_and_convert_cpu.config.yaml"
```

### 场景 3: 仅重新编码（不提取关键帧）
```bash
# 适合动态画面多的视频，使用高质量 HEVC 编码
python main.py "游戏录制.mp4" --config "config/hevc_nvenc.vbr.28.config.yaml"
```

### 场景 4: 监控视频压缩
```bash
# 监控视频通常变化少，提取关键帧即可
python main.py "监控录像" --config "config/keyframe_extract.config.yaml"
```

## 参数调整建议

### 关键帧参数
```yaml
# 录播视频（静态画面多）
threshold: 0.15      # 更敏感，捕捉细微变化
min_interval: 5.0    # 较大间隔，避免过多帧

# 一般视频（动态适中）
threshold: 0.25
min_interval: 1.0

# 动态视频（不推荐使用关键帧）
# 改用纯转换模式
```

### FFmpeg 编码质量
```yaml
# GPU (hevc_nvenc)
# cq: 18-23 (高质量), 24-28 (平衡), 29-35 (高压缩)

# CPU (libx265)
# crf: 18-23 (高质量), 24-28 (平衡), 29-35 (高压缩)
```

## 控制快捷键（FFmpeg 转换时）

- **p** - 暂停当前任务
- **r** - 恢复任务
- **q** - 退出当前任务
- **Ctrl+C** - 紧急终止

## 常见问题

**Q: 组合模式太慢怎么办？**
A: 可以先用关键帧模式快速压缩，如果还需要进一步压缩再转换。

**Q: 关键帧提取后画面卡顿？**
A: 降低 `min_interval` 参数，或降低 `threshold` 以提取更多帧。

**Q: GPU 编码速度没变化？**
A: 检查 `nvidia-smi` 确认显卡支持，或改用 CPU 配置。

**Q: 如何查看中间步骤的临时文件？**
A: 修改代码中的 `delete=False` 并注释掉清理逻辑。
