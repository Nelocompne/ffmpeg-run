# ffmpeg-run (预览版)
基于ffmpeg命令运行器，使用配置文件方便进行管理参数和执行。

## 功能特性
- ✅ FFmpeg 批量视频转换
- ✅ 关键帧提取与视频压缩
- ✅ **关键帧提取 + 转换流水线（新）**
- ✅ 支持暂停/恢复/退出控制
- ✅ 实时进度显示
- ✅ 灵活的配置文件管理

## 运行方式

**环境准备：** 确保系统已安装 `ffmpeg` 并已添加到环境变量。python >= 3.10
```bash
pip install -r requirements.txt # 安装依赖
```

### 1. FFmpeg 转换模式（默认）
```bash
python main.py "C:\Videos\test.mp4" # 转换单个文件
python main.py "C:\Videos\BatchFolder" # 批量转换目录
python main.py "C:\Videos" --config "config/hevc_nvenc.vbr.28.config.yaml" # 指定配置
python main.py /home/user/videos/ # Linux 下运行
```

### 2. 关键帧提取模式
关键帧提取会分析视频内容，提取发生显著变化的帧，然后重新渲染成新视频（保留原音频），可大幅减少视频大小。

```bash
# 使用关键帧提取配置文件
python main.py "C:\Videos\test.mp4" --config "config/keyframe_extract.config.yaml"

# 或通过命令行指定模式
python main.py "C:\Videos\test.mp4" --mode keyframe

# 批量处理
python main.py "C:\Videos\BatchFolder" --config "config/keyframe_extract.config.yaml"
```

### 3. 组合模式（关键帧提取 + 转换）⭐ 推荐
先提取关键帧，再对关键帧视频进行高效编码，实现**最大压缩比**。

```bash
# GPU 编码版（需要 NVIDIA 显卡）
python main.py "C:\Videos\test.mp4" --config "config/keyframe_and_convert.config.yaml"

# CPU 编码版（通用）
python main.py "C:\Videos\test.mp4" --config "config/keyframe_and_convert_cpu.config.yaml"

# 或通过命令行指定模式
python main.py "C:\Videos\test.mp4" --mode both

# 批量处理
python main.py "C:\Videos\BatchFolder" --config "config/keyframe_and_convert.config.yaml"
```

**流水线处理流程：**
1. 🎬 提取关键帧，生成临时视频（保留原音频）
2. 🔄 对临时视频进行 FFmpeg 编码转换
3. 🗑️ 删除临时文件，输出最终结果

**适用场景：**
- 📺 录播视频压缩（直播录制、静态画面较多）
- 📚 教程视频优化
- 📹 监控视频压缩
- 🎮 游戏录制压缩

**参数说明：**
- `threshold`: 帧差异阈值 (0.0-1.0)，越小越敏感，关键帧越多
- `min_interval`: 最小关键帧间隔（秒），避免变化过快

## 处理模式对比

| 模式 | 说明 | 压缩效果 | 处理速度 | 适用场景 |
|------|------|----------|----------|----------|
| `convert` | 仅 FFmpeg 转换 | 中等 | 最快 | 一般视频转换 |
| `keyframe` | 仅关键帧提取 | 高 | 中等 | 静态画面多的视频 |
| `both` | 关键帧 + 转换 | **最高** | 较慢 | 需要极限压缩 |

## 配置文件说明

### 转换模式配置
- [config/default_config.yaml](config/default_config.yaml) - 默认配置
- [config/hevc_nvenc.vbr.28.config.yaml](config/hevc_nvenc.vbr.28.config.yaml) - NVIDIA GPU 编码
- [config/libx265.crf.25.config.yaml](config/libx265.crf.25.config.yaml) - CPU 编码

### 关键帧提取配置
- [config/keyframe_extract.config.yaml](config/keyframe_extract.config.yaml) - 仅关键帧提取

### 组合模式配置 ⭐
- [config/keyframe_and_convert.config.yaml](config/keyframe_and_convert.config.yaml) - GPU 版（推荐）
- [config/keyframe_and_convert_cpu.config.yaml](config/keyframe_and_convert_cpu.config.yaml) - CPU 版

## TODO
- [x] 自定义输出文件命名
- [x] 支持控制暂停/恢复任务进度
- [x] 任务处理进度
- [x] 关键帧提取功能
- [x] 关键帧 + 转换流水线处理
- [x] ~~对媒体文件的智能处理~~ ffmpeg原生的过滤参数等支持

## 灵感来源
- [FFmpegFreeUI](https://github.com/Lake1059/FFmpegFreeUI)
- [FFBox](https://github.com/ttqftech/FFBox)