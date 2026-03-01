# sponsor_page.py - 赞助页面
import streamlit as st
from quota_manager import get_quota_manager

# 手动控制开关 - 改成 False 就关闭赞助
SPONSOR_OPEN = True  # True=开, False=关


def show_sponsor_page():
    """显示赞助页面"""

    # 检查赞助是否开放
    if not SPONSOR_OPEN:
        st.error("""
        ### ⛔ 本月赞助名额已满

        非常感谢大家的支持！本月赞助已达到限额。

        下个月1号会重新开放，敬请期待！
        """)
        if st.button("← 返回主页", use_container_width=True):
            st.session_state["show_sponsor"] = False
            st.rerun()
        return  # 直接返回，不显示后面的内容

    st.markdown("## 💖 赞助支持，让好工具长久运转")

    st.markdown("""
    ### 为什么需要赞助？
    运行这个工具需要：
    - 🖥️ 服务器租用费用
    - ⚡ 电费和带宽成本
    - 🛠️ 持续开发和维护
    - 📞 用户支持与服务

    您的赞助将直接用于：
    1. **升级服务器** - 处理更快，支持更长视频
    2. **增加功能** - 更多格式，批量处理
    3. **长期维护** - 稳定可靠的服务

    **赞助完全自愿，免费版依然可用！**
    """)

    st.divider()

    # ✅ 在这里获取 quota_manager
    quota_manager = get_quota_manager()

    # 显示赞助套餐
    st.markdown("### 🎁 赞助套餐")

    cols = st.columns(3)

    for idx, (tier, info) in enumerate(quota_manager.sponsor_tiers.items()):
        with cols[idx]:
            with st.container():
                st.markdown(f"""
                <div style="border:1px solid #ddd; border-radius:10px; padding:20px; text-align:center; height:280px;">
                    <h3>{'🥉 青铜' if tier == 'bronze' else '🥈 白银' if tier == 'silver' else '🥇 黄金'}</h3>
                    <h2 style="color:#FF4081;">¥{info['price']}</h2>
                    <p>获得 {info['videos']} 次转换</p>
                    <p>每次最长 {info['duration']} 分钟</p>
                    <p>🔄 永久有效，不限时</p>
                </div>
                """, unsafe_allow_html=True)

                if st.button(f"选择 {tier.capitalize()}", key=f"btn_{tier}"):
                    st.session_state["sponsor_tier"] = tier
                    st.session_state["show_payment"] = True

    st.divider()

    # 支付方式说明
    # 支付方式说明
    st.markdown("""
    ### 💳 支付方式

    本工具通过 **爱发电** 平台收款：

    👉 **[点击这里前往爱发电赞助](https://afdian.com/a/bilivideototext)**

    **流程：**
    1. 点击上方链接选择套餐赞助
    2. 赞助后私信我你的「爱发电订单号」和「用户ID」
    3. 24小时内为您充值

    **用户ID在网站侧边栏可以看到**
    *自动支付正在开发中，敬请期待！*
    """)



    # 显示支付信息
    if st.session_state.get("show_payment", False):
        tier = st.session_state["sponsor_tier"]
        # ✅ 这里用的是函数内的 quota_manager
        info = quota_manager.sponsor_tiers[tier]

        st.success(f"""
        ### ✅ 您选择了 {tier.capitalize()} 赞助套餐

        **赞助金额：** ¥{info['price']}
        **获得次数：** {info['videos']} 次转换
        **每次时长：** 最长 {info['duration']} 分钟

        **您的赞助码：** `SPONSOR_{int(st.time.time())}_{tier.upper()}`

        **请通过以下方式联系我们：**
        - 📱 B站/抖音私信：**@小明小工具**
        - 📧 邮件：support@example.com
        - 💬 微信：bili_tool

        发送赞助码后，我们将在24小时内为您充值！
        """)

        # 生成二维码（模拟）
        st.info("📱 支付二维码（模拟）- 实际接入支付宝/微信支付API")

        if st.button("返回重新选择"):
            st.session_state["show_payment"] = False
            st.rerun()


