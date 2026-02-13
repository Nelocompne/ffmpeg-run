import yaml
import os
from pathlib import Path
from string import Template

class ConfigManager:
    def __init__(self, config_path=None):
        self.default_config = {
            "ffmpeg_params": ["-c:v", "libx264", "-crf", "23", "-preset", "fast", "-c:a", "aac"],
            "output_suffix": "_converted",
            "output_format": "mp4",
            "output_dir": "./output",
            "mode": "convert",  # convert 或 keyframe
            "keyframe_options": {
                "threshold": 0.3,
                "min_interval": 0.5
            }
        }
        self.config = self.load_config(config_path) if config_path else self.default_config

    def load_config(self, config_path):
        """加载YAML配置文件"""
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = yaml.safe_load(f)
                # 合并配置，保留默认值作为后备
                return {**self.default_config, **user_config}
        return self.default_config

    def build_output_filename(self, input_path, custom_field=""):
        """
        根据配置中的模板生成输出文件名。
        支持：[原文件名]_[自定义字段].[格式]
        """
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_format = self.config['output_format']
        
        raw_template = self.config.get('output_template', "$name$custom.$ext")
        template = Template(raw_template)
        output_name = template.substitute(
            name=base_name,
            custom=f"{custom_field}" if custom_field else "",
            ext=output_format
        )
        return output_name

    def get_output_path(self, input_path, custom_field=""):
        """
        构建完整的输出路径，支持绝对路径和相对路径。
        """
        filename = self.build_output_filename(input_path, custom_field)
        output_dir = self.config['output_dir']

        # 使用 pathlib 处理路径（推荐方式）
        output_path = Path(output_dir)

        # 如果是相对路径，则基于当前工作目录解析
        if not output_path.is_absolute():
            output_path = Path.cwd() / output_path

        # 创建输出目录（包括父级）
        output_path.mkdir(parents=True, exist_ok=True)

        return str(output_path / filename)
    
    def get_mode(self):
        """获取处理模式: convert 或 keyframe"""
        return self.config.get('mode', 'convert')
    
    def get_keyframe_options(self):
        """获取关键帧提取选项"""
        return self.config.get('keyframe_options', {
            'threshold': 0.3,
            'min_interval': 0.5
        })