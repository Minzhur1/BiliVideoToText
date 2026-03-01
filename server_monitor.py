# server_monitor.py - 服务器资源监控
import psutil
import os
import time
import json
from datetime import datetime
import shutil


class ServerMonitor:
    """服务器资源监控，防止过载崩溃"""

    def __init__(self):
        self.cpu_threshold = 80  # CPU超过80%告警
        self.mem_threshold = 85  # 内存超过85%告警
        self.disk_threshold = 90  # 磁盘超过90%告警
        self.queue_file = "processing_queue.json"
        self.max_concurrent = 2  # 最大并发处理数
        self.load_queue()

    def load_queue(self):
        """加载处理队列"""
        if os.path.exists(self.queue_file):
            try:
                with open(self.queue_file, 'r') as f:
                    self.queue = json.load(f)
            except:
                self.queue = {"processing": [], "waiting": []}
        else:
            self.queue = {"processing": [], "waiting": []}

    def save_queue(self):
        """保存队列"""
        with open(self.queue_file, 'w') as f:
            json.dump(self.queue, f)

    def get_server_status(self) -> dict:
        """获取服务器状态"""
        try:
            status = {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "processing_count": len(self.queue["processing"]),
                "waiting_count": len(self.queue["waiting"]),
                "is_busy": False,
                "can_accept": True,
                "message": "✅ 服务器正常"
            }

            # 判断是否繁忙
            if status["cpu_percent"] > self.cpu_threshold:
                status["is_busy"] = True
                status["message"] = "⚠️ 服务器当前繁忙，处理可能较慢"

            if status["memory_percent"] > self.mem_threshold:
                status["is_busy"] = True
                status["message"] = "⚠️ 服务器内存负载较高"

            # 判断是否还能接受新任务
            if status["processing_count"] >= self.max_concurrent:
                status["can_accept"] = False
                status["message"] = "⏳ 当前处理队列已满，请稍后再试"

            return status
        except Exception as e:
            return {
                "cpu_percent": 0,
                "memory_percent": 0,
                "disk_percent": 0,
                "processing_count": 0,
                "waiting_count": 0,
                "is_busy": False,
                "can_accept": True,
                "message": f"监控异常: {str(e)}"
            }

    def add_to_queue(self, task_id: str, task_info: dict) -> bool:
        """添加到处理队列"""
        status = self.get_server_status()

        if not status["can_accept"]:
            # 添加到等待队列
            self.queue["waiting"].append({
                "id": task_id,
                "info": task_info,
                "added_time": datetime.now().isoformat()
            })
            self.save_queue()
            return False

        # 添加到处理队列
        self.queue["processing"].append({
            "id": task_id,
            "info": task_info,
            "start_time": datetime.now().isoformat()
        })
        self.save_queue()
        return True

    def remove_from_queue(self, task_id: str):
        """从队列中移除"""
        # 从处理队列移除
        self.queue["processing"] = [t for t in self.queue["processing"] if t["id"] != task_id]

        # 如果有等待的，移一个到处理队列
        if len(self.queue["processing"]) < self.max_concurrent and self.queue["waiting"]:
            next_task = self.queue["waiting"].pop(0)
            next_task["start_time"] = datetime.now().isoformat()
            self.queue["processing"].append(next_task)

        self.save_queue()

    def auto_cleanup(self):
        """自动清理临时文件"""
        try:
            cleaned = 0
            freed_space = 0

            # 清理临时文件
            patterns = [
                "/tmp/bili_audio_*",
                "/tmp/bili_video_*",
                "./temp_*.mp4",
                "./temp_*.wav",
                "./转录结果.txt",
                "./*.part",
                "./*.ytdl"
            ]

            import glob
            for pattern in patterns:
                for f in glob.glob(pattern):
                    try:
                        size = os.path.getsize(f)
                        os.remove(f)
                        cleaned += 1
                        freed_space += size
                    except:
                        pass

            # 清理超过7天的日志
            cutoff = time.time() - 7 * 86400
            for f in glob.glob("*.log"):
                if os.path.getmtime(f) < cutoff:
                    try:
                        os.remove(f)
                        cleaned += 1
                    except:
                        pass

            return {
                "cleaned_files": cleaned,
                "freed_mb": freed_space / 1024 / 1024
            }
        except Exception as e:
            return {"error": str(e)}


_server_monitor = None


def get_server_monitor():
    global _server_monitor
    if _server_monitor is None:
        _server_monitor = ServerMonitor()
    return _server_monitor