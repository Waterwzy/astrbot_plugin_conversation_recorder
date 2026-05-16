# astrbot_plugin_conversation_recorder

用户消息记录插件

一个可以记录特定用户发送的文本消息，方便放入`女娲.skill`蒸馏。

## 插件指令：
> [!TIP]
>
> 本插件所有指令仅有管理员有权使用。
>
> 本插件所有指令注册了`cr`插件组，方便管理

1. `/cr clear user`
用于清除指定用户的记录。

参数：
- user:必填项，指定用户的id

2. `/cr show`
用于展示目前收集到的所有记录

> [!IMPORTANT]
>
> 本指令输出的是一个json文件，为一个dict；key为记录用户的id，value为记录的消息列表，每个元素为一条消息。

一个挺简单的插件，没啥好说的（
