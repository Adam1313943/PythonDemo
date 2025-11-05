# Let's Encrypt 憑證自動更新工具

一個用 Python 編寫的 Let's Encrypt SSL/TLS 憑證自動更新工具，支援多網域管理、電子郵件通知和自動服務重載。

## 功能特色

- ✅ **自動憑證更新**: 自動檢測憑證到期時間並進行更新
- ✅ **多網域支援**: 可同時管理多個網域的憑證
- ✅ **靈活的排程**: 支援 systemd timer 和 crontab 兩種排程方式
- ✅ **電子郵件通知**: 更新成功或失敗時自動發送通知
- ✅ **詳細日誌記錄**: 完整的操作記錄和錯誤追蹤
- ✅ **自動服務重載**: 更新後自動重新載入 Nginx、Apache 等服務
- ✅ **測試模式**: 支援 dry-run 模式，安全測試設定
- ✅ **可自訂門檻**: 自訂憑證到期前幾天開始更新

## 系統需求

- Python 3.6 或更高版本
- Certbot (Let's Encrypt 官方客戶端)
- Root 權限 (更新憑證需要)
- Linux 作業系統

## 安裝步驟

### 1. 安裝系統依賴

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip certbot

# CentOS/RHEL
sudo yum install python3 python3-pip certbot

# 如果使用 Nginx
sudo apt install python3-certbot-nginx

# 如果使用 Apache
sudo apt install python3-certbot-apache
```

### 2. 下載並安裝工具

```bash
# 克隆專案
git clone https://github.com/yourusername/PythonDemo.git
cd PythonDemo

# 安裝 Python 依賴
sudo pip3 install -r requirements.txt

# 創建安裝目錄
sudo mkdir -p /opt/cert-renewal
sudo cp cert_renewal.py /opt/cert-renewal/
sudo chmod +x /opt/cert-renewal/cert_renewal.py

# 創建日誌目錄
sudo mkdir -p /var/log/cert-renewal
```

### 3. 設定配置檔

```bash
# 複製範例設定檔
sudo cp config.example.json /opt/cert-renewal/config.json

# 編輯設定檔
sudo nano /opt/cert-renewal/config.json
```

#### 設定檔說明

```json
{
  "domains": [
    "example.com",        // 要管理的網域列表
    "www.example.com"
  ],
  "renewal_threshold_days": 30,  // 憑證到期前幾天開始更新
  "log_directory": "/var/log/cert-renewal",  // 日誌目錄
  "log_level": "INFO",  // 日誌等級: DEBUG, INFO, WARNING, ERROR
  "certbot_args": [     // 傳遞給 certbot 的額外參數
    "--quiet",
    "--no-self-upgrade"
  ],
  "reload_services": [  // 憑證更新後需要重載的服務
    "nginx"
  ],
  "email_notifications": {
    "enabled": true,    // 是否啟用郵件通知
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "your-email@gmail.com",
    "password": "your-app-password",  // Gmail 需使用應用程式密碼
    "from_addr": "your-email@gmail.com",
    "to_addrs": [       // 通知收件人列表
      "admin@example.com"
    ]
  }
}
```

## 使用方式

### 手動執行

```bash
# 正常執行
sudo python3 /opt/cert-renewal/cert_renewal.py

# 測試模式 (不會實際更新憑證)
sudo python3 /opt/cert-renewal/cert_renewal.py --dry-run

# 使用自訂設定檔
sudo python3 /opt/cert-renewal/cert_renewal.py --config /path/to/config.json
```

### 自動排程執行

#### 方法 1: 使用 systemd timer (推薦)

```bash
# 複製 service 和 timer 檔案
sudo cp cert-renewal.service /etc/systemd/system/
sudo cp cert-renewal.timer /etc/systemd/system/

# 重新載入 systemd
sudo systemctl daemon-reload

# 啟用並啟動 timer
sudo systemctl enable cert-renewal.timer
sudo systemctl start cert-renewal.timer

# 檢查 timer 狀態
sudo systemctl status cert-renewal.timer

# 查看下次執行時間
sudo systemctl list-timers cert-renewal.timer

# 手動觸發執行 (測試用)
sudo systemctl start cert-renewal.service

# 查看執行日誌
sudo journalctl -u cert-renewal.service -f
```

#### 方法 2: 使用 Crontab

```bash
# 編輯 root 的 crontab
sudo crontab -e

# 加入以下內容 (每天凌晨 2:00 和下午 2:00 執行)
0 2,14 * * * /usr/bin/python3 /opt/cert-renewal/cert_renewal.py --config /opt/cert-renewal/config.json >> /var/log/cert-renewal/cron.log 2>&1
```

## 首次設定 Let's Encrypt 憑證

在使用本工具前，您需要先手動取得 Let's Encrypt 憑證：

```bash
# 使用 Nginx
sudo certbot --nginx -d example.com -d www.example.com

# 使用 Apache
sudo certbot --apache -d example.com -d www.example.com

# 使用 Standalone 模式 (需要暫停網頁伺服器)
sudo certbot certonly --standalone -d example.com -d www.example.com

# 使用 Webroot 模式
sudo certbot certonly --webroot -w /var/www/html -d example.com -d www.example.com
```

## 測試設定

```bash
# 執行 dry-run 測試
sudo python3 /opt/cert-renewal/cert_renewal.py --dry-run

# 檢查日誌
sudo tail -f /var/log/cert-renewal/renewal.log
```

## 故障排除

### 憑證更新失敗

1. **檢查 certbot 是否正確安裝**:
   ```bash
   certbot --version
   ```

2. **手動測試 certbot 更新**:
   ```bash
   sudo certbot renew --dry-run
   ```

3. **檢查憑證路徑**:
   ```bash
   sudo ls -la /etc/letsencrypt/live/
   ```

4. **查看詳細日誌**:
   ```bash
   sudo tail -100 /var/log/cert-renewal/renewal.log
   ```

### 服務重載失敗

1. **檢查服務狀態**:
   ```bash
   sudo systemctl status nginx
   ```

2. **測試設定檔**:
   ```bash
   # Nginx
   sudo nginx -t

   # Apache
   sudo apache2ctl configtest
   ```

### 郵件通知未收到

1. **檢查 SMTP 設定**:
   - 確認 SMTP 伺服器和端口正確
   - Gmail 需要使用「應用程式密碼」而非帳號密碼
   - 檢查防火牆是否阻擋 SMTP 端口

2. **查看日誌中的錯誤訊息**:
   ```bash
   sudo grep -i "email\|smtp" /var/log/cert-renewal/renewal.log
   ```

## 安全性建議

1. **保護設定檔**: 設定檔包含敏感資訊 (如郵件密碼)
   ```bash
   sudo chmod 600 /opt/cert-renewal/config.json
   sudo chown root:root /opt/cert-renewal/config.json
   ```

2. **使用應用程式密碼**: Gmail 等服務建議使用應用程式專用密碼而非主密碼

3. **定期檢查日誌**: 定期檢查更新日誌確保一切正常運作

4. **測試備援**: 定期測試憑證更新流程，避免到期前才發現問題

## 目錄結構

```
PythonDemo/
├── cert_renewal.py           # 主程式
├── config.example.json       # 設定檔範例
├── cert-renewal.service      # systemd service 檔案
├── cert-renewal.timer        # systemd timer 檔案
├── crontab.example          # crontab 範例
├── requirements.txt         # Python 依賴套件
└── README.md               # 說明文件
```

## 日誌範例

```
2024-11-05 02:00:00 - __main__ - INFO - ============================================================
2024-11-05 02:00:00 - __main__ - INFO - 開始執行 Let's Encrypt 憑證自動更新
2024-11-05 02:00:00 - __main__ - INFO - ============================================================
2024-11-05 02:00:01 - __main__ - INFO - 網域 example.com 的憑證還有 45 天到期
2024-11-05 02:00:01 - __main__ - INFO - 網域 example.com 不需要更新 (剩餘 45 天)
2024-11-05 02:00:02 - __main__ - INFO - 所有憑證都在有效期限內，無需更新
2024-11-05 02:00:02 - __main__ - INFO - ============================================================
2024-11-05 02:00:02 - __main__ - INFO - 憑證更新流程完成
2024-11-05 02:00:02 - __main__ - INFO - ============================================================
```

## 常見問題 (FAQ)

### Q: 多久檢查一次憑證？
A: 預設使用 systemd timer 每天檢查兩次（凌晨 2:00 和下午 2:00）。

### Q: 憑證到期前多久會自動更新？
A: 預設是 30 天，可在 `config.json` 中調整 `renewal_threshold_days`。

### Q: 支援哪些網頁伺服器？
A: 支援所有 certbot 支援的伺服器，包括 Nginx、Apache、Lighttpd 等。

### Q: 可以管理多個不同的網域嗎？
A: 可以，在 `domains` 陣列中列出所有要管理的網域即可。

### Q: 更新失敗會怎樣？
A: 程式會記錄錯誤到日誌，並發送郵件通知管理員。

## 授權條款

MIT License

## 貢獻

歡迎提交 Issue 和 Pull Request！

## 聯絡方式

如有問題或建議，請開 Issue 或聯絡專案維護者。

---

**注意**: 本工具需要 root 權限執行，請確保在受信任的環境中使用。
