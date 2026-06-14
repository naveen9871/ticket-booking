import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings


def _build_booking_html(ticket: dict) -> str:
    t = ticket.get("ticket", ticket)
    seats = t.get("seats", "")
    movie = t.get("movie", "")
    theatre = t.get("theatre", "")
    city = t.get("city", "")
    screen = t.get("screen", "")
    start_time = t.get("start_time", "")
    booking_id = t.get("booking_id", "")
    total = t.get("total_price", "")

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"/></head>
<body style="margin:0;padding:0;background:#0a0f1a;font-family:Arial,sans-serif;color:#edf4f2;">
  <div style="max-width:520px;margin:40px auto;background:#141c28;border-radius:16px;overflow:hidden;border:1px solid rgba(245,166,35,0.3);">
    <div style="background:linear-gradient(135deg,#F5A623,#EF4444);padding:24px;text-align:center;">
      <div style="font-size:40px;">🎬</div>
      <h1 style="color:#fff;margin:8px 0 4px;font-size:22px;">Booking Confirmed!</h1>
      <p style="color:rgba(255,255,255,0.8);margin:0;font-size:13px;">Booking #{booking_id}</p>
    </div>
    <div style="padding:28px;">
      <table style="width:100%;border-collapse:collapse;">
        {"".join(f'<tr><td style="padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.08);color:rgba(237,244,242,0.55);font-size:13px;">{k}</td><td style="padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.08);text-align:right;font-weight:600;font-size:13px;">{v}</td></tr>' for k, v in [("Movie", movie), ("Theatre", f"{theatre} · {city}"), ("Screen", screen), ("Showtime", start_time), ("Seats", seats), ("Total Paid", f"₹{total}")])}
      </table>
      <div style="margin-top:24px;padding:16px;background:rgba(245,166,35,0.08);border:1px solid rgba(245,166,35,0.25);border-radius:10px;text-align:center;">
        <p style="margin:0;font-size:13px;color:rgba(237,244,242,0.7);">Present this confirmation at the theatre gate or use the QR code on your mTicket.</p>
      </div>
      <p style="text-align:center;font-size:12px;color:rgba(237,244,242,0.35);margin-top:24px;">
        Ticketly · Autonomous Booking Platform · <a href="https://arosai.in" style="color:#F5A623;text-decoration:none;">arosai.in</a>
      </p>
    </div>
  </div>
</body>
</html>
"""


async def send_booking_confirmation(to_email: str, ticket: dict):
    if not settings.SENDGRID_API_KEY:
        _send_via_smtp_or_skip(to_email, ticket)
        return
    try:
        import sendgrid
        from sendgrid.helpers.mail import Content, Email, Mail, To

        sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        t = ticket.get("ticket", ticket)
        message = Mail(
            from_email=Email(settings.EMAIL_FROM, settings.EMAIL_FROM_NAME),
            to_emails=To(to_email),
            subject=f"✅ Booking Confirmed – {t.get('movie', 'Your Movie')}",
            html_content=Content("text/html", _build_booking_html(ticket)),
        )
        sg.client.mail.send.post(request_body=message.get())
    except Exception as e:
        print(f"[email] SendGrid failed: {e}")


def _send_via_smtp_or_skip(to_email: str, ticket: dict):
    # No-op in dev when no SMTP configured — just log
    t = ticket.get("ticket", ticket)
    print(f"[email] Would send confirmation to {to_email} for booking #{t.get('booking_id')}")
