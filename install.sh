#!/bin/bash
# Let's Encrypt 憑證自動更新工具安裝腳本

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 檢查是否為 root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}錯誤: 此腳本需要 root 權限執行${NC}"
    echo "請使用: sudo $0"
    exit 1
fi

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Let's Encrypt 憑證自動更新工具${NC}"
echo -e "${GREEN}安裝腳本${NC}"
echo -e "${GREEN}================================${NC}"
echo

# 安裝目錄
INSTALL_DIR="/opt/cert-renewal"
LOG_DIR="/var/log/cert-renewal"

# 步驟 1: 檢查並安裝依賴
echo -e "${YELLOW}[1/6] 檢查系統依賴...${NC}"

if ! command -v python3 &> /dev/null; then
    echo "正在安裝 Python 3..."
    if [ -f /etc/debian_version ]; then
        apt update
        apt install -y python3 python3-pip
    elif [ -f /etc/redhat-release ]; then
        yum install -y python3 python3-pip
    else
        echo -e "${RED}無法辨識的系統，請手動安裝 Python 3${NC}"
        exit 1
    fi
else
    echo "✓ Python 3 已安裝"
fi

if ! command -v certbot &> /dev/null; then
    echo "正在安裝 Certbot..."
    if [ -f /etc/debian_version ]; then
        apt install -y certbot
    elif [ -f /etc/redhat-release ]; then
        yum install -y certbot
    else
        echo -e "${RED}無法辨識的系統，請手動安裝 Certbot${NC}"
        exit 1
    fi
else
    echo "✓ Certbot 已安裝"
fi

# 步驟 2: 詢問使用的網頁伺服器
echo
echo -e "${YELLOW}[2/6] 選擇您使用的網頁伺服器${NC}"
echo "1) Nginx"
echo "2) Apache"
echo "3) 其他/不安裝插件"
read -p "請選擇 [1-3]: " webserver_choice

case $webserver_choice in
    1)
        echo "正在安裝 Certbot Nginx 插件..."
        if [ -f /etc/debian_version ]; then
            apt install -y python3-certbot-nginx
        elif [ -f /etc/redhat-release ]; then
            yum install -y python3-certbot-nginx
        fi
        ;;
    2)
        echo "正在安裝 Certbot Apache 插件..."
        if [ -f /etc/debian_version ]; then
            apt install -y python3-certbot-apache
        elif [ -f /etc/redhat-release ]; then
            yum install -y python3-certbot-apache
        fi
        ;;
    3)
        echo "跳過網頁伺服器插件安裝"
        ;;
    *)
        echo -e "${YELLOW}無效選擇，跳過插件安裝${NC}"
        ;;
esac

# 步驟 3: 安裝 Python 依賴
echo
echo -e "${YELLOW}[3/6] 安裝 Python 依賴套件...${NC}"
pip3 install -r requirements.txt

# 步驟 4: 創建安裝目錄
echo
echo -e "${YELLOW}[4/6] 創建安裝目錄...${NC}"
mkdir -p "$INSTALL_DIR"
mkdir -p "$LOG_DIR"

# 複製檔案
cp cert_renewal.py "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/cert_renewal.py"

if [ ! -f "$INSTALL_DIR/config.json" ]; then
    cp config.example.json "$INSTALL_DIR/config.json"
    echo "✓ 已創建設定檔: $INSTALL_DIR/config.json"
    echo -e "${YELLOW}  請編輯此檔案以配置您的網域和通知設定${NC}"
else
    echo "✓ 設定檔已存在，保留原有設定"
fi

# 設定權限
chmod 600 "$INSTALL_DIR/config.json"
chown root:root "$INSTALL_DIR/config.json"

echo "✓ 檔案已安裝到 $INSTALL_DIR"

# 步驟 5: 設定自動執行
echo
echo -e "${YELLOW}[5/6] 設定自動執行排程${NC}"
echo "1) 使用 systemd timer (推薦)"
echo "2) 使用 crontab"
echo "3) 不設定自動執行"
read -p "請選擇 [1-3]: " schedule_choice

case $schedule_choice in
    1)
        if command -v systemctl &> /dev/null; then
            cp cert-renewal.service /etc/systemd/system/
            cp cert-renewal.timer /etc/systemd/system/
            systemctl daemon-reload
            systemctl enable cert-renewal.timer
            systemctl start cert-renewal.timer
            echo "✓ systemd timer 已啟用"
            echo "  使用 'systemctl status cert-renewal.timer' 檢查狀態"
        else
            echo -e "${RED}此系統不支援 systemd，請改用 crontab${NC}"
        fi
        ;;
    2)
        CRON_CMD="0 2,14 * * * /usr/bin/python3 $INSTALL_DIR/cert_renewal.py --config $INSTALL_DIR/config.json >> $LOG_DIR/cron.log 2>&1"
        (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
        echo "✓ Crontab 已設定 (每天 2:00 和 14:00 執行)"
        ;;
    3)
        echo "跳過自動執行設定"
        ;;
    *)
        echo -e "${YELLOW}無效選擇，跳過自動執行設定${NC}"
        ;;
esac

# 步驟 6: 測試安裝
echo
echo -e "${YELLOW}[6/6] 測試安裝...${NC}"
read -p "是否要執行測試模式 (dry-run)? [y/N]: " test_choice

if [[ "$test_choice" =~ ^[Yy]$ ]]; then
    echo "執行測試..."
    python3 "$INSTALL_DIR/cert_renewal.py" --config "$INSTALL_DIR/config.json" --dry-run || true
fi

# 完成
echo
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}安裝完成！${NC}"
echo -e "${GREEN}================================${NC}"
echo
echo "下一步操作:"
echo "1. 編輯設定檔: nano $INSTALL_DIR/config.json"
echo "2. 確保已使用 certbot 取得初始憑證"
echo "3. 執行測試: python3 $INSTALL_DIR/cert_renewal.py --dry-run"
echo
echo "詳細說明請參閱 README.md"
echo
