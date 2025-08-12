from ErisPulse import sdk
from typing import Dict, Any

class Main:
    def __init__(self):
        self.sdk = sdk
        self.logger = sdk.logger
        
        # 加载配置
        self.config = self._load_config()
        
        # 注册指令处理器
        self._register_commands()
        
        self.logger.info("信息统计查询模块已加载")

    @staticmethod
    def should_eager_load():
        return True

    def _load_config(self) -> Dict[str, Any]:
        """
        加载模块配置，如果不存在则创建默认配置
        """
        config = self.sdk.config.getConfig("InfoQuery")
        if not config:
            default_config = {
                "commands": {
                    "stats": "stats",
                    "platform": "platform",
                    "recent": "recent",
                    "user": "user",
                    "group": "group",
                    "help": "infohelp"
                },
                "default_limit": 10,
                "max_limit": 50
            }
            self.sdk.config.setConfig("InfoQuery", default_config)
            self.logger.info("已创建默认配置文件")
            return default_config
        return config

    def _register_commands(self):
        """
        注册指令处理器
        """
        # 注册消息事件监听器，处理指令
        @sdk.adapter.on("message")
        async def handle_command(data):
            await self._process_command(data)

    async def _process_command(self, data):
        """
        处理指令消息
        """
        # 检查是否为指令消息
        message = data.get("alt_message", "")
        if not message.startswith("/"):
            return
            
        # 解析指令
        parts = message[1:].strip().split()
        if not parts:
            return
            
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        # 获取配置的命令映射
        cmd_config = self.config.get("commands", {})
        
        # 确定发送目标
        platform = data.get("platform")
        detail_type = data.get("detail_type")
        target_type = "user" if detail_type == "private" else "group"
        target_id = data.get("user_id") if target_type == "user" else data.get("group_id")
        
        # 获取适配器发送器
        if hasattr(sdk.adapter, platform):
            sender = getattr(sdk.adapter, platform).Send.To(target_type, target_id)
        else:
            self.logger.warning(f"不支持的平台: {platform}")
            return
            
        # 处理指令
        try:
            if command == cmd_config.get("stats", "stats"):
                await self._handle_stats_command(sender, args)
            elif command == cmd_config.get("platform", "platform"):
                await self._handle_platform_command(sender, args)
            elif command == cmd_config.get("recent", "recent"):
                await self._handle_recent_command(sender, args)
            elif command == cmd_config.get("user", "user"):
                await self._handle_user_command(sender, args, data.get("user_id"))
            elif command == cmd_config.get("group", "group"):
                await self._handle_group_command(sender, args, data.get("group_id"))
            elif command == cmd_config.get("help", "infohelp"):
                await self._handle_help_command(sender)
        except Exception as e:
            self.logger.error(f"处理指令时出错: {e}")
            sender.Text("处理指令时发生错误，请查看日志了解详情。")

    async def _handle_stats_command(self, sender, args):
        """
        处理统计信息查询指令
        """
        try:
            # 获取InfoStats模块实例
            info_stats = sdk.InfoStats
            
            # 获取统计数据
            total_stats = info_stats.get_total_stats()
            
            # 构造回复消息
            response = "[统计信息]\n"
            response += f"总消息数: {total_stats['total_messages']}\n"
            response += f"总通知数: {total_stats['total_notices']}\n"
            response += f"总请求数: {total_stats['total_requests']}\n"
            response += f"总事件数: {total_stats['total_events']}"
            
            sender.Text(response)
        except AttributeError:
            sender.Text("未找到InfoStats模块，请确保该模块已正确加载")
        except Exception as e:
            self.logger.error(f"处理统计信息指令时出错: {e}")
            sender.Text("获取统计数据时发生错误")

    async def _handle_platform_command(self, sender, args):
        """
        处理平台统计信息查询指令
        """
        try:
            # 获取InfoStats模块实例
            info_stats = sdk.InfoStats
            
            # 获取平台统计数据
            platform_stats = info_stats.get_platform_stats()
            
            # 构造回复消息
            response = "[平台统计信息]\n\n"
            
            # 消息统计
            response += "[消息统计]\n"
            if platform_stats['messages_by_platform']:
                for platform, count in platform_stats['messages_by_platform'].items():
                    response += f"  {platform}: {count}\n"
            else:
                response += "  暂无数据\n"
            
            response += "\n[通知统计]\n"
            if platform_stats['notices_by_platform']:
                for platform, count in platform_stats['notices_by_platform'].items():
                    response += f"  {platform}: {count}\n"
            else:
                response += "  暂无数据\n"
            
            response += "\n[请求统计]\n"
            if platform_stats['requests_by_platform']:
                for platform, count in platform_stats['requests_by_platform'].items():
                    response += f"  {platform}: {count}\n"
            else:
                response += "  暂无数据\n"
            
            sender.Text(response)
        except AttributeError:
            sender.Text("未找到InfoStats模块，请确保该模块已正确加载")
        except Exception as e:
            self.logger.error(f"处理平台统计指令时出错: {e}")
            sender.Text("获取平台统计数据时发生错误")

    async def _handle_recent_command(self, sender, args):
        """
        处理最近事件查询指令
        """
        try:
            # 获取参数
            default_limit = self.config.get("default_limit", 10)
            max_limit = self.config.get("max_limit", 50)
            
            limit = default_limit
            if args:
                try:
                    limit = min(int(args[0]), max_limit)
                except ValueError:
                    pass
            
            # 获取InfoStats模块实例
            info_stats = sdk.InfoStats
            
            # 获取最近事件
            recent_events = info_stats.get_recent_events(limit)
            
            if not recent_events:
                sender.Text("暂无最近事件")
                return
            
            # 构造回复消息
            response = f"[最近 {len(recent_events)} 条事件]\n"
            
            for i, event in enumerate(reversed(recent_events[-limit:]), 1):
                timestamp = event['timestamp'].strftime("%m-%d %H:%M:%S")
                event_type = event['type']
                platform = event['platform']
                detail_type = event['detail_type']
                
                response += f"{i}. [{timestamp}] [{platform}] {detail_type}\n"
                
                # 添加用户或群组信息
                if event.get('user_id'):
                    response += f"    用户: {event['user_id']}\n"
                if event.get('group_id'):
                    response += f"    群组: {event['group_id']}\n"
                
                # 添加消息内容（如果是消息或有内容的通知/请求）
                if event.get('alt_message'):
                    msg_preview = event['alt_message'][:30] + "..." if len(event['alt_message']) > 30 else event['alt_message']
                    response += f"    内容: {msg_preview}\n"
                
                response += "\n"
            
            sender.Text(response.strip())
        except AttributeError:
            sender.Text("未找到InfoStats模块，请确保该模块已正确加载")
        except Exception as e:
            self.logger.error(f"处理最近事件指令时出错: {e}")
            sender.Text("获取最近事件时发生错误")

    async def _handle_user_command(self, sender, args, sender_user_id):
        """
        处理用户统计信息查询指令
        """
        try:
            # 获取用户ID参数
            user_id = None
            if args:
                user_id = args[0]
            else:
                user_id = sender_user_id  # 使用发送者ID
            
            if not user_id:
                sender.Text("请提供用户ID或在私聊中使用此指令")
                return
            
            # 获取InfoStats模块实例
            info_stats = sdk.InfoStats
            
            # 获取用户统计数据
            user_stats = info_stats.get_user_stats(user_id)
            
            # 构造回复消息
            response = f"[用户 {user_id} 的统计信息]\n\n"
            response += f"总消息数: {user_stats['total_messages']}\n"
            response += f"总通知数: {user_stats['total_notices']}\n"
            response += f"总请求数: {user_stats['total_requests']}\n"
            response += f"总事件数: {user_stats['total_events']}\n"
            
            if user_stats['platforms']:
                response += f"涉及平台: {', '.join(user_stats['platforms'])}\n"
            
            # 显示最近事件
            if user_stats['recent_events']:
                response += f"\n最近 {len(user_stats['recent_events'])} 条事件:\n"
                for event in reversed(user_stats['recent_events']):
                    timestamp = event['timestamp'].strftime("%m-%d %H:%M:%S")
                    event_type = event['type']
                    platform = event['platform']
                    detail_type = event['detail_type']
                    
                    response += f"  [{timestamp}] [{platform}] {detail_type}\n"
            else:
                response += "\n暂无最近事件"
            
            sender.Text(response)
        except AttributeError:
            sender.Text("未找到InfoStats模块，请确保该模块已正确加载")
        except Exception as e:
            self.logger.error(f"处理用户统计指令时出错: {e}")
            sender.Text("获取用户统计数据时发生错误")

    async def _handle_group_command(self, sender, args, sender_group_id):
        """
        处理群组统计信息查询指令
        """
        try:
            # 获取群组ID参数
            group_id = None
            if args:
                group_id = args[0]
            else:
                group_id = sender_group_id  # 使用发送者所在群组ID
            
            if not group_id:
                sender.Text("请提供群组ID或在群组中使用此指令")
                return
            
            # 获取InfoStats模块实例
            info_stats = sdk.InfoStats
            
            # 获取群组统计数据
            group_stats = info_stats.get_group_stats(group_id)
            
            # 构造回复消息
            response = f"[群组 {group_id} 的统计信息]\n\n"
            response += f"总消息数: {group_stats['total_messages']}\n"
            response += f"总通知数: {group_stats['total_notices']}\n"
            response += f"总请求数: {group_stats['total_requests']}\n"
            response += f"总事件数: {group_stats['total_events']}\n"
            response += f"参与者数: {group_stats['participant_count']}\n"
            
            if group_stats['platforms']:
                response += f"涉及平台: {', '.join(group_stats['platforms'])}\n"
            
            # 显示最近事件
            if group_stats['recent_events']:
                response += f"\n最近 {len(group_stats['recent_events'])} 条事件:\n"
                for event in reversed(group_stats['recent_events']):
                    timestamp = event['timestamp'].strftime("%m-%d %H:%M:%S")
                    event_type = event['type']
                    platform = event['platform']
                    detail_type = event['detail_type']
                    
                    if event.get('user_id'):
                        response += f"  用户:{event['user_id']} "
                    
                    response += f"[{timestamp}] [{platform}] {detail_type}\n"
            else:
                response += "\n暂无最近事件"
            
            sender.Text(response)
        except AttributeError:
            sender.Text("未找到InfoStats模块，请确保该模块已正确加载")
        except Exception as e:
            self.logger.error(f"处理群组统计指令时出错: {e}")
            sender.Text("获取群组统计数据时发生错误")

    async def _handle_help_command(self, sender):
        """
        处理帮助指令
        """
        cmd_config = self.config.get("commands", {})
        
        help_text = """[InfoQuery 帮助信息]

指令列表:
"""
        # 动态生成指令列表
        help_text += f"/{cmd_config.get('stats', 'stats')} - 显示总体统计信息\n"
        help_text += f"/{cmd_config.get('platform', 'platform')} - 显示各平台统计信息\n"
        help_text += f"/{cmd_config.get('recent', 'recent')} [数量] - 显示最近事件（默认10条，最多50条）\n"
        help_text += f"/{cmd_config.get('user', 'user')} [用户ID] - 显示用户统计信息（私聊中可省略ID）\n"
        help_text += f"/{cmd_config.get('group', 'group')} [群组ID] - 显示群组统计信息（群组中可省略ID）\n"
        help_text += f"/{cmd_config.get('help', 'infohelp')} - 显示此帮助信息\n"
        
        help_text += "\n注意：所有指令均需在开头添加 '/' 前缀。\n"
        help_text += "可以通过修改 config.toml 中 InfoQuery.commands 部分来自定义指令名称。"
        
        sender.Text(help_text)