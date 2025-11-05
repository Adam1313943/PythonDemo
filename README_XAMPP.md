# XAMPP 環境專用 - Let's Encrypt 憑證自動更新工具

專門為 XAMPP 環境 (WordPress、PHP 開發) 設計的 Let's Encrypt SSL/TLS 憑證自動更新工具，支援 Windows、Linux 和 macOS。

## 功能特色

- ✅ **XAMPP 專用設計**: 自動檢測 XAMPP 安裝路徑
- ✅ **跨平台支援**: Windows、Linux、macOS 都可使用
- ✅ **自動更新 Apache 設定**: 自動修改 httpd-ssl.conf
- ✅ **智慧憑證管理**: 自動檢測到期時間並更新
- ✅ **WordPress 友善**: 專為 WordPress 網站設計
- ✅ **自動重啟服務**: 更新後自動重啟 XAMPP Apache
- ✅ **Windows 工作排程**: 支援 Windows Task Scheduler
- ✅ **詳細日誌記錄**: 完整的操作記錄

## 適用環境

- XAMPP (任何版本)
- WordPress 網站
- PHP 開發環境
- Windows、Linux、macOS

## 系統需求

### Windows
- Python 3.6 或更高版本
- XAMPP for Windows
- win-acme (Windows ACME 客戶端)
- 系統管理員權限

### Linux/macOS
- Python 3.6 或更高版本
- XAMPP for Linux/macOS
- Certbot
- Root 權限

## 安裝步驟

### Windows 環境安裝

#### 1. 安裝 Python

```powershell
# 下載並安裝 Python 3
# https://www.python.org/downloads/

# 確認安裝
python --version
```

#### 2. 安裝 win-acme

```powershell
# 下載 win-acme
# https://github.com/win-acme/win-acme/releases

# 解壓縮到 C:\Tools\win-acme\
# (或您喜歡的路徑，記得更新設定檔)
```

#### 3. 下載工具並設定

```powershell
# 下載此專案
git clone https://github.com/yourusername/PythonDemo.git
cd PythonDemo

# 執行自動安裝腳本 (需要系統管理員權限)
# 右鍵點選 setup_task_scheduler.bat -> 以系統管理員身份執行
```

#### 4. 設定配置檔

編輯 `C:\xampp-cert-renewal\xampp_config.json`:

```json
{
  "domains": [
    "yourdomain.com",
    "www.yourdomain.com"
  ],
  "renewal_threshold_days": 30,
  "log_directory": "./logs",
  "log_level": "INFO",
  "xampp_path": "C:\\xampp",
  "win_acme_path": "C:\\Tools\\win-acme\\wacs.exe",
  "cert_base_path": ""
}
```

#### 5. 使用 win-acme 取得初始憑證

```powershell
# 進入 win-acme 目錄
cd C:\Tools\win-acme

# 執行 win-acme
.\wacs.exe

# 選擇選項:
# M: 建立新憑證 (使用完整選項)
# 選擇: 2 (Manual input)
# 輸入您的網域: yourdomain.com,www.yourdomain.com
# 選擇驗證方式 (建議使用 HTTP-01)
# 選擇安裝位置: 選擇不自動安裝，稍後手動設定
```

#### 6. 手動設定 XAMPP Apache SSL

編輯 `C:\xampp\apache\conf\extra\httpd-ssl.conf`:

找到以下行並修改為您的憑證路徑:

```apache
# 將這些路徑改為 win-acme 產生的憑證位置
SSLCertificateFile "C:/ProgramData/win-acme/httpsacme-v02.api.letsencrypt.org/yourdomain.com-crt.pem"
SSLCertificateKeyFile "C:/ProgramData/win-acme/httpsacme-v02.api.letsencrypt.org/yourdomain.com-key.pem"
SSLCertificateChainFile "C:/ProgramData/win-acme/httpsacme-v02.api.letsencrypt.org/yourdomain.com-chain.pem"
```

重啟 XAMPP Apache:
```powershell
# 使用 XAMPP 控制面板停止並啟動 Apache
# 或使用命令列
net stop Apache2.4
net start Apache2.4
```

#### 7. 測試工具

```powershell
# 測試模式 (不會實際更新)
python C:\xampp-cert-renewal\xampp_cert_renewal.py --dry-run

# 正式執行
python C:\xampp-cert-renewal\xampp_cert_renewal.py
```

### Linux/macOS 環境安裝

#### 1. 安裝依賴

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip certbot

# macOS (使用 Homebrew)
brew install python certbot
```

#### 2. 安裝工具

```bash
# 克隆專案
git clone https://github.com/yourusername/PythonDemo.git
cd PythonDemo

# 建立安裝目錄
sudo mkdir -p /opt/xampp-cert-renewal
sudo cp xampp_cert_renewal.py /opt/xampp-cert-renewal/
sudo cp xampp_config.example.json /opt/xampp-cert-renewal/xampp_config.json
sudo chmod +x /opt/xampp-cert-renewal/xampp_cert_renewal.py

# 建立日誌目錄
sudo mkdir -p /opt/xampp-cert-renewal/logs
```

#### 3. 設定配置檔

編輯 `/opt/xampp-cert-renewal/xampp_config.json`:

```json
{
  "domains": [
    "yourdomain.com",
    "www.yourdomain.com"
  ],
  "renewal_threshold_days": 30,
  "log_directory": "/opt/xampp-cert-renewal/logs",
  "log_level": "INFO",
  "xampp_path": "/opt/lampp",
  "cert_base_path": "/etc/letsencrypt/live"
}
```

#### 4. 使用 Certbot 取得初始憑證

```bash
# 暫停 XAMPP Apache
sudo /opt/lampp/lampp stop

# 使用 Certbot standalone 模式
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# 或使用 webroot 模式 (不需停止 Apache)
sudo certbot certonly --webroot -w /opt/lampp/htdocs -d yourdomain.com -d www.yourdomain.com

# 重新啟動 XAMPP
sudo /opt/lampp/lampp start
```

#### 5. 設定 XAMPP Apache SSL

編輯 `/opt/lampp/apache/conf/extra/httpd-ssl.conf`:

```apache
SSLCertificateFile "/etc/letsencrypt/live/yourdomain.com/cert.pem"
SSLCertificateKeyFile "/etc/letsencrypt/live/yourdomain.com/privkey.pem"
SSLCertificateChainFile "/etc/letsencrypt/live/yourdomain.com/chain.pem"
```

重啟 XAMPP:
```bash
sudo /opt/lampp/lampp restart
```

#### 6. 設定 Cron 自動執行

```bash
# 編輯 root crontab
sudo crontab -e

# 加入以下內容 (每天凌晨 2:00 和下午 2:00 執行)
0 2,14 * * * /usr/bin/python3 /opt/xampp-cert-renewal/xampp_cert_renewal.py --config /opt/xampp-cert-renewal/xampp_config.json >> /opt/xampp-cert-renewal/logs/cron.log 2>&1
```

## 使用方式

### Windows

#### 手動執行

```powershell
# 正常執行
python C:\xampp-cert-renewal\xampp_cert_renewal.py

# 測試模式
python C:\xampp-cert-renewal\xampp_cert_renewal.py --dry-run

# 使用自訂設定檔
python C:\xampp-cert-renewal\xampp_cert_renewal.py --config C:\path\to\config.json
```

#### 使用工作排程器

```powershell
# 查看排程狀態
schtasks /Query /TN "XAMPP Certificate Renewal"

# 手動執行排程任務
schtasks /Run /TN "XAMPP Certificate Renewal"

# 查看執行歷史
# 開啟「工作排程器」-> 尋找「XAMPP Certificate Renewal」-> 查看「歷程記錄」標籤
```

### Linux/macOS

```bash
# 正常執行
sudo python3 /opt/xampp-cert-renewal/xampp_cert_renewal.py

# 測試模式
sudo python3 /opt/xampp-cert-renewal/xampp_cert_renewal.py --dry-run

# 查看日誌
tail -f /opt/xampp-cert-renewal/logs/xampp_renewal.log
```

## WordPress 特別注意事項

### 1. 確保網站可從外部存取

Let's Encrypt 需要驗證網域所有權，確保:
- 網域 DNS 指向您的伺服器
- 防火牆開放 80 和 443 埠
- XAMPP Apache 正在運行

### 2. WordPress 設定 HTTPS

取得憑證後，在 WordPress 中啟用 HTTPS:

1. **修改 wp-config.php** (在 `C:\xampp\htdocs\yoursite\wp-config.php`):

```php
// 在 'That's all, stop editing!' 之前加入
define('FORCE_SSL_ADMIN', true);
if (isset($_SERVER['HTTP_X_FORWARDED_PROTO']) && $_SERVER['HTTP_X_FORWARDED_PROTO'] === 'https') {
    $_SERVER['HTTPS'] = 'on';
}
```

2. **更新 WordPress 網址**:
   - 登入 WordPress 管理後台
   - 設定 -> 一般設定
   - WordPress 位址 (URL): `https://yourdomain.com`
   - 網站位址 (URL): `https://yourdomain.com`
   - 儲存變更

3. **安裝 Really Simple SSL 外掛** (可選):
   - 自動處理混合內容問題
   - 自動重定向 HTTP 到 HTTPS

### 3. XAMPP 虛擬主機設定

如果使用虛擬主機，編輯 `C:\xampp\apache\conf\extra\httpd-vhosts.conf`:

```apache
<VirtualHost *:443>
    DocumentRoot "C:/xampp/htdocs/yoursite"
    ServerName yourdomain.com
    ServerAlias www.yourdomain.com

    SSLEngine on
    SSLCertificateFile "C:/ProgramData/win-acme/httpsacme-v02.api.letsencrypt.org/yourdomain.com-crt.pem"
    SSLCertificateKeyFile "C:/ProgramData/win-acme/httpsacme-v02.api.letsencrypt.org/yourdomain.com-key.pem"
    SSLCertificateChainFile "C:/ProgramData/win-acme/httpsacme-v02.api.letsencrypt.org/yourdomain.com-chain.pem"

    <Directory "C:/xampp/htdocs/yoursite">
        AllowOverride All
        Require all granted
    </Directory>
</VirtualHost>
```

## 故障排除

### Windows 常見問題

#### 問題 1: 找不到 XAMPP 路徑

**解決方案**:
```json
// 在 xampp_config.json 中明確指定路徑
{
  "xampp_path": "C:\\xampp"  // 或 D:\\xampp
}
```

#### 問題 2: win-acme 執行失敗

**解決方案**:
1. 確認 win-acme 路徑正確
2. 以系統管理員身份執行
3. 檢查防火牆設定
4. 確保網域 DNS 已正確設定

#### 問題 3: Apache 無法重啟

**解決方案**:
```powershell
# 檢查 Apache 設定
C:\xampp\apache\bin\httpd.exe -t

# 查看錯誤日誌
type C:\xampp\apache\logs\error.log

# 手動重啟
net stop Apache2.4
net start Apache2.4
```

#### 問題 4: 工作排程器未執行

**解決方案**:
1. 開啟「工作排程器」
2. 找到「XAMPP Certificate Renewal」
3. 右鍵 -> 內容
4. 檢查「觸發程序」和「動作」設定
5. 確認「以最高權限執行」已勾選

### Linux/macOS 常見問題

#### 問題 1: Certbot 權限錯誤

**解決方案**:
```bash
# 使用 sudo 執行
sudo certbot renew
```

#### 問題 2: XAMPP Apache 無法重啟

**解決方案**:
```bash
# 檢查 XAMPP 狀態
sudo /opt/lampp/lampp status

# 查看錯誤日誌
sudo tail -100 /opt/lampp/logs/error_log

# 測試 Apache 設定
sudo /opt/lampp/bin/httpd -t
```

### WordPress 相關問題

#### 問題: 混合內容警告 (Mixed Content)

**解決方案**:
1. 安裝 Really Simple SSL 外掛
2. 或手動更新資料庫:

```sql
UPDATE wp_options SET option_value = replace(option_value, 'http://yourdomain.com', 'https://yourdomain.com') WHERE option_name = 'home' OR option_name = 'siteurl';

UPDATE wp_posts SET post_content = replace(post_content, 'http://yourdomain.com', 'https://yourdomain.com');

UPDATE wp_postmeta SET meta_value = replace(meta_value, 'http://yourdomain.com', 'https://yourdomain.com');
```

## 日誌範例

```
2024-11-05 02:00:00 - __main__ - INFO - ============================================================
2024-11-05 02:00:00 - __main__ - INFO - 開始執行 XAMPP Let's Encrypt 憑證自動更新
2024-11-05 02:00:00 - __main__ - INFO - 作業系統: Windows
2024-11-05 02:00:00 - __main__ - INFO - XAMPP 路徑: C:\xampp
2024-11-05 02:00:00 - __main__ - INFO - ============================================================
2024-11-05 02:00:01 - __main__ - INFO - 網域 yourdomain.com 的憑證還有 25 天到期
2024-11-05 02:00:01 - __main__ - INFO - 網域 yourdomain.com 需要更新 (剩餘 25 天)
2024-11-05 02:00:05 - __main__ - INFO - 使用 win-acme 更新憑證: yourdomain.com
2024-11-05 02:00:15 - __main__ - INFO - 憑證更新成功: yourdomain.com
2024-11-05 02:00:15 - __main__ - INFO - 更新 Apache SSL 設定: yourdomain.com
2024-11-05 02:00:16 - __main__ - INFO - Apache SSL 設定更新成功
2024-11-05 02:00:16 - __main__ - INFO - 憑證已更新，重新啟動 Apache...
2024-11-05 02:00:20 - __main__ - INFO - Apache 重新啟動成功
2024-11-05 02:00:20 - __main__ - INFO - ============================================================
2024-11-05 02:00:20 - __main__ - INFO - 憑證更新流程完成
2024-11-05 02:00:20 - __main__ - INFO - ============================================================
```

## 安全性建議

1. **保護設定檔**:
   - Windows: 設定檔案權限，只有管理員可讀取
   - Linux: `chmod 600 /opt/xampp-cert-renewal/xampp_config.json`

2. **定期備份**: 定期備份憑證和設定檔

3. **監控日誌**: 定期檢查日誌確保更新正常運作

4. **測試備援**: 定期測試憑證更新流程

## 常見問題 (FAQ)

### Q: XAMPP 可以使用 Let's Encrypt 嗎？
A: 可以！本工具專門為 XAMPP 環境設計，完全支援。

### Q: WordPress 網站會受影響嗎？
A: 不會。更新過程只需幾秒鐘，對網站幾乎無影響。

### Q: 需要停止 XAMPP 嗎？
A: 不需要。工具會自動重啟 Apache，無需手動停止。

### Q: 支援多個網站嗎？
A: 支援！在 `domains` 陣列中加入所有網域即可。

### Q: Windows 家用版可以用嗎？
A: 可以！只要有 Python 和 win-acme 就能使用。

### Q: 憑證會自動更新嗎？
A: 會！設定好工作排程器或 Cron 後就全自動了。

## 參考資源

- [Let's Encrypt 官方網站](https://letsencrypt.org/)
- [win-acme GitHub](https://github.com/win-acme/win-acme)
- [Certbot 官方文件](https://certbot.eff.org/)
- [XAMPP 官方網站](https://www.apachefriends.org/)
- [WordPress HTTPS 指南](https://wordpress.org/support/article/https-for-wordpress/)

## 授權條款

MIT License

## 貢獻

歡迎提交 Issue 和 Pull Request！

---

**專為 XAMPP WordPress 使用者設計** 🚀
