# quota_manager.py - 完整修复版本
import json
import os
import time
import hashlib
from datetime import date, datetime, timedelta
from typing import Dict, Tuple, Optional
import streamlit as st


class QuotaManager:
    """用户配额管理器"""

    def __init__(self, data_file="user_quotas.json"):
        self.data_file = data_file
        self.max_free_per_day = 3  # 每天最多3个免费视频
        self.max_duration = 5  # 每个视频最长5分钟

        # 赞助价格表（明码标价）
        self.sponsor_tiers = {
            "bronze": {
                "price": 10,
                "videos": 10,
                "duration": 15,  # 每个视频最多15分钟
                "desc": "青铜赞助 - ¥10得10次转换（每次最长15分钟）"
            },
            "silver": {
                "price": 30,
                "videos": 35,
                "duration": 20,
                "desc": "白银赞助 - ¥30得35次转换（每次最长20分钟）"
            },
            "gold": {
                "price": 50,
                "videos": 70,
                "duration": 30,
                "desc": "黄金赞助 - ¥50得70次转换（每次最长30分钟）"
            }
        }

        self.load_data()

    def load_data(self):
        """加载用户数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                # 确保数据结构正确
                self._ensure_data_structure()
            except:
                self.data = self._init_data()
        else:
            self.data = self._init_data()

    def _ensure_data_structure(self):
        """确保数据结构正确（修复旧的set问题）"""
        # 确保daily_stats存在
        if "daily_stats" not in self.data:
            self.data["daily_stats"] = {}

        # 确保每个daily_stats中的unique_users是list
        for date_key, stats in self.data["daily_stats"].items():
            if "unique_users" in stats and isinstance(stats["unique_users"], set):
                stats["unique_users"] = list(stats["unique_users"])
            elif "unique_users" not in stats:
                stats["unique_users"] = []

    def _init_data(self):
        """初始化数据"""
        return {
            "users": {},
            "invite_codes": {},
            "sponsors": {},
            "daily_stats": {}
        }

    def save_data(self):
        """保存数据"""
        try:
            # 确保数据可序列化
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存失败: {e}")
            # 保存备份
            backup_file = f"user_quotas_backup_{int(time.time())}.json"
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump({"error": str(e), "data": str(self.data)}, f)

    def get_user_id(self) -> str:
        """获取用户唯一标识"""
        # 测试模式：从session文件读取
        if os.path.exists(".test_session"):
            try:
                with open(".test_session", "r") as f:
                    test_user = f.read().strip()
                    if test_user:
                        return test_user
            except:
                pass

        try:
            # 正常模式：从Streamlit session获取
            if 'user_id' not in st.session_state:
                import socket
                hostname = socket.gethostname()
                timestamp = str(int(time.time()))
                user_hash = hashlib.md5(f"{hostname}_{timestamp}".encode()).hexdigest()[:16]
                st.session_state.user_id = f"user_{user_hash}"

            return st.session_state.user_id
        except:
            # 降级方案
            if 'fallback_user_id' not in st.session_state:
                st.session_state.fallback_user_id = f"temp_{int(time.time())}"
            return st.session_state.fallback_user_id

    def check_quota(self, video_duration: int) -> Tuple[bool, str, dict]:
        """
        检查用户是否有免费额度
        返回: (是否允许, 提示信息, 用户数据)
        """
        user_id = self.get_user_id()
        today = date.today().isoformat()

        # 初始化用户数据
        if user_id not in self.data["users"]:
            self.data["users"][user_id] = {
                "free_used_today": 0,
                "last_use_date": today,
                "total_converted": 0,
                "sponsor_balance": 0,
                "sponsor_expire": None,
                "invited_by": None,
                "invites": [],
                "invite_code": self._generate_invite_code(user_id),  # 加上这个！
                "history": []
            }

        user_data = self.data["users"][user_id]

        # 如果是新的一天，重置免费使用次数
        if user_data["last_use_date"] != today:
            user_data["free_used_today"] = 0
            user_data["last_use_date"] = today

        # 检查视频时长
        if video_duration > self.max_duration:
            # 检查是否有赞助额度（可以处理更长视频）
            if user_data["sponsor_balance"] > 0 and video_duration <= 30:
                return True, f"✨ 使用赞助额度（剩余{user_data['sponsor_balance']}次）", user_data
            return False, f"⏱️ 免费版仅支持{self.max_duration}分钟以内的视频", user_data

        # 检查免费额度
        if user_data["free_used_today"] >= self.max_free_per_day:
            # 检查是否有赞助余额
            if user_data["sponsor_balance"] > 0:
                return True, f"✨ 使用赞助额度（剩余{user_data['sponsor_balance']}次）", user_data
            return False, "free_limit", user_data

        return True, "free", user_data

    def record_usage(self, video_url: str, duration: int, quota_type: str = "free"):
        """记录使用情况"""
        user_id = self.get_user_id()
        today = date.today().isoformat()

        # 确保用户存在
        if user_id not in self.data["users"]:
            self.data["users"][user_id] = {
                "free_used_today": 0,
                "last_use_date": today,
                "total_converted": 0,
                "sponsor_balance": 0,
                "sponsor_expire": None,
                "invited_by": None,
                "invites": [],
                "invite_code": self._generate_invite_code(user_id),
                "history": []
            }

        user_data = self.data["users"][user_id]

        # 更新使用次数
        if quota_type == "free":
            user_data["free_used_today"] += 1
        elif quota_type == "sponsor":
            user_data["sponsor_balance"] = max(0, user_data.get("sponsor_balance", 0) - 1)

        user_data["total_converted"] += 1
        user_data["history"].append({
            "time": datetime.now().isoformat(),
            "url": video_url[:50],
            "duration": duration,
            "type": quota_type
        })

        # 只保留最近20条记录
        if len(user_data["history"]) > 20:
            user_data["history"] = user_data["history"][-20:]

        # 更新每日统计 - 使用list代替set
        if today not in self.data["daily_stats"]:
            self.data["daily_stats"][today] = {
                "total_conversions": 0,
                "free_conversions": 0,
                "sponsor_conversions": 0,
                "unique_users": []  # 用list代替set
            }

        self.data["daily_stats"][today]["total_conversions"] += 1
        if quota_type == "free":
            self.data["daily_stats"][today]["free_conversions"] += 1
        else:
            self.data["daily_stats"][today]["sponsor_conversions"] += 1

        # 使用list来存储唯一用户
        if user_id not in self.data["daily_stats"][today]["unique_users"]:
            self.data["daily_stats"][today]["unique_users"].append(user_id)

        self.save_data()

    def _generate_invite_code(self, user_id: str) -> str:
        """生成邀请码"""
        code = hashlib.md5(f"{user_id}_{int(time.time())}".encode()).hexdigest()[:8].upper()
        self.data["invite_codes"][code] = {
            "owner": user_id,
            "used_by": [],
            "created": datetime.now().isoformat()
        }
        return code

    def use_invite_code(self, invite_code: str) -> Tuple[bool, str]:
        """使用邀请码"""
        invite_code = invite_code.upper()
        user_id = self.get_user_id()

        if invite_code not in self.data["invite_codes"]:
            return False, "邀请码无效"

        invite_data = self.data["invite_codes"][invite_code]

        # 不能邀请自己
        if invite_data["owner"] == user_id:
            return False, "不能使用自己的邀请码"

        # 检查是否已被使用
        if user_id in invite_data["used_by"]:
            return False, "你已经使用过邀请码了"

        # 记录使用
        invite_data["used_by"].append(user_id)

        # 给邀请者奖励
        if invite_data["owner"] in self.data["users"]:
            owner_data = self.data["users"][invite_data["owner"]]
            if "invite_rewards" not in owner_data:
                owner_data["invite_rewards"] = 0
            owner_data["invite_rewards"] += 1

        # 给新用户奖励（免费一次）
        if user_id in self.data["users"]:
            user_data = self.data["users"][user_id]
            user_data["invited_by"] = invite_data["owner"]
            # 如果今天已经用完免费，奖励一次赞助次数
            if user_data.get("free_used_today", 0) >= self.max_free_per_day:
                user_data["sponsor_balance"] = user_data.get("sponsor_balance", 0) + 1
            else:
                # 否则减少今天的已用次数
                user_data["free_used_today"] = max(0, user_data["free_used_today"] - 1)

        self.save_data()
        return True, "邀请成功！你获得一次额外转换机会"

    def get_user_status(self) -> dict:
        """获取用户状态（用于显示）"""
        user_id = self.get_user_id()
        user_data = self.data["users"].get(user_id, {})
        today = date.today().isoformat()

        # 如果是新的一天，重置计数（显示时计算）
        if user_data.get("last_use_date") != today:
            free_remaining = self.max_free_per_day
        else:
            free_remaining = max(0, self.max_free_per_day - user_data.get("free_used_today", 0))

        sponsor_balance = user_data.get("sponsor_balance", 0)
        invite_rewards = user_data.get("invite_rewards", 0)

        return {
            "free_remaining": free_remaining,
            "sponsor_balance": sponsor_balance,
            "invite_rewards": invite_rewards,
            "total_converted": user_data.get("total_converted", 0),
            "invite_code": user_data.get("invite_code", ""),
            "can_use_sponsor": sponsor_balance > 0 or invite_rewards > 0
        }

    def get_daily_stats(self) -> dict:
        """获取今日统计（用于监控）"""
        today = date.today().isoformat()
        stats = self.data["daily_stats"].get(today, {
            "total_conversions": 0,
            "free_conversions": 0,
            "sponsor_conversions": 0,
            "unique_users": []
        })

        return {
            "total": stats["total_conversions"],
            "free": stats["free_conversions"],
            "sponsor": stats["sponsor_conversions"],
            "users": len(stats.get("unique_users", []))
        }

    def add_sponsor(self, tier: str, payment_id: str) -> Tuple[bool, str]:
        """添加赞助"""
        if tier not in self.sponsor_tiers:
            return False, "无效的赞助等级"

        tier_info = self.sponsor_tiers[tier]
        user_id = self.get_user_id()

        # 确保用户存在
        if user_id not in self.data["users"]:
            self.data["users"][user_id] = {
                "free_used_today": 0,
                "last_use_date": date.today().isoformat(),
                "total_converted": 0,
                "sponsor_balance": 0,
                "sponsor_expire": None,
                "invited_by": None,
                "invites": [],
                "invite_code": self._generate_invite_code(user_id),
                "history": []
            }

        user_data = self.data["users"][user_id]

        # 增加赞助余额
        user_data["sponsor_balance"] = user_data.get("sponsor_balance", 0) + tier_info["videos"]

        # 记录赞助
        if "sponsor_history" not in user_data:
            user_data["sponsor_history"] = []

        user_data["sponsor_history"].append({
            "tier": tier,
            "amount": tier_info["price"],
            "videos": tier_info["videos"],
            "payment_id": payment_id,
            "time": datetime.now().isoformat()
        })

        self.save_data()
        return True, f"赞助成功！获得{tier_info['videos']}次转换额度"


# 单例模式
_quota_manager = None


def get_quota_manager():
    global _quota_manager
    if _quota_manager is None:
        _quota_manager = QuotaManager()

    return _quota_manager
