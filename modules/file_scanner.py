import os
from pathlib import Path

# 常见的音视频文件扩展名
SUPPORTED_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', 
                        '.mp3', '.wav', '.flac', '.aac', '.m4a'}

class FileScanner:
    @staticmethod
    def is_media_file(filepath):
        return Path(filepath).suffix.lower() in SUPPORTED_EXTENSIONS

    @staticmethod
    def scan(source):
        """
        扫描输入源，返回文件路径列表。
        source 可以是文件或目录。
        """
        files = []
        source = str(source)
        
        if os.path.isfile(source):
            if FileScanner.is_media_file(source):
                files.append(source)
        elif os.path.isdir(source):
            for root, _, filenames in os.walk(source):
                for fname in filenames:
                    fpath = os.path.join(root, fname)
                    if FileScanner.is_media_file(fpath):
                        files.append(fpath)
        else:
            print(f"警告: 路径不存在 {source}")
        return files