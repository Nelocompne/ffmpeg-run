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

## 参数调整建议

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

**Q: GPU 编码速度没变化？**
A: 检查 `nvidia-smi` 确认显卡支持，或改用 CPU 配置。
