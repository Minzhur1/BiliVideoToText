# api_handler.py - 处理第三方语音识别API
import requests
import time
import json
from typing import Optional, Tuple
import os


class TranscriptionAPI:
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化转录API处理器
        目前使用免费/测试API，后续可替换为付费API
        """
        self.api_key = api_key or "demo_key"  # 测试用
        self.base_url = "https://api.openai-proxy.com/v1"  # 示例代理API

    def transcribe_audio(self, audio_url: str, language: str = "zh") -> Tuple[str, str]:
        """
        通过API转录音频

        Args:
            audio_url: 音频URL或本地文件路径
            language: 语言代码 (zh, en等)

        Returns:
            (language, text) 语言和转录文本
        """
        print(f"[API] 开始转录，语言: {language}")

        try:
            # 方法1：如果audio_url是本地文件，模拟上传
            if os.path.exists(audio_url):
                return self._simulate_transcription(language)

            # 方法2：如果是URL，尝试调用真实API
            # 这里先返回模拟数据，后续可替换为真实API调用
            time.sleep(2)  # 模拟API调用延迟

            # 根据语言生成模拟文本
            if language == "zh":
                text = f"""这是中文视频的转录文本示例。通过调用语音识别API，我们可以将音频转换为文字。

当前时间: {time.strftime("%Y-%m-%d %H:%M:%S")}
处理语言: 中文
状态: 成功

这是一个模拟的转录结果。实际部署时，这里会调用真实的语音识别API（如OpenAI Whisper API或国内类似服务）。

对于实际应用，你需要：
1. 获取API密钥
2. 设置付费账户
3. 处理API调用限制
4. 管理成本预算

当前演示版用于验证用户需求和基本功能。"""
                return "zh", text
            else:
                text = f"""This is an example English transcription text. By calling speech recognition APIs, we can convert audio to text.

Current time: {time.strftime("%Y-%m-%d %H:%M:%S")}
Processing language: English
Status: Success

This is a simulated transcription result. In actual deployment, this would call a real speech recognition API (like OpenAI Whisper API or similar services).

For real applications, you would need to:
1. Obtain API keys
2. Set up a paid account
3. Handle API rate limits
4. Manage cost budgeting

This demo version is for validating user demand and basic functionality."""
                return "en", text

        except Exception as e:
            print(f"[API] 转录失败: {e}")
            # 返回模拟数据作为降级方案
            return language, f"转录服务暂时不可用，请稍后重试。错误: {str(e)}"

    def _simulate_transcription(self, language: str) -> Tuple[str, str]:
        """模拟转录过程"""
        time.sleep(3)  # 模拟处理时间

        if language == "zh":
            text = """语音识别API转录结果示例：

各位观众大家好，欢迎收看今天的视频。今天我们讨论的主题是如何将B站视频快速转换为文字稿。

这种方法有很多应用场景：
1. 学习笔记：学生可以快速记录课程重点
2. 内容创作：自媒体作者可以提取视频文案
3. 无障碍访问：为听力障碍者提供文字内容
4. 多语言翻译：先转文字再翻译

技术实现上，我们使用了先进的语音识别技术，能够准确识别中文普通话和多种方言。识别准确率在清晰音频条件下可达95%以上。

注意事项：
- 背景音乐或噪音可能影响识别准确率
- 多人对话场景需要更高级的处理
- 专业术语可能需要后期校对

感谢使用我们的服务！"""
            return "zh", text
        else:
            text = """Speech recognition API transcription example:

Hello everyone, welcome to today's video. Today we're discussing how to quickly convert Bilibili videos into text transcripts.

This method has many application scenarios:
1. Study notes: Students can quickly record key points of lectures
2. Content creation: Content creators can extract video scripts
3. Accessibility: Provide text content for the hearing impaired
4. Multilingual translation: Convert to text first, then translate

Technically, we use advanced speech recognition technology that can accurately recognize Mandarin Chinese and various dialects. Recognition accuracy can reach over 95% under clear audio conditions.

Notes:
- Background music or noise may affect recognition accuracy
- Multi-person conversations require more advanced processing
- Professional terminology may need post-editing

Thank you for using our service!"""
            return "en", text

    def estimate_cost(self, duration_seconds: int, language: str = "zh") -> float:
        """估算处理成本（单位：元）"""
        # OpenAI Whisper API 价格：$0.006/分钟 ≈ 0.043元/分钟
        cost_per_minute = 0.043
        minutes = duration_seconds / 60
        estimated_cost = minutes * cost_per_minute

        print(f"[成本估算] 时长: {minutes:.1f}分钟, 预估成本: ¥{estimated_cost:.3f}")
        return estimated_cost


# 工具函数
def get_video_info(url: str) -> dict:
    """获取视频基本信息"""
    import yt_dlp

    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            return {
                'title': info.get('title', '未知标题'),
                'duration': info.get('duration', 0),
                'uploader': info.get('uploader', '未知上传者'),
                'view_count': info.get('view_count', 0),
                'thumbnail': info.get('thumbnail', ''),
            }
    except Exception as e:
        print(f"[视频信息] 获取失败: {e}")
        return {
            'title': '视频信息获取失败',
            'duration': 0,
            'uploader': '未知',
            'view_count': 0,
            'thumbnail': '',
        }