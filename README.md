# ErisPulse-InfoQuery

信息统计查询模块，用于查询 InfoStats 模块收集的统计数据。

## 功能

该模块提供了一系列指令，用于查询由 `ErisPulse-InfoStats` 模块收集的统计信息，支持所有平台。

## 指令列表

- `/stats` - 显示总体统计信息
- `/platform` - 显示各平台统计信息
- `/recent [数量]` - 显示最近事件（默认10条，最多50条）
- `/user [用户ID]` - 显示用户统计信息（私聊中可省略ID）
- `/group [群组ID] - 显示群组统计信息（群组中可省略ID）
- `/infohelp` - 显示帮助信息

## 配置

模块支持自定义指令名称。默认配置如下：

```toml
[InfoQuery]
default_limit = 10
max_limit = 50

[InfoQuery.commands]
stats = "stats"
platform = "platform"
recent = "recent"
user = "user"
group = "group"
help = "infohelp"
```