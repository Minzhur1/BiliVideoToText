import yt_dlp
import os
import subprocess
import sys

def download_bilibili_video(url, output_file):
    try:
        print(" 开始下载视频...")
        print(f"链接: {url}")

        if output_file.endswith('.mp4'):
            output_base = output_file[:-4]
        else:
            output_base = output_file

        ydl_opts = {
            'outtmpl': output_base,
            'quiet': False,
            'no_warnings': False,
            # 改成这个：只要有视频+音频就行，不限分辨率
            'format': 'bestvideo+bestaudio/best',
            'ignoreerrors': False,
            'no_color': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            print(f"[BiliBili] 找到视频: {info.get('title', '未知')}")
            
            formats = info.get('formats', [])
            if formats:
                print(f"可用格式 (前3个):")
                for i, f in enumerate(formats[:3]):
                    format_note = f.get('format_note', '未知')
                    height = f.get('height', '未知')
                    ext = f.get('ext', '未知')
                    has_video = f.get('vcodec') != 'none'
                    has_audio = f.get('acodec') != 'none'
                    type_desc = "音视频" if has_video and has_audio else ("视频" if has_video else "音频")
                    print(f"  {i + 1}. {format_note} {height}p ({ext}) - {type_desc}")

            print("开始下载...")
            ydl.download([url])

            downloaded_files = []
            possible_extensions = ['.mp4', '.mkv', '.webm']

            for ext in possible_extensions:
                possible_file = output_base + ext
                if os.path.exists(possible_file):
                    downloaded_files.append(possible_file)

            import glob
            pattern_files = glob.glob(output_base + ".*")
            for f in pattern_files:
                if f not in downloaded_files and any(f.endswith(ext) for ext in possible_extensions):
                    downloaded_files.append(f)

            if downloaded_files:
                actual_file = downloaded_files[0]

                if actual_file != output_file:
                    if os.path.exists(output_file):
                        os.remove(output_file)
                    os.rename(actual_file, output_file)
                    print(f"重命名: {os.path.basename(actual_file)} -> {os.path.basename(output_file)}")

                file_size = os.path.getsize(output_file) / 1024 / 1024
                print(f" 下载成功！")
                print(f"文件: {output_file} ({file_size:.1f} MB)")
                return True
            else:
                print(" 下载失败: 未找到下载的文件")
                return False

    except Exception as e:
        print(f" 下载失败: {e}")
        return False

def extract_audio_from_video(video_file, audio_file):
    try:
        print(" 提取音频...")

        if not os.path.exists(video_file):
            print(f" 视频文件不存在: {video_file}")
            import glob
            possible_files = glob.glob("temp_video*")
            video_files = [f for f in possible_files if f.lower().endswith(('.mp4', '.mkv', '.webm', '.flv'))]

            if video_files:
                video_file = video_files[0]
                print(f" 找到视频文件: {video_file}")
            else:
                print(" 未找到任何视频文件")
                return False

        print(f" 输入视频: {video_file}")
        file_size = os.path.getsize(video_file) / 1024 / 1024
        print(f" 文件大小: {file_size:.1f} MB")

        command = [
            'ffmpeg',
            '-i', video_file,
            '-vn',
            '-acodec', 'pcm_s16le',
            '-ar', '16000',
            '-ac', '1',
            audio_file,
            '-y',
            '-loglevel', 'warning'
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )

        if result.returncode == 0:
            if os.path.exists(audio_file) and os.path.getsize(audio_file) > 0:
                audio_size = os.path.getsize(audio_file) / 1024
                print(f" 音频提取成功！")
                print(f" 音频文件: {audio_file} ({audio_size:.1f} KB)")
                return True
            else:
                print(" 音频提取失败: 输出文件为空")
                return False
        else:
            error_msg = result.stderr[:300] if result.stderr else "未知错误"
            print(f" 音频提取失败: {error_msg}")
            return False

    except FileNotFoundError:
        print(" 音频提取失败: ffmpeg未找到")
        return False
    except Exception as e:
        print(f" 音频提取失败: {e}")
        return False

