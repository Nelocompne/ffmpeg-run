import os
import platform
from pathlib import Path

def is_network_path(path_str):
    """
    判断路径是否为网络路径。
    Windows下检查是否以 \\ 开头，Linux下通常检查是否为 // 或特定挂载点。
    """
    path = str(path_str)
    if platform.system() == "Windows":
        return path.startswith("\\\\")
    else:
        # Linux下通常网络路径挂载在 /mnt 或 /media，或者以 // 开头
        return path.startswith("//") or path.startswith("/mnt/") or path.startswith("/media/")

def normalize_path(path_str):
    """
    规范化路径分隔符 (主要针对Windows传入的混合斜杠)
    """
    return str(Path(path_str).resolve())