import smtplib
import traceback
from email.mime.text import MIMEText
from email.utils import formatdate
from email.mime.multipart import MIMEMultipart
from loguru import logger
from typing import List, Dict, Optional

def send_email_notification(
    email_config: Dict,
    subject: str,
    body: str,
    is_html: bool = False
) -> None:
    """
    发送邮件通知
    
    :param email_config: 邮件配置字典
    :param subject: 邮件主题
    :param body: 邮件正文
    :param is_html: 是否为HTML格式邮件
    """
    # 检查是否启用邮件通知
    if not email_config.get('enable', False):
        logger.info("邮件通知已禁用，不发送通知")
        return
    
    try:
        if is_html:
            # 创建多部分邮件消息
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = email_config.get('sender')
            msg['To'] = ', '.join(email_config.get('recipients', []))
            msg['Date'] = formatdate(localtime=True)
            
            # 添加文本和HTML部分
            text_part = MIMEText(body, 'plain', 'utf-8')
            html_part = MIMEText(body, 'html', 'utf-8')
            msg.attach(text_part)
            msg.attach(html_part)
        else:
            # 创建纯文本邮件消息
            msg = MIMEText(body, 'plain', 'utf-8')
            msg['Subject'] = subject
            msg['From'] = email_config.get('sender')
            msg['To'] = ', '.join(email_config.get('recipients', []))
            msg['Date'] = formatdate(localtime=True)
        
        server_port = email_config.get('smtp_port', 465)
        server = smtplib.SMTP_SSL(
            email_config.get('smtp_server'),
            server_port,
            timeout=10,
        )

        # server.ehlo()
        server.login(
            email_config.get('smtp_username'),
            email_config.get('smtp_password'),
        )
    
        server.send_message(msg)

        server.quit()
        
        logger.info("邮件通知发送成功")
    except Exception as e:
        logger.error(f"发送邮件通知失败: {str(e)}")
        logger.debug(traceback.format_exc())
        raise
