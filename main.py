# main.py - 修改为可接收参数版本
import bilibili_tools as bt
import audio_to_text as att
import os
import datetime
import sys
import zhconv

# 原来的测试链接保留，用于无参数时备用
chinese_video = "https://www.bilibili.com/video/BV1Z4RHYKEcB/?buvid=Y14FDA1BD71A315A4DAC9841A1FC203958A0&from_spmid=united.player-video-detail.relatedvideo.0&is_story_h5=false&mid=l%2Bd%2Fib0w3kRQyZrx1pQbDX8FTQ%2FSZMtL1rElX6M3iMo%3D&plat_id=114&share_from=ugc&share_medium=iphone&share_plat=ios&share_session_id=2F11EC94-3E85-48F9-B213-938571CD0B01&share_source=weixin&share_tag=s_i&timestamp=1768996789&unique_k=nmC2y2x&up_id=46405906&vd_source=688f060be2ebf588fd3d3d3e983cb009"
english_video = "https://www.bilibili.com/video/BV1b8i7BpEfv?buvid=Y14FDA1BD71A315A4DAC9841A1FC203958A0&from_spmid=tm.recommend.0.0&is_story_h5=false&mid=l%2Bd%2Fib0w3kRQyZrx1pQbDX8FTQ%2FSZMtL1rElX6M3iMo%3D&plat_id=114&share_from=ugc&share_medium=iphone&share_plat=ios&share_session_id=057014A8-A599-4BD0-8C52-4F7B96129EF8&share_source=WEIXIN&share_tag=s_i&timestamp=1768814878&unique_k=6O6vxhq&up_id=36141489"


def main(video_url=None, model_size="medium", output_filename="转录结果.txt"):
    """
    主处理函数
    Args:
        video_url: 视频链接
        model_size: 模型大小
        output_filename: 输出文件名（完整路径）
    """
    # 决定使用哪个链接
    if video_url is None:
        url = chinese_video
        print(f"[信息] 使用测试链接: {url[:50]}...")
    else:
        url = video_url

    print("=== B站视频转文字工具 ===")
    print("=" * 40)
    print(f"处理链接: {url}")
    print(f"使用模型: {model_size}")
    print(f"输出文件: {output_filename}")
    print("=" * 40)

    # 1. 下载视频
    print("\n[1/3] 下载视频...")
    video_file = "temp_video.mp4"
    if not bt.download_bilibili_video(url, video_file):
        print("视频下载失败")
        return None

    # 2. 提取音频
    print("\n[2/3] 提取音频...")
    audio_file = "temp_audio.wav"
    if not bt.extract_audio_from_video(video_file, audio_file):
        print("音频提取失败")
        return None

    # 3. 语音转文字
    print(f"\n[3/3] 语音转文字 (使用{model_size}模型)...")

    # 调用音频转文字函数
    lang, text = att.detect_and_transcribe(audio_file, model_size=model_size)

    if not text:
        print("转录失败")
        return None

    print(f"转录成功！语言: {lang}")
    print(f"原始文本长度: {len(text)} 字符")

    # 4. 中文处理：繁体转简体
    if lang == 'zh':
        print("\n中文处理：繁体转简体...")
        text = zhconv.convert(text, 'zh-cn')
        print("繁转简完成")

    # 5. 生成时间戳
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # 6. 保存文件
    print(f"\n保存文件: {output_filename}")

    # 确保目录存在
    output_dir = os.path.dirname(output_filename)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(output_filename, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("B站视频转录结果\n")
        f.write("=" * 60 + "\n\n")

        f.write(f"视频链接: {url}\n")
        f.write(f"处理时间: {timestamp}\n")
        f.write(f"使用模型: {model_size}\n")
        f.write(f"检测语言: {lang}\n")
        f.write(f"文本长度: {len(text)} 字符\n")

        f.write("\n" + "=" * 60 + "\n")
        f.write("转录文本:\n")
        f.write("=" * 60 + "\n\n")

        f.write(text)

    print(f"文件保存成功！")

    # 7. 显示文件信息
    if os.path.exists(output_filename):
        size_kb = os.path.getsize(output_filename) / 1024
        print(f"文件大小: {size_kb:.1f} KB")

    # 8. 预览内容
    print(f"\n内容预览（前300字符）:")
    print("-" * 60)
    preview = text[:300] + "..." if len(text) > 300 else text
    print(preview)
    print("-" * 60)

    # 9. 清理临时文件
    print(f"\n清理临时文件...")
    for temp_file in [video_file, audio_file]:
        if os.path.exists(temp_file):
            os.remove(temp_file)
            print(f"  已删除: {temp_file}")

    print(f"\n处理完成！")
    return output_filename  # 返回文件路径


if __name__ == "__main__":
    # 检查是否通过命令行传递了参数
    if len(sys.argv) > 1:
        video_url = sys.argv[1]

        model_size = sys.argv[2] if len(sys.argv) > 2 else "medium"

        # 第三个参数是输出文件路径
        output_filename = sys.argv[3] if len(sys.argv) > 3 else "转录结果.txt"

        main(video_url=video_url, model_size=model_size, output_filename=output_filename)
    else:
        print("=== 交互模式 ===")
        print("1. 直接使用测试链接")
        print("2. 输入自定义链接")

        choice = input("请选择 (1/2): ").strip()

        if choice == "2":
            user_url = input("请输入B站视频链接: ").strip()
            if user_url:
                model_choice = input("模型大小 (1.small 2.medium 3.large-v3，默认2): ").strip()
                model_map = {"1": "small", "2": "medium", "3": "large-v3"}
                model_size = model_map.get(model_choice, "medium")
                main(video_url=user_url, model_size=model_size)
            else:
                print("使用测试链接...")
                main()
        else:
            main()