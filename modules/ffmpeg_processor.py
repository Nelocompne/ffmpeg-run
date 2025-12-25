import subprocess
import os
import sys
from .path_utils import is_network_path

class FFmpegProcessor:
    def __init__(self, ffmpeg_path="ffmpeg"):
        self.ffmpeg_path = ffmpeg_path

    def run_conversion(self, input_file, output_file, ffmpeg_args=None):
        """
        执行单个FFmpeg转换任务。
        ffmpeg_args: 从配置中读取的参数列表。
        """
        # 构建命令
        # 注意: 网络路径在Windows下通常可以直接传给ffmpeg，但确保ffmpeg有权限访问
        cmd = [self.ffmpeg_path, "-i", input_file]
        
        if ffmpeg_args:
            cmd.extend(ffmpeg_args)
            
        cmd.append(output_file)

        print(f"执行命令: {' '.join(cmd)}")
        
        try:
            # 使用subprocess运行，实时输出日志
            result = subprocess.run(
                cmd, 
                check=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                text=True,
                errors='replace' # 防止编码错误
            )
            print(f"成功: {os.path.basename(input_file)} -> {os.path.basename(output_file)}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"错误: 转换失败 {input_file}")
            print(e.output)
            return False
        except FileNotFoundError:
            print(f"错误: 未找到 ffmpeg。请确保 '{self.ffmpeg_path}' 在系统PATH中或指定正确路径。")
            return False