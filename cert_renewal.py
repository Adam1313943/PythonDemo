#!/usr/bin/env python3
"""
Let's Encrypt Certificate Auto-Renewal Tool
自動更新 Let's Encrypt SSL/TLS 憑證
"""

import os
import sys
import subprocess
import logging
import json
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Dict, List, Optional


class CertificateRenewer:
    """管理 Let's Encrypt 憑證更新的核心類別"""

    def __init__(self, config_path: str = "config.json"):
        """
        初始化憑證更新器

        Args:
            config_path: 設定檔路徑
        """
        self.config_path = config_path
        self.config = self._load_config()
        self._setup_logging()

    def _load_config(self) -> Dict:
        """載入設定檔"""
        if not os.path.exists(self.config_path):
            print(f"錯誤: 找不到設定檔 {self.config_path}")
            print("請使用 config.example.json 作為範本創建 config.json")
            sys.exit(1)

        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _setup_logging(self):
        """設置日誌記錄"""
        log_dir = self.config.get('log_directory', '/var/log/cert-renewal')
        os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(log_dir, 'renewal.log')
        log_level = getattr(logging, self.config.get('log_level', 'INFO'))

        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

    def check_certificate_expiry(self, domain: str) -> Optional[int]:
        """
        檢查憑證到期天數

        Args:
            domain: 網域名稱

        Returns:
            剩餘天數，若無法取得則返回 None
        """
        cert_path = f"/etc/letsencrypt/live/{domain}/cert.pem"

        if not os.path.exists(cert_path):
            self.logger.warning(f"憑證檔案不存在: {cert_path}")
            return None

        try:
            cmd = [
                'openssl', 'x509', '-in', cert_path,
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

    def renew_certificate(self, domain: str, dry_run: bool = False) -> bool:
        """
        更新指定網域的憑證

        Args:
            domain: 網域名稱
            dry_run: 是否為測試模式

        Returns:
            更新是否成功
        """
        self.logger.info(f"開始更新憑證: {domain} (dry_run={dry_run})")

        cmd = ['certbot', 'renew']

        if dry_run:
            cmd.append('--dry-run')

        # 添加額外的 certbot 參數
        certbot_args = self.config.get('certbot_args', [])
        cmd.extend(certbot_args)

        # 指定特定網域
        if domain:
            cmd.extend(['--cert-name', domain])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            self.logger.info(f"憑證更新成功: {domain}")
            self.logger.debug(f"Certbot 輸出: {result.stdout}")

            return True

        except subprocess.CalledProcessError as e:
            self.logger.error(f"憑證更新失敗: {domain}")
            self.logger.error(f"錯誤訊息: {e.stderr}")
            return False

    def reload_services(self) -> bool:
        """
        重新載入需要更新憑證的服務

        Returns:
            是否成功重新載入所有服務
        """
        services = self.config.get('reload_services', [])

        if not services:
            self.logger.info("沒有需要重新載入的服務")
            return True

        all_success = True

        for service in services:
            try:
                self.logger.info(f"重新載入服務: {service}")
                subprocess.run(
                    ['systemctl', 'reload', service],
                    check=True,
                    capture_output=True
                )
                self.logger.info(f"服務 {service} 重新載入成功")

            except subprocess.CalledProcessError as e:
                self.logger.error(f"重新載入服務 {service} 失敗: {e.stderr}")
                all_success = False

        return all_success

    def send_notification(self, subject: str, message: str):
        """
        發送電子郵件通知

        Args:
            subject: 郵件主旨
            message: 郵件內容
        """
        email_config = self.config.get('email_notifications')

        if not email_config or not email_config.get('enabled', False):
            self.logger.debug("電子郵件通知未啟用")
            return

        try:
            msg = MIMEMultipart()
            msg['From'] = email_config['from_addr']
            msg['To'] = ', '.join(email_config['to_addrs'])
            msg['Subject'] = subject

            msg.attach(MIMEText(message, 'plain', 'utf-8'))

            server = smtplib.SMTP(
                email_config['smtp_server'],
                email_config.get('smtp_port', 587)
            )
            server.starttls()

            if email_config.get('username') and email_config.get('password'):
                server.login(email_config['username'], email_config['password'])

            server.send_message(msg)
            server.quit()

            self.logger.info(f"已發送通知郵件: {subject}")

        except Exception as e:
            self.logger.error(f"發送郵件失敗: {e}")

    def run(self, dry_run: bool = False):
        """
        執行憑證更新流程

        Args:
            dry_run: 是否為測試模式
        """
        self.logger.info("=" * 60)
        self.logger.info("開始執行 Let's Encrypt 憑證自動更新")
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
        if renewal_needed:
            for domain in renewal_needed:
                if self.renew_certificate(domain, dry_run):
                    renewal_success.append(domain)
                else:
                    renewal_failed.append(domain)

            # 如果有成功更新的憑證，重新載入服務
            if renewal_success and not dry_run:
                self.logger.info("重新載入相關服務...")
                self.reload_services()
        else:
            self.logger.info("所有憑證都在有效期限內，無需更新")

        # 產生摘要報告
        summary = self._generate_summary(
            domains, renewal_needed, renewal_success, renewal_failed
        )

        self.logger.info("\n" + summary)

        # 發送通知
        if renewal_failed:
            self.send_notification(
                "⚠️ Let's Encrypt 憑證更新失敗",
                summary
            )
        elif renewal_success:
            self.send_notification(
                "✅ Let's Encrypt 憑證更新成功",
                summary
            )

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
            summary_lines.append("✅ 更新成功:")
            for domain in renewal_success:
                summary_lines.append(f"   - {domain}")
            summary_lines.append("")

        if renewal_failed:
            summary_lines.append("❌ 更新失敗:")
            for domain in renewal_failed:
                summary_lines.append(f"   - {domain}")
            summary_lines.append("")

        return "\n".join(summary_lines)


def main():
    """主程式進入點"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Let\'s Encrypt 憑證自動更新工具'
    )
    parser.add_argument(
        '--config',
        default='config.json',
        help='設定檔路徑 (預設: config.json)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='測試模式，不會實際更新憑證'
    )

    args = parser.parse_args()

    try:
        renewer = CertificateRenewer(config_path=args.config)
        renewer.run(dry_run=args.dry_run)
        sys.exit(0)

    except KeyboardInterrupt:
        print("\n程式被使用者中斷")
        sys.exit(1)

    except Exception as e:
        print(f"發生錯誤: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
