import argparse
import os
import sys
from modules.config_handler import ConfigManager
from modules.file_scanner import FileScanner
from modules.ffmpeg_processor import FFmpegProcessor
from modules.path_utils import normalize_path

def main():
    parser = argparse.ArgumentParser(description="跨平台FFmpeg批量处理工具")
    parser.add_argument("input", nargs='?', help="输入文件或目录路径 (如果不传入，则使用当前目录配置)")
    parser.add_argument("--config", "-c", help="指定YAML配置文件路径", default=None)
    
    args = parser.parse_args()

    # 1. 确定配置文件路径
    config_path = args.config
    
    # 如果命令行没指定配置，且输入了目录，则检查该目录下是否有配置文件
    if not config_path and args.input:
        potential_config = os.path.join(args.input, "config.yaml")
        if os.path.exists(potential_config):
            config_path = potential_config
        else:
            # 默认读取运行目录下的配置
            config_path = "config/default_config.yaml" 

    # 2. 初始化模块
    config = ConfigManager(config_path)
    scanner = FileScanner()
    processor = FFmpegProcessor()

    # 3. 确定输入源
    input_source = args.input
    if not input_source:
        print("错误: 必须指定输入文件或目录。使用 -h 查看帮助。")
        sys.exit(1)

    # 规范化路径
    input_source = normalize_path(input_source)
    
    # 4. 扫描文件
    file_list = scanner.scan(input_source)
    if not file_list:
        print("未找到可处理的媒体文件。")
        sys.exit(0)

    print(f"找到 {len(file_list)} 个文件，开始处理...")

    # 5. 处理任务
    for file_path in file_list:
        # 根据配置生成输出路径
        # 这里 custom_field 可以通过更复杂的逻辑传入，例如从文件名解析或配置中读取
        output_path = config.get_output_path(file_path, custom_field=config.config.get('output_suffix', ''))
        
        config_dict = config.config
        global_opts = config_dict.get("global_options", [])
        input_opts = config_dict.get("input_options", [])
        output_opts = config_dict.get("output_options", [])

        # 执行转换
        success = processor.run_conversion(
            file_path,
            output_path,
            global_opts=global_opts,
            input_opts=input_opts,
            output_opts=output_opts
        )
        
        if not success:
            print(f"跳过后续操作: {file_path}")

if __name__ == "__main__":
    main()