from nonebot import on_notice
from nonebot.adapters.onebot.v11 import PokeNotifyEvent
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata
from nonebot.rule import to_me
from nonebot_plugin_alconna import Alconna, on_alconna
from nonebot_plugin_htmlrender import template_to_pic

from zhenxun.configs.config import Config
from zhenxun.configs.path_config import TEMPLATE_PATH
from zhenxun.configs.utils import PluginExtraData, RegisterConfig
from zhenxun.services.log import logger
from zhenxun.utils.enum import PluginType
from zhenxun.utils.message import MessageUtils
from zhenxun.utils.rules import notice_rule

from .data_source import get_status_info

__plugin_meta__ = PluginMetadata(
    name="服务器自我检查",
    description="查看服务器当前状态",
    usage="""
    查看服务器当前状态
    指令:
        自检
        戳一戳BOT
    """.strip(),
    extra=PluginExtraData(
        author="HibiKier",
        version="0.1",
        plugin_type=PluginType.SUPERUSER,
        configs=[RegisterConfig(
            key="type",
            value="mix",
            help="自检触发方式 ['message', 'poke', 'mix']",
            default_value="mix",
        )],
    ).dict(),
)

async def handle_self_check():
    try:
        logger.info("触发自检")
        data = await get_status_info()
        image = await template_to_pic(
            template_path=str((TEMPLATE_PATH / "check").absolute()),
            template_name="main.html",
            templates={"data": data},
            pages={
                "viewport": {"width": 195, "height": 750},
                "base_url": f"file://{TEMPLATE_PATH}",
            },
            wait=2,
        )
        await MessageUtils.build_message(image).send()
        logger.info("自检成功")
    except Exception as e:
        await MessageUtils.build_message(f"自检失败: {e}").send()
        logger.error("自检失败", e=e)

check_type = Config.get_config("check", "type")

check_handlers = {
    "message": on_alconna(
        Alconna("自检"), rule=to_me(), permission=SUPERUSER, block=True, priority=1
    ),
    "poke": on_notice(
        priority=5,
        permission=SUPERUSER,
        block=False,
        rule=notice_rule(PokeNotifyEvent) & to_me(),
    ),
    "mix": [
        on_alconna(
            Alconna("自检"), rule=to_me(), permission=SUPERUSER, block=True, priority=1
        ),
        on_notice(
            priority=5,
            permission=SUPERUSER,
            block=False,
            rule=notice_rule(PokeNotifyEvent) & to_me(),
        )
    ],
}

handlers = check_handlers.get(check_type)
handlerste = check_handlers.get("mix")


if handlers:
    if isinstance(handlers, list):
        for handler in handlers:
            @handler.handle()
            async def handle_check():
                await handle_self_check()
    else:
        @handlers.handle()
        async def handle_check():
            await handle_self_check()
