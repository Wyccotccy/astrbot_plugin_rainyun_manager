# astrbot_plugin_rainyun_manager

# 雨云管理插件 (Rainyun Manager)

一个功能完整的 AstrBot 插件，用于通过雨云 API 管理账号下的云服务器、域名、SSL 证书、订单及用户信息等资源。支持管理员指令和 LLM 工具调用双入口。

## ✨ 功能特性

- **丰富的 API 覆盖**：对接雨云 48 个 API，涵盖产品、域名、DNS、DNSSEC、SSL 证书、积分、用户、订单等模块
- **双入口**：
  - **管理员指令**：通过 `/rainyun` 命令组进行快速查询
  - **LLM 工具**：对外暴露 4 个 LLM 工具，大模型可自动搜索并执行操作，Token 友好
- **灵活权限控制**：支持仅管理员、管理员和成员、白名单三种使用范围
- **功能开关**：提供插件总开关、查询功能总开关、操作功能总开关
- **安全设计**：操作类工具严格权限校验，关键操作需管理员或白名单授权

## 📦 安装

1. 在 AstrBot WebUI 的「插件管理」页面，点击「安装插件」
2. 输入本插件仓库地址：`https://github.com/Wyccotccy/astrbot_plugin_rainyun_manager`
3. 或手动将插件目录 `rainyun_manager` 放置到 AstrBot 的 `data/plugins` 下，然后重载插件

## ⚙️ 配置

安装完成后，在插件管理页面找到「雨云管理插件」，点击「配置」进入设置界面。

### 必填项

| 配置项 | 说明 |
|--------|------|
| **api_key** | 雨云 API 密钥，获取地址：https://app.rainyun.com/account/settings/api-key |

### 权限范围

| 配置项 | 说明 |
|--------|------|
| **access_mode** | 插件使用权限范围，可选：`仅管理员`、`管理员和成员`、`白名单模式` |
| **whitelist** | 白名单用户 ID 列表（当 `access_mode` 为白名单模式时生效） |

### 功能开关

| 配置项 | 说明 |
|--------|------|
| **enable_plugin** | 插件总开关 |
| **enable_query** | 查询功能总开关（关闭后所有只读查询工具不可用） |
| **enable_operation** | 操作功能总开关（关闭后所有修改类工具不可用） |

## 🕹️ 管理员指令

所有指令均使用 `/rainyun` 命令组，仅管理员可用（权限受配置控制）。

| 指令 | 说明 |
|------|------|
| `/rainyun status` | 查询账号下所有产品汇总及使用情况 |
| `/rainyun domains` | 获取域名列表 |
| `/rainyun user` | 获取用户信息 |

后续版本会陆续增加更多快捷指令。

## 🤖 LLM 工具使用

插件向大模型暴露 4 个工具，LLM 会自动搜索并调用：

| 工具名 | 功能 | 说明 |
|--------|------|------|
| **search_query_tool** | 搜索查询类工具 | 通过关键词搜索可用的查询功能（如域名列表、产品状态等） |
| **search_execution_tool** | 搜索操作类工具 | 通过关键词搜索可用的操作功能（如续费、添加解析等） |
| **complete_tool_list** | 查看完整工具列表 | 当搜索无结果时调用，列出所有可用工具 |
| **executive_tool** | 执行指定工具 | 传入工具名称和 JSON 参数，执行具体操作 |

**示例对话：**

> 用户：帮我看看我的雨云服务器还有多久到期？
> 
> 机器人（调用 search_query_tool 搜索 "到期"）→ 找到 get_product_summary
> → 调用 executive_tool 执行 get_product_summary → 返回到期时间列表

> 用户：添加一条域名解析，把 www 指向 1.2.3.4
> 
> 机器人（调用 search_execution_tool 搜索 "添加解析"）→ 找到 add_dns_record
> → 询问缺少的域名 ID → 用户提供域名 ID
> → 调用 executive_tool 执行 add_dns_record → 返回添加结果

## 📁 项目结构
```

rainyun_manager/
├── main.py             # 插件主代码
├── metadata.yaml       # 插件元数据
├── _conf_schema.json   # 配置项 Schema
├── requirements.txt    # 依赖声明
└── README.md           # 本文件

```

## 🔗 相关链接

- [雨云 API 密钥获取](https://app.rainyun.com/account/settings/api-key)
- [AstrBot 官方文档](https://github.com/Soulter/AstrBot)

## 📝 开发者

- **作者**：Wyccotccy
- **版本**：1.0.0

如有问题或建议，欢迎在 GitHub 仓库提交 Issue。
