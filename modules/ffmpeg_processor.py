import subprocess
import os
import sys
import re
import time
import signal
import threading
import psutil
from pathlib import Path

class FFmpegProcessor:
    def __init__(self, ffmpeg_path="ffmpeg"):
        self.ffmpeg_path = ffmpeg_path
        self.current_proc = None          # subprocess.Popen 对象
        self.current_psutil_proc = None   # psutil.Process 对象（FFmpeg 主进程）
        self._lock = threading.Lock()
        self._progress_info = {"current_time": "00:00:00.000", "total_duration": None}
        self._stop_event = threading.Event()
        self._suspended = False

    def _parse_time(self, time_str):
        try:
            parts = time_str.split(':')
            h, m, s = int(parts[0]), int(parts[1]), float(parts[2])
            return h * 3600 + m * 60 + s
        except (ValueError, IndexError):
            return 0.0

    def _get_duration(self, input_file):
        ffprobe_path = str(Path(self.ffmpeg_path).parent / "ffprobe")
        if not Path(ffprobe_path).exists():
            ffprobe_path = "ffprobe"

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

    def _suspend_process_tree(self, proc):
        """递归挂起进程及其所有子进程（Windows 更有效）"""
        try:
            children = proc.children(recursive=True)
            for child in reversed(children):  # 先挂起子进程
                if child.is_running():
                    if sys.platform == "win32":
                        child.suspend()
                    else:
                        child.send_signal(signal.SIGSTOP)
            if proc.is_running():
                if sys.platform == "win32":
                    proc.suspend()
                else:
                    proc.send_signal(signal.SIGSTOP)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    def _resume_process_tree(self, proc):
        """递归恢复进程树"""
        try:
            if proc.is_running():
                if sys.platform == "win32":
                    proc.resume()
                else:
                    proc.send_signal(signal.SIGCONT)
            children = proc.children(recursive=True)
            for child in children:  # 后恢复子进程
                if child.is_running():
                    if sys.platform == "win32":
                        child.resume()
                    else:
                        child.send_signal(signal.SIGCONT)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    def pause_current_task(self):
        with self._lock:
            if self.current_psutil_proc and not self._suspended:
                self._suspend_process_tree(self.current_psutil_proc)
                self._suspended = True
                print("\n⏸️  FFmpeg 任务已暂停。按 'r' 恢复，'q' 退出。")
                return True
        return False

    def resume_current_task(self):
        with self._lock:
            if self.current_psutil_proc and self._suspended:
                self._resume_process_tree(self.current_psutil_proc)
                self._suspended = False
                print("\n▶️  FFmpeg 任务已恢复。")
                return True
        return False

    def stop_current_task(self):
        with self._lock:
            if self.current_psutil_proc and self.current_psutil_proc.is_running():
                try:
                    # 先尝试优雅终止
                    self.current_psutil_proc.terminate()
                    gone, alive = psutil.wait_procs([self.current_psutil_proc], timeout=3)
                    for p in alive:
                        # 强制杀死（包括子进程）
                        for child in p.children(recursive=True):
                            try:
                                child.kill()
                            except psutil.NoSuchProcess:
                                pass
                        try:
                            p.kill()
                        except psutil.NoSuchProcess:
                            pass
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
    
            self.current_proc = None
            self.current_psutil_proc = None
            self._stop_event.set()
            self._suspended = False
            print("\n⏹️  FFmpeg 任务已强制终止。")
            return True

    def _stdout_reader(self, pipe):
        """独立线程读取 stdout 并解析进度"""
        while not self._stop_event.is_set():
            line = pipe.readline()
            if not line:
                break
            match = re.search(r"time=(\d+:\d+:\d+\.\d+)", line)
            if match:
                with self._lock:
                    self._progress_info["current_time"] = match.group(1)

    def run_conversion(self, input_file, output_file, global_opts=None, input_opts=None, output_opts=None):
        cmd = [self.ffmpeg_path, "-hide_banner", "-nostdin"]
        if global_opts:
            cmd.extend(global_opts)
        if input_opts:
            cmd.extend(input_opts)
        cmd += ["-i", input_file]
        if output_opts:
            cmd.extend(output_opts)
        cmd.append(output_file)

        print(f"执行命令: {' '.join(cmd)}")

        total_duration = self._get_duration(input_file)
        with self._lock:
            self._progress_info["total_duration"] = total_duration

        try:
            self._stop_event.clear()
            self._suspended = False

            with self._lock:
                self.current_proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    encoding='utf-8',
                    errors='replace',
                    bufsize=1  # 行缓冲
                )
                self.current_psutil_proc = psutil.Process(self.current_proc.pid)

            # 启动 stdout 读取线程（非阻塞）
            reader_thread = threading.Thread(
                target=self._stdout_reader,
                args=(self.current_proc.stdout,),
                daemon=True
            )
            reader_thread.start()

            # 主循环：显示进度（每 0.5 秒）
            last_update = 0
            while self.current_proc.poll() is None:
                now = time.time()
                if now - last_update > 0.5:
                    with self._lock:
                        current_time_str = self._progress_info["current_time"]
                        total = self._progress_info["total_duration"]

                    if total and total > 0:
                        current_sec = self._parse_time(current_time_str)
                        progress = min(100.0, (current_sec / total) * 100)
                        bar_length = 30
                        filled = int(bar_length * progress // 100)
                        bar = '█' * filled + '-' * (bar_length - filled)
                        print(f"\r进度: |{bar}| {progress:.1f}% ({current_time_str})", end='', flush=True)
                    else:
                        print(f"\r处理中: {current_time_str}", end='', flush=True)
                    last_update = now

                time.sleep(0.1)  # 避免忙等待

            # 等待读取线程结束
            reader_thread.join(timeout=1)

            success = self.current_proc.returncode == 0

            with self._lock:
                self.current_proc = None
                self.current_psutil_proc = None

            if success:
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