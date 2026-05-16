import asyncio
import json
import shutil
import time
import traceback

import astrbot.api.message_components as Comp
from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, StarTools


class ConversationRecorder(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.record_list = {}
        self._cr_lock = asyncio.Lock()

    def get_list(self):
        """获取插件持久化文件，同时备份损坏的文件，创建默认文件
        Returns:
            record_list(dict):获取到的插件的record_list
        """
        data_dir = StarTools.get_data_dir()
        if not data_dir.exists():
            data_dir.mkdir(parents=True)
        file_path = data_dir / "records.json"

        if not file_path.exists():
            # 创建默认结构
            default_recordlist = {}
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(default_recordlist, f, ensure_ascii=False, indent=4)
            return default_recordlist

        try:
            with open(file_path, encoding="utf-8") as f:
                record_list = json.load(f)
                # record_list = self.check_list_format(record_list)
        except json.JSONDecodeError as e:
            logger.error(f"records.json 文件损坏，正在备份并重新创建: {e}")
            # 备份损坏的文件
            backup_path = data_dir / f"records.json.backup.{int(time.time())}"
            try:
                shutil.copy(file_path, backup_path)
                logger.info(f"已备份损坏文件到: {backup_path}")
            except Exception as backup_error:
                logger.warning(f"备份失败: {backup_error}")

            # 创建新的默认文件
            default_recordlist = {}
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(default_recordlist, f, ensure_ascii=False, indent=4)
            logger.info("已重新创建 records.json 文件")
            return default_recordlist
        except Exception as e:
            logger.error(f"读取 records.json 失败: {e}")
            logger.error(traceback.format_exc())
            raise e
        return record_list

    def write_record(self, record_list):
        """将插件的record_list写入持久化文件"""
        data_dir = StarTools.get_data_dir()
        if not data_dir.exists():
            data_dir.mkdir(parents=True)
        file_path = data_dir / "records.json"
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(record_list, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(e)
            raise e
        return

    async def initialize(self):
        """异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
        async with self._cr_lock:
            self.record_list = self.get_list()

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def record_msg(self, event: AstrMessageEvent):
        """记录特定用户发送的文本内容"""
        msg = event.get_message_str()
        sender_id = event.get_sender_id()
        if not (isinstance(msg, str) and msg != ""):
            return
        if sender_id not in self.config["record_ids"]:
            return
        async with self._cr_lock:
            if self.record_list.get(sender_id) is None:
                self.record_list[sender_id] = []
            self.record_list[sender_id].append(msg)
            self.write_record(self.record_list)

    @filter.command_group("cr")
    def cr():
        pass

    @filter.permission_type(filter.PermissionType.ADMIN)
    @cr.command("clear")
    async def clear(self, event: AstrMessageEvent, user: str):
        """清除指定用户的消息记录"""
        if user not in self.config["record_ids"]:
            yield event.plain_result(f"用户{user}不在插件的记录范围内，无法清除记录")
            return
        async with self._cr_lock:
            self.record_list.pop(user, None)
            self.write_record(self.record_list)
        yield event.plain_result(f"用户{user}的消息记录已被清除")

    @filter.permission_type(filter.PermissionType.ADMIN)
    @cr.command("show")
    async def show(self, event: AstrMessageEvent):
        """展示收集到的所有消息"""
        file_path = StarTools.get_data_dir() / "records.json"
        async with self._cr_lock:
            chain = [Comp.File(file=str(file_path), name="record.json")]
        yield event.chain_result(chain)

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
