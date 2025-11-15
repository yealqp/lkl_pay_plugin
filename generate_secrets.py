#!/usr/bin/env python3
"""
安全密钥生成工具
用于生成 API_SECRET_KEY 和 CALLBACK_SECRET
"""

import secrets
import json
import os

def generate_secrets():
    """生成强随机密钥"""
    api_key = secrets.token_urlsafe(32)
    callback_secret = secrets.token_urlsafe(32)
    
    print("=" * 80)
    print("安全密钥已生成")
    print("=" * 80)
    print()
    print("API_SECRET_KEY (用于 Python API 认证):")
    print(api_key)
    print()
    print("CALLBACK_SECRET (用于回调签名):")
    print(callback_secret)
    print()
    print("=" * 80)
    print("配置说明:")
    print("=" * 80)
    print()
    print("1. 将以下内容添加到 python_api/config.json:")
    print()
    config_example = {
        "API_SECRET_KEY": api_key,
        "CALLBACK_SECRET": callback_secret,
        "ALLOWED_CALLBACK_DOMAINS": ["example.com", "www.example.com"]
    }
    print(json.dumps(config_example, indent=4, ensure_ascii=False))
    print()
    print("2. 在 PHP 后台插件配置中添加:")
    print(f"   api_secret_key: {api_key}")
    print()
    print("3. 在 lkl_pay/controller/IndexController.php 中设置:")
    print(f"   $secret = '{callback_secret}';")
    print()
    print("=" * 80)
    print("⚠️  重要提醒:")
    print("=" * 80)
    print("- 请妥善保管这些密钥，不要泄露")
    print("- 不要将密钥提交到版本控制系统")
    print("- Python 和 PHP 的密钥必须保持一致")
    print("- 定期更换密钥以提高安全性")
    print("=" * 80)
    
    # 询问是否自动更新配置文件
    try:
        update = input("\n是否自动更新 python_api/config.json? (y/n): ").strip().lower()
        if update == 'y':
            config_path = os.path.join(os.path.dirname(__file__), 'python_api', 'config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                config['API_SECRET_KEY'] = api_key
                config['CALLBACK_SECRET'] = callback_secret
                
                if 'ALLOWED_CALLBACK_DOMAINS' not in config:
                    domains = input("请输入允许的回调域名（逗号分隔）: ").strip()
                    config['ALLOWED_CALLBACK_DOMAINS'] = [d.strip() for d in domains.split(',') if d.strip()]
                
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4, ensure_ascii=False)
                
                print(f"\n✅ 配置文件已更新: {config_path}")
                print("⚠️  请记得同步更新 PHP 端的配置！")
            else:
                print(f"\n❌ 配置文件不存在: {config_path}")
    except KeyboardInterrupt:
        print("\n\n操作已取消")

if __name__ == "__main__":
    generate_secrets()
