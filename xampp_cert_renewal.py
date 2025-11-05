#!/usr/bin/env python3
"""
Let's Encrypt Certificate Auto-Renewal Tool for XAMPP
XAMPP 環境專用的 Let's Encrypt 憑證自動更新工具
支援 Windows、Linux 和 macOS
"""

import os
import sys
import subprocess
import logging
import json
import platform
import shutil
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class XAMPPCertificateRenewer:
    """XAMPP 環境的憑證更新管理器"""

    def __init__(self, config_path: str = "xampp_config.json"):
        """
        初始化 XAMPP 憑證更新器

        Args:
            config_path: 設定檔路徑
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.platform = platform.system()  # Windows, Linux, Darwin (macOS)
        self.xampp_path = self._detect_xampp_path()
        self._setup_logging()

    def _load_config(self) -> Dict:
        """載入設定檔"""
        if not os.path.exists(self.config_path):
            print(f"錯誤: 找不到設定檔 {self.config_path}")
            print("請使用 xampp_config.example.json 作為範本創建 xampp_config.json")
            sys.exit(1)

        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _detect_xampp_path(self) -> str:
        """自動檢測 XAMPP 安裝路徑"""
        # 使用設定檔中的路徑
        if 'xampp_path' in self.config and self.config['xampp_path']:
            xampp_path = self.config['xampp_path']
            if os.path.exists(xampp_path):
                return xampp_path

        # 自動檢測常見路徑
        common_paths = {
            'Windows': [
                'C:\\xampp',
                'D:\\xampp',
                'C:\\Program Files\\xampp',
                'C:\\Program Files (x86)\\xampp'
            ],
            'Linux': [
                '/opt/lampp',
                '/opt/xampp',
                '/usr/local/xampp'
            ],
            'Darwin': [  # macOS
                '/Applications/XAMPP',
                '/opt/lampp'
            ]
        }

        paths_to_check = common_paths.get(self.platform, [])

        for path in paths_to_check:
            if os.path.exists(path):
                print(f"找到 XAMPP 安裝於: {path}")
                return path

        print(f"錯誤: 無法找到 XAMPP 安裝路徑")
        print(f"請在設定檔中指定 xampp_path")
        sys.exit(1)

    def _setup_logging(self):
        """設置日誌記錄"""
        log_dir = self.config.get('log_directory', './logs')
        os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(log_dir, 'xampp_renewal.log')
        log_level = getattr(logging, self.config.get('log_level', 'INFO'))

        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

    def get_cert_path(self, domain: str) -> str:
        """取得憑證路徑"""
        if self.platform == 'Windows':
            # Windows 使用 win-acme 或 certbot
            cert_base = self.config.get('cert_base_path', 'C:\\ProgramData\\letsencrypt-win-simple')
        else:
            # Linux/macOS 使用 certbot
            cert_base = '/etc/letsencrypt/live'

        return os.path.join(cert_base, domain)

    def check_certificate_expiry(self, domain: str) -> Optional[int]:
        """
        檢查憑證到期天數

        Args:
            domain: 網域名稱

        Returns:
            剩餘天數，若無法取得則返回 None
        """
        cert_path = os.path.join(self.get_cert_path(domain), 'cert.pem')

        if not os.path.exists(cert_path):
            self.logger.warning(f"憑證檔案不存在: {cert_path}")
            return None

        try:
            # 使用 openssl 檢查憑證
            openssl_cmd = 'openssl'
            if self.platform == 'Windows' and os.path.exists(os.path.join(self.xampp_path, 'apache', 'bin', 'openssl.exe')):
                openssl_cmd = os.path.join(self.xampp_path, 'apache', 'bin', 'openssl.exe')

            cmd = [
                openssl_cmd, 'x509', '-in', cert_path,
                '-noout', '-enddate'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # 解析到期日期
            expiry_str = result.stdout.strip().replace('notAfter=', '')
            expiry_date = datetime.strptime(expiry_str, '%b %d %H:%M:%S %Y %Z')

            days_remaining = (expiry_date - datetime.now()).days
            self.logger.info(f"網域 {domain} 的憑證還有 {days_remaining} 天到期")

            return days_remaining

        except subprocess.CalledProcessError as e:
            self.logger.error(f"檢查憑證時發生錯誤: {e}")
            return None
        except Exception as e:
            self.logger.error(f"解析憑證日期時發生錯誤: {e}")
            return None

    def renew_certificate_windows(self, domain: str) -> bool:
        """
        在 Windows 上使用 win-acme 更新憑證

        Args:
            domain: 網域名稱

        Returns:
            更新是否成功
        """
        self.logger.info(f"使用 win-acme 更新憑證: {domain}")

        # win-acme 路徑
        wacs_path = self.config.get('win_acme_path', 'C:\\Tools\\win-acme\\wacs.exe')

        if not os.path.exists(wacs_path):
            self.logger.error(f"找不到 win-acme: {wacs_path}")
            self.logger.info("請從 https://github.com/win-acme/win-acme/releases 下載")
            return False

        try:
            # 執行 win-acme 更新
            cmd = [wacs_path, '--renew', '--baseuri', 'https://acme-v02.api.letsencrypt.org/']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            self.logger.info(f"憑證更新成功: {domain}")
            self.logger.debug(f"win-acme 輸出: {result.stdout}")

            return True

        except subprocess.CalledProcessError as e:
            self.logger.error(f"憑證更新失敗: {domain}")
            self.logger.error(f"錯誤訊息: {e.stderr}")
            return False

    def renew_certificate_linux(self, domain: str) -> bool:
        """
        在 Linux/macOS 上使用 certbot 更新憑證

        Args:
            domain: 網域名稱

        Returns:
            更新是否成功
        """
        self.logger.info(f"使用 certbot 更新憑證: {domain}")

        try:
            cmd = ['certbot', 'renew', '--cert-name', domain, '--quiet']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            self.logger.info(f"憑證更新成功: {domain}")
            self.logger.debug(f"Certbot 輸出: {result.stdout}")

            return True

        except subprocess.CalledProcessError as e:
            self.logger.error(f"憑證更新失敗: {domain}")
            self.logger.error(f"錯誤訊息: {e.stderr}")
            return False

    def update_apache_ssl_config(self, domain: str) -> bool:
        """
        更新 XAMPP Apache 的 SSL 設定

        Args:
            domain: 網域名稱

        Returns:
            更新是否成功
        """
        self.logger.info(f"更新 Apache SSL 設定: {domain}")

        # SSL 設定檔路徑
        ssl_conf_path = os.path.join(
            self.xampp_path,
            'apache',
            'conf',
            'extra',
            'httpd-ssl.conf'
        )

        if not os.path.exists(ssl_conf_path):
            self.logger.error(f"找不到 SSL 設定檔: {ssl_conf_path}")
            return False

        try:
            # 備份原始設定檔
            backup_path = f"{ssl_conf_path}.backup.{datetime.now().strftime('%Y%m%d%H%M%S')}"
            shutil.copy2(ssl_conf_path, backup_path)
            self.logger.info(f"已備份設定檔到: {backup_path}")

            # 讀取設定檔
            with open(ssl_conf_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 取得新憑證路徑
            cert_dir = self.get_cert_path(domain)
            cert_file = os.path.join(cert_dir, 'cert.pem')
            key_file = os.path.join(cert_dir, 'privkey.pem')
            chain_file = os.path.join(cert_dir, 'chain.pem')

            # 更新憑證路徑（針對 Windows 路徑格式）
            if self.platform == 'Windows':
                cert_file = cert_file.replace('\\', '/')
                key_file = key_file.replace('\\', '/')
                chain_file = chain_file.replace('\\', '/')

            # 替換憑證路徑
            content = re.sub(
                r'SSLCertificateFile\s+"[^"]*"',
                f'SSLCertificateFile "{cert_file}"',
                content
            )
            content = re.sub(
                r'SSLCertificateKeyFile\s+"[^"]*"',
                f'SSLCertificateKeyFile "{key_file}"',
                content
            )
            content = re.sub(
                r'SSLCertificateChainFile\s+"[^"]*"',
                f'SSLCertificateChainFile "{chain_file}"',
                content
            )

            # 寫回設定檔
            with open(ssl_conf_path, 'w', encoding='utf-8') as f:
                f.write(content)

            self.logger.info("Apache SSL 設定更新成功")
            return True

        except Exception as e:
            self.logger.error(f"更新 Apache SSL 設定失敗: {e}")
            return False

    def restart_apache(self) -> bool:
        """
        重新啟動 XAMPP Apache 服務

        Returns:
            重啟是否成功
        """
        self.logger.info("重新啟動 XAMPP Apache...")

        try:
            if self.platform == 'Windows':
                # Windows: 使用 XAMPP 控制面板或批次檔
                apache_stop = os.path.join(self.xampp_path, 'apache_stop.bat')
                apache_start = os.path.join(self.xampp_path, 'apache_start.bat')

                if os.path.exists(apache_stop) and os.path.exists(apache_start):
                    subprocess.run([apache_stop], shell=True, check=True)
                    import time
                    time.sleep(2)
                    subprocess.run([apache_start], shell=True, check=True)
                else:
                    # 使用 net 命令（如果 Apache 安裝為服務）
                    subprocess.run(['net', 'stop', 'Apache2.4'], shell=True, check=False)
                    import time
                    time.sleep(2)
                    subprocess.run(['net', 'start', 'Apache2.4'], shell=True, check=True)

            else:
                # Linux/macOS: 使用 lampp 命令
                lampp_cmd = os.path.join(self.xampp_path, 'lampp')
                subprocess.run([lampp_cmd, 'restart'], check=True)

            self.logger.info("Apache 重新啟動成功")
            return True

        except subprocess.CalledProcessError as e:
            self.logger.error(f"重新啟動 Apache 失敗: {e}")
            return False

    def run(self, dry_run: bool = False):
        """
        執行憑證更新流程

        Args:
            dry_run: 是否為測試模式
        """
        self.logger.info("=" * 60)
        self.logger.info("開始執行 XAMPP Let's Encrypt 憑證自動更新")
        self.logger.info(f"作業系統: {self.platform}")
        self.logger.info(f"XAMPP 路徑: {self.xampp_path}")
        self.logger.info("=" * 60)

        domains = self.config.get('domains', [])
        renewal_threshold = self.config.get('renewal_threshold_days', 30)

        if not domains:
            self.logger.warning("設定檔中沒有指定任何網域")
            return

        renewal_needed = []
        renewal_success = []
        renewal_failed = []

        # 檢查每個網域的憑證
        for domain in domains:
            days_remaining = self.check_certificate_expiry(domain)

            if days_remaining is None:
                self.logger.warning(f"無法檢查網域 {domain} 的憑證，將嘗試更新")
                renewal_needed.append(domain)
            elif days_remaining <= renewal_threshold:
                self.logger.info(f"網域 {domain} 需要更新 (剩餘 {days_remaining} 天)")
                renewal_needed.append(domain)
            else:
                self.logger.info(f"網域 {domain} 不需要更新 (剩餘 {days_remaining} 天)")

        # 更新需要更新的憑證
        if renewal_needed and not dry_run:
            for domain in renewal_needed:
                # 根據作業系統選擇更新方式
                if self.platform == 'Windows':
                    success = self.renew_certificate_windows(domain)
                else:
                    success = self.renew_certificate_linux(domain)

                if success:
                    renewal_success.append(domain)
                    # 更新 Apache 設定
                    self.update_apache_ssl_config(domain)
                else:
                    renewal_failed.append(domain)

            # 如果有成功更新的憑證，重新啟動 Apache
            if renewal_success:
                self.logger.info("憑證已更新，重新啟動 Apache...")
                self.restart_apache()
        elif renewal_needed and dry_run:
            self.logger.info("測試模式：以下網域需要更新")
            for domain in renewal_needed:
                self.logger.info(f"  - {domain}")
        else:
            self.logger.info("所有憑證都在有效期限內，無需更新")

        # 產生摘要報告
        summary = self._generate_summary(
            domains, renewal_needed, renewal_success, renewal_failed
        )

        self.logger.info("\n" + summary)

        self.logger.info("=" * 60)
        self.logger.info("憑證更新流程完成")
        self.logger.info("=" * 60)

    def _generate_summary(
        self,
        all_domains: List[str],
        renewal_needed: List[str],
        renewal_success: List[str],
        renewal_failed: List[str]
    ) -> str:
        """產生執行摘要報告"""
        summary_lines = [
            "",
            "=" * 60,
            "憑證更新摘要報告",
            "=" * 60,
            f"總共監控的網域數: {len(all_domains)}",
            f"需要更新的網域數: {len(renewal_needed)}",
            f"更新成功的網域數: {len(renewal_success)}",
            f"更新失敗的網域數: {len(renewal_failed)}",
            ""
        ]

        if renewal_success:
            summary_lines.append("✓ 更新成功:")
            for domain in renewal_success:
                summary_lines.append(f"   - {domain}")
            summary_lines.append("")

        if renewal_failed:
            summary_lines.append("✗ 更新失敗:")
            for domain in renewal_failed:
                summary_lines.append(f"   - {domain}")
            summary_lines.append("")

        return "\n".join(summary_lines)


def main():
    """主程式進入點"""
    import argparse

    parser = argparse.ArgumentParser(
        description='XAMPP 環境專用的 Let\'s Encrypt 憑證自動更新工具'
    )
    parser.add_argument(
        '--config',
        default='xampp_config.json',
        help='設定檔路徑 (預設: xampp_config.json)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='測試模式，不會實際更新憑證'
    )

    args = parser.parse_args()

    try:
        renewer = XAMPPCertificateRenewer(config_path=args.config)
        renewer.run(dry_run=args.dry_run)
        sys.exit(0)

    except KeyboardInterrupt:
        print("\n程式被使用者中斷")
        sys.exit(1)

    except Exception as e:
        print(f"發生錯誤: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
