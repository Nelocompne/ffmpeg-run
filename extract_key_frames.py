import cv2
import numpy as np
import subprocess
import os
import tempfile
from pathlib import Path

def extract_key_frames(video_path, threshold=0.3, min_interval=0.5):
    """
    提取视频的关键帧
    threshold: 帧差异阈值，越小越敏感
    min_interval: 最小帧间隔(秒)，避免太频繁的变化
    """
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    key_frames = []
    prev_frame = None
    frame_count = 0
    min_frames_interval = int(fps * min_interval)
    last_key_frame_pos = -min_frames_interval
    
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
                
                if mean_diff > threshold or not key_frames:
                    key_frames.append({
                        'frame': frame,
                        'index': frame_count,
                        'timestamp': frame_count / fps
                    })
                    last_key_frame_pos = frame_count
                    print(f"关键帧 {len(key_frames)}: 帧 {frame_count}, 差异值 {mean_diff:.3f}")
            else:
                # 第一帧
                key_frames.append({
                    'frame': frame,
                    'index': frame_count,
                    'timestamp': 0
                })
                last_key_frame_pos = 0
            
            prev_frame = gray
        else:
            # 跳过帧但更新prev_frame保持连续性
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, (160, 90))
            if prev_frame is None:
                prev_frame = gray
        
        frame_count += 1
    
    cap.release()
    print(f"共提取 {len(key_frames)} 个关键帧，原始总帧数 {total_frames}")
    return key_frames, fps

def render_keyframe_video(key_frames, fps, output_path, original_video_path):
    """
    将关键帧渲染成视频，并合并原音频
    """
    if not key_frames:
        print("没有关键帧")
        return
    
    # 创建临时无音频视频
    temp_video = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
    temp_video.close()
    
    # 获取视频尺寸
    height, width = key_frames[0]['frame'].shape[:2]
    
    # 准备输出视频
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_video.name, fourcc, fps, (width, height))
    
    # 计算每个关键帧应持续多少帧
    total_duration = key_frames[-1]['timestamp']
    frame_durations = []
    
    for i in range(len(key_frames)):
        if i < len(key_frames) - 1:
            duration = key_frames[i + 1]['timestamp'] - key_frames[i]['timestamp']
        else:
            # 最后一帧持续到原视频结束
            cap = cv2.VideoCapture(original_video_path)
            total_duration = cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS)
            cap.release()
            duration = total_duration - key_frames[i]['timestamp']
        
        frame_count = int(duration * fps)
        frame_durations.append(frame_count)
        
        # 写入该关键帧对应的所有帧
        for _ in range(frame_count):
            out.write(key_frames[i]['frame'])
    
    out.release()
    print(f"视频渲染完成，总帧数: {sum(frame_durations)}")
    
    # 合并原音频
    final_output = output_path
    merge_audio(original_video_path, temp_video.name, final_output)
    
    # 清理临时文件
    os.unlink(temp_video.name)

def merge_audio(original_video, video_no_audio, output_path):
    """
    使用ffmpeg合并原视频的音频
    """
    cmd = [
        'ffmpeg',
        '-i', video_no_audio,  # 无音频的视频
        '-i', original_video,  # 原视频（用于提取音频）
        '-c:v', 'copy',        # 复制视频流
        '-c:a', 'aac',         # 音频编码
        '-map', '0:v:0',       # 从第一个输入映射视频
        '-map', '1:a:0',       # 从第二个输入映射音频
        '-shortest',           # 以较短的流为准
        '-y',                  # 覆盖输出文件
        output_path
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"视频已保存到: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"音频合并失败: {e.stderr.decode()}")
        # 如果失败，至少保留无音频的视频
        shutil.copy(video_no_audio, output_path)
        print(f"已保存无音频版本: {output_path}")

def process_video(input_path, output_path, threshold=0.3, min_interval=0.5):
    """
    主处理函数
    threshold: 帧差异阈值 (0.0-1.0)，越小越容易检测到变化
    min_interval: 最小关键帧间隔(秒)，避免变化过快
    """
    print(f"开始处理视频: {input_path}")
    print(f"参数: threshold={threshold}, min_interval={min_interval}s")
    
    # 提取关键帧
    key_frames, fps = extract_key_frames(input_path, threshold, min_interval)
    
    if len(key_frames) < 2:
        print("警告: 只检测到1个关键帧，将使用整个视频作为单帧")
    
    # 渲染视频
    render_keyframe_video(key_frames, fps, output_path, input_path)

# 使用示例
if __name__ == "__main__":
    input_video = "//alice.xn--90w1j/sub1000/brec/4233412-非門Feemnn/录制-4233412-20260123-155119-300-【B站限定】清楚的巨大学中文.flv"   # 输入视频路径
    output_video = "10s_output_keyframes.mp4"  # 输出视频路径
    
    # 调整参数来适应你的视频
    process_video(
        input_video, 
        output_video, 
        threshold=0.2,      # 帧差异阈值，根据你的视频调整（0.1-0.5）
        min_interval=5   # 最小关键帧间隔（秒）
    )
