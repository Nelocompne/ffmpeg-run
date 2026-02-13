import argparse
import os
import sys
import threading
import time
import atexit          # 新增
from modules.config_handler import ConfigManager
from modules.file_scanner import FileScanner
from modules.ffmpeg_processor import FFmpegProcessor
from modules.keyframe_extractor import KeyFrameExtractor
from modules.path_utils import normalize_path

# 全局变量
processor = None
should_exit = False

def keyboard_listener():
    global should_exit, processor
    print("\n⌨️  控制提示: 按 'p' 暂停, 'r' 恢复, 'q' 退出当前任务\n")
    while not should_exit:
        try:
            key = input().strip().lower()
            if key == 'p':
                if processor:
                    processor.pause_current_task()
            elif key == 'r':
                if processor:
                    processor.resume_current_task()
            elif key == 'q':
                if processor:
                    processor.stop_current_task()
                should_exit = True
                break
        except EOFError:
            time.sleep(1)

def cleanup_on_exit():
    """程序退出时确保 FFmpeg 被杀死"""
    global processor
    if processor:
        processor.stop_current_task()

def main():
    global processor, should_exit

    parser = argparse.ArgumentParser(description="FFmpeg 批量转换工具（支持暂停/恢复/安全退出）")
    parser.add_argument("input", help="输入文件或目录路径")
    parser.add_argument("--config", "-c", help="指定YAML配置文件路径", default=None)
    parser.add_argument("--mode", "-m", help="处理模式: convert 或 keyframe", choices=['convert', 'keyframe'], default=None)
    args = parser.parse_args()

    config_path = args.config
    if not config_path and args.input:
        potential_config = os.path.join(args.input, "config.yaml")
        if os.path.exists(potential_config):
            config_path = potential_config
        else:
            config_path = "config/default_config.yaml"

    config = ConfigManager(config_path)
    scanner = FileScanner()
    
    # 从命令行参数或配置文件获取处理模式
    mode = args.mode if args.mode else config.get_mode()
    
    # 根据模式初始化不同的处理器
    if mode == 'keyframe':
        keyframe_opts = config.get_keyframe_options()
        processor = KeyFrameExtractor(
            threshold=keyframe_opts.get('threshold', 0.3),
            min_interval=keyframe_opts.get('min_interval', 0.5)
        )
        print(f"🎬 模式: 关键帧提取")
        print(f"   参数: threshold={keyframe_opts.get('threshold', 0.3)}, min_interval={keyframe_opts.get('min_interval', 0.5)}s")
    else:
        processor = FFmpegProcessor()
        print(f"🎬 模式: FFmpeg 转换")

    # 注册退出清理钩子（兜底）- 仅对 FFmpeg 处理器有效
    if isinstance(processor, FFmpegProcessor):
        atexit.register(cleanup_on_exit)

    input_source = normalize_path(args.input)
    file_list = scanner.scan(input_source)
    if not file_list:
        print("未找到可处理的媒体文件。")
        return

    print(f"找到 {len(file_list)} 个文件，开始处理...")

    # 仅在 FFmpeg 模式下启动键盘监听
    if isinstance(processor, FFmpegProcessor):
        listener_thread = threading.Thread(target=keyboard_listener, daemon=True)
        listener_thread.start()

    try:
        for file_path in file_list:
            if should_exit:
                print("用户请求退出，停止后续任务。")
                break

            output_path = config.get_output_path(file_path, custom_field=config.config.get('output_suffix', ''))

            if mode == 'keyframe':
                # 关键帧提取模式
                success = processor.process_video(file_path, output_path)
            else:
                # FFmpeg 转换模式
                config_dict = config.config
                global_opts = config_dict.get("global_options", [])
                input_opts = config_dict.get("input_options", [])
                output_opts = config_dict.get("output_options", [])

                if "ffmpeg_params" in config_dict and not output_opts:
                    output_opts = config_dict["ffmpeg_params"]

                success = processor.run_conversion(
                    file_path,
                    output_path,
                    global_opts=global_opts,
                    input_opts=input_opts,
                    output_opts=output_opts
                )

            if not success and should_exit:
                break

        print("所有任务完成。")

    except KeyboardInterrupt:
        print("\n\n🛑 检测到 Ctrl+C，正在终止任务...")
        if isinstance(processor, FFmpegProcessor):
            processor.stop_current_task()
        sys.exit(1)

if __name__ == "__main__":
    main()