import os
import sys
import io
import whisper

# 修复 Windows 编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='ignore')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='ignore')


def detect_and_transcribe(audio_path, model_size="small"):
    """
    自动检测语言并转录
    """
    if not os.path.exists(audio_path):
        print(f"❌ 文件不存在: {audio_path}")
        return None, None

    print(f"🔍 语音转文字中...")

    try:
        # 直接使用官方 whisper
        return _transcribe_whisper(audio_path, model_size)
    except Exception as e:
        print(f"❌ 转录失败: {e}")
        return None, None


def _transcribe_whisper(audio_path, model_size="small"):
    """
    使用官方 whisper 转录
    """
    print(f"加载模型 {model_size}...")
    
    # 加载模型
    model = whisper.load_model(model_size)
    
    print("开始转录...")
    
    # 转录
    result = model.transcribe(
        audio_path,
        fp16=False,  # CPU 模式
        verbose=False
    )
    
    text = result["text"].strip()
    detected_lang = result["language"]
    
    # 语言名称映射
    lang_names = {
        'zh': '中文', 'en': '英文', 'ja': '日文',
        'ko': '韩文', 'fr': '法文', 'de': '德文',
        'es': '西班牙文', 'ru': '俄文'
    }
    lang_name = lang_names.get(detected_lang, detected_lang)
    
    print(f"✅ 转录完成！语言: {lang_name}, 长度: {len(text)} 字符")
    
    return detected_lang, text


# 简洁的测试函数
def test():
    """测试功能"""
    if os.path.exists("test.wav"):
        lang, text = detect_and_transcribe("test.wav", "tiny")  # 测试用 tiny 更快
        if text:
            print(f"\n预览: {text[:100]}...")
    else:
        print("❌ 请先准备test.wav文件")


if __name__ == "__main__":
    test()
