# 🚀 快速配置指南

## 第1步：生成安全密钥

运行密钥生成工具：
```bash
python generate_secrets.py
```

这将生成两个密钥：
- `API_SECRET_KEY` - 用于 Python API 认证
- `CALLBACK_SECRET` - 用于回调签名验证

**保存好这两个密钥，接下来会用到！**

---

## 第2步：配置 Python 后端

编辑文件：`python_api/config.json`

```json
{
    "LAKALA_MERCH_ID": "你的商户ID",
    "LAKALA_KEY": 你的KEY,
    "LAKALA_ORIGIN": "你的ORIGIN",
    "LAKALA_CHANNEL_ID": 15,
    "API_SECRET_KEY": "步骤1生成的API_SECRET_KEY",
    "CALLBACK_SECRET": "步骤1生成的CALLBACK_SECRET",
    "ALLOWED_CALLBACK_DOMAINS": ["你的域名.com", "www.你的域名.com"]
}
```

**重要字段说明：**
- `API_SECRET_KEY`: 复制步骤1生成的密钥
- `CALLBACK_SECRET`: 复制步骤1生成的密钥
- `ALLOWED_CALLBACK_DOMAINS`: 填写你的网站域名

---

## 第3步：配置 PHP 后台

登录 PHP 后台 -> 插件管理 -> 拉卡拉收银台 -> 配置

填写以下字段：

| 字段名 | 说明 | 示例值 |
|--------|------|--------|
| **Python后端地址** | Python API 的完整地址 | `http://localhost:8080` |
| **API密钥** | 与 Python 的 `API_SECRET_KEY` 一致 | 步骤1生成的密钥 |
| **回调签名密钥** | 与 Python 的 `CALLBACK_SECRET` 一致 | 步骤1生成的密钥 |
| **支持货币单位** | 货币代码 | `CNY` |

**⚠️ 关键：** 
- `API密钥` 必须与 Python 配置的 `API_SECRET_KEY` 完全一致
- `回调签名密钥` 必须与 Python 配置的 `CALLBACK_SECRET` 完全一致

---

## 第4步：重启 Python 服务

```bash
# 停止旧进程
Get-Process | Where-Object { $_.ProcessName -like "*python*" } | Stop-Process -Force

# 启动新进程
cd python_api
python main.py
```

---

## 第5步：测试验证

### 测试1：访问 Python API（应要求密钥）
```bash
# 无密钥访问（应失败）
curl -X POST http://localhost:8080/lakala/create_order

# 有密钥访问（应成功）
curl -X POST http://localhost:8080/lakala/create_order \
  -H "X-API-Key: 你的API_SECRET_KEY" \
  -H "Content-Type: application/json" \
  -d '{"invoice_id":"test","tradeAmount":"0.01",...}'
```

### 测试2：完整支付流程
1. 在网站发起充值 0.01 元
2. 跳转到拉卡拉收银台
3. 完成支付
4. 等待 5-10 秒
5. 检查账户余额是否增加 0.01 元（不是 1 元！）

---

## ✅ 配置完成检查清单

完成配置后，请确认：

- [ ] 已生成两个强随机密钥（至少32位）
- [ ] Python `config.json` 已配置 `API_SECRET_KEY`
- [ ] Python `config.json` 已配置 `CALLBACK_SECRET`
- [ ] Python `config.json` 已配置 `ALLOWED_CALLBACK_DOMAINS`
- [ ] PHP 后台已配置 `API密钥`（与 Python 一致）
- [ ] PHP 后台已配置 `回调签名密钥`（与 Python 一致）
- [ ] Python 服务已重启
- [ ] 测试支付流程正常
- [ ] 测试金额正确（0.01元入账0.01元，不是1元）

---

## 🔒 安全提醒

### 生产环境必须：

1. **启用 HTTPS**
   - 配置 SSL 证书
   - 强制 HTTPS 访问

2. **保护密钥安全**
   - 不要将密钥提交到 Git
   - 不要在日志中打印密钥
   - 定期更换密钥

3. **日志文件权限**
   ```bash
   chmod 600 python_api/app.log
   chmod 600 lkl_pay/*.log
   ```

4. **网络隔离**
   - Python API 建议只监听内网
   - 通过 Nginx 反向代理访问

---

## ❓ 常见问题

### Q1: 提示 "签名验证失败"
**A:** 检查 Python 和 PHP 的 `CALLBACK_SECRET` 是否完全一致

### Q2: 提示 "无效的API密钥"
**A:** 检查 PHP 配置的 `api_secret_key` 与 Python 的 `API_SECRET_KEY` 是否一致

### Q3: 充值0.01元变成了1元
**A:** 这是之前的 bug，更新代码后重启服务即可解决

### Q4: 支付后没有回调
**A:** 检查：
- payOrderNo 是否正确提取
- Python 日志中是否有轮询记录
- 回调域名是否在白名单中

### Q5: 如何更换密钥？
**A:** 
1. 运行 `python generate_secrets.py` 生成新密钥
2. 更新 Python `config.json`
3. 更新 PHP 后台配置
4. 重启 Python 服务

---

## 📚 更多文档

- `SECURITY.md` - 详细的安全说明
- `README.md` - 项目说明
- `lkl_api.md` - 拉卡拉 API 文档

---

**配置完成！** 🎉

如有问题，请查看日志文件：
- Python: `python_api/app.log`
- PHP: `lkl_pay/lkl_pay.log`
- PHP Controller: `lkl_pay/lkl_pay_controller.log`
