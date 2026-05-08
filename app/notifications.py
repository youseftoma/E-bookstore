import smtplib
from email.mime.text import MIMEText
from .config import settings
# Gmail credentials
sender = settings.SEDNER_EMAIL
password = settings.EMAIL_PASSWORD

def send_verify_gmail(receiver, verify_url):
    # Create the HTML message
    html_content = f"""
    <html>
      <body>
        <p>Hello,<br>
           Please verify your email by clicking the link below:<br><br>
           
           <div style="text-align:center; margin-top:20px;">
                <a href="{verify_url}" 
                    style="display:inline-block;
                            padding:12px 24px;
                            font-size:16px;
                            color:#ffffff;
                            background-color:#007BFF;
                            text-decoration:none;
                            border-radius:6px;">
                    Verify Email
                </a>
            </div>
        </p>
      </body>
    </html>
    """

    # Build MIMEText object
    msg = MIMEText(html_content, "html")
    msg["Subject"] = "Email Verification"
    msg["From"] = sender
    msg["To"] = receiver

    # Send email through Gmail’s SMTP server
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, receiver, msg.as_string())
        print("Verification email sent successfully!")
        return True
    except Exception as e:
        print("Error sending email:", e)
        return False