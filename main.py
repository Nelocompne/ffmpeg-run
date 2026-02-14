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

def process_single_file(file_path, config, keyframe_extractor=None, ffmpeg_processor=None):
    """
    处理单个文件，支持关键帧提取和转换的流水线处理
    
    Args:
        file_path: 输入文件路径
        config: 配置管理器
        keyframe_extractor: 关键帧提取器（可选）
        ffmpeg_processor: FFmpeg处理器（可选）
    
    Returns:
        bool: 是否成功
    """
    import tempfile
    from pathlib import Path
    
    mode = config.get_mode()
    output_path = config.get_output_path(file_path, custom_field=config.config.get('output_suffix', ''))
    
    # 情况1: 仅关键帧提取
    if mode == 'keyframe':
        return keyframe_extractor.process_video(file_path, output_path)
    
    # 情况2: 仅转换
    elif mode == 'convert':
        config_dict = config.config
        global_opts = config_dict.get("global_options", [])
        input_opts = config_dict.get("input_options", [])
        output_opts = config_dict.get("output_options", [])
        
        if "ffmpeg_params" in config_dict and not output_opts:
            output_opts = config_dict["ffmpeg_params"]
        
        return ffmpeg_processor.run_conversion(
            file_path,
            output_path,
            global_opts=global_opts,
            input_opts=input_opts,
            output_opts=output_opts
        )
    
    # 情况3: 关键帧提取 + 转换（流水线）
    elif mode == 'both':
        print(f"\n{'='*60}")
        print(f"🔄 流水线处理: {Path(file_path).name}")
        print(f"   步骤1: 关键帧提取")
        print(f"   步骤2: FFmpeg 转换")
        print(f"{'='*60}")
        
        # 创建临时文件用于存储关键帧视频
        temp_file = tempfile.NamedTemporaryFile(
            suffix=f'.{config.config.get("output_format", "mp4")}',
            delete=False
        )
        temp_path = temp_file.name
        temp_file.close()
        
        try:
            # 步骤1: 提取关键帧
            print("\n[步骤 1/2] 提取关键帧...")
            success = keyframe_extractor.process_video(file_path, temp_path)
            
            if not success:
                print("❌ 关键帧提取失败，跳过转换步骤")
                return False
            
            # 步骤2: FFmpeg 转换
            print("\n[步骤 2/2] FFmpeg 转换...")
            config_dict = config.config
            global_opts = config_dict.get("global_options", [])
            input_opts = config_dict.get("input_options", [])
            output_opts = config_dict.get("output_options", [])
            
            if "ffmpeg_params" in config_dict and not output_opts:
                output_opts = config_dict["ffmpeg_params"]
            
            success = ffmpeg_processor.run_conversion(
                temp_path,
                output_path,
                global_opts=global_opts,
                input_opts=input_opts,
                output_opts=output_opts
            )
            
            if success:
                print(f"\n✅ 流水线处理完成: {Path(output_path).name}")
            else:
                print(f"\n❌ FFmpeg 转换失败")
            
            return success
            
        finally:
            # 清理临时文件
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    print(f"🗑️  已清理临时文件")
            except Exception as e:
                print(f"⚠️  清理临时文件失败: {e}")
    
    return False


def main():
    global processor, should_exit

    parser = argparse.ArgumentParser(description="FFmpeg 批量转换工具（支持暂停/恢复/安全退出）")
    parser.add_argument("input", help="输入文件或目录路径")
    parser.add_argument("--config", "-c", help="指定YAML配置文件路径", default=None)
    parser.add_argument("--mode", "-m", help="处理模式: convert, keyframe 或 both", 
                        choices=['convert', 'keyframe', 'both'], default=None)
    args = parser.parse_args()

    config_path = args.config
    if not config_path and args.input:
        potential_config = os.path.join(args.input, "config.yaml")
        if os.path.exists(potential_config):
            config_path = potential_config
        else:
            config_path = "config/default_config.yaml"

    config = ConfigManager(config_path)
    
    # 从命令行参数覆盖配置文件中的模式
    if args.mode:
        config.config['mode'] = args.mode
    
    scanner = FileScanner()
    mode = config.get_mode()
    
    # 根据模式初始化处理器
    keyframe_extractor = None
    ffmpeg_processor = None
    
    if config.is_keyframe_enabled():
        keyframe_opts = config.get_keyframe_options()
        keyframe_extractor = KeyFrameExtractor(
            threshold=keyframe_opts.get('threshold', 0.3),
            min_interval=keyframe_opts.get('min_interval', 0.5)
        )
    
    if config.is_convert_enabled():
        ffmpeg_processor = FFmpegProcessor()
        processor = ffmpeg_processor  # 用于全局清理
    
    # 显示模式信息
    if mode == 'both':
        keyframe_opts = config.get_keyframe_options()
        print(f"🎬 模式: 关键帧提取 + FFmpeg 转换（流水线）")
        print(f"   关键帧参数: threshold={keyframe_opts.get('threshold', 0.3)}, min_interval={keyframe_opts.get('min_interval', 0.5)}s")
    elif mode == 'keyframe':
        keyframe_opts = config.get_keyframe_options()
        print(f"🎬 模式: 关键帧提取")
        print(f"   参数: threshold={keyframe_opts.get('threshold', 0.3)}, min_interval={keyframe_opts.get('min_interval', 0.5)}s")
    else:
        print(f"🎬 模式: FFmpeg 转换")

    # 注册退出清理钩子（仅对 FFmpeg 处理器有效）
    if ffmpeg_processor:
        atexit.register(cleanup_on_exit)

    input_source = normalize_path(args.input)
    file_list = scanner.scan(input_source)
    if not file_list:
        print("未找到可处理的媒体文件。")
        return

    print(f"找到 {len(file_list)} 个文件，开始处理...")

    # 仅在启用 FFmpeg 时启动键盘监听
    if ffmpeg_processor:
        listener_thread = threading.Thread(target=keyboard_listener, daemon=True)
        listener_thread.start()

    try:
        for file_path in file_list:
            if should_exit:
                print("用户请求退出，停止后续任务。")
                break

            success = process_single_file(
                file_path,
                config,
                keyframe_extractor=keyframe_extractor,
                ffmpeg_processor=ffmpeg_processor
            )

            if not success and should_exit:
                break

        print("\n" + "="*60)
        print("✅ 所有任务完成。")
        print("="*60)

    except KeyboardInterrupt:
        print("\n\n🛑 检测到 Ctrl+C，正在终止任务...")
        if ffmpeg_processor:
            ffmpeg_processor.stop_current_task()
        sys.exit(1)

if __name__ == "__main__":
    main()