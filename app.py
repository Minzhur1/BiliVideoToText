# app.py - 完整的B站视频转文字工具
import streamlit as st
import subprocess
import sys
import os
import time
import locale
import tempfile
from datetime import datetime

# 导入配额管理和监控模块
from quota_manager import get_quota_manager
from server_monitor import get_server_monitor
from sponsor_page import show_sponsor_page

# 设置页面配置
st.set_page_config(
    page_title="BiliVideoToText",
    page_icon="🎬",
    layout="centered",
    initial_sidebar_state="expanded"
)

# 自定义宽度CSS
st.markdown("""
<style>
    /* 限制主要内容容器宽度 */
    section[data-testid="stMain"] > div {
        max-width: 900px;
        margin: 0 auto;
        padding-left: 1rem;
        padding-right: 1rem;
    }

    /* 确保页面背景全宽 */
    .stApp {
        width: 100% !important;
    }

    /* 侧边栏样式 */
    .css-1d391kg {
        padding-top: 2rem;
    }

    /* 状态标签 */
    .status-badge {
        display: inline-block;
        padding: 0.2rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }

    .status-free {
        background-color: #e7f7ed;
        color: #0a7c42;
        border: 1px solid #a3e9c0;
    }

    .status-sponsor {
        background-color: #fff3cd;
        color: #856404;
        border: 1px solid #ffeaa7;
    }
</style>
""", unsafe_allow_html=True)

# ================ 侧边栏 ================
with st.sidebar:
    st.markdown("### 👤 我的状态")

    # 初始化管理器
    quota_manager = get_quota_manager()
    server_monitor = get_server_monitor()

    # 获取用户状态
    user_status = quota_manager.get_user_status()

    # 显示状态徽章
    col1, col2 = st.columns(2)
    with col1:
        if user_status["free_remaining"] > 0:
            st.markdown(f'<span class="status-badge status-free">🎁 免费: {user_status["free_remaining"]}</span>',
                        unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-badge status-free">🎁 免费: 0</span>', unsafe_allow_html=True)

    with col2:
        if user_status["sponsor_balance"] > 0:
            st.markdown(f'<span class="status-badge status-sponsor">✨ 赞助: {user_status["sponsor_balance"]}</span>',
                        unsafe_allow_html=True)

    # 累计转换
    st.caption(f"📊 累计转换: {user_status['total_converted']} 个视频")

    st.markdown("---")
    st.markdown(f"**🔑 你的用户ID**: `{quota_manager.get_user_id()}`")
    st.caption("赞助时复制这个ID发给我")

    st.divider()

    # 邀请码功能
    with st.expander("🎁 邀请好友得免费次数"):
        st.markdown(f"""
        您的邀请码:  
        **`{user_status['invite_code']}`**

        每邀请一位好友注册并使用，您可获得 **1次额外转换**！
        """)

        invite_input = st.text_input("输入好友邀请码", placeholder="例如：ABC123", key="invite_input")
        if st.button("使用邀请码", use_container_width=True):
            if invite_input:
                success, msg = quota_manager.use_invite_code(invite_input)
                if success:
                    st.success(msg)
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(msg)

    # 赞助入口
    with st.expander("💖 赞助支持"):
        st.markdown("""
        赞助我们，获得更多转换次数！

        - 🥉 **青铜** ¥10 = 10次
        - 🥈 **白银** ¥30 = 35次  
        - 🥇 **黄金** ¥50 = 70次
        """)
        if st.button("查看赞助套餐", use_container_width=True):
            st.session_state["show_sponsor"] = True
            st.rerun()

    # 服务器状态
    st.divider()
    st.markdown("### 🖥️ 服务器状态")
    server_status = server_monitor.get_server_status()

    # 显示服务器状态
    status_color = "🟢" if not server_status["is_busy"] else "🟡"
    st.caption(f"{status_color} {server_status['message']}")

    # 显示资源使用情况
    col1, col2 = st.columns(2)
    with col1:
        st.caption(f"CPU: {server_status['cpu_percent']:.0f}%")
    with col2:
        st.caption(f"内存: {server_status['memory_percent']:.0f}%")

    # 显示队列
    if server_status['processing_count'] > 0:
        st.caption(f"处理中: {server_status['processing_count']} | 等待: {server_status['waiting_count']}")

# ================ 主页面 ================
st.markdown('<p style="font-size:18px; color:#666;"> ❤️让每一段视频，都能被轻松阅读和分析！</p>', unsafe_allow_html=True)

st.title("B站视频转文字工具（免费体验版)")

st.markdown("""
 ⭐ 粘贴链接，一键获取视频文字稿<br>
 ⭐ 已成功转换 **1,000+** 个视频<br>
 ⭐ 免费体验版，暂支持 **5分钟** 视频（赞助用户可延长至30分钟）
""", unsafe_allow_html=True)

st.write("")
st.write("")
st.write("")
st.write("")

# 检查是否显示赞助页面
if st.session_state.get("show_sponsor", False):
    show_sponsor_page()
    if st.button("← 返回主页", use_container_width=True):
        st.session_state["show_sponsor"] = False
        st.rerun()
    st.stop()

# --- 用户输入区域 ---
url = st.text_input(
    "请粘贴B站视频链接，再按Enter",
    placeholder="例如：https://www.bilibili.com/video/BV1xx411c7LU",
    key="url_input"
)

# --- 语言选择 ---
model_size = st.radio(
    "选择识别语言",
    ["英文", "中文"],
    index=0,
    horizontal=True
)

model_map = {
    "英文": "small",
    "中文": "large-v3"
}
selected_model = model_map[model_size]


def extract_pure_text_with_link(full_content, video_url):
    """
    从完整内容中提取信息并格式化为：
    1. 视频链接
    2. 空行
    3. 纯文本内容
    """
    lines = full_content.split('\n')

    # 提取视频链接
    extracted_url = None
    for line in lines:
        if line.startswith("视频链接:"):
            extracted_url = line.replace("视频链接:", "").strip()
            break

    display_url = video_url if video_url else (extracted_url if extracted_url else "未知链接")

    # 提取纯文本内容
    in_text_section = False
    pure_lines = []

    for line in lines:
        if "转录文本:" in line:
            in_text_section = True
            continue

        if "=" * 60 in line:
            continue

        if in_text_section:
            if line.strip() and not line.startswith("转录文本:"):
                pure_lines.append(line)

    # 如果没找到，尝试提取主要内容
    if not pure_lines:
        skip_header = False
        for line in lines:
            if "=" * 60 in line:
                if not skip_header:
                    skip_header = True
                else:
                    continue

            if skip_header and line.strip() and not line.startswith("视频链接:"):
                pure_lines.append(line)

    pure_text = '\n'.join(pure_lines).strip()

    if pure_text:
        return f"视频链接: {display_url}\n\n{pure_text}"
    else:
        return f"视频链接: {display_url}\n\n{full_content[:1000]}"


def check_bilibili_duration(url, max_minutes=5):
    """
    使用yt-dlp检测B站视频时长
    """
    import yt_dlp

    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            duration_seconds = info.get('duration', 0)

            if duration_seconds == 0:
                return False, "无法获取视频时长，请确认链接是否有效"

            duration_minutes = duration_seconds / 60

            if duration_minutes > max_minutes:
                return False, f"视频时长 {duration_minutes:.0f}分钟，超过{max_minutes}分钟限制"

            return True, f"✅ 视频时长: {duration_minutes:.1f} 分钟"

    except Exception as e:
        return False, f"视频检测失败: {str(e)}"


# ================ 核心转换区域 ================
with st.container():
    if st.button("开始转换", type="primary", use_container_width=True):
        if not url:
            st.warning("请输入一个有效的B站视频链接。")
            st.stop()

        # === 检查服务器状态 ===
        server_status = server_monitor.get_server_status()

        if not server_status["can_accept"]:
            st.error(server_status["message"])
            st.info(f"当前处理中: {server_status['processing_count']} 个 | 等待中: {server_status['waiting_count']} 个")
            st.stop()

        # === 获取视频时长 ===
        with st.spinner("正在获取视频信息..."):
            try:
                import yt_dlp

                with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
                    info = ydl.extract_info(url, download=False)
                    duration_seconds = info.get('duration', 0)
                    duration_minutes = duration_seconds / 60
                    video_title = info.get('title', '未知标题')
            except Exception as e:
                st.error(f"无法获取视频信息: {str(e)}")
                st.stop()

        # === 检查配额 ===
        is_allowed, quota_msg, user_data = quota_manager.check_quota(int(duration_minutes))

        # 处理免费额度用完的情况
        if not is_allowed:
            if quota_msg == "free_limit":
                st.error("""
                ### 🎯 免费额度已用完！

                您今天已转换了3个视频，看来您对这个工具很有需求！

                **下一步您可以：**

                1. **🎁 邀请好友** - 每邀请一人得一次免费额度
                   - 点击侧边栏"邀请好友得免费次数"
                   - 分享您的邀请码给朋友

                2. **💖 赞助支持** - 获得更多转换次数
                   - 🥉 青铜 ¥10 = 10次
                   - 🥈 白银 ¥30 = 35次  
                   - 🥇 黄金 ¥50 = 70次

                3. **⏳ 明天再来** - 每天3次免费额度
                """)

                # 显示快捷赞助按钮
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("🥉 10元/10次", use_container_width=True):
                        st.session_state["show_sponsor"] = True
                        st.rerun()
                with col2:
                    if st.button("🥈 30元/35次", use_container_width=True):
                        st.session_state["show_sponsor"] = True
                        st.rerun()
                with col3:
                    if st.button("🥇 50元/70次", use_container_width=True):
                        st.session_state["show_sponsor"] = True
                        st.rerun()
            else:
                st.error(quota_msg)
            st.stop()
        else:
            st.success(quota_msg)

        # === 添加到队列 ===
        task_id = f"task_{int(time.time())}_{hash(url)}"
        if not server_monitor.add_to_queue(task_id, {"url": url, "title": video_title}):
            st.warning("当前服务器繁忙，已加入等待队列...")

        # === 开始处理 ===
        with st.spinner(f"正在转换《{video_title}》，这可能需要1-5分钟，请耐心等待..."):
            try:
                # 使用系统临时目录
                temp_dir = tempfile.gettempdir()
                output_filename = os.path.join(temp_dir, f"bili_result_{int(time.time())}.txt")

                # 构建命令
                cmd = [
                    sys.executable,
                    os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py"),
                    url,
                    selected_model,
                    output_filename
                ]

                # 执行命令
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )

                # 检查是否成功
                if result.returncode == 0:
                    if os.path.exists(output_filename) and os.path.getsize(output_filename) > 0:
                        with open(output_filename, 'r', encoding='utf-8') as f:
                            full_content = f.read()

                        # 确定使用的配额类型
                        quota_type = "sponsor" if "✨" in quota_msg else "free"

                        # 记录使用
                        quota_manager.record_usage(url, int(duration_minutes), quota_type)

                        # 从队列移除
                        server_monitor.remove_from_queue(task_id)

                        # 提取并格式化内容
                        formatted_content = extract_pure_text_with_link(full_content, url)

                        st.success("✅ 转换成功！")

                        # 显示视频信息
                        with st.container():
                            st.markdown(f"**视频标题**: {video_title}")
                            st.markdown(f"**视频时长**: {duration_minutes:.1f} 分钟")
                            st.markdown(f"**处理时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

                        # 下载按钮
                        st.download_button(
                            label="📥 下载文字稿 (.txt)",
                            data=formatted_content,
                            file_name=f"B站视频文字稿_{int(time.time())}.txt",
                            mime="text/plain",
                            use_container_width=True
                        )

                        # 预览
                        pure_text_part = formatted_content.split('\n\n', 1)[
                            1] if '\n\n' in formatted_content else formatted_content
                        preview_text = pure_text_part[:500] + ("..." if len(pure_text_part) > 500 else "")

                        with st.expander("点击预览文字稿（前500字）"):
                            link_line = formatted_content.split('\n')[0]
                            st.text(link_line)
                            st.text("")
                            st.text(preview_text)

                        # 显示剩余额度
                        new_status = quota_manager.get_user_status()
                        if new_status["free_remaining"] > 0:
                            st.info(f"📅 今日还可免费转换 {new_status['free_remaining']} 次")
                        if new_status["sponsor_balance"] > 0:
                            st.info(f"✨ 赞助余额还剩 {new_status['sponsor_balance']} 次")

                        # 清理临时文件
                        try:
                            os.remove(output_filename)
                        except:
                            pass

                    else:
                        st.error("文件生成失败或为空。")
                        with st.expander("查看详细输出"):
                            st.text("标准输出:")
                            st.code(result.stdout[-1000:] if len(result.stdout) > 1000 else result.stdout)
                            st.text("错误输出:")
                            st.code(result.stderr[-1000:] if len(result.stderr) > 1000 else result.stderr)
                else:
                    st.error("转换过程出现错误。")
                    with st.expander("查看错误详情"):
                        st.text("标准输出:")
                        st.code(result.stdout[-1000:] if len(result.stdout) > 1000 else result.stdout)
                        st.text("错误输出:")
                        st.code(result.stderr[-1000:] if len(result.stderr) > 1000 else result.stderr)

            except Exception as e:
                st.error(f"程序执行异常：{e}")
                with st.expander("查看异常详情"):
                    st.code(str(e))
            finally:
                # 确保从队列移除
                server_monitor.remove_from_queue(task_id)

# ================ 页脚信息 ================
st.divider()

# 显示今日统计
stats = quota_manager.get_daily_stats()
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("今日转换", stats["total"])
with col2:
    st.metric("免费转换", stats["free"])
with col3:
    st.metric("活跃用户", stats["users"])

st.divider()

st.markdown("""
### 🤝 遇到特殊情况或想支持我们？
为保障绝大多数用户的免费与稳定体验，网页版严格限时5分钟。
如果您有**5分钟以上视频的紧急转换需求**，我们非常乐意协助。处理超长视频需要消耗大量计算资源，若您愿意**支持我们承担这部分额外成本**，欢迎通过社交媒体（B站/抖音）私信 **@小明小工具** 与我们详谈。
您的支持能让我们为所有人持续提供并改进这项免费服务。
""")

st.markdown("""
### ♻️ 关于数据与隐私的透明承诺
- **无需登录**：本工具完全免费，无需注册或登录。
- **临时处理**：您提交的视频链接和生成的文字稿仅用于实时转换，**不会被我们存储或用于任何其他目的**。
- **技术原理**：核心语音识别由 OpenAI Whisper AI 提供技术支持。
- **这是体验版**：我们正在努力优化，感谢您的理解与支持！
""")

# 技术合作伙伴
st.markdown("""
### 🛠️ 技术合作伙伴
**本服务由以下顶尖技术驱动：**
- **OpenAI Whisper**：提供核心语音识别引擎
- **Streamlit Cloud**：提供稳定的云端服务
- **yt-dlp**：保障B站视频高速下载
""")

# 版权声明
st.markdown("""
---
© BiliVideoToText v1.0 保留所有权利 (2026)

""")
