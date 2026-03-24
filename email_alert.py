import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time

# ---------------- SMTP Configuration ----------------
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

EMAIL_ADDRESS = "YOUR_SENDER_EMAIL@gmail.com"
EMAIL_PASSWORD = "YOUR_GMAIL_APP_PASSWORD"
TO_EMAIL_ADDRESS = "YOUR_RECEIVER_EMAIL@gmail.com"

# ---------------- Alert Cooldown ----------------
LAST_EMAIL_TIME = 0
EMAIL_COOLDOWN = 60   # seconds (send max once per minute)

# ---------------- Email Alert Function ----------------
def send_email_alert(subject: str, message: str):
    global LAST_EMAIL_TIME

    current_time = time.time()
    if current_time - LAST_EMAIL_TIME < EMAIL_COOLDOWN:
        return  # Skip sending email (cooldown active)

    try:
        # Create email
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = TO_EMAIL_ADDRESS
        msg['Subject'] = subject

        msg.attach(MIMEText(message, 'plain'))

        # Connect to Gmail SMTP
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.ehlo()
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

        server.sendmail(
            EMAIL_ADDRESS,
            TO_EMAIL_ADDRESS,
            msg.as_string()
        )

        server.quit()

        LAST_EMAIL_TIME = current_time
        print(f"[{time.strftime('%H:%M:%S')}] 📧 Email sent: {subject}")

    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] ❌ Email failed: {e}")


# ---------------- Standalone Test ----------------
if __name__ == "__main__":
    send_email_alert(
        "Railway Obstacle Alert Test",
        "Obstacle detected on railway track. Immediate attention required."
    )
