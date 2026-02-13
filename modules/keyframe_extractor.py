import cv2
import numpy as np
import subprocess
import os
import tempfile
import shlex
from pathlib import Path

class KeyFrameExtractor:
    """关键帧提取器 - 用于检测和提取视频的关键帧"""
    
    def __init__(self, threshold=0.3, min_interval=0.5):
        """
        初始化关键帧提取器
        
        Args:
            threshold: 帧差异阈值 (0.0-1.0)，越小越容易检测到变化
            min_interval: 最小关键帧间隔(秒)，避免变化过快
        """
        self.threshold = threshold
        self.min_interval = min_interval
    
    def extract_key_frames(self, video_path):
        """
        提取视频的关键帧
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            tuple: (关键帧列表, fps)
        """
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        key_frames = []
        prev_frame = None
        frame_count = 0
        min_frames_interval = int(fps * self.min_interval)
        last_key_frame_pos = -min_frames_interval
        
        print(f"开始提取关键帧: {Path(video_path).name}")
        print(f"参数: threshold={self.threshold}, min_interval={self.min_interval}s")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            # 每帧都处理，但只在一定间隔后判断是否需要新关键帧
            if frame_count - last_key_frame_pos >= min_frames_interval:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray = cv2.resize(gray, (160, 90))  # 降低分辨率加快计算
                
                if prev_frame is not None:
                    # 计算帧差异
                    diff = cv2.absdiff(gray, prev_frame)
                    mean_diff = np.mean(diff) / 255.0
                    
                    if mean_diff > self.threshold or not key_frames:
                        key_frames.append({
                            'frame': frame,
                            'index': frame_count,
                            'timestamp': frame_count / fps
                        })
                        last_key_frame_pos = frame_count
                        print(f"  关键帧 {len(key_frames)}: 帧 {frame_count}, 时间 {frame_count/fps:.2f}s, 差异值 {mean_diff:.3f}")
                else:
                    # 第一帧
                    key_frames.append({
                        'frame': frame,
                        'index': frame_count,
                        'timestamp': 0
                    })
                    last_key_frame_pos = 0
                    print(f"  关键帧 1: 帧 0 (第一帧)")
                
                prev_frame = gray
            else:
                # 跳过帧但更新prev_frame保持连续性
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray = cv2.resize(gray, (160, 90))
                if prev_frame is None:
                    prev_frame = gray
            
            frame_count += 1
            
            # 显示进度
            if frame_count % 100 == 0:
                progress = (frame_count / total_frames) * 100
                print(f"\r  扫描进度: {progress:.1f}% ({frame_count}/{total_frames})", end='', flush=True)
        
        cap.release()
        print(f"\n✅ 共提取 {len(key_frames)} 个关键帧，原始总帧数 {total_frames}")
        return key_frames, fps
    
    def render_keyframe_video(self, key_frames, fps, output_path, original_video_path):
        """
        将关键帧渲染成视频，并合并原音频
        
        Args:
            key_frames: 关键帧列表
            fps: 帧率
            output_path: 输出文件路径
            original_video_path: 原视频路径（用于提取音频）
        """
        if not key_frames:
            print("❌ 没有关键帧可以渲染")
            return False
        
        # 创建临时无音频视频
        temp_video = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        temp_video.close()
        
        try:
            # 获取视频尺寸
            height, width = key_frames[0]['frame'].shape[:2]
            
            # 准备输出视频
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(temp_video.name, fourcc, fps, (width, height))
            
            # 计算每个关键帧应持续多少帧
            cap = cv2.VideoCapture(original_video_path)
            total_duration = cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS)
            cap.release()
            
            frame_durations = []
            total_frames_written = 0
            
            print("开始渲染关键帧视频...")
            for i in range(len(key_frames)):
                if i < len(key_frames) - 1:
                    duration = key_frames[i + 1]['timestamp'] - key_frames[i]['timestamp']
                else:
                    # 最后一帧持续到原视频结束
                    duration = total_duration - key_frames[i]['timestamp']
                
                frame_count = max(1, int(duration * fps))  # 至少写入1帧
                frame_durations.append(frame_count)
                
                # 写入该关键帧对应的所有帧
                for _ in range(frame_count):
                    out.write(key_frames[i]['frame'])
                    total_frames_written += 1
                
                progress = ((i + 1) / len(key_frames)) * 100
                print(f"\r  渲染进度: {progress:.1f}% ({i+1}/{len(key_frames)})", end='', flush=True)
            
            out.release()
            print(f"\n✅ 视频渲染完成，总帧数: {total_frames_written}")
            
            # 合并原音频
            success = self._merge_audio(original_video_path, temp_video.name, output_path)
            
            return success
            
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_video.name)
            except:
                pass
    
    def _merge_audio(self, original_video, video_no_audio, output_path):
        """
        使用 ffmpeg 合并原视频的音频
        
        Args:
            original_video: 原视频路径
            video_no_audio: 无音频的视频路径
            output_path: 输出路径
            
        Returns:
            bool: 是否成功
        """
        cmd = [
            'ffmpeg',
            '-hide_banner',
            '-y',
            '-i', video_no_audio,  # 无音频的视频
            '-i', original_video,  # 原视频（用于提取音频）
            '-c:v', 'copy',        # 复制视频流
            '-c:a', 'aac',         # 音频编码
            '-map', '0:v:0',       # 从第一个输入映射视频
            '-map', '1:a:0?',      # 从第二个输入映射音频（如果存在）
            '-shortest',           # 以较短的流为准
            output_path
        ]
        
        # 安全打印命令
        safe_cmd = ' '.join(shlex.quote(str(arg)) for arg in cmd)
        print(f"合并音频: {safe_cmd}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode == 0:
                print(f"✅ 视频已保存到: {output_path}")
                return True
            else:
                print(f"⚠️ 音频合并失败，尝试保存无音频版本...")
                print(f"   错误信息: {result.stderr}")
                # 如果失败，至少保留无音频的视频
                import shutil
                shutil.copy(video_no_audio, output_path)
                print(f"✅ 已保存无音频版本: {output_path}")
                return True
                
        except FileNotFoundError:
            print("❌ 未找到 ffmpeg，请确保已安装并添加到 PATH")
            return False
        except Exception as e:
            print(f"❌ 音频合并异常: {e}")
            return False
    
    def process_video(self, input_path, output_path):
        """
        主处理函数：提取关键帧并渲染成视频
        
        Args:
            input_path: 输入视频路径
            output_path: 输出视频路径
            
        Returns:
            bool: 是否成功
        """
        print(f"\n{'='*60}")
        print(f"处理视频: {Path(input_path).name}")
        print(f"{'='*60}")
        
        # 提取关键帧
        key_frames, fps = self.extract_key_frames(input_path)
        
        if len(key_frames) < 2:
            print("⚠️ 只检测到1个或更少关键帧，将使用整个视频")
            if len(key_frames) == 0:
                return False
        
        # 渲染视频
        success = self.render_keyframe_video(key_frames, fps, output_path, input_path)
        
        if success:
            print(f"✅ 处理完成: {Path(output_path).name}\n")
        else:
            print(f"❌ 处理失败\n")
        
        return success
