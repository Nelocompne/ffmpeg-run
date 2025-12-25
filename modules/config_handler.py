import yaml
import os
from string import Template

class ConfigManager:
    def __init__(self, config_path=None):
        self.default_config = {
            "ffmpeg_params": ["-c:v", "libx264", "-crf", "23", "-preset", "fast", "-c:a", "aac"],
            "output_suffix": "_converted",
            "output_format": "mp4",
            "output_dir": "./output"
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
        input_path = os.path.normpath(input_path)
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_format = self.config['output_format']
        
        # 简单的模板替换逻辑
        # 用户可以在配置中写 "[name]_[custom].ext" 或直接在这里硬编码规则
        raw_template = self.config.get('output_template', "$name$custom.$ext")
        
        # 使用Python的Template进行安全替换
        template = Template(raw_template)
        output_name = template.substitute(
            name=base_name,
            custom=f"_{custom_field}" if custom_field else "",
            ext=output_format
        )
        
        return output_name

    def get_output_path(self, input_path, custom_field=""):
        """构建完整的输出路径"""
        filename = self.build_output_filename(input_path, custom_field)
        output_dir = self.config['output_dir']
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        return os.path.join(output_dir, filename)