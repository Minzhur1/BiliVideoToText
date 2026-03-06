import os
import sys
import io
from faster_whisper import WhisperModel

# 修复 Windows 编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='ignore')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='ignore')


def detect_and_transcribe(audio_path, model_size="small"):
    """
    自动检测语言并转录
    中文使用优化参数，英文保持原样
    """
    if not os.path.exists(audio_path):
        print(f"❌ 文件不存在: {audio_path}")
        return None, None

    print(f"🔍 语音转文字中...")

    try:
        return _transcribe_faster_optimized(audio_path, model_size)
    except Exception as e:
        print(f"❌ 转录失败: {e}")
        return None, None


def _transcribe_faster_optimized(audio_path, model_size="small"):
    """
    使用Faster-Whisper，针对不同语言优化参数
    """
    # 1. 先检测语言
    print("检测语言中...")

    # 对于中文，使用更大的模型或优化参数
    if model_size == "small" or model_size == "tiny":
        detect_model = WhisperModel("base", device="cpu", compute_type="int8")
    else:
        detect_model = WhisperModel(model_size, device="cpu", compute_type="int8")

    segments, info = detect_model.transcribe(audio_path, beam_size=1)
    detected_lang = info.language
    lang_prob = info.language_probability

    # 语言名称映射
    lang_names = {
        'zh': '中文', 'en': '英文', 'ja': '日文',
        'ko': '韩文', 'fr': '法文', 'de': '德文',
        'es': '西班牙文', 'ru': '俄文'
    }
    lang_name = lang_names.get(detected_lang, detected_lang)

    print(f"✅ 检测到语言: {lang_name} ({detected_lang}), 置信度: {lang_prob:.2%}")

    # 2. 根据语言选择转录策略
    if detected_lang == 'zh':
        print("🀄 使用中文优化参数...")
        return _transcribe_chinese_optimized(audio_path, model_size)
    else:
        print(f"🌍 使用标准参数处理{lang_name}...")
        return _transcribe_standard(audio_path, detected_lang, model_size)


def _transcribe_chinese_optimized(audio_path, model_size="small"):
    """
    中文优化转录
    """
    # 中文推荐使用至少medium模型
    if model_size in ["tiny", "small", "base"]:
        print("💡 建议：中文内容使用medium或large模型效果更好")

    # 加载模型
    model = WhisperModel(
        model_size,
        device="cpu",
        compute_type="int8",
        download_root="./models"
    )

    print("开始中文转录（优化模式）...")

    # 中文优化参数
    segments, info = model.transcribe(
        audio_path,
        language="zh",
        beam_size=8,
        best_of=5,
        temperature=0.0,
        vad_filter=True,
        vad_parameters=dict(
            min_silence_duration_ms=500,
            speech_pad_ms=200
        ),
        initial_prompt="这是一段中文语音"
    )

    texts = []
    for segment in segments:
        texts.append(segment.text)

    text = " ".join(texts).strip()
    print(f"✅ 中文转录完成！长度: {len(text)} 字符")

    return "zh", text


def _transcribe_standard(audio_path, language, model_size="small"):
    """
    标准转录（主要用于英文和其他语言）
    """
    model = WhisperModel(
        model_size,
        device="cpu",
        compute_type="int8",
        download_root="./models"
    )

    print(f"开始{language}转录...")

    segments, info = model.transcribe(
        audio_path,
        language=language,
        beam_size=5,
        best_of=3,
        temperature=0.0,
        vad_filter=True
    )

    texts = []
    for segment in segments:
        texts.append(segment.text)

    text = " ".join(texts).strip()
    print(f"✅ {language}转录完成！长度: {len(text)} 字符")

    return language, text


def test():
    """测试功能"""
    if os.path.exists("test.wav"):
        lang, text = detect_and_transcribe("test.wav", "tiny")
        if text:
            print(f"\n预览: {text[:100]}...")
    else:
        print("❌ 请先准备test.wav文件")


if __name__ == "__main__":
    test()
