# ffmpeg-run (预览版)
基于ffmpeg命令运行器，使用配置文件方便进行管理参数和执行。

## 功能特性
- ✅ FFmpeg 批量视频转换
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

## 配置文件说明

### 配置文件
- [config/default_config.yaml](config/default_config.yaml) - 默认配置
- [config/hevc_nvenc.vbr.28.config.yaml](config/hevc_nvenc.vbr.28.config.yaml) - NVIDIA GPU 编码
- [config/libx265.crf.25.config.yaml](config/libx265.crf.25.config.yaml) - CPU 编码

## TODO
- [x] 自定义输出文件命名
- [x] 支持控制暂停/恢复任务进度
- [x] 任务处理进度
- [x] ~~对媒体文件的智能处理~~ ffmpeg原生的过滤参数等支持

## 灵感来源
- [FFmpegFreeUI](https://github.com/Lake1059/FFmpegFreeUI)
- [FFBox](https://github.com/ttqftech/FFBox)
