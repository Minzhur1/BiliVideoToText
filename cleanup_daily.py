#!/usr/bin/env python3
# cleanup_daily.py - 每日自动清理脚本（配合crontab使用）

import os
import sys
import json
import glob
import shutil
import time
from datetime import datetime, timedelta


def cleanup_temp_files():
    """清理临时文件"""
    print(f"[{datetime.now()}] 开始清理临时文件...")

    patterns = [
        "/tmp/bili_audio_*",
        "/tmp/bili_video_*",
        "./temp_*.mp4",
        "./temp_*.wav",
        "./转录结果.txt",
        "./*.part",
        "./*.ytdl"
    ]

    cleaned = 0
    freed_space = 0

    for pattern in patterns:
        for f in glob.glob(pattern):
            try:
                size = os.path.getsize(f)
                os.remove(f)
                cleaned += 1
                freed_space += size
                print(f"  删除: {f} ({size / 1024:.1f} KB)")
            except Exception as e:
                print(f"  删除失败 {f}: {e}")

    print(f"清理完成: 删除了 {cleaned} 个文件，释放 {freed_space / 1024 / 1024:.2f} MB")


def cleanup_old_quotas():
    """清理7天前的配额记录（备份）"""
    print(f"[{datetime.now()}] 开始清理旧配额数据...")

    quota_file = "user_quotas.json"
    if not os.path.exists(quota_file):
        print("配额文件不存在")
        return

    try:
        with open(quota_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 创建备份
        backup_file = f"backups/user_quotas_{datetime.now().strftime('%Y%m%d')}.json"
        os.makedirs("backups", exist_ok=True)

        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"已备份到: {backup_file}")

        # 清理7天前的备份
        cutoff = time.time() - 7 * 86400
        for f in glob.glob("backups/user_quotas_*.json"):
            if os.path.getmtime(f) < cutoff:
                os.remove(f)
                print(f"删除旧备份: {f}")

    except Exception as e:
        print(f"清理配额失败: {e}")


def cleanup_logs():
    """清理日志文件"""
    print(f"[{datetime.now()}] 开始清理日志...")

    log_files = glob.glob("*.log")
    cutoff = time.time() - 3 * 86400  # 保留3天

    cleaned = 0
    for f in log_files:
        if os.path.getmtime(f) < cutoff:
            try:
                os.remove(f)
                cleaned += 1
                print(f"删除日志: {f}")
            except:
                pass

    print(f"清理了 {cleaned} 个日志文件")


def check_disk_space():
    """检查磁盘空间"""
    import psutil

    disk = psutil.disk_usage('/')
    percent = disk.percent

    print(f"[{datetime.now()}] 磁盘使用: {percent:.1f}%")

    if percent > 90:
        print("⚠️ 警告：磁盘使用率超过90%，需要扩容或深度清理")
        # 深度清理：删除所有临时文件
        for f in glob.glob("/tmp/*"):
            if os.path.isfile(f) and os.path.getmtime(f) < time.time() - 86400:
                try:
                    os.remove(f)
                except:
                    pass


if __name__ == "__main__":
    print("=" * 50)
    print("每日自动清理任务开始")
    print("=" * 50)

    cleanup_temp_files()
    cleanup_old_quotas()
    cleanup_logs()
    check_disk_space()

    print("=" * 50)
    print("清理任务完成")
    print("=" * 50)