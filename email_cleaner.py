import imaplib
import email
import os
from bs4 import BeautifulSoup
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load email credentials from environment variables
EMAIL = os.getenv("EMAIL_H4")
PASSWORD = os.getenv("EMAIL_H4_PASSWORD")
IMAP_SERVER = "imap.gmail.com"  # Change this if using a different email provider

# Load SMTP credentials for sending email
SMTP_SERVER = "smtp.gmail.com"  # Change this if using a different email provider
SMTP_PORT = 587
SENDER_EMAIL = os.getenv("EMAIL_H4")  # Use the same email for sending
SENDER_PASSWORD = os.getenv("EMAIL_H4_PASSWORD")  # Use the same password
RECIPIENT_EMAIL = os.getenv("EMAIL_H4")  # recipient email as an environment variable

# Connect to the email server
def connect_to_email():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, PASSWORD)
    print("Connected to email server.")
    return mail

# Search for newsletter emails and move them to a folder
def filter_newsletters(mail, folder_name="Newsletters"):
    mail.select("inbox")
    # Search for emails with common newsletter keywords
    status, messages = mail.search(None, '(OR SUBJECT "newsletter" SUBJECT "promotion")')
    email_ids = messages[0].split()

    print(f"Found {len(email_ids)} emails matching the criteria.")

    # Create the folder if it doesn't exist
    try:
        mail.create(folder_name)
    except:
        pass  # Folder already exists

    # Move emails to the folder
    for email_id in email_ids:
        mail.copy(email_id, folder_name)
        mail.store(email_id, "+FLAGS", "\\Deleted")
    mail.expunge()
    return folder_name

# Extract unsubscribe links from emails
def extract_unsubscribe_links(mail, folder_name="Newsletters"):
    mail.select(folder_name)
    status, messages = mail.search(None, "ALL")
    email_ids = messages[0].split()

    print(f"Found {len(email_ids)} emails in the '{folder_name}' folder.")

    unsubscribe_data = []

    for email_id in email_ids:
        status, data = mail.fetch(email_id, "(RFC822)")
        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)

        # Get the email subject and sender
        subject = msg["subject"] or "Unknown Subject"
        sender = msg["from"] or "Unknown Sender"

        # Extract the email body
        html_content = None
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    try:
                        # Attempt to decode using the specified charset
                        charset = part.get_content_charset() or "utf-8"
                        html_content = part.get_payload(decode=True).decode(charset)
                    except (UnicodeDecodeError, LookupError):
                        # Fallback to ISO-8859-1 if decoding fails
                        print(f"Warning: Failed to decode email content. Falling back to ISO-8859-1.")
                        html_content = part.get_payload(decode=True).decode("ISO-8859-1")
        else:
            try:
                # Attempt to decode using the specified charset
                charset = msg.get_content_charset() or "utf-8"
                html_content = msg.get_payload(decode=True).decode(charset)
            except (UnicodeDecodeError, LookupError):
                # Fallback to ISO-8859-1 if decoding fails
                print(f"Warning: Failed to decode email content. Falling back to ISO-8859-1.")
                html_content = msg.get_payload(decode=True).decode("ISO-8859-1")

        if not html_content:
            print(f"Warning: No HTML content found in email from {sender}. Skipping.")
            continue

        # Parse the HTML content
        soup = BeautifulSoup(html_content, "html.parser")
        links = soup.find_all("a")

        # Search for unsubscribe links
        for link in links:
            if link.string and ("unsubscribe" in link.string.lower() or "frameld" in link.string.lower() or "fra meld" in link.string.lower()):
                company_name = sender.split("<")[0].strip()  # Extract company name from sender
                unsubscribe_link = link["href"]

                # Avoid duplicates
                if not any(company_name == row[0] for row in unsubscribe_data):
                    unsubscribe_data.append([company_name, unsubscribe_link])

    print(f"Extracted {len(unsubscribe_data)} unsubscribe links.")
    return unsubscribe_data

# Send the unsubscribe links via email in a table format
def send_email_with_links(unsubscribe_data):
    # Create the email
    msg = MIMEMultipart("alternative")
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = "Unsubscribe Links"

    # Create the HTML table
    html = """
    <html>
    <body>
        <p>Here are the unsubscribe links extracted from your emails:</p>
        <table border="1" style="border-collapse: collapse; width: 100%;">
            <thead>
                <tr>
                    <th style="padding: 8px; text-align: left; background-color: #f2f2f2;">Newsletter Name</th>
                    <th style="padding: 8px; text-align: left; background-color: #f2f2f2;">Unsubscribe Link</th>
                </tr>
            </thead>
            <tbody>
    """

    for company_name, unsubscribe_link in unsubscribe_data:
        html += f"""
                <tr>
                    <td style="padding: 8px; text-align: left;">{company_name}</td>
                    <td style="padding: 8px; text-align: left;"><a href="{unsubscribe_link}">{unsubscribe_link}</a></td>
                </tr>
        """

    html += """
            </tbody>
        </table>
    </body>
    </html>
    """

    # Attach the HTML content to the email
    msg.attach(MIMEText(html, "html"))

    # Send the email
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)

    print(f"Email sent to {RECIPIENT_EMAIL} with unsubscribe links.")

# Main function
def main():
    mail = connect_to_email()
    try:
        folder_name = filter_newsletters(mail)
        unsubscribe_data = extract_unsubscribe_links(mail, folder_name)
        if unsubscribe_data:
            send_email_with_links(unsubscribe_data)  # Send the unsubscribe links via email
        else:
            print("No unsubscribe links were found.")
    finally:
        mail.logout()

if __name__ == "__main__":
    main()
