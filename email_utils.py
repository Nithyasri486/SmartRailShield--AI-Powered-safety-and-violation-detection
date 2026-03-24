import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from datetime import datetime, timedelta

# Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "nithyasri482006sri@gmail.com"  # Placeholder
SENDER_PASSWORD = "dlwsvsljsyuubzgl"    # Placeholder
RECEIVER_EMAIL = "sshunmugapriya49@gmail.com" # Placeholder

def generate_fine_assets(plate_number, amount=500):
    """Generates QR code and PDF for the fine"""
    try:
        import qrcode
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except ImportError:
        print("⚠️ qrcode or reportlab not installed. Cannot generate fine assets.")
        return None, None, None

    curr_time = datetime.now()
    due_date = curr_time + timedelta(days=10)
    due_date_str = due_date.strftime("%Y-%m-%d")
    detection_time_str = curr_time.strftime("%Y-%m-%d %H:%M:%S")

    # 1. Create QR Code
    # Placeholder UPI link
    payment_data = f"upi://pay?pa=nithyasri482006sri@oksbi&pn=Nithyasri&am={amount}&cu=INR&tn=Fine for {plate_number}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(payment_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    qr_path = f"fine_qr_{plate_number.replace('-', '_')}.png"
    qr_img.save(qr_path)

    # 2. Create PDF
    pdf_path = f"fine_notice_{plate_number.replace('-', '_')}.pdf"
    c = canvas.Canvas(pdf_path, pagesize=letter)
    
    # Title
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(300, 750, "SMART RAIL SHIELD")
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(300, 720, "OFFICIAL FINE NOTICE")
    
    # Details
    c.setFont("Helvetica", 12)
    c.drawString(100, 680, f"Detection Time : {detection_time_str}")
    c.drawString(100, 660, f"Vehicle Plate  : {plate_number}")
    c.drawString(100, 640, f"Fine Amount    : Rs. {amount}")
    
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(0.8, 0, 0) # Red color for due date
    c.drawString(100, 610, f"PAYMENT DUE DATE: {due_date_str}")
    c.setFillColorRGB(0, 0, 0) # Back to black
    
    c.setFont("Helvetica", 11)
    c.drawString(100, 580, "This fine has been automatically generated for unauthorized access or traffic violation.")
    c.drawString(100, 565, "Please scan the QR code below using any UPI app (GPay, PhonePe, Paytm, etc.) to pay.")
    
    # Draw QR image
    c.drawImage(qr_path, 150, 250, width=250, height=250)
    
    # Footer
    c.setFont("Helvetica-Oblique", 10)
    c.drawCentredString(300, 200, "This is a computer-generated document and does not require a signature.")
    c.drawCentredString(300, 185, "© 2026 SmartRail Shield Security Systems")
    
    c.save()

    return qr_path, pdf_path, due_date_str

def send_email_alert(subject, body, plate_number=None):
    """
    Sends an email alert. 
    If plate_number is provided, it attaches a QR code and PDF fine notice.
    """
    # If using default placeholders, just print to console
    if "placeholder" in SENDER_EMAIL or "smartrailshield@gmail.com" in SENDER_EMAIL:
        print(f"📧 EMAIL MOCK: To: {RECEIVER_EMAIL} | Subject: {subject}")
        if plate_number:
            print(f"📎 Would attach fine notice for plate: {plate_number}")
        return True

    qr_path = None
    pdf_path = None
    
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = subject

        # Check if we should include fine assets
        if plate_number:
            qr_path, pdf_path, due_date_str = generate_fine_assets(plate_number)
            if qr_path and pdf_path:
                body += f"\n\n--- FINE INFORMATION ---\n"
                body += f"A fine of Rs. 500 has been issued to vehicle {plate_number}.\n"
                body += f"Due Date: {due_date_str}\n"
                body += f"Please scan the attached QR code or refer to the PDF for payment instructions."

        msg.attach(MIMEText(body, 'plain'))

        # Attach PDF
        if pdf_path and os.path.exists(pdf_path):
            try:
                with open(pdf_path, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header("Content-Disposition", f"attachment; filename= {os.path.basename(pdf_path)}")
                    msg.attach(part)
            except Exception as e:
                print(f"Error attaching PDF: {e}")

        # Attach QR Image
        if qr_path and os.path.exists(qr_path):
            try:
                with open(qr_path, "rb") as attachment:
                    part = MIMEBase("image", "png")
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header("Content-Disposition", f"attachment; filename= {os.path.basename(qr_path)}")
                    msg.attach(part)
            except Exception as e:
                print(f"Error attaching QR: {e}")

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, text)
        server.quit()
        
        print(f"✅ Email sent successfully to {RECEIVER_EMAIL}")
        
        # Cleanup
        if qr_path and os.path.exists(qr_path): os.remove(qr_path)
        if pdf_path and os.path.exists(pdf_path): os.remove(pdf_path)
            
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {str(e)}")
        # Cleanup on error
        if qr_path and os.path.exists(qr_path): os.remove(qr_path)
        if pdf_path and os.path.exists(pdf_path): os.remove(pdf_path)
        return False
