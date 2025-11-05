@echo off
REM XAMPP Let's Encrypt 憑證自動更新 - Windows 工作排程器設定腳本
REM 請以系統管理員身份執行此批次檔

echo ============================================
echo XAMPP Let's Encrypt 憑證自動更新
echo Windows 工作排程器設定
echo ============================================
echo.

REM 檢查是否以管理員身份執行
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo 錯誤: 此腳本需要系統管理員權限
    echo 請以系統管理員身份執行此批次檔
    pause
    exit /b 1
)

REM 設定安裝目錄
set INSTALL_DIR=C:\xampp-cert-renewal

echo [1/4] 建立安裝目錄...
if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%"
    echo 已建立目錄: %INSTALL_DIR%
) else (
    echo 目錄已存在: %INSTALL_DIR%
)

echo.
echo [2/4] 複製檔案...
copy /Y xampp_cert_renewal.py "%INSTALL_DIR%\"
if not exist "%INSTALL_DIR%\xampp_config.json" (
    copy /Y xampp_config.example.json "%INSTALL_DIR%\xampp_config.json"
    echo 已建立設定檔: %INSTALL_DIR%\xampp_config.json
    echo 請編輯此檔案以配置您的網域和 XAMPP 路徑
) else (
    echo 設定檔已存在，保留原有設定
)

REM 建立日誌目錄
if not exist "%INSTALL_DIR%\logs" (
    mkdir "%INSTALL_DIR%\logs"
)

echo.
echo [3/4] 設定工作排程器...

REM 複製並修改 XML 檔案
copy /Y xampp_task_scheduler.xml "%INSTALL_DIR%\task.xml"

REM 匯入工作排程
schtasks /Create /TN "XAMPP Certificate Renewal" /XML "%INSTALL_DIR%\task.xml" /F

if %errorLevel% equ 0 (
    echo 工作排程設定成功！
    echo.
    echo 排程詳細資訊:
    schtasks /Query /TN "XAMPP Certificate Renewal" /V /FO LIST
) else (
    echo 工作排程設定失敗
    echo 請手動使用「工作排程器」設定
)

echo.
echo [4/4] 安裝完成！
echo.
echo ============================================
echo 下一步操作:
echo ============================================
echo 1. 編輯設定檔: %INSTALL_DIR%\xampp_config.json
echo 2. 設定您的網域名稱和 XAMPP 路徑
echo 3. 安裝 win-acme: https://github.com/win-acme/win-acme/releases
echo 4. 使用 win-acme 取得初始憑證
echo 5. 執行測試: python %INSTALL_DIR%\xampp_cert_renewal.py --dry-run
echo.
echo 查看工作排程:
echo   - 開啟「工作排程器」
echo   - 尋找「XAMPP Certificate Renewal」
echo.
echo 手動執行:
echo   schtasks /Run /TN "XAMPP Certificate Renewal"
echo.
echo 詳細說明請參閱 README_XAMPP.md
echo ============================================
echo.

pause
