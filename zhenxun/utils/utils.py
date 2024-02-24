import os
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import httpx

from zhenxun.services.log import logger


class WithdrawManager:
    """
    消息撤回
    """

    _data = {}

    @classmethod
    def append(cls, message_id: str, second: int):
        """添加一个撤回消息id和时间

        参数:
            message_id: 撤回消息id
            time: 延迟时间
        """
        cls._data[message_id] = second

    @classmethod
    def remove(cls, message_id: str):
        """删除一个数据

        参数:
            message_id: 撤回消息id
        """
        if message_id in cls._data:
            del cls._data[message_id]


class ResourceDirManager:
    """
    临时文件管理器
    """

    temp_path = []

    @classmethod
    def __tree_append(cls, path: Path):
        """递归添加文件夹

        参数:
            path: 文件夹路径
        """
        for f in os.listdir(path):
            file = path / f
            if file.is_dir():
                if file not in cls.temp_path:
                    cls.temp_path.append(file)
                    logger.debug(f"添加临时文件夹: {path}")
                cls.__tree_append(file)

    @classmethod
    def add_temp_dir(cls, path: str | Path, tree: bool = False):
        """添加临时清理文件夹，这些文件夹会被自动清理

        参数:
            path: 文件夹路径
            tree: 是否递归添加文件夹
        """
        if isinstance(path, str):
            path = Path(path)
        if path not in cls.temp_path:
            cls.temp_path.append(path)
            logger.debug(f"添加临时文件夹: {path}")
        if tree:
            cls.__tree_append(path)


class CountLimiter:
    """
    次数检测工具，检测调用次数是否超过设定值
    """

    def __init__(self, max_count: int):
        self.count = defaultdict(int)
        self.max_count = max_count

    def add(self, key: Any):
        self.count[key] += 1

    def check(self, key: Any) -> bool:
        if self.count[key] >= self.max_count:
            self.count[key] = 0
            return True
        return False


class UserBlockLimiter:
    """
    检测用户是否正在调用命令
    """

    def __init__(self):
        self.flag_data = defaultdict(bool)
        self.time = time.time()

    def set_true(self, key: Any):
        self.time = time.time()
        self.flag_data[key] = True

    def set_false(self, key: Any):
        self.flag_data[key] = False

    def check(self, key: Any) -> bool:
        if time.time() - self.time > 30:
            self.set_false(key)
            return False
        return self.flag_data[key]


class FreqLimiter:
    """
    命令冷却，检测用户是否处于冷却状态
    """

    def __init__(self, default_cd_seconds: int):
        self.next_time = defaultdict(float)
        self.default_cd = default_cd_seconds

    def check(self, key: Any) -> bool:
        return time.time() >= self.next_time[key]

    def start_cd(self, key: Any, cd_time: int = 0):
        self.next_time[key] = time.time() + (
            cd_time if cd_time > 0 else self.default_cd
        )

    def left_time(self, key: Any) -> float:
        return self.next_time[key] - time.time()


async def get_user_avatar(uid: int | str) -> bytes | None:
    """快捷获取用户头像

    参数:
        uid: 用户id
    """
    url = f"http://q1.qlogo.cn/g?b=qq&nk={uid}&s=160"
    async with httpx.AsyncClient() as client:
        for _ in range(3):
            try:
                return (await client.get(url)).content
            except Exception as e:
                logger.error("获取用户头像错误", "Util", target=uid)
    return None


async def get_group_avatar(gid: int | str) -> bytes | None:
    """快捷获取用群头像

    参数:
        :param gid: 群号
    """
    url = f"http://p.qlogo.cn/gh/{gid}/{gid}/640/"
    async with httpx.AsyncClient() as client:
        for _ in range(3):
            try:
                return (await client.get(url)).content
            except Exception as e:
                logger.error("获取群头像错误", "Util", target=gid)
    return None