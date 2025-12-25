import subprocess
import os
import sys
import re
import time
from pathlib import Path

class FFmpegProcessor:
    def __init__(self, ffmpeg_path="ffmpeg"):
        self.ffmpeg_path = ffmpeg_path

    def _parse_time(self, time_str):
        try:
            parts = time_str.split(':')
            h, m, s = int(parts[0]), int(parts[1]), float(parts[2])
            return h * 3600 + m * 60 + s
        except (ValueError, IndexError):
            return 0.0

    def _get_duration(self, input_file):
        """使用 ffprobe 获取总时长"""
        ffprobe_path = str(Path(self.ffmpeg_path).parent / "ffprobe")
        if not Path(ffprobe_path).exists():
            ffprobe_path = "ffprobe"  # fallback to PATH

        cmd = [
            ffprobe_path,
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            input_file
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                return float(result.stdout.strip())
        except (ValueError, subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return None

    def run_conversion(self, input_file, output_file, global_opts=None, input_opts=None, output_opts=None):
        """
        正确构建 FFmpeg 命令：
        ffmpeg [global_options] [input_options] -i input [output_options] output
        """
        # 默认全局选项（必须包含 -hide_banner -nostdin）
        cmd = [self.ffmpeg_path]

        # 添加固定全局选项
        cmd += ["-hide_banner", "-nostdin"]

        # 添加用户自定义全局选项
        if global_opts:
            cmd.extend(global_opts)

        # 添加输入选项
        if input_opts:
            cmd.extend(input_opts)

        # 添加输入文件
        cmd += ["-i", input_file]

        # 添加输出选项
        if output_opts:
            cmd.extend(output_opts)

        # 添加输出文件
        cmd.append(output_file)

        print(f"执行命令: {' '.join(cmd)}")

        total_duration = self._get_duration(input_file)

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace'
            )

            last_update = 0

            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break

                if line:
                    match = re.search(r"time=(\d+:\d+:\d+\.\d+)", line)
                    if match:
                        current_time = self._parse_time(match.group(1))
                        now = time.time()
                        if now - last_update > 0.5:
                            if total_duration and total_duration > 0:
                                progress = min(100.0, (current_time / total_duration) * 100)
                                bar_length = 30
                                filled = int(bar_length * progress // 100)
                                bar = '█' * filled + '-' * (bar_length - filled)
                                print(f"\r进度: |{bar}| {progress:.1f}% ({match.group(1)})", end='', flush=True)
                            else:
                                print(f"\r处理中: {match.group(1)}", end='', flush=True)
                            last_update = now

            process.wait()

            if process.returncode == 0:
                print(f"\n✅ 成功: {Path(input_file).name} -> {Path(output_file).name}")
                return True
            else:
                print(f"\n❌ 失败: FFmpeg 返回非零状态码")
                return False

        except FileNotFoundError:
            print(f"\n❌ 错误: 未找到 ffmpeg。请确保 '{self.ffmpeg_path}' 在系统 PATH 中。")
            return False
        except Exception as e:
            print(f"\n❌ 异常: {e}")
            return False