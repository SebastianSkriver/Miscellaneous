import imaplib
import email
import os
import csv
from bs4 import BeautifulSoup
from datetime import datetime

# Load email credentials from environment variables
EMAIL = os.getenv("EMAIL_H4")
PASSWORD = os.getenv("EMAIL_H4_PASSWORD")
IMAP_SERVER = "imap.gmail.com"  # Change this if using a different email provider

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

    unsubscribe_data = {}

    for email_id in email_ids:
        status, data = mail.fetch(email_id, "(RFC822)")
        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)

        # Get the email subject and sender
        subject = msg["subject"]
        sender = msg["from"]

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
                if company_name not in unsubscribe_data:
                    unsubscribe_data[company_name] = unsubscribe_link

    print(f"Extracted {len(unsubscribe_data)} unsubscribe links.")
    return unsubscribe_data

# Write unsubscribe links to a CSV file
def write_to_csv(unsubscribe_data, output_dir=".", output_file_prefix="unsubscribe_links"):
    # Generate a unique filename with a timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # Format: YYYYMMDD_HHMMSS
    output_file = os.path.join(output_dir, f"{output_file_prefix}_{timestamp}.csv")

    if not unsubscribe_data:
        print("No unsubscribe links found. CSV file will not be created.")
        return None

    with open(output_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Company/Newsletter", "Unsubscribe Link"])
        for company, link in unsubscribe_data.items():
            writer.writerow([company, link])

    print(f"Unsubscribe links have been saved to '{output_file}'.")
    return output_file

# Main function
def main():
    mail = connect_to_email()
    try:
        folder_name = filter_newsletters(mail)
        unsubscribe_data = extract_unsubscribe_links(mail, folder_name)
        output_file = write_to_csv(unsubscribe_data)
        if output_file:
            print(f"CSV file generated: {output_file}")
        else:
            print("No CSV file was generated.")
    finally:
        mail.logout()

if __name__ == "__main__":
    main()
