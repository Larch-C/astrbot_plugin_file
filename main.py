from astrbot.api.message_components import *
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api import AstrBotConfig
from astrbot.api.star import Context, Star, register
from astrbot.core.utils.io import download_image_by_url, download_file
import os
import shutil
import time
import asyncio
import aiohttp
import uuid

# 创建配置对象
# 注册插件的装饰器
@register("文件操作", "Chris", "一个简单的文件发送、删除、移动、复制和查看文件夹内容插件", "1.2.0")
class FileSenderPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.base_path = config.get('FileBasePath', '/default/path')  # 配置文件中的基础路径
        self.user_waiting = {}  # 等待上传文件的用户 {uid: {'time': time, 'path': path, 'extension': ext}}
    
    def normalize_path(self, input_path: str) -> str:
        """规范化路径，兼容Windows和Linux"""
        # 规范化路径分隔符
        normalized_path = input_path.replace('\\', '/').replace('//', '/')
        
        # 处理绝对路径和相对路径
        if os.path.isabs(normalized_path):
            # 如果是绝对路径，直接使用
            return os.path.normpath(normalized_path)
        else:
            # 如果是相对路径，与base_path拼接
            return os.path.normpath(os.path.join(self.base_path, normalized_path))

    # 根据路径发送文件
    async def send_file(self, event: AstrMessageEvent, file_path: str):
        full_file_path = self.normalize_path(file_path)

        # 检查文件是否存在
        if not os.path.exists(full_file_path):
            yield event.plain_result(f"文件 {file_path} 不存在，请检查路径。")
            return

        # 检查文件是否为文件而非文件夹
        if os.path.isdir(full_file_path):
            yield event.plain_result(f"指定的路径是一个目录，而不是文件：{file_path}")
            return

        # 检查文件大小（限制为2GB）
        file_size = os.path.getsize(full_file_path)
        if file_size == 0:
            yield event.plain_result(f"文件 {file_path} 是空文件，无法发送。")
            return
        if file_size > 2 * 1024 * 1024 * 1024:  # 2GB
            yield event.plain_result(f"文件 {file_path} 大小超过2GB限制，无法发送。")
            return

        # 获取文件名（不带路径）
        file_name = os.path.basename(file_path)

        # 检查文件是否可读
        try:
            with open(full_file_path, 'rb') as f:
                f.read(1)  # 测试读取
        except Exception as e:
            yield event.plain_result(f"无法读取文件 {file_path}: {str(e)}")
            return

        # 发送文件
        yield event.plain_result(f"开始发送文件 {file_name}...")
        yield event.plain_result(f"文件路径: {full_file_path}")
        yield event.plain_result(f"文件大小: {file_size / 1024:.2f} KB")
        
        try:
            yield event.chain_result([File(name=file_name, file=full_file_path)])
            yield event.plain_result(f"文件 {file_name} 已发送。")
        except Exception as e:
            yield event.plain_result(f"发送文件失败: {str(e)}")
            yield event.plain_result("可能的原因:")
            yield event.plain_result("1. 文件路径包含特殊字符")
            yield event.plain_result("2. 文件大小超过平台限制")
            yield event.plain_result("3. 文件类型不被支持")
            yield event.plain_result("4. 机器人没有文件访问权限")

    # 根据路径删除文件
    async def delete_file(self, event: AstrMessageEvent, file_path: str):
        full_file_path = self.normalize_path(file_path)

        # 检查文件是否存在
        if not os.path.exists(full_file_path):
            yield event.plain_result(f"文件 {file_path} 不存在，请检查路径。")
            return

        # 检查文件是否为文件而非文件夹
        if os.path.isdir(full_file_path):
            yield event.plain_result(f"指定的路径是一个目录，而不是文件：{file_path}")
            return

        try:
            # 删除文件
            os.remove(full_file_path)
            yield event.plain_result(f"文件 {file_path} 已成功删除。")
        except Exception as e:
            yield event.plain_result(f"删除文件时发生错误: {str(e)}")

    # 根据路径删除目录
    async def delete_directory(self, event: AstrMessageEvent, dir_path: str):
        full_dir_path = self.normalize_path(dir_path)

        # 检查目录是否存在
        if not os.path.exists(full_dir_path):
            yield event.plain_result(f"目录 {dir_path} 不存在，请检查路径。")
            return

        # 检查是否是目录
        if not os.path.isdir(full_dir_path):
            yield event.plain_result(f"指定路径 {dir_path} 不是一个目录。")
            return

        try:
            # 删除目录及其中所有内容
            shutil.rmtree(full_dir_path)
            yield event.plain_result(f"目录 {dir_path} 已成功删除。")
        except Exception as e:
            yield event.plain_result(f"删除目录时发生错误: {str(e)}")

    # 查看目录内容
    async def list_files(self, event: AstrMessageEvent, dir_path: str):
        full_dir_path = self.normalize_path(dir_path)

        # 检查目录是否存在
        if not os.path.exists(full_dir_path):
            yield event.plain_result(f"目录 {dir_path} 不存在，请检查路径。")
            return

        # 检查是否是目录
        if not os.path.isdir(full_dir_path):
            yield event.plain_result(f"指定路径 {dir_path} 不是一个目录。")
            return

        # 获取目录内容
        try:
            files = os.listdir(full_dir_path)
            if not files:
                yield event.plain_result(f"目录 {dir_path} 是空的。")
                return

            # 格式化文件和文件夹输出
            result = ""
            for file in files:
                full_path = os.path.join(full_dir_path, file)
                if os.path.isdir(full_path):
                    result += f"/{file}\n"  # 文件夹前加 '/'
                else:
                    result += f"{file}\n"  # 文件不加 '/'

            yield event.plain_result(f"目录 {dir_path} 的内容：\n{result}")
        except Exception as e:
            yield event.plain_result(f"读取目录时发生错误: {str(e)}")

    # 移动文件或目录
    async def move(self, event: AstrMessageEvent, source_path: str, destination_path: str):
        source_full_path = self.normalize_path(source_path)
        destination_full_path = self.normalize_path(destination_path)

        # 检查源文件/目录是否存在
        if not os.path.exists(source_full_path):
            yield event.plain_result(f"源路径 {source_path} 不存在，请检查路径。")
            return

        try:
            # 移动文件或目录
            shutil.move(source_full_path, destination_full_path)
            yield event.plain_result(f"文件/目录 {source_path} 已成功移动到 {destination_path}。")
        except Exception as e:
            yield event.plain_result(f"移动文件/目录时发生错误: {str(e)}")

    # 复制文件或目录
    async def copy(self, event: AstrMessageEvent, source_path: str, destination_path: str):
        source_full_path = self.normalize_path(source_path)
        destination_full_path = self.normalize_path(destination_path)

        # 检查源文件/目录是否存在
        if not os.path.exists(source_full_path):
            yield event.plain_result(f"源路径 {source_path} 不存在，请检查路径。")
            return

        try:
            # 复制文件或目录
            if os.path.isdir(source_full_path):
                shutil.copytree(source_full_path, destination_full_path)
            else:
                shutil.copy2(source_full_path, destination_full_path)
            yield event.plain_result(f"文件/目录 {source_path} 已成功复制到 {destination_path}。")
        except Exception as e:
            yield event.plain_result(f"复制文件/目录时发生错误: {str(e)}")

    # 处理文件上传到指定目录
    async def upload_file(self, event: AstrMessageEvent, file_path: str, file_content: bytes, file_name: str):
        target_dir = self.normalize_path(file_path)
        full_file_path = os.path.join(target_dir, file_name)
        
        # 确保目录存在
        if not os.path.exists(target_dir):
            try:
                os.makedirs(target_dir)
            except Exception as e:
                yield event.plain_result(f"创建目录失败: {str(e)}")
                return
        
        # 检查文件大小（限制为50MB）
        file_size = len(file_content)
        if file_size > 50 * 1024 * 1024:  # 50MB
            yield event.plain_result(f"文件 {file_name} 大小超过50MB限制，无法上传。")
            return
        
        try:
            # 写入文件
            with open(full_file_path, 'wb') as f:
                f.write(file_content)
            yield event.plain_result(f"文件 {file_name} 已成功上传到 {file_path}")
            yield event.plain_result(f"文件大小: {file_size / 1024:.2f} KB")
        except Exception as e:
            yield event.plain_result(f"上传文件失败: {str(e)}")

    # 解析命令并发送文件
    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("发送")
    async def send_file_command(self, event: AstrMessageEvent):
        '''发送指定文件'''
        messages = event.get_messages()

        if not messages:
            yield event.plain_result("请输入文件路径，格式为 /path/file")
            return

        # 处理消息中的 At 对象
        message_text = ""
        for message in messages:
            if isinstance(message, At):
                continue  # 跳过 At 类型的消息
            message_text = message.text
            break  # 获取第一个非 At 消息

        parts = message_text.split(None, 1)

        # 检查命令格式是否正确
        if len(parts) < 2:
            yield event.plain_result("请输入正确的文件路径，格式为 /path/file")
            return

        file_path = parts[1]

        # 调用文件发送方法
        async for result in self.send_file(event, file_path):
            yield result

    # 解析命令并删除文件
    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("删除")
    async def delete_file_command(self, event: AstrMessageEvent):
        '''删除指定文件'''
        messages = event.get_messages()

        if not messages:
            yield event.plain_result("请输入文件路径，格式为 删除 路径")
            return

        # 处理消息中的 At 对象
        message_text = ""
        for message in messages:
            if isinstance(message, At):
                continue  # 跳过 At 类型的消息
            message_text = message.text
            break  # 获取第一个非 At 消息

        parts = message_text.split(None, 1)

        # 检查命令格式是否正确
        if len(parts) < 2:
            yield event.plain_result("请输入正确的文件路径，格式为 /path/file")
            return

        file_path = parts[1]

        # 调用文件删除方法
        async for result in self.delete_file(event, file_path):
            yield result

    # 解析命令并删除目录
    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("删除目录")
    async def delete_directory_command(self, event: AstrMessageEvent):
        '''删除指定目录'''
        messages = event.get_messages()

        if not messages:
            yield event.plain_result("请输入目录路径，格式为 删除目录 路径")
            return

        # 处理消息中的 At 对象
        message_text = ""
        for message in messages:
            if isinstance(message, At):
                continue  # 跳过 At 类型的消息
            message_text = message.text
            break  # 获取第一个非 At 消息

        parts = message_text.split(None, 1)

        # 检查命令格式是否正确
        if len(parts) < 2:
            yield event.plain_result("请输入正确的目录路径，格式为 删除目录 /path")
            return

        dir_path = parts[1]

        # 调用删除目录方法
        async for result in self.delete_directory(event, dir_path):
            yield result

    # 解析命令并查看目录内容
    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("查看")
    async def list_file_command(self, event: AstrMessageEvent):
        '''查看指定目录的文件和子目录'''
        messages = event.get_messages()

        if not messages:
            yield event.plain_result("请输入目录路径，格式为 查看 路径")
            return

        # 处理消息中的 At 对象
        message_text = ""
        for message in messages:
            if isinstance(message, At):
                continue  # 跳过 At 类型的消息
            message_text = message.text
            break  # 获取第一个非 At 消息

        parts = message_text.split(None, 1)

        # 检查命令格式是否正确
        if len(parts) < 2:
            # 获取当前插件目录
            current_file = os.path.abspath(__file__)
            plugin_dir = os.path.dirname(os.path.dirname(current_file))
            
            help_message = f"""请输入正确的目录路径，格式为 查看 路径
当前插件所在目录: {plugin_dir}
示例: 查看 C:\\Users\\用户名\\Documents 或 查看 /home/user/documents"""
            
            yield event.plain_result(help_message)
            return

        dir_path = parts[1]

        # 调用查看目录内容方法
        async for result in self.list_files(event, dir_path):
            yield result

    # 显示帮助信息
    @filter.command("文件帮助")
    async def show_help(self, event: AstrMessageEvent):
        '''显示帮助信息'''
        help_text = """指令说明：    
/发送 路径 - 发送指定路径的文件（绝对路径） 
/上传 后缀名 上传目录 - 上传文件到指定目录（如: /上传 .mp4 /Chris）
/删除 路径 - 删除指定路径的文件（绝对路径） 
/删除目录 路径 - 删除指定路径的目录（绝对路径） 
/查看 路径 - 查看指定目录的文件和子目录（绝对路径） 
/移动 源路径 目标路径 - 移动指定路径的文件或目录
/复制 源路径 目标路径 - 复制指定路径的文件或目录
/插件路径 - 获取插件基础路径（此插件的上上级目录）
/文件帮助 - 显示本帮助信息（除此命令外，其余命令均默认开启管理员权限。）

上传说明: 
- 文件名格式为 file_时间戳.后缀名
- 示例: /上传 .mp4 /Chris (视频文件) /上传 .jpg /temp (图片文件) /上传 无后缀 /data (无扩展名)"""
        yield event.plain_result(help_text)

    # 解析命令并移动文件或目录
    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("移动")
    async def move_command(self, event: AstrMessageEvent):
        '''移动指定文件或目录'''
        messages = event.get_messages()

        if not messages:
            yield event.plain_result("请输入源路径和目标路径，格式为 移动 源路径 目标路径")
            return

        # 处理消息中的 At 对象
        message_text = ""
        for message in messages:
            if isinstance(message, At):
                continue  # 跳过 At 类型的消息
            message_text = message.text
            break  # 获取第一个非 At 消息

        parts = message_text.split(None, 2)

        # 检查命令格式是否正确
        if len(parts) < 3:
            yield event.plain_result("请输入正确的路径格式，格式为 移动 源路径 目标路径")
            return

        source_path = parts[1]
        destination_path = parts[2]

        # 调用移动方法
        async for result in self.move(event, source_path, destination_path):
            yield result

    # 解析命令并复制文件或目录
    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("复制")
    async def copy_command(self, event: AstrMessageEvent):
        '''复制指定文件或目录'''
        messages = event.get_messages()

        if not messages:
            yield event.plain_result("请输入源路径和目标路径，格式为 复制 源路径 目标路径")
            return

        # 处理消息中的 At 对象
        message_text = ""
        for message in messages:
            if isinstance(message, At):
                continue  # 跳过 At 类型的消息
            message_text = message.text
            break  # 获取第一个非 At 消息

        parts = message_text.split(None, 2)

        # 检查命令格式是否正确
        if len(parts) < 3:
            yield event.plain_result("请输入正确的路径格式，格式为 复制 源路径 目标路径")
            return

        source_path = parts[1]
        destination_path = parts[2]

        # 调用复制方法
        async for result in self.copy(event, source_path, destination_path):
            yield result

    # 获取插件路径（main.py的上上级目录）
    async def get_plugin_base_path(self, event: AstrMessageEvent):
        try:
            # 获取当前文件的绝对路径
            current_file = os.path.abspath(__file__)
            # 获取上上级目录
            plugin_base_path = os.path.dirname(os.path.dirname(current_file))
            
            yield event.plain_result(f"插件基础路径: {plugin_base_path}")
        except Exception as e:
            yield event.plain_result(f"获取插件路径失败: {str(e)}")

    # 解析命令并获取插件路径
    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("插件路径")
    async def plugin_path_command(self, event: AstrMessageEvent):
        '''获取插件基础路径'''
        async for result in self.get_plugin_base_path(event):
            yield result

    # 解析命令并处理文件上传
    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("上传")
    async def upload_command(self, event: AstrMessageEvent):
        '''上传文件，格式: /上传 后缀名 上传目录 (如 /上传 .mp4 /Chris)'''
        messages = event.get_messages()

        if not messages:
            yield event.plain_result("请输入后缀名和上传目录，格式为: 上传 .mp4 /Chris")
            return

        # 处理消息中的 At 对象
        message_text = ""
        for message in messages:
            if isinstance(message, At):
                continue  # 跳过 At 类型的消息
            message_text = message.text
            break  # 获取第一个非 At 消息

        parts = message_text.split(None, 2)

        # 检查命令格式是否正确
        if len(parts) < 3:
            yield event.plain_result("请输入后缀名和上传目录，格式为: 上传 .mp4 /Chris")
            return

        extension = parts[1].strip()
        target_path = parts[2].strip()
        
        # 处理特殊情况
        if extension == "无后缀":
            extension = ""
        elif not extension.startswith(".") and extension != "":
            extension = "." + extension  # 自动添加点号

        uid = event.get_sender_id()
        self.user_waiting[uid] = {
            'time': time.time(), 
            'path': target_path,
            'extension': extension
        }
        
        ext_text = f"后缀名 {extension}" if extension else "无后缀"
        yield event.plain_result(f"文件上传器: 请在 60s 内上传一个文件，将保存到 {target_path}，文件 {ext_text}。")
        await asyncio.sleep(60)
        
        if uid in self.user_waiting:
            yield event.plain_result(
                f"文件上传器: {event.get_sender_name()}/{event.get_sender_id()} 未在规定时间内上传文件。"
            )
            self.user_waiting.pop(uid)

    # 处理用户发送的文件消息
    @filter.event_message_type(filter.EventMessageType.ALL)
    async def handle_file_message(self, event: AstrMessageEvent):
        '''处理用户上传的文件'''
        uid = event.get_sender_id()
        
        # 检查用户是否在等待上传文件
        if uid not in self.user_waiting:
            return
        
        # 先检查是否有文件或图片组件
        has_file = False
        for comp in event.message_obj.message:
            if isinstance(comp, (File, Image, Video)):
                has_file = True
                break
        
        # 如果没有文件组件，不处理
        if not has_file:
            return
        
        # 获取等待信息
        waiting_info = self.user_waiting.pop(uid)
        target_path = waiting_info['path']
        extension = waiting_info['extension']
        
        for comp in event.message_obj.message:
            if isinstance(comp, (File, Image, Video)):
                try:
                    # 生成文件名: 时间戳 + 扩展名
                    file_name = f"file_{int(time.time())}{extension}"
                    
                    # 统一使用 get_file() 方法获取文件路径
                    if hasattr(comp, 'get_file'):
                        file_path = await comp.get_file()
                        if file_path and os.path.exists(file_path):
                            with open(file_path, 'rb') as f:
                                file_content = f.read()
                        else:
                            yield event.plain_result(f"无法获取文件: {file_path}")
                            return
                    else:
                        yield event.plain_result("该文件类型不支持 get_file() 方法")
                        return
                    
                    # 上传文件
                    async for result in self.upload_file(event, target_path, file_content, file_name):
                        yield result
                    return  # 处理完第一个文件就退出
                        
                except Exception as e:
                    yield event.plain_result(f"处理文件失败: {str(e)}")
                    return
