import asyncio
import json
import re
import aiohttp
from typing import Any

from astrbot.api import star, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.message_components import Plain
from astrbot.core.message.message_event_result import MessageChain

# ============================================================================
# 48 个雨云 API 工具的完整定义（内部工具库）
# 每个工具包含：name, description, type(query/operation), parameters, keywords(50个)
# ============================================================================

INTERNAL_TOOLS: list[dict[str, Any]] = [
    # --------------------------------- 产品类 ---------------------------------
    {
        "name": "get_product_summary",
        "description": "获取雨云用户产品汇总数据和使用情况，包括所有产品的状态、到期时间、使用量等信息",
        "type": "query",
        "parameters": {},
        "keywords": [
            "产品汇总", "使用情况", "产品状态", "到期时间", "服务器状态", "总体概览", "账号概览",
            "产品信息", "产品列表汇总", "product summary", "usage", "overview", "status",
            "云服务器状态", "主机状态", "全部产品", "产品总览", "资源使用", "服务器汇总",
            "查看产品", "我的产品", "产品概览", "账号产品", "产品概况", "all products",
            "资源概览", "查看服务器", "我的服务器", "服务器列表", "使用量", "汇总数据",
            "账户信息", "面板概览", "dashboard", "summary", "查看使用情况", "资源情况",
            "服务器概况", "服务状态", "账号状态", "在用的产品", "机器状态", "机器列表",
            "product overview", "服务汇总", "当前产品", "已购产品", "产品详情汇总"
        ]
    },
    {
        "name": "get_product_id_list",
        "description": "获取雨云产品ID列表，可按产品类型和区域筛选",
        "type": "query",
        "parameters": {
            "product_type": {"type": "string", "required": False, "description": "产品类型，可选: rvh(云服务器)/rcs(云应用)/rgs(云游戏)/rbm(裸金属)/ros(对象存储)/rcdn(CDN)"},
            "region": {"type": "string", "required": False, "description": "区域"}
        },
        "keywords": [
            "产品ID", "ID列表", "产品标识", "产品编号", "id list", "product id",
            "服务器ID", "获取ID", "查看ID", "产品id列表", "产品号", "机器编号",
            "服务器编号", "产品识别码", "产品查询", "筛选产品", "按类型查产品",
            "产品类型筛选", "区域筛选", "产品过滤", "list id", "get id",
            "产品分类", "product type", "region", "产品区域", "产品搜索",
            "查找产品", "搜索产品", "查id", "获取产品号", "编号列表",
            "产品清单", "产品目录", "产品索引", "产品检索", "按条件查询",
            "product filter", "id查询", "产品查找", "编号查询", "identifier",
            "产品定位", "产品枚举", "列表id", "id检索", "获取编号"
        ]
    },
    {
        "name": "point_renew",
        "description": "使用雨云积分续费产品",
        "type": "operation",
        "parameters": {
            "product_type": {"type": "string", "required": True, "description": "产品类型: rvh/rcs/rgs/rbm/ros/rcdn"},
            "product_id": {"type": "integer", "required": True, "description": "产品ID"},
            "duration_day": {"type": "integer", "required": True, "description": "续费天数"}
        },
        "keywords": [
            "积分续费", "续费", "积分", "使用积分", "续期", "延长", "renew", "point renew",
            "积分延长", "积分抵扣", "积分支付", "免费续费", "积分兑换天数", "续费天数",
            "用积分续", "积续", "point续费", "积分续期", "延长到期", "续费产品",
            "product renew", "续费操作", "云服务器续费", "主机续费", "延长使用",
            "积分消费", "积分使用", "续费功能", "自动续费积分", "积分续",
            "天数续费", "续费时长", "产品续期", "服务续费", "续费服务",
            "服务器续期", "积分换时长", "积分加时间", "延长服务器", "续时间",
            "加天数", "加时间", "续费机器", "机器续费", "云服务续费",
            "续费云服务器", "renewal", "extend", "积分延长服务", "延长产品"
        ]
    },
    {
        "name": "get_fast_install_apps",
        "description": "查询雨云服务器可快速安装的APP列表",
        "type": "query",
        "parameters": {
            "product_type": {"type": "string", "required": True, "description": "产品类型: rcs(云应用)/rgs(云游戏)"},
            "os_name": {"type": "string", "required": False, "description": "操作系统名称，可选"}
        },
        "keywords": [
            "快速安装", "一键安装", "应用列表", "APP列表", "可安装应用", "fast install",
            "软件安装", "预装应用", "应用市场", "应用商店", "一键部署", "快速部署",
            "安装程序", "可装软件", "应用安装", "quick install", "app install",
            "支持的应用", "模板应用", "应用模板", "预置应用", "预设应用", "装机",
            "部署应用", "安装列表", "软件列表", "软件库", "应用库", "程序列表",
            "游戏服务器应用", "云应用安装", "软件商店", "安装选项", "可选应用",
            "一键装", "快速装", "应用快捷安装", "源码部署", "环境安装",
            "一键搭建", "快速搭建", "app list", "applications", "软件市场",
            "可用的应用", "安装包", "可用软件", "应用中心", "软件中心"
        ]
    },
    {
        "name": "get_product_zones",
        "description": "获取雨云可用区列表",
        "type": "query",
        "parameters": {},
        "keywords": [
            "可用区", "区域", "数据中心", "节点", "机房", "zones", "region", "可用区域",
            "部署区域", "服务器位置", "云区域", "地区", "地理位置", "机房位置",
            "可用地区", "可选区域", "zone list", "数据中心位置", "节点列表",
            "区域列表", "可选数据中心", "服务器机房", "机房列表", "云节点",
            "区域选择", "部署地区", "地域", "所在区域", "位置", "location",
            "可用位置", "节点地区", "云机房", "数据节点", "服务器区域", "物理区域",
            "机房区域", "zone", "area", "dc", "datacenter", "地区列表",
            "可选地区", "节点区域", "边缘节点", "计算区域", "cloud region"
        ]
    },
    {
        "name": "get_task_log",
        "description": "获取雨云产品任务日志，查看操作记录和执行状态",
        "type": "query",
        "parameters": {
            "options": {"type": "string", "required": True, "description": "标准查询参数（JSON格式）"},
            "log_type": {"type": "string", "required": True, "description": "日志类型"}
        },
        "keywords": [
            "任务日志", "操作日志", "执行记录", "日志", "操作记录", "task log", "log",
            "运行日志", "事件记录", "历史记录", "操作历史", "任务记录", "审计日志",
            "活动日志", "日志查询", "查询日志", "查看日志", "执行日志", "任务历史",
            "操作审计", "日志记录", "任务执行", "后台任务", "异步任务", "job log",
            "任务状态", "执行状态", "操作追踪", "变更记录", "事件日志", "日志查看",
            "activity log", "history", "任务详情", "日志列表", "操作详情",
            "运行记录", "后台日志", "系统日志", "操作追踪记录", "任务跟踪",
            "日志信息", "记录查询", "任务监控", "操作监控", "日志检索"
        ]
    },

    # --------------------------------- 域名类 ---------------------------------
    {
        "name": "get_domain_list",
        "description": "获取雨云域名列表",
        "type": "query",
        "parameters": {
            "options": {"type": "string", "required": True, "description": "标准查询参数（JSON格式）"}
        },
        "keywords": [
            "域名列表", "域名", "domain list", "所有域名", "域名管理", "查看域名",
            "域名概览", "我的域名", "域名汇总", "全部域名", "域名信息", "domains",
            "已注册域名", "域名清单", "域名目录", "列出域名", "域名查看", "域名页",
            "域名查询", "查询域名", "域名面板", "域名控制台", "域名总览",
            "域名资产", "域名资源", "domain管理", "域名检索", "list domains",
            "获取域名", "域名页面", "域名一览", "展示域名", "域名列表页",
            "域名记录", "域名库", "名下域名", "账户域名", "域名概览页",
            "域名数据", "域名资料", "domain info", "查看所有域名", "域名集合"
        ]
    },
    {
        "name": "get_domain_detail",
        "description": "获取雨云单个域名的详细信息",
        "type": "query",
        "parameters": {
            "id": {"type": "string", "required": True, "description": "域名ID"}
        },
        "keywords": [
            "域名详情", "域名信息", "域名详细", "域名资料", "查看域名", "domain detail",
            "域名属性", "域名配置", "域名设置", "域名具体", "单个域名", "特定域名",
            "域名状态", "域名内容", "域名数据", "详细信息", "detail", "域名查看详细",
            "域名解析信息", "域名管理详情", "域名细节", "域名完整信息", "domain info detail",
            "查询域名详情", "获取域名信息", "查看具体域名", "指定域名", "域名详细资料",
            "域名详细配置", "域名详细数据", "域名详细页", "域名具体信息", "域名属性查看",
            "域名详细内容", "域名记录详情", "域名元数据", "单域名详情", "域名详细情况",
            "域名详情页", "域名总览详情", "域名参数", "域名详情查看", "domain详细"
        ]
    },
    {
        "name": "get_dns_records",
        "description": "获取域名DNS解析记录列表",
        "type": "query",
        "parameters": {
            "id": {"type": "string", "required": True, "description": "域名ID"},
            "limit": {"type": "integer", "required": True, "description": "每页大小"},
            "page_no": {"type": "integer", "required": True, "description": "页码"}
        },
        "keywords": [
            "DNS记录", "解析记录", "DNS", "域名解析", "解析列表", "dns records",
            "DNS查询", "DNS解析记录", "解析查看", "记录查询", "解析设置",
            "域名DNS", "DNS配置", "解析配置", "DNS记录查询", "查看DNS",
            "解析信息", "DNS列表", "解析记录列表", "record list", "dns list",
            "A记录", "CNAME记录", "MX记录", "TXT记录", "AAAA记录", "SRV记录",
            "解析", "域名记录", "DNS管理", "DNS详情", "解析数据",
            "解析内容", "DNS条目", "解析规则", "dns entry", "域名指向",
            "dns解析", "解析查询", "记录查看", "DNS查看", "解析记录查询",
            "获取解析", "查看解析", "解析详情", "DNS信息", "域名绑定"
        ]
    },
    {
        "name": "add_dns_record",
        "description": "添加域名DNS解析记录",
        "type": "operation",
        "parameters": {
            "id": {"type": "string", "required": True, "description": "域名ID"},
            "host": {"type": "string", "required": True, "description": "主机名"},
            "type": {"type": "string", "required": True, "description": "解析类型: A/CNAME/MX/TXT/AAAA/SRV"},
            "value": {"type": "string", "required": True, "description": "解析值"},
            "ttl": {"type": "integer", "required": True, "description": "解析生效时间(秒)"},
            "line": {"type": "string", "required": True, "description": "线路: DEFAULT/LTEL/LCNC/LMOB/LEDU/LSEO/LFOR"},
            "level": {"type": "integer", "required": False, "description": "优先等级（MX记录用）"},
            "rain_product_id": {"type": "integer", "required": False, "description": "关联产品ID"},
            "rain_product_type": {"type": "string", "required": False, "description": "关联产品类型: rcs/rvh/rgs/rbm"}
        },
        "keywords": [
            "添加DNS", "新增解析", "添加解析", "新建DNS", "增加解析记录",
            "添加域名解析", "add dns", "创建解析", "增加DNS", "新增解析记录",
            "DNS添加", "解析添加", "加解析", "新建解析", "创建DNS记录",
            "添加A记录", "添加CNAME", "添加MX", "添加TXT", "添加AAAA", "添加SRV",
            "解析新增", "域名绑定IP", "域名指向", "解析指向", "设置解析",
            "配置DNS", "DNS设置", "添加记录", "create dns", "new record",
            "建立解析", "绑定域名", "域名配置", "解析规则添加", "设置域名解析",
            "创建域名解析", "增加一条解析", "添加一条解析", "新增dns", "dns解析添加",
            "域名加解析", "添加解析规则", "解析建立", "新建DNS记录", "添加域名记录"
        ]
    },
    {
        "name": "update_dns_record",
        "description": "修改域名DNS解析记录",
        "type": "operation",
        "parameters": {
            "id": {"type": "string", "required": True, "description": "域名ID"},
            "record_id": {"type": "integer", "required": True, "description": "记录ID"},
            "host": {"type": "string", "required": True, "description": "主机名"},
            "type": {"type": "string", "required": True, "description": "解析类型: A/CNAME/MX/TXT/AAAA/SRV"},
            "value": {"type": "string", "required": True, "description": "解析值"},
            "ttl": {"type": "integer", "required": True, "description": "解析生效时间(秒)"},
            "line": {"type": "string", "required": True, "description": "线路: DEFAULT/LTEL/LCNC/LMOB/LEDU/LSEO/LFOR"}
        },
        "keywords": [
            "修改DNS", "更新解析", "修改解析", "编辑DNS", "更改解析记录",
            "update dns", "变更解析", "DNS修改", "解析修改", "修改解析记录",
            "更新DNS记录", "编辑解析", "改DNS", "重设解析", "修改域名解析",
            "DNS更新", "解析更新", "改解析", "变更DNS", "修改记录",
            "更新记录", "edit dns", "modify dns", "修改A记录", "修改CNAME",
            "修改MX", "修改TXT", "修改AAAA", "修改SRV", "解析变更",
            "DNS变更", "解析重设", "DNS重设", "更改DNS", "修改解析设置",
            "更新域名解析", "修改域名记录", "改域名解析", "解析编辑", "DNS编辑",
            "修改指向", "更新指向", "更改指向", "修改解析规则", "更新解析规则"
        ]
    },
    {
        "name": "delete_dns_record",
        "description": "删除域名DNS解析记录",
        "type": "operation",
        "parameters": {
            "id": {"type": "string", "required": True, "description": "域名ID"},
            "record_id": {"type": "integer", "required": True, "description": "要删除的解析记录ID"}
        },
        "keywords": [
            "删除DNS", "删除解析", "移除解析", "删除解析记录", "DNS删除",
            "delete dns", "去掉解析", "清除解析", "移除DNS", "删除域名解析",
            "解析删除", "DNS移除", "去除DNS", "删解析", "删除记录",
            "remove dns", "清除DNS", "删除A记录", "删除CNAME", "删除MX",
            "删除TXT", "删除AAAA", "删除SRV", "解析清除", "解除解析",
            "解绑域名", "取消解析", "撤销解析", "去掉DNS", "删除解析规则",
            "删除DNS记录", "移除DNS记录", "清理解析", "解析移除", "删除指向",
            "取消指向", "去掉绑定", "解除绑定", "删除域名记录", "dns条目删除",
            "废弃解析", "停用解析", "移除解析规则", "删除域名指向", "清理DNS"
        ]
    },
    {
        "name": "get_dnssec",
        "description": "获取域名DNSSEC详情",
        "type": "query",
        "parameters": {
            "id": {"type": "string", "required": True, "description": "域名ID"}
        },
        "keywords": [
            "DNSSEC", "DNSSEC详情", "DNSSEC信息", "DNSSEC状态", "域名安全扩展",
            "DNSSEC查询", "查看DNSSEC", "获取DNSSEC", "DNS安全", "域名安全",
            "安全扩展", "DNSSEC配置", "DNSSEC设置", "dnssec info", "dnssec detail",
            "DNSSEC查看", "安全DNS", "域名签名", "DNS签名", "dnssec status",
            "DNSSEC情况", "DNSSEC数据", "DNSSEC记录", "DNSSEC查询结果", "签名信息",
            "域名安全扩展详情", "DNSSEC内容", "查看安全扩展", "获取安全扩展", "dnssec",
            "域名安全设置", "安全扩展详情", "DNSSEC查看详情", "域名保护", "DNS保护",
            "域名验证", "DNS验证", "域名加密", "DNS加密", "安全解析"
        ]
    },
    {
        "name": "add_dnssec",
        "description": "添加域名DNSSEC",
        "type": "operation",
        "parameters": {
            "id": {"type": "string", "required": True, "description": "域名ID"},
            "domain": {"type": "string", "required": True, "description": "域名"},
            "keyalg": {"type": "string", "required": True, "description": "密钥算法"},
            "keydigest": {"type": "string", "required": True, "description": "密钥摘要"},
            "keytag": {"type": "string", "required": True, "description": "密钥标签"},
            "keytype": {"type": "string", "required": True, "description": "密钥类型"}
        },
        "keywords": [
            "添加DNSSEC", "开启DNSSEC", "启用DNSSEC", "设置DNSSEC", "新建DNSSEC",
            "配置DNSSEC", "添加域名安全", "add dnssec", "create dnssec",
            "DNSSEC添加", "DNSSEC启用", "DNSSEC开启", "部署DNSSEC", "建立DNSSEC",
            "安全扩展添加", "新增DNSSEC", "添加安全扩展", "域名安全设置", "DNS安全设置",
            "打开DNSSEC", "启动DNSSEC", "添加签名", "配置签名", "增加DNSSEC",
            "安装DNSSEC", "激活DNSSEC", "设置域名安全", "添加域名保护", "开启安全扩展",
            "DNSSEC登记", "注册DNSSEC", "添加DNS安全", "开启域名验证", "配置安全扩展",
            "enable dnssec", "setup dnssec", "安装安全扩展", "添加加密", "配置加密"
        ]
    },
    {
        "name": "delete_dnssec",
        "description": "删除域名DNSSEC",
        "type": "operation",
        "parameters": {
            "id": {"type": "string", "required": True, "description": "域名ID"},
            "domain": {"type": "string", "required": True, "description": "域名"},
            "keydigest": {"type": "string", "required": True, "description": "密钥摘要"},
            "keytag": {"type": "integer", "required": True, "description": "密钥标签"}
        },
        "keywords": [
            "删除DNSSEC", "关闭DNSSEC", "停用DNSSEC", "移除DNSSEC", "取消DNSSEC",
            "delete dnssec", "remove dnssec", "DNSSEC删除", "DNSSEC关闭", "DNSSEC停用",
            "安全扩展删除", "移除安全扩展", "删除安全扩展", "关闭安全扩展", "去掉DNSSEC",
            "解除DNSSEC", "卸载DNSSEC", "清除DNSSEC", "DNSSEC移除", "取消安全扩展",
            "删除域名安全", "关闭域名安全", "停用安全扩展", "禁用DNSSEC", "disable dnssec",
            "去除DNSSEC", "清理DNSSEC", "撤销DNSSEC", "删除签名", "移除签名",
            "域名保护删除", "安全设置删除", "删除加密", "移除加密", "关闭签名",
            "废弃DNSSEC", "下掉DNSSEC", "取消域名验证", "关闭域名验证", "删除安全配置"
        ]
    },
    {
        "name": "sync_dnssec",
        "description": "同步域名DNSSEC",
        "type": "operation",
        "parameters": {
            "id": {"type": "string", "required": True, "description": "域名ID"}
        },
        "keywords": [
            "同步DNSSEC", "DNSSEC同步", "刷新DNSSEC", "更新DNSSEC", "sync dnssec",
            "DNSSEC刷新", "同步安全扩展", "刷新安全扩展", "更新安全扩展", "同步域名安全",
            "重新同步", "强制同步", "手动同步", "刷新签名", "同步签名",
            "DNSSEC更新", "安全扩展同步", "域名签名同步", "签名同步", "dnssec sync",
            "同步DNS安全", "刷新DNS安全", "同步域名签名", "重新加载DNSSEC", "reload dnssec",
            "DNSSEC重载", "刷新域名安全", "更新域名安全", "重整DNSSEC", "DNSSEC重置同步",
            "同步验证", "刷新验证", "更新验证", "安全同步", "证书同步"
        ]
    },
    {
        "name": "disable_domain_lock",
        "description": "关闭域名锁定",
        "type": "operation",
        "parameters": {
            "id": {"type": "string", "required": True, "description": "域名ID"}
        },
        "keywords": [
            "关闭域名锁定", "解锁域名", "域名解锁", "取消锁定", "解除锁定",
            "disable lock", "unlock domain", "打开锁定", "移除锁定", "关闭锁定",
            "域名解锁操作", "解锁", "去锁", "取消域名锁", "解封域名",
            "域名保护关闭", "关闭锁定保护", "取消保护", "暂停保护", "关闭域名保护",
            "允许转移", "解除域名锁定", "关锁定", "去除锁定", "停用锁定",
            "解锁操作", "关闭安全锁", "关闭域名锁", "取消域名锁定", "释放域名",
            "域名解禁", "解封", "开启转移", "允许转让", "解除转让锁定",
            "关闭transfer lock", "域名自由转移", "取消安全锁定", "停用安全锁", "域解锁"
        ]
    },
    {
        "name": "enable_domain_lock",
        "description": "开启域名锁定",
        "type": "operation",
        "parameters": {
            "id": {"type": "string", "required": True, "description": "域名ID"}
        },
        "keywords": [
            "开启域名锁定", "锁定域名", "域名锁定", "加锁", "上锁",
            "enable lock", "lock domain", "设置锁定", "打开锁定", "开启锁定",
            "域名保护", "安全锁定", "禁止转移", "锁定保护", "域名加锁",
            "开锁设置", "开启域名锁", "启用锁定", "启动锁定", "域名防护",
            "开启域名保护", "激活锁定", "设置域名锁", "域名安全锁", "防止转移",
            "禁止转让", "锁定setting", "开启安全锁", "打开域名锁", "启用保护",
            "开启transfer lock", "上锁域名", "域名加固", "安全加固", "盗用保护",
            "域名防丢", "防转移", "锁定配置", "保护设置", "安全锁定设置"
        ]
    },
    {
        "name": "renew_domain",
        "description": "续费域名",
        "type": "operation",
        "parameters": {
            "id": {"type": "string", "required": True, "description": "域名ID"},
            "duration": {"type": "integer", "required": True, "description": "续费年限(1-10)"}
        },
        "keywords": [
            "续费域名", "域名续费", "续期域名", "延长域名", "renew domain",
            "域名续期", "续费", "续约", "域名延长", "加长时间",
            "延长注册", "域名续费操作", "域名再续", "继续使用域名", "续费一年",
            "域名年费", "续年限", "续时长", "域名付费", "付费续期",
            "域名到期续", "续费域名操作", "延长域名有效期", "续期操作", "domain renew",
            "域名保留", "继续域名", "域名续", "续费服务", "域名购买续费",
            "注册续费", "域名时长", "续域名", "续费功能", "域名过期续",
            "延长域名时间", "域名续时长", "域名续约操作", "续费年限", "域名年续"
        ]
    },
    {
        "name": "get_domain_renew_price",
        "description": "获取域名续费价格",
        "type": "query",
        "parameters": {
            "id": {"type": "string", "required": True, "description": "域名ID"}
        },
        "keywords": [
            "域名续费价格", "续费价格", "域名价格", "续费多少钱", "查询续费价格",
            "renew price", "domain price", "价格查询", "续费费用", "续费成本",
            "域名费用", "续费金额", "查看价格", "询价", "价格",
            "续费报价", "续费单价", "域名续费费用", "续费询价", "域续价格",
            "获取续费价", "查看续费价格", "查询价格", "续费价目", "定价",
            "续费要多少钱", "域名续费金额", "查询域名价格", "域名续费多少钱", "price check",
            "获取价格", "域名续费查询", "续费金额查询", "费用查询", "续费报价查询",
            "价格获取", "续费参考", "域名续费报价", "查看域名价格", "续费价格查询"
        ]
    },
    {
        "name": "check_domain_available",
        "description": "检查域名是否可以注册",
        "type": "query",
        "parameters": {
            "domain": {"type": "string", "required": True, "description": "要检查的域名（中文域名支持汉字及punycode转码）"},
            "suffix": {"type": "string", "required": True, "description": "要检查的后缀，多个用英文逗号分割，如: com,net,org"}
        },
        "keywords": [
            "检查域名", "域名可用", "能否注册", "是否可注册", "域名查询",
            "check domain", "whois", "域名检查", "查域名", "查询域名状态",
            "域名是否存在", "检查能否注册", "域名注册检查", "域名可用性", "查是否被注册",
            "域名检测", "域名状态", "是否已被注册", "检查域名状态", "域名探查",
            "域名搜索", "搜域名", "找域名", "查询域名", "域名可注册",
            "查询域名可用", "域名预查", "域名筛选", "验证域名", "域名核验",
            "搜索域名", "域名试查", "可用域名", "未被注册", "可注册域名",
            "domain available", "domain check", "域名空可用", "验证域名可用", "域名空查询"
        ]
    },
    {
        "name": "get_free_subdomain_list",
        "description": "获取免费二级域名列表",
        "type": "query",
        "parameters": {
            "options": {"type": "string", "required": True, "description": "标准查询参数（JSON格式）"}
        },
        "keywords": [
            "免费域名", "二级域名", "免费二级域名", "子域名", "赠送域名",
            "free domain", "free subdomain", "白嫖域名", "免费子域名", "二级域",
            "免费域", "免费二级", "子域列表", "subdomain list", "免费域名列表",
            "获取免费域名", "查看免费域名", "已申请免费域名", "我的免费域名", "二级域名列表",
            "免费二级域", "subdomain", "免费二级列表", "免费域名查看", "二级域名管理",
            "免费域名资产", "赠品域名", "附赠域名", "免费域列表", "free二级",
            "查看子域名", "子域名列表", "申请的子域名", "账号免费域名", "免费域列表查询"
        ]
    },
    {
        "name": "create_free_subdomain",
        "description": "创建免费二级域名",
        "type": "operation",
        "parameters": {
            "domain_name": {"type": "string", "required": True, "description": "父域名"},
            "host_name": {"type": "string", "required": True, "description": "前缀（主机名）"},
            "target_type": {"type": "string", "required": True, "description": "目标类型: rcs/rvh/rgs/rbm/custom"},
            "target_info": {"type": "string", "required": True, "description": "目标信息"},
            "is_cloud_flare_proxied": {"type": "boolean", "required": False, "description": "是否启用Cloudflare代理"}
        },
        "keywords": [
            "创建免费域名", "申请免费域名", "新建二级域名", "添加免费域名", "免费域名创建",
            "create free domain", "add subdomain", "注册免费域名", "开通免费域名", "建免费二级",
            "免费二级域名创建", "申请二级域名", "创建子域名", "新建子域名", "添加子域名",
            "免费子域创建", "生成免费域名", "获取免费域名", "建立二级域名", "创建二级域",
            "申领免费域名", "创建免费二级", "免费域创建", "子域名申请", "申请免费子域",
            "免费域名开通", "注册二级域名", "开通二级域名", "建免费域名", "添加免费二级",
            "新建域名", "免费建站域名", "创建域名", "新增域名", "白嫖域名创建"
        ]
    },
    {
        "name": "delete_free_subdomain",
        "description": "删除免费二级域名",
        "type": "operation",
        "parameters": {
            "id": {"type": "integer", "required": True, "description": "免费二级域名ID"}
        },
        "keywords": [
            "删除免费域名", "删除二级域名", "移除免费域名", "删除子域名", "免费域名删除",
            "delete free domain", "remove subdomain", "取消免费域名", "释放免费域名", "删除免费二级",
            "清理免费域名", "删免费域", "去掉免费域名", "免费二级删除", "删除子域",
            "子域名删除", "移除子域名", "取消子域名", "释放子域名", "删除申请",
            "撤销免费域名", "废弃免费域名", "删二级域", "清除免费域名", "取消免费二级",
            "免费域移除", "删除免费子域", "取消申请", "撤销申请", "free domain delete",
            "清理子域名", "销毁免费域名", "去除免费域名", "免费域名回收", "删除创建"
        ]
    },
    {
        "name": "change_free_subdomain_proxy",
        "description": "修改免费二级域名的CDN设置",
        "type": "operation",
        "parameters": {
            "id": {"type": "integer", "required": True, "description": "免费二级域名ID"},
            "is_enable": {"type": "boolean", "required": True, "description": "是否启用CDN代理"}
        },
        "keywords": [
            "CDN设置", "修改CDN", "免费域名CDN", "CDN代理", "切换CDN",
            "域名加速", "Cloudflare代理", "开启CDN", "关闭CDN", "CDN配置",
            "代理设置", "proxy设置", "CDN开关", "cdn on off", "cdn toggle",
            "缓存加速", "启用加速", "停用加速", "CDN修改", "加速设置",
            "免费域名加速", "二级域名CDN", "域名CDN", "子域名加速", "cdn proxy",
            "启用代理", "关闭代理", "修改代理", "cdn enable", "cdn disable",
            "免费域CDN", "修改免费域CDN", "切换代理", "CDN变更", "域名代理设置",
            "cloudflare开关", "CF代理", "免费域名代理", "开启代理", "关闭代理"
        ]
    },
    {
        "name": "get_usable_free_domains",
        "description": "获取可用的免费域名列表（可用于申请）",
        "type": "query",
        "parameters": {},
        "keywords": [
            "可用免费域名", "可申请域名", "免费域名可用", "可用的免费域", "可注册免费",
            "usable domains", "available domains", "免费域名池", "可选择的免费域", "可选域名",
            "免费域名选项", "能用的免费域名", "域名选择", "备用域名", "待选域名",
            "免费域列表可用", "可用二级域名", "可用的二级域名", "免费域可用列表", "可选免费",
            "未使用免费域名", "空余免费域名", "可领取域名", "可用的免费二级", "可用域列表",
            "免费域名选项列表", "free domain available", "二级可用", "可用子域", "可供申请"
        ]
    },
    {
        "name": "register_domain",
        "description": "注册域名（购买新域名）",
        "type": "operation",
        "parameters": {
            "domain": {"type": "string", "required": True, "description": "要注册的域名"},
            "duration": {"type": "integer", "required": True, "description": "注册年限(1-10)"},
            "type": {"type": "string", "required": True, "description": "域名类型: normal(普通)/premium(溢价)"},
            "template_sys_id": {"type": "string", "required": False, "description": "已有域名信息模板ID"},
            "new_template_info": {"type": "object", "required": False, "description": "新建域名信息模板（与template_sys_id二选一）"}
        },
        "keywords": [
            "注册域名", "购买域名", "域名注册", "买域名", "新域名",
            "register domain", "buy domain", "域名购买", "申请域名", "注册新域名",
            "域名下单", "订购域名", "选购域名", "域名交易", "域名购入",
            "新建域名注册", "首次注册", "注册操作", "开通域名", "域名申领",
            "域名购买操作", "域名注册操作", "域名登记", "域名订购", "purchase domain",
            "买新域名", "购入域名", "下单域名", "抢注域名", "域名注册申请",
            "域名注册服务", "域名付费注册", "购买新域名", "选购", "订域"
        ]
    },

    # --------------------------------- 积分兑换 ---------------------------------
    {
        "name": "get_reward_items",
        "description": "获取可兑换积分物品列表（已废弃，建议用get_reward_products）",
        "type": "query",
        "parameters": {},
        "keywords": [
            "积分物品", "兑换物品", "积分兑换", "积分商品", "reward items",
            "积分换物", "积分商城", "积分礼品", "积分商品列表", "可兑换物品",
            "兑换列表", "积分兑换列表", "积分换", "积分奖品", "积分福利",
            "积分商城物品", "reward list", "积分换购", "物品兑换", "查看兑换",
            "积分可换", "积分赠品", "积分换实物", "积分消费", "积分购物"
        ]
    },
    {
        "name": "get_reward_products",
        "description": "获取可兑换积分产品列表",
        "type": "query",
        "parameters": {},
        "keywords": [
            "积分产品", "可兑换产品", "积分兑换产品", "积分换产品", "产品兑换",
            "reward products", "积分商城产品", "积分商品", "积分兑换列表", "兑换产品列表",
            "积分换购产品", "积分可换产品", "积分产品列表", "积分兑换商城", "兑换产品",
            "积分商城列表", "产品积分兑换", "查看积分产品", "积分产品查询", "积分兑换选项",
            "积分换购", "积分选购", "积分选购产品", "积分商城产品列表", "产品兑换列表",
            "积分换服务器", "积分兑产品", "products reward", "积分消费产品", "积分商城"
        ]
    },
    {
        "name": "redeem_reward_item",
        "description": "兑换积分物品（通过物品ID）",
        "type": "operation",
        "parameters": {
            "item_id": {"type": "integer", "required": True, "description": "物品ID"}
        },
        "keywords": [
            "兑换物品", "积分兑换", "兑换", "积分换", "redeem item",
            "积分消费", "使用积分", "换取物品", "积分购买", "积分换取",
            "物品兑换操作", "执行兑换", "兑换操作", "积分兑", "兑现",
            "积分下单", "积分交易", "积分换东西", "兑换奖品", "领积分物品",
            "积分兑物品", "积分领取", "积分兑换操作", "兑换积分物品", "积分购",
            "积分兑换物品执行", "积分兑换执行", "积分换礼品", "积分兑现", "兑奖"
        ]
    },
    {
        "name": "redeem_reward_product",
        "description": "兑换可兑换积分产品",
        "type": "operation",
        "parameters": {
            "product_id": {"type": "integer", "required": True, "description": "产品ID"},
            "product_type": {"type": "string", "required": True, "description": "产品类型: rvh/rcs/rgs/rbm/ros/rcdn/ssl_order"}
        },
        "keywords": [
            "兑换产品", "积分换产品", "积分兑产品", "产品兑换操作", "redeem product",
            "积分兑换产品执行", "积分购买产品", "积分换购产品", "兑换操作", "执行产品兑换",
            "积分消费产品", "积分兑服务器", "积分换服务器", "积分购产品", "兑换产品执行",
            "积分下单产品", "产品积分兑换执行", "积分换购", "积分实物兑换", "积分兑",
            "积分兑换产品操作", "积分产品兑换操作", "积分兑云服务器", "积分换主机", "购买产品积分"
        ]
    },

    # --------------------------------- 用户类 ---------------------------------
    {
        "name": "get_user_info",
        "description": "获取雨云用户数据",
        "type": "query",
        "parameters": {},
        "keywords": [
            "用户信息", "用户数据", "账号信息", "我的信息", "个人信息",
            "user info", "个人资料", "账号资料", "账户详情", "用户详情",
            "查看用户", "获取用户", "user data", "profile", "账号",
            "账户信息", "我的账号", "账号数据", "用户资料", "个人数据",
            "查看个人信息", "获取账号信息", "账号概览", "用户设置", "用户配置",
            "信息查询", "资料查询", "用户属性", "账号属性", "个人信息查看",
            "用户信息查询", "个人信息获取", "账号信息获取", "获取用户数据", "user profile",
            "身份信息", "账户详情查看", "用户信息获取", "查看账号", "我的资料"
        ]
    },
    {
        "name": "update_user_setting",
        "description": "设置雨云用户数据（修改账号设置）",
        "type": "operation",
        "parameters": {
            "option": {"type": "string", "required": True, "description": "设置项: name/icon/alipay_account/alipay_name/password/email/phone/apikey/totp/login_tfa/unbind_social_media"}
        },
        "keywords": [
            "修改用户", "设置用户", "更新用户", "修改资料", "账号设置",
            "update user", "修改账号", "更改信息", "设置信息", "修改个人信息",
            "用户设置", "修改密码", "改昵称", "改头像", "绑定邮箱",
            "修改手机", "修改邮箱", "更新资料", "更新账号", "修改用户数据",
            "编辑资料", "编辑用户", "修改配置", "更新设置", "设置修改",
            "改名字", "换头像", "更新api密钥", "修改api密钥", "更换密钥",
            "重设密码", "修改安全设置", "开启两步验证", "关闭两步验证", "修改支付信息",
            "修改支付宝", "解绑社交账号", "修改个人信息操作", "修改账户", "更新账号设置"
        ]
    },
    {
        "name": "get_user_logs",
        "description": "查询雨云用户日志",
        "type": "query",
        "parameters": {
            "options": {"type": "string", "required": True, "description": "标准查询参数（JSON格式）"},
            "log_type": {"type": "string", "required": True, "description": "日志类型"}
        },
        "keywords": [
            "用户日志", "我的日志", "账号日志", "操作记录", "活动记录",
            "user log", "个人日志", "日志查询", "用户操作日志", "登录日志",
            "行为日志", "使用记录", "历史", "操作历史", "用户历史",
            "账户日志", "账号活动", "活动日志", "安全日志", "登录记录",
            "用户活动", "访问日志", "审计", "用户审计", "日志记录",
            "查日志", "看日志", "查询日志", "日志信息", "用户操作记录",
            "个人活动", "账户记录", "账号历史", "用户时间线", "活动历史"
        ]
    },
    {
        "name": "get_user_messages",
        "description": "获取用户站内信与服务事件",
        "type": "query",
        "parameters": {},
        "keywords": [
            "站内信", "消息", "通知", "服务事件", "系统消息",
            "messages", "站内消息", "服务通知", "事件通知", "公告",
            "用户消息", "我的消息", "消息中心", "通知中心", "消息列表",
            "查看消息", "服务消息", "系统通知", "平台通知", "私信",
            "inbox", "收件箱", "消息栏", "站内通知", "推送消息",
            "用户通知", "账号消息", "查看通知", "消息提醒", "事件提醒",
            "最新消息", "未读消息", "读取消息", "查看站内信", "系统公告"
        ]
    },
    {
        "name": "read_user_message",
        "description": "已读站内信（标记为已读）",
        "type": "operation",
        "parameters": {
            "id": {"type": "string", "required": True, "description": "站内信ID"}
        },
        "keywords": [
            "已读消息", "标记已读", "阅读站内信", "查看消息", "打开消息",
            "read message", "已读", "消息已读", "读消息", "标记阅读",
            "读取站内信", "消息阅读", "查看详情", "打开站内信", "标记为已读",
            "确认阅读", "阅读消息", "看消息", "展开消息", "点开消息",
            "查看站内信详情", "已阅", "阅消息", "标记", "阅读通知",
            "查看通知详情", "读站内信", "处理消息", "消息处理", "通知标记已读"
        ]
    },

    # --------------------------------- 状态/公共 ---------------------------------
    {
        "name": "get_node_status",
        "description": "获取雨云节点网络状态",
        "type": "query",
        "parameters": {
            "options": {"type": "string", "required": True, "description": "标准查询参数（JSON格式）"}
        },
        "keywords": [
            "节点状态", "网络状态", "服务器状态", "节点监控", "运行状态",
            "node status", "服务状态", "在线状态", "节点健康", "网络监控",
            "雨云状态", "平台状态", "系统状态", "服务器监控", "状态查询",
            "节点信息", "节点情况", "网络情况", "节点可用", "服务可用",
            "探测状态", "健康检查", "存活检测", "ping状态", "延迟",
            "连通性", "状态监控", "实时状态", "当前状态", "服务监控",
            "节点网络", "数据中心状态", "机房状态", "status check", "health check",
            "node health", "服务器健康", "状态页面", "status page", "节点检测"
        ]
    },
    {
        "name": "get_app_config",
        "description": "获取雨云页面公共配置信息",
        "type": "query",
        "parameters": {},
        "keywords": [
            "页面配置", "站点配置", "公共配置", "app配置", "应用配置",
            "app config", "平台配置", "站点设置", "系统配置", "全局配置",
            "网站配置", "页面设置", "config", "配置信息", "application config",
            "基础配置", "公共设置", "站点信息", "平台信息", "网站设置",
            "配置查看", "获取配置", "配置数据", "环境配置", "运行配置",
            "系统设置", "全局设置", "平台参数", "基础设置", "站点参数",
            "网站参数", "应用设置", "app设置", "平台配置查看", "获取站点配置"
        ]
    },

    # --------------------------------- 订单 ---------------------------------
    {
        "name": "get_expense_orders",
        "description": "用户获取雨云订单列表",
        "type": "query",
        "parameters": {
            "options": {"type": "string", "required": True, "description": "标准查询参数（JSON格式）"}
        },
        "keywords": [
            "订单列表", "订单", "我的订单", "消费记录", "购买记录",
            "order list", "orders", "账单", "交易记录", "费用记录",
            "消费明细", "购买历史", "支出记录", "历史订单", "交易明细",
            "订单记录", "消费订单", "支付记录", "充值记录", "账单列表",
            "查看订单", "订单查询", "订单管理", "我的账单", "消费清单",
            "购买订单", "费用列表", "账单明细", "账单查看", "交易列表",
            "历史消费", "支付明细", "购物记录", "消费历史", "费用查询"
        ]
    },

    # --------------------------------- SSL 证书 ---------------------------------
    {
        "name": "get_ssl_list",
        "description": "获取SSL证书列表",
        "type": "query",
        "parameters": {
            "options": {"type": "string", "required": True, "description": "标准查询参数（JSON格式）"}
        },
        "keywords": [
            "SSL证书列表", "证书列表", "SSL", "TLS证书", "https证书",
            "ssl list", "certificates", "我的证书", "证书管理", "安全证书",
            "服务器证书", "网站证书", "加密证书", "证书概览", "ssl cert",
            "查看证书", "证书汇总", "ssl证书管理", "证书信息", "cert list",
            "所有证书", "获取证书列表", "证书查询", "ssl查询", "证书资源",
            "加密凭证", "安全凭证", "SSL列表", "TLS列表", "我的SSL",
            "证书资产", "证书一览", "ssl证书概览", "证书存储", "证书库"
        ]
    },
    {
        "name": "upload_ssl_cert",
        "description": "上传SSL证书",
        "type": "operation",
        "parameters": {
            "cert": {"type": "string", "required": True, "description": "证书内容（PEM格式）"},
            "key": {"type": "string", "required": True, "description": "私钥内容（PEM格式）"}
        },
        "keywords": [
            "上传SSL", "上传证书", "导入证书", "SSL上传", "证书上传",
            "upload ssl", "添加证书", "导入SSL", "证书导入", "SSL导入",
            "安装证书", "部署证书", "ssl证书上传", "自定义证书", "自有证书",
            "手动上传", "证书安装", "安装SSL", "部署SSL", "ssl upload",
            "上传https证书", "导入https证书", "证书部署", "添加SSL证书", "上传安全证书",
            "自定义SSL", "自有SSL", "导入我的证书", "证书添加", "上传加密证书",
            "导入安全证书", "手动导入证书", "证书文件上传", "ssl cert upload", "上传cert"
        ]
    },
    {
        "name": "get_ssl_detail",
        "description": "查看SSL证书详情",
        "type": "query",
        "parameters": {
            "id": {"type": "string", "required": True, "description": "SSL证书ID"}
        },
        "keywords": [
            "SSL证书详情", "证书详情", "查看证书", "证书信息", "ssl detail",
            "证书详细", "查看SSL", "ssl信息", "证书内容", "证书状态",
            "证书详情查看", "SSL详情", "证书到期", "证书有效期", "证书属性",
            "查看证书详情", "ssl查看", "证书数据", "证书信息查看", "cert detail",
            "ssl详细", "ssl证书信息", "获取证书详情", "证书具体信息", "证书详细资料",
            "ssl证书详情查看", "查看具体证书", "证书查阅", "ssl证书查阅", "证书元信息"
        ]
    },
    {
        "name": "replace_ssl_cert",
        "description": "替换SSL证书",
        "type": "operation",
        "parameters": {
            "id": {"type": "string", "required": True, "description": "SSL证书ID"},
            "cert": {"type": "string", "required": True, "description": "新证书内容（PEM格式）"},
            "key": {"type": "string", "required": True, "description": "新私钥内容（PEM格式）"}
        },
        "keywords": [
            "替换SSL", "更新证书", "替换证书", "更换证书", "SSL替换",
            "replace ssl", "更新SSL", "证书替换", "更换SSL", "ssl更新",
            "证书更新", "刷新证书", "证书更换", "替换https证书", "更新https证书",
            "ssl证书替换", "ssl证书更新", "更换加密证书", "更新安全证书", "证书重新部署",
            "替换安全证书", "ssl renew", "证书翻新", "重装证书", "重新上传证书",
            "刷新SSL", "ssl replace", "cert replace", "更新cert", "替换cert",
            "证书变更", "ssl变更", "证书刷新", "SSL刷新", "更新证书内容"
        ]
    },
    {
        "name": "create_ssl_cert_order",
        "description": "创建SSL证书申请",
        "type": "operation",
        "parameters": {
            "domains": {"type": "string", "required": True, "description": "域名列表（逗号分割）"},
            "verify_method": {"type": "string", "required": True, "description": "验证方式: dns/http/auto"}
        },
        "keywords": [
            "申请SSL", "创建SSL", "SSL申请", "免费SSL", "证书申请",
            "apply ssl", "request ssl", "签发证书", "SSL证书申请", "创建证书",
            "申请证书", "新建SSL", "SSL签发", "免费证书", "免费https",
            "Let's Encrypt", "申请免费证书", "创建免费SSL", "ssl order", "证书订单",
            "申请https证书", "创建https证书", "https证书申请", "域名证书申请", "ssl certificate apply",
            "新建证书申请", "SSL创建", "证书签发", "订单申请", "证书请求",
            "申请域名证书", "证书申领", "SSL下单", "证书订购", "create ssl"
        ]
    },
    {
        "name": "verify_ssl_cert_order",
        "description": "验证SSL证书申请",
        "type": "operation",
        "parameters": {
            "order_id": {"type": "integer", "required": True, "description": "SSL证书订单ID"}
        },
        "keywords": [
            "验证SSL", "证书验证", "SSL验证", "确认申请", "验证证书申请",
            "verify ssl", "ssl验证", "证书确认", "验证申请", "确认SSL",
            "SSL确认", "证书审核", "验证审核", "ssl验证操作", "证书验证操作",
            "验证域名", "域名验证", "dns验证", "http验证", "证书校验",
            "验证操作", "ssl verify", "cert verify", "验证签发", "确认签发",
            "证书颁发验证", "ssl申请验证", "证书申请验证", "审核证书", "证书审批"
        ]
    },
    {
        "name": "get_ssl_cert_orders",
        "description": "获取SSL证书申请列表",
        "type": "query",
        "parameters": {
            "options": {"type": "string", "required": True, "description": "标准查询参数（JSON格式）"}
        },
        "keywords": [
            "SSL申请列表", "证书申请列表", "申请记录", "SSL申请记录", "ssl orders",
            "证书申请记录", "申请列表", "查看申请", "ssl申请查询", "证书订单列表",
            "查看SSL申请", "我的申请", "SSL申请历史", "证书申请历史", "ssl request list",
            "申请记录查询", "证书申请查询", "ssl订单列表", "ssl申请一览", "查看证书申请",
            "获取申请列表", "申请单列表", "证书申请单", "ssl申请清单", "证书申请目录"
        ]
    },
    {
        "name": "get_ssl_order_list",
        "description": "获取SSL证书订单列表",
        "type": "query",
        "parameters": {},
        "keywords": [
            "SSL订单", "证书订单", "ssl订单列表", "SSL订单列表", "证书订单列表",
            "ssl order list", "购买SSL记录", "SSL购买记录", "证书购买历史", "SSL订购记录",
            "我的SSL订单", "SSL交易", "证书交易", "购买证书", "ssl purchase",
            "SSL付费记录", "证书消费", "SSL消费记录", "证书订单管理", "查看SSL订单",
            "SSL订单记录", "证书订单查询", "获取SSL订单", "ssl order查询", "证书订单记录"
        ]
    },
    {
        "name": "create_ssl_order",
        "description": "创建SSL证书订单（购买SSL证书）",
        "type": "operation",
        "parameters": {
            "domains": {"type": "string", "required": False, "description": "域名"},
            "duration": {"type": "integer", "required": False, "description": "购买时长（月）"},
            "price": {"type": "number", "required": False, "description": "价格（用于核验）"},
            "productId": {"type": "integer", "required": False, "description": "产品ID"},
            "withCouponId": {"type": "integer", "required": False, "description": "优惠券ID"}
        },
        "keywords": [
            "购买SSL", "SSL购买", "购买证书", "SSL下单", "证书购买",
            "buy ssl", "purchase ssl", "订购SSL", "SSL订购", "证书下单",
            "创建SSL订单", "下订单", "ssl order create", "ssl购买操作", "证书订购操作",
            "付费SSL", "商业SSL", "付费证书", "购买https证书", "SSL购买操作",
            "证书交易下单", "SSL商品购买", "下单SSL", "ssl create order", "购买加密证书",
            "订购证书", "ssl付费", "证书付费", "下单购买", "创建购买订单"
        ]
    },
    {
        "name": "get_ssl_order_detail",
        "description": "获取SSL证书订单信息",
        "type": "query",
        "parameters": {
            "id": {"type": "string", "required": True, "description": "订单ID"}
        },
        "keywords": [
            "SSL订单详情", "订单详情", "查看订单", "订单信息", "ssl order detail",
            "SSL订单信息", "证书订单详情", "查看SSL订单", "SSL订单查看", "订单详细",
            "获取订单信息", "查看具体订单", "ssl订单详细", "证书订单信息", "订单查询",
            "SSL订单查询", "我的订单详情", "购买详情", "支付详情", "订单内容",
            "SSL购买详情", "证书购买详情", "订单详情查看", "查看购买", "订单信息查看"
        ]
    },
]


# ============================================================================
# 构建关键词索引（关键词 -> 工具名列表）
# ============================================================================
def build_keyword_index(tools: list[dict]) -> dict[str, list[str]]:
    """构建关键词倒排索引，用于快速搜索"""
    index: dict[str, list[str]] = {}
    for tool in tools:
        for kw in tool.get("keywords", []):
            kw_lower = kw.lower().strip()
            if kw_lower not in index:
                index[kw_lower] = []
            if tool["name"] not in index[kw_lower]:
                index[kw_lower].append(tool["name"])
    return index

KEYWORD_INDEX = build_keyword_index(INTERNAL_TOOLS)
TOOL_MAP = {tool["name"]: tool for tool in INTERNAL_TOOLS}


def search_tools_by_keyword(query: str) -> list[dict]:
    """通过关键词搜索工具，返回匹配的工具列表（去重，按匹配度排序）"""
    query_lower = query.lower().strip()
    scores: dict[str, int] = {}
    
    # 精确匹配
    if query_lower in KEYWORD_INDEX:
        for name in KEYWORD_INDEX[query_lower]:
            scores[name] = scores.get(name, 0) + 10
    
    # 部分匹配（关键词包含查询词）
    for kw, names in KEYWORD_INDEX.items():
        if query_lower in kw:
            for name in names:
                scores[name] = scores.get(name, 0) + 5
    
    # 部分匹配（查询词包含关键词）
    for kw, names in KEYWORD_INDEX.items():
        if kw in query_lower:
            for name in names:
                scores[name] = scores.get(name, 0) + 3
    
    # 模糊匹配（单个字符匹配）
    for kw, names in KEYWORD_INDEX.items():
        if any(word in kw for word in query_lower.split()):
            for name in names:
                scores[name] = scores.get(name, 0) + 1
    
    # 按分数降序排列
    sorted_names = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [TOOL_MAP[name] for name, _ in sorted_names if name in TOOL_MAP]


# ============================================================================
# 权限验证
# ============================================================================
def check_permission(event: AstrMessageEvent, config: dict) -> tuple[bool, str]:
    """验证用户权限，返回 (是否通过, 错误信息)"""
    access_mode = config.get("access_mode", "admin_only")
    sender_id = str(event.get_sender_id())
    
    if access_mode == "admin_only":
        if event.role != "admin":
            return False, f"权限不足：当前为「仅管理员」模式，用户 {sender_id} 不是管理员，无法使用雨云管理功能。请联系管理员获取权限。"
        return True, ""
    
    elif access_mode == "admin_and_member":
        if event.role not in ("admin", "member"):
            return False, f"权限不足：当前为「管理员和成员」模式，用户 {sender_id} 角色为 {event.role}，无法使用雨云管理功能。"
        return True, ""
    
    elif access_mode == "whitelist":
        whitelist = config.get("whitelist", [])
        if sender_id not in whitelist:
            return False, f"权限不足：当前为「白名单模式」，用户 {sender_id} 不在白名单中。请管理员将您的ID加入插件配置的白名单。当前白名单：{whitelist}"
        return True, ""
    
    return False, f"权限验证失败：未知的权限模式 {access_mode}"


# ============================================================================
# API 调用
# ============================================================================
async def call_rainyun_api(
    method: str,
    path: str,
    api_key: str,
    params: dict | None = None,
    body: dict | None = None,
) -> dict:
    """调用雨云API的统一方法"""
    base_url = "https://api.v2.rainyun.com"
    url = f"{base_url}{path}"
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json",
    }
    
    try:
        async with aiohttp.ClientSession(trust_env=True) as session:
            if method == "GET":
                async with session.get(url, headers=headers, params=params, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    text = await resp.text()
                    return {"status_code": resp.status, "body": text}
            elif method == "POST":
                async with session.post(url, headers=headers, json=body, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    text = await resp.text()
                    return {"status_code": resp.status, "body": text}
            elif method == "PUT":
                async with session.put(url, headers=headers, json=body, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    text = await resp.text()
                    return {"status_code": resp.status, "body": text}
            elif method == "PATCH":
                async with session.patch(url, headers=headers, json=body, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    text = await resp.text()
                    return {"status_code": resp.status, "body": text}
            elif method == "DELETE":
                async with session.delete(url, headers=headers, json=body, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    text = await resp.text()
                    return {"status_code": resp.status, "body": text}
            else:
                return {"error": f"不支持的HTTP方法: {method}"}
    except asyncio.TimeoutError:
        return {"error": "请求雨云API超时（30秒）。请检查网络连接或稍后重试。"}
    except aiohttp.ClientError as e:
        return {"error": f"网络请求错误：{str(e)}。请检查网络连接或API配置。"}
    except Exception as e:
        return {"error": f"调用雨云API时发生未知错误：{str(e)}"}


# ============================================================================
# 将内部工具映射到实际 API 调用
# ============================================================================
TOOL_API_MAP: dict[str, dict] = {
    "get_product_summary":        {"method": "GET",    "path": "/product/"},
    "get_product_id_list":        {"method": "GET",    "path": "/product/id_list", "use_params": True},
    "point_renew":                {"method": "POST",   "path": "/product/point_renew"},
    "get_fast_install_apps":      {"method": "GET",    "path": "/fast-install-app", "use_body_for_get": True},
    "get_product_zones":          {"method": "GET",    "path": "/product/zones"},
    "get_task_log":               {"method": "GET",    "path": "/product/task_log", "use_params": True},
    "get_domain_list":            {"method": "GET",    "path": "/product/domain/", "use_params": True},
    "get_domain_detail":          {"method": "GET",    "path": "/product/domain/{id}"},
    "get_dns_records":            {"method": "GET",    "path": "/product/domain/{id}/dns/", "use_params": True},
    "add_dns_record":             {"method": "POST",   "path": "/product/domain/{id}/dns"},
    "update_dns_record":          {"method": "PATCH",  "path": "/product/domain/{id}/dns"},
    "delete_dns_record":          {"method": "DELETE", "path": "/product/domain/{id}/dns/"},
    "get_dnssec":                 {"method": "GET",    "path": "/product/domain/{id}/dnssec"},
    "add_dnssec":                {"method": "POST",   "path": "/product/domain/{id}/dnssec"},
    "delete_dnssec":             {"method": "POST",   "path": "/product/domain/{id}/dnssec/delete"},
    "sync_dnssec":               {"method": "POST",   "path": "/product/domain/{id}/dnssec/sync"},
    "disable_domain_lock":        {"method": "PUT",    "path": "/product/domain/{id}/lock/disable"},
    "enable_domain_lock":         {"method": "PUT",    "path": "/product/domain/{id}/lock/enable"},
    "renew_domain":               {"method": "POST",   "path": "/product/domain/{id}/renew"},
    "get_domain_renew_price":     {"method": "GET",    "path": "/product/domain/{id}/renew-price"},
    "check_domain_available":     {"method": "POST",   "path": "/product/domain/check"},
    "get_free_subdomain_list":    {"method": "GET",    "path": "/product/domain/free_subdomain", "use_params": True},
    "create_free_subdomain":      {"method": "POST",   "path": "/product/domain/free_subdomain"},
    "delete_free_subdomain":      {"method": "DELETE", "path": "/product/domain/free_subdomain"},
    "change_free_subdomain_proxy":{"method": "POST",   "path": "/product/domain/free_subdomain/proxy"},
    "get_usable_free_domains":    {"method": "GET",    "path": "/product/domain/free_subdomain/usable"},
    "register_domain":            {"method": "POST",   "path": "/product/domain/register"},
    "get_reward_items":           {"method": "GET",    "path": "/user/reward/items"},
    "get_reward_products":        {"method": "GET",    "path": "/user/reward/products"},
    "redeem_reward_item":         {"method": "POST",   "path": "/user/reward/items"},
    "redeem_reward_product":      {"method": "POST",   "path": "/user/reward/products"},
    "get_user_info":              {"method": "GET",    "path": "/user/"},
    "update_user_setting":        {"method": "PATCH",  "path": "/user/"},
    "get_user_logs":              {"method": "GET",    "path": "/user/logs", "use_params": True},
    "get_user_messages":          {"method": "GET",    "path": "/user/msg/"},
    "read_user_message":          {"method": "GET",    "path": "/user/msg/read/{id}"},
    "get_node_status":            {"method": "GET",    "path": "/status", "use_params": True},
    "get_app_config":             {"method": "GET",    "path": "/app_config"},
    "get_expense_orders":         {"method": "GET",    "path": "/expense/orders/list", "use_body_for_get": True},
    "get_ssl_list":               {"method": "GET",    "path": "/product/sslcenter/", "use_params": True},
    "upload_ssl_cert":            {"method": "POST",   "path": "/product/sslcenter/"},
    "get_ssl_detail":             {"method": "GET",    "path": "/product/sslcenter/{id}"},
    "replace_ssl_cert":           {"method": "PUT",    "path": "/product/sslcenter/{id}", "use_params": True},
    "create_ssl_cert_order":      {"method": "POST",   "path": "/product/sslcenter/cert/order"},
    "verify_ssl_cert_order":      {"method": "POST",   "path": "/product/sslcenter/cert/order_verify"},
    "get_ssl_cert_orders":        {"method": "GET",    "path": "/product/sslcenter/cert/orders", "use_params": True},
    "get_ssl_order_list":         {"method": "GET",    "path": "/product/sslcenter/order"},
    "create_ssl_order":           {"method": "POST",   "path": "/product/sslcenter/order"},
    "get_ssl_order_detail":       {"method": "GET",    "path": "/product/sslcenter/order/{id}"},
}


async def execute_tool(tool_name: str, parameters: dict, api_key: str) -> str:
    """执行工具调用"""
    if tool_name not in TOOL_MAP:
        return f"错误：未找到工具「{tool_name}」。请检查工具名称是否正确，可使用 complete_tool_list 查看所有可用工具。"
    
    if tool_name not in TOOL_API_MAP:
        return f"错误：工具「{tool_name}」尚未配置API映射，请联系插件开发者。"
    
    api_config = TOOL_API_MAP[tool_name]
    method = api_config["method"]
    path = api_config["path"]
    
    # 替换路径参数 {id}
    for key, value in parameters.items():
        path = path.replace(f"{{{key}}}", str(value))
    
    # 分离路径参数和请求体参数
    path_params = {}
    body_params = {}
    for key, value in parameters.items():
        if f"{{{key}}}" in api_config["path"]:
            path_params[key] = value
        else:
            body_params[key] = value
    
    # 特殊处理某些GET请求的参数
    if method == "GET":
        if api_config.get("use_params"):
            path_params = {**path_params, **body_params}
            body_params = {}
        elif api_config.get("use_body_for_get"):
            body_params = body_params
            path_params = {}
        else:
            path_params = {**path_params, **body_params}
            body_params = {}
    
    result = await call_rainyun_api(
        method=method,
        path=path,
        api_key=api_key,
        params=path_params if path_params else None,
        body=body_params if body_params and method != "GET" else None,
    )
    
    if "error" in result:
        return f"执行「{tool_name}」失败：{result['error']}"
    
    status = result.get("status_code", "未知")
    body = result.get("body", "")
    
    if status == 200:
        return f"✅ 执行「{tool_name}」成功！\nAPI返回状态码：{status}\n返回数据：\n{body}"
    else:
        return f"❌ 执行「{tool_name}」失败。\nAPI返回状态码：{status}\n错误信息：\n{body}\n\n请检查参数是否正确，或联系雨云客服确认API状态。"


# ============================================================================
# 主插件类
# ============================================================================
class Main(star.Star):
    def __init__(self, context: star.Context, config: dict | None = None):
        super().__init__(context)
        self.config = config or {}
        logger.info("雨云管理插件已初始化")
    
    async def terminate(self):
        logger.info("雨云管理插件已卸载")
    
    # ========================================================================
    # 验证通用权限
    # ========================================================================
    def _check_global_permission(self, event: AstrMessageEvent) -> tuple[bool, str]:
        """检查全局权限（总开关 + 权限范围）"""
        if not self.config.get("enable_plugin", True):
            return False, "雨云管理插件已被管理员禁用（插件总开关已关闭）。如需使用请联系管理员在插件配置中开启。"
        
        passed, err = check_permission(event, self.config)
        if not passed:
            return False, err
        
        return True, ""
    
    def _check_query_enabled(self) -> tuple[bool, str]:
        """检查查询功能是否启用"""
        if not self.config.get("enable_query", True):
            return False, "查询功能总开关已关闭，无法执行查询操作。如需使用请联系管理员开启。"
        return True, ""
    
    def _check_operation_enabled(self) -> tuple[bool, str]:
        """检查操作功能是否启用"""
        if not self.config.get("enable_operation", True):
            return False, "操作功能总开关已关闭，无法执行操作类功能。如需使用请联系管理员开启。"
        return True, ""
    
    def _get_api_key(self) -> str:
        """获取API密钥"""
        return self.config.get("api_key", "")

    # ========================================================================
    # 管理员指令组
    # ========================================================================
    @filter.command_group("rainyun")
    def rainyun(self):
        """雨云管理指令组"""
        pass

    @rainyun.command("status")
    async def cmd_status(self, event: AstrMessageEvent):
        """查看雨云账号产品汇总状态（管理员专用）"""
        ok, err = self._check_global_permission(event)
        if not ok:
            yield event.plain_result(f"❌ {err}")
            return
        
        ok, err = self._check_query_enabled()
        if not ok:
            yield event.plain_result(f"❌ {err}")
            return
        
        api_key = self._get_api_key()
        if not api_key:
            yield event.plain_result("❌ 未配置雨云API密钥，请在插件配置中填写 X-Api-Key。")
            return
        
        result = await execute_tool("get_product_summary", {}, api_key)
        yield event.plain_result(result)
    
    @rainyun.command("domains")
    async def cmd_domains(self, event: AstrMessageEvent):
        """查看域名列表（管理员专用）"""
        ok, err = self._check_global_permission(event)
        if not ok:
            yield event.plain_result(f"❌ {err}")
            return
        
        ok, err = self._check_query_enabled()
        if not ok:
            yield event.plain_result(f"❌ {err}")
            return
        
        api_key = self._get_api_key()
        if not api_key:
            yield event.plain_result("❌ 未配置雨云API密钥，请在插件配置中填写 X-Api-Key。")
            return
        
        result = await execute_tool("get_domain_list", {"options": "{}"}, api_key)
        yield event.plain_result(result)
    
    @rainyun.command("user")
    async def cmd_user(self, event: AstrMessageEvent):
        """查看雨云用户信息（管理员专用）"""
        ok, err = self._check_global_permission(event)
        if not ok:
            yield event.plain_result(f"❌ {err}")
            return
        
        ok, err = self._check_query_enabled()
        if not ok:
            yield event.plain_result(f"❌ {err}")
            return
        
        api_key = self._get_api_key()
        if not api_key:
            yield event.plain_result("❌ 未配置雨云API密钥，请在插件配置中填写 X-Api-Key。")
            return
        
        result = await execute_tool("get_user_info", {}, api_key)
        yield event.plain_result(result)

    # ========================================================================
    # 外部工具1: Search_query_tool (搜索查询工具)
    # ========================================================================
    @filter.llm_tool(name="search_query_tool")
    async def search_query_tool(self, event: AstrMessageEvent, keyword: str) -> str:
        '''
        搜索雨云查询类工具。通过关键词查找可用的查询功能。
        当你需要查询雨云账号的产品、域名、SSL证书、订单、用户信息、日志等数据时，先用此工具搜索对应的功能。

        Args:
            keyword(string): 搜索关键词，支持中文或英文，例如"域名列表"、"产品状态"、"DNS记录"、"SSL证书"、"订单"
        '''
        # 权限检查
        passed, err = check_permission(event, self.config)
        if not passed:
            return f"❌ {err}"
        if not self.config.get("enable_plugin", True):
            return "❌ 插件总开关已关闭。"
        if not self.config.get("enable_query", True):
            return "❌ 查询功能总开关已关闭。"
        
        results = search_tools_by_keyword(keyword)
        query_results = [t for t in results if t["type"] == "query"]
        
        if not query_results:
            return f"未找到与「{keyword}」相关的查询工具。建议尝试其他关键词，或使用 complete_tool_list 查看所有可用工具。"
        
        lines = [f"找到 {len(query_results)} 个与「{keyword}」相关的查询工具："]
        for tool in query_results[:10]:
            params_desc = ""
            if tool["parameters"]:
                params_desc = "，参数：" + "、".join(
                    f"{k}({v.get('description','')}，{'必填' if v.get('required') else '可选'})"
                    for k, v in tool["parameters"].items()
                )
            lines.append(f"  • {tool['name']}：{tool['description']}{params_desc}")
        
        if len(query_results) > 10:
            lines.append(f"  ... 还有 {len(query_results) - 10} 个工具，请缩小搜索范围。")
        
        lines.append("\n请选择其中一个工具，使用 executive_tool 执行。")
        return "\n".join(lines)
    
    # ========================================================================
    # 外部工具2: Search_execution_tool (搜索操作工具)
    # ========================================================================
    @filter.llm_tool(name="search_execution_tool")
    async def search_execution_tool(self, event: AstrMessageEvent, keyword: str) -> str:
        '''
        搜索雨云操作类工具。通过关键词查找可用的操作/修改功能。
        当你需要执行操作（如续费、添加解析、申请证书、修改设置、删除记录等）时，先用此工具搜索对应的功能。

        Args:
            keyword(string): 搜索关键词，支持中文或英文，例如"续费"、"添加DNS"、"申请SSL"、"修改解析"、"删除记录"
        '''
        passed, err = check_permission(event, self.config)
        if not passed:
            return f"❌ {err}"
        if not self.config.get("enable_plugin", True):
            return "❌ 插件总开关已关闭。"
        if not self.config.get("enable_operation", True):
            return "❌ 操作功能总开关已关闭。"
        
        results = search_tools_by_keyword(keyword)
        operation_results = [t for t in results if t["type"] == "operation"]
        
        if not operation_results:
            return f"未找到与「{keyword}」相关的操作工具。建议尝试其他关键词，或使用 complete_tool_list 查看所有可用工具。"
        
        lines = [f"找到 {len(operation_results)} 个与「{keyword}」相关的操作工具："]
        for tool in operation_results[:10]:
            params_desc = ""
            if tool["parameters"]:
                params_desc = "，参数：" + "、".join(
                    f"{k}({v.get('description','')}，{'必填' if v.get('required') else '可选'})"
                    for k, v in tool["parameters"].items()
                )
            lines.append(f"  • {tool['name']}：{tool['description']}{params_desc}")
        
        if len(operation_results) > 10:
            lines.append(f"  ... 还有 {len(operation_results) - 10} 个工具，请缩小搜索范围。")
        
        lines.append("\n请选择其中一个工具，使用 executive_tool 执行。")
        return "\n".join(lines)
    
    # ========================================================================
    # 外部工具3: Complete_tool_list (完整工具列表)
    # ========================================================================
    @filter.llm_tool(name="complete_tool_list")
    async def complete_tool_list(self, event: AstrMessageEvent, category: str = "all") -> str:
        '''
        获取雨云管理插件的完整工具列表。当搜索不到需要的工具时使用此功能查看所有可用工具。
        支持按类别筛选：query(查询类)、operation(操作类)、all(全部)。

        Args:
            category(string): 筛选类别，可选值：query(仅查询类)/operation(仅操作类)/all(全部)，默认为all
        '''
        passed, err = check_permission(event, self.config)
        if not passed:
            return f"❌ {err}"
        if not self.config.get("enable_plugin", True):
            return "❌ 插件总开关已关闭。"
        
        filtered_tools = INTERNAL_TOOLS
        if category == "query":
            filtered_tools = [t for t in INTERNAL_TOOLS if t["type"] == "query"]
        elif category == "operation":
            if not self.config.get("enable_operation", True):
                return "❌ 操作功能总开关已关闭。"
            filtered_tools = [t for t in INTERNAL_TOOLS if t["type"] == "operation"]
        
        lines = [f"雨云管理插件共有 {len(filtered_tools)} 个可用工具（类别：{category}）："]
        for tool in filtered_tools:
            params_summary = ""
            if tool["parameters"]:
                required_params = [k for k, v in tool["parameters"].items() if v.get("required")]
                optional_params = [k for k, v in tool["parameters"].items() if not v.get("required")]
                parts = []
                if required_params:
                    parts.append(f"必填：{', '.join(required_params)}")
                if optional_params:
                    parts.append(f"可选：{', '.join(optional_params)}")
                params_summary = "（" + "；".join(parts) + "）"
            type_label = "🔍查询" if tool["type"] == "query" else "⚡操作"
            lines.append(f"  [{type_label}] {tool['name']}{params_summary}")
        
        lines.append("\n请选择其中一个工具，使用 executive_tool 执行，需传入工具名称和参数。")
        return "\n".join(lines)
    
    # ========================================================================
    # 外部工具4: Executive_tool (执行工具)
    # ========================================================================
    @filter.llm_tool(name="executive_tool")
    async def executive_tool(self, event: AstrMessageEvent, tool_name: str, parameters: str) -> str:
        '''
        执行指定的雨云管理工具。在执行前请确保已通过搜索工具确认工具名称和参数。
        传入工具名称和JSON格式的参数字符串。

        Args:
            tool_name(string): 要执行的工具名称（从搜索工具返回的结果中获取）
            parameters(string): JSON格式的参数字符串，例如 {"id": "123", "host": "www", "type": "A", "value": "1.2.3.4", "ttl": 600, "line": "DEFAULT"}
        '''
        # 全局权限检查
        passed, err = check_permission(event, self.config)
        if not passed:
            return f"❌ {err}"
        if not self.config.get("enable_plugin", True):
            return "❌ 插件总开关已关闭。"
        
        # 解析参数
        try:
            params = json.loads(parameters) if parameters else {}
        except json.JSONDecodeError as e:
            return f"❌ 参数解析失败：无法将参数解析为JSON格式。错误详情：{str(e)}。请确保参数是有效的JSON字符串，例如：{{\"key\": \"value\"}}"
        
        # 检查工具是否存在
        if tool_name not in TOOL_MAP:
            return f"❌ 工具「{tool_name}」不存在。请使用 search_query_tool、search_execution_tool 或 complete_tool_list 查找正确的工具名称。"
        
        tool = TOOL_MAP[tool_name]
        
        # 根据工具类型检查开关
        if tool["type"] == "query" and not self.config.get("enable_query", True):
            return "❌ 查询功能总开关已关闭，无法执行查询类工具。"
        if tool["type"] == "operation" and not self.config.get("enable_operation", True):
            return "❌ 操作功能总开关已关闭，无法执行操作类工具。"
        
        # 验证必填参数
        missing_params = []
        for param_name, param_info in tool["parameters"].items():
            if param_info.get("required", False) and param_name not in params:
                missing_params.append(f"{param_name}（{param_info.get('description', '无描述')}）")
        
        if missing_params:
            return f"❌ 执行「{tool_name}」失败：缺少必填参数。\n缺少的参数：\n" + "\n".join(f"  • {mp}" for mp in missing_params) + f"\n\n工具描述：{tool['description']}\n请补充参数后重试。"
        
        api_key = self._get_api_key()
        if not api_key:
            return "❌ 未配置雨云API密钥（X-Api-Key）。请联系管理员在插件配置中填写API密钥后重试。"
        
        # 执行
        result = await execute_tool(tool_name, params, api_key)
        return result
