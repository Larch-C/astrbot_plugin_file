
<div align="center">

![:name](https://count.getloli.com/@astrbot_plugin_file?name=astrbot_plugin_file&theme=minecraft&padding=6&offset=0&align=top&scale=1&pixelated=1&darkmode=auto)

# astrbot_plugin_file

_✨ [astrbot](https://github.com/AstrBotDevs/AstrBot) 文件操作 ✨_  

[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![AstrBot](https://img.shields.io/badge/AstrBot-3.4%2B-orange.svg)](https://github.com/Soulter/AstrBot)
[![GitHub](https://img.shields.io/badge/作者-Chris-blue)](https://github.com/Chris95743)

</div>

## 🤝 介绍

- 一个简单的文件发送、删除、移动、复制和查看文件夹内容插件，命令均默认开启管理员权限。

## 📦 安装

- 可以直接在astrbot的插件市场搜索astrbot_plugin_file，点击安装，耐心等待安装完成即可
- 若是安装失败，可以尝试直接克隆源码：

```bash
# 克隆仓库到插件目录
cd /AstrBot/data/plugins
git clone https://github.com/Chris95743/astrbot_plugin_file

# 控制台重启AstrBot
```

## ⌨️ 使用说明

### 命令

- 进行基本简单的文件操作，包括查看，发送，删除（包括目录），移动，复制本地文件。
- 当然，出于安全考虑，以上所有命令仅限管理员使用。
- Windows用户可直接使用，如果您是docker用户，请提前在AstrBot容器和协议端容器挂载好需要进行操作的目录。
- 安全（重要）：进行文件操作前务必三思！！！尤其是使用删删除功能时。

- 指令调用，如下：

```plaintext
/发送 路径 - 发送指定路径的文件（绝对路径） 
/删除 路径 - 删除指定路径的文件（绝对路径） 
/删除目录 路径 - 删除指定路径的目录（绝对路径） 
/查看 路径 - 查看指定目录的文件和子目录（绝对路径） 
/移动 源路径 目标路径 - 移动指定路径的文件或目录
/复制 源路径 目标路径 - 复制指定路径的文件或目录
/文件帮助 - 显示本帮助信息（除此命令外，其余命令均默认开启管理员权限。）
```


## 🤝 可能用途


- [ ] 用于在QQ上快速取出一些存在电脑中的文件。
- [ ] 快捷删除一些因报错而无法在控制台上直接删除的插件。
- [ ] 作为文件操作函数工具的补充（补充了删除和发送功能）。
- [ ] 再次提醒（重要）：进行文件操作前务必三思！！！尤其是使用删删除功能时。

## 👥 贡献指南

- 🌟 Star 这个项目！（点右上角的星星，感谢支持！）
- 🐛 提交 Issue 报告问题
- 💡 提出新功能建议
- 🔧 提交 Pull Request 改进代码

## 📌 注意事项

- 最后提醒（重要）：进行文件操作前务必三思！！！尤其是使用删删除功能时。
- 本插件仅供学习交流，作者不承担任何责任，如有需要，可QQ联系:1436198704。
- 其实本来只想写个文件发送的功能，但后来想着既然写都写了，就干脆添加了一些文件操作的内容。
