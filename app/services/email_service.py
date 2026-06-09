import os
import smtplib

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from dotenv import load_dotenv


load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")


def send_briefing_email(subject: str, body: str):
    if not EMAIL_ADDRESS:
        raise ValueError("EMAIL_ADDRESS가 설정되지 않았습니다.")

    if not EMAIL_APP_PASSWORD:
        raise ValueError("EMAIL_APP_PASSWORD가 설정되지 않았습니다.")

    msg = MIMEMultipart()

    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_ADDRESS
    msg["Subject"] = subject

    msg.attach(
        MIMEText(
            body,
            "plain",
            "utf-8",
        )
    )

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()

        server.login(
            EMAIL_ADDRESS,
            EMAIL_APP_PASSWORD,
        )

        server.send_message(msg)

    print("이메일 발송 완료")