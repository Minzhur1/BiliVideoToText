
import yt_dlp
import os
import subprocess
import sys


def download_bilibili_video(url, output_file):
    """
    下载B站视频
    Args:
        url: B站视频链接
        output_file: 输出文件名
    Returns:
        bool: 下载是否成功
    """
    try:
        print(" 开始下载视频...")
        print(f"链接: {url}")

        # 准备输出文件路径
        if output_file.endswith('.mp4'):
            output_base = output_file[:-4]
        else:
            output_base = output_file

        # yt-dlp配置 - 简化版本，避免复杂格式选择
        ydl_opts = {
            'outtmpl': output_base,
            'quiet': False,
            'no_warnings': False,
            'format': 'best[height<=720]',  # 直接用已合并的格式
            # 删掉 format_sort 和 merge_output_format

            # 核心修改：使用简单的格式选择字符串
            # 优先选择720p以下的已合并音视频格式
            'format': 'bv*[height<=720]+ba/b[height<=720]',

            # 备用：如果上面找不到，选择最佳质量但限制720p
            #'format_sort': ['res:720', 'ext:mp4:m4a'],

            # 简化合并设置
            #'merge_output_format': 'mp4',

            # 其他设置
            'ignoreerrors': False,
            'no_color': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 先获取信息看看可用格式
            info = ydl.extract_info(url, download=False)
            print(f"[BiliBili] 找到视频: {info.get('title', '未知')}")

            # 显示可用的格式（前3个）
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

            # 开始下载
            print("开始下载...")
            ydl.download([url])

            # 检查下载的文件
            downloaded_files = []
            possible_extensions = ['.mp4', '.mkv', '.webm']

            for ext in possible_extensions:
                possible_file = output_base + ext
                if os.path.exists(possible_file):
                    downloaded_files.append(possible_file)

            # 也检查带数字后缀的文件（yt-dlp有时会添加）
            import glob
            pattern_files = glob.glob(output_base + ".*")
            for f in pattern_files:
                if f not in downloaded_files and any(f.endswith(ext) for ext in possible_extensions):
                    downloaded_files.append(f)

            if downloaded_files:
                # 使用第一个找到的文件
                actual_file = downloaded_files[0]

                # 如果实际文件名不是我们想要的，重命名
                if actual_file != output_file:
                    # 先删除可能存在的旧文件
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
                # 列出当前目录所有文件
                print("当前目录内容:")
                for f in os.listdir('.'):
                    print(f"  - {f}")
                return False

    except yt_dlp.utils.DownloadError as e:
        print(f" 下载失败 (DownloadError): {e}")

        # 尝试最简单的格式
        try:
            print("尝试使用'worst'格式...")
            simple_opts = {
                'outtmpl': output_base,
                'format': 'worst',
                'quiet': False,
            }
            with yt_dlp.YoutubeDL(simple_opts) as ydl:
                ydl.download([url])

            # 检查是否成功
            if os.path.exists(output_base + '.mp4'):
                os.rename(output_base + '.mp4', output_file)
                print(f" 使用最简单格式下载成功")
                return True
        except Exception as e2:
            print(f" 备用方案也失败: {e2}")

        return False

    except Exception as e:
        print(f" 下载失败 (其他错误): {e}")
        import traceback
        traceback.print_exc()

        # 最后的尝试：最简化的格式选择
        try:
            print("最后尝试: 使用默认格式...")
            default_opts = {
                'outtmpl': output_base,
                'quiet': False,
            }
            with yt_dlp.YoutubeDL(default_opts) as ydl:
                ydl.download([url])

            # 检查下载
            import glob
            for ext in ['.mp4', '.mkv', '.webm']:
                if os.path.exists(output_base + ext):
                    os.rename(output_base + ext, output_file)
                    print(f" 最终尝试成功")
                    return True
        except Exception as e3:
            print(f" 所有尝试都失败: {e3}")

        return False


def extract_audio_from_video(video_file, audio_file):
    """
    从视频中提取音频
    Args:
        video_file: 视频文件路径
        audio_file: 音频输出文件路径
    Returns:
        bool: 提取是否成功
    """
    try:
        print(" 提取音频...")

        # 检查视频文件是否存在
        if not os.path.exists(video_file):
            print(f" 视频文件不存在: {video_file}")

            # 尝试寻找可能的文件
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

        # 构建ffmpeg命令
        command = [
            'ffmpeg',
            '-i', video_file,
            '-vn',
            '-acodec', 'pcm_s16le',
            '-ar', '16000',
            '-ac', '1',
            audio_file,
            '-y',
            '-loglevel', 'warning'  # 减少输出
        ]

        # 执行命令
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
            print(f" 音频提取失败:")
            print(f"  错误: {error_msg}")
            return False

    except FileNotFoundError:
        print(" 音频提取失败: ffmpeg未找到")
        print(" 请确保ffmpeg已正确安装并添加到PATH")
        return False
    except Exception as e:
        print(f" 音频提取失败: {e}")
        return False


# 简单的测试
if __name__ == "__main__":
    print("测试bilibili_tools模块...")
    # 这里可以添加简单的自测试代码

    print("模块加载成功，请通过main.py或app.py使用")
