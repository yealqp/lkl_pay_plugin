# zjmf_lkl_plugin - 魔方财务拉卡拉支付插件

作者: yealqp  
QQ: 1592239257  
开发方式: 纯 AI 开发  
开源协议: GPLv3 

**采用 Python 后端架构，提供更好的安全性和可维护性。**

---

## 📁 项目结构

```
pay/
├── lkl_pay/                    # PHP 插件（魔方财务）
│   ├── LklPayPlugin.php       # 插件主类
│   ├── controller/
│   │   └── IndexController.php # 回调处理
│   └── config.php             # 插件配置
│
├── python_api/                 # Python 后端 API
│   ├── main.py                # 主应用
│   ├── config.json            # 配置文件
│
└── 文档/
    ├── SETUP_GUIDE.md         # 📖 快速配置指南
    ├── SECURITY.md            # 🔒 安全配置（必读！）
    └── generate_secrets.py    # 🔑 密钥生成工具
```

---

## 🚀 快速开始（3步完成）

### 第1步：获取拉卡拉参数

1. 电脑浏览器打开拉卡拉缴费易页面
2. 按 F12 → 网络（Network）
3. 找到以下参数：
   - `merchId`
   - `key`
   - `origin`
   - `channelId`

### 第2步：配置并生成密钥

```bash
# 1. 生成安全密钥
python generate_secrets.py

# 2. 编辑 python_api/config.json
# 填入拉卡拉参数和生成的密钥
```

### 第3步：部署

#### 方式A：Docker 部署（推荐，已构建好镜像）

```powershell
# 镜像已经构建完成！位于 python_api/docker-export/

# 直接使用已构建的镜像部署：
cd python_api
docker load -i docker-export/lakala-payment-api_latest_20251115_123111.tar.gz
docker-compose up -d
```

#### 方式B：直接运行

```bash
cd python_api
pip install -r requirements.txt
python main.py
```

详细步骤见：**[SETUP_GUIDE.md](SETUP_GUIDE.md)**

---

## 📦 已构建的 Docker 镜像

✅ **镜像已准备就绪！**

- 📁 文件: `python_api/docker-export/lakala-payment-api_latest_20251115_123111.tar.gz`
- 💾 大小: 约 117 MB
- 🕐 构建时间: 2025-11-15 12:31
- 🐳 镜像: `lakala-payment-api:latest`

**快速部署：**
```bash
# 导入镜像
docker load -i lakala-payment-api_latest_20251115_123111.tar.gz

# 启动容器
docker-compose up -d
```

部署清单见：[python_api/docker-export/DEPLOY_CHECKLIST.txt](python_api/docker-export/DEPLOY_CHECKLIST.txt)

---

## ✨ 功能特性

### 支付功能
✅ 拉卡拉聚合收银台支付  
✅ 自动轮询支付状态（5秒/次）  
✅ 支付成功自动回调入账  
✅ 金额单位自动转换（分→元，已修复金额问题）  

### 安全特性（重要！）
✅ API 密钥认证  
✅ 回调签名验证（防伪造刷钱）  
✅ 防重放攻击  
✅ 回调域名白名单  
✅ 敏感信息保护  

### 部署方式
✅ Docker 容器化（已构建）  
✅ 传统直接部署  
✅ 跨平台支持  

---

## 📚 完整文档

### 🎯 新手必读
1. **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - 详细配置教程
2. **[SECURITY.md](SECURITY.md)** - 安全配置（生产环境必须配置）

---

## ⚠️ 重要提醒

### 生产环境必须配置：

1. **生成强随机密钥**
   ```bash
   python generate_secrets.py
   ```

2. **配置 Python**（`python_api/config.json`）
   ```json
   {
       "API_SECRET_KEY": "生成的密钥1",
       "CALLBACK_SECRET": "生成的密钥2",
       "ALLOWED_CALLBACK_DOMAINS": ["你的域名.com"]
   }
   ```

3. **配置 PHP 后台**
   - 插件管理 → 拉卡拉收银台 → 配置
   - 填入与 Python 一致的密钥

4. **启用 HTTPS**（生产环境必需）

**⚠️ 不配置安全密钥可能导致被刷钱！** 详见 [SECURITY.md](SECURITY.md)

---

## 🛠️ 技术架构

```
用户 → PHP网站 → Python API → 拉卡拉
                    ↓
              轮询支付状态
                    ↓
              PHP回调入账
```

**技术栈:**
- Python 3.11 + FastAPI
- 签名验证机制
- 防重放攻击

## 📞 联系方式

- **作者**: yealqp
- **QQ**: 1592239257
- **开源**: 免费开放源码

---

**声明**: 本插件开源免费，对比某些付费插件，功能可能不够完善，但核心支付流程稳定可靠。欢迎提 Issue 和 PR！

**License**: GPLv3
