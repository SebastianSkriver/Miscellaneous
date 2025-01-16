import imaplib
import email
import os
import csv
from bs4 import BeautifulSoup

# Load email credentials from environment variables
EMAIL = os.getenv("EMAIL_H4")
PASSWORD = os.getenv("EMAIL_H4_PASSWORD")
IMAP_SERVER = "imap.gmail.com"  # Change this if using a different email provider

# Connect to the email server
def connect_to_email():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, PASSWORD)
    return mail

# Search for newsletter emails and move them to a folder
def filter_newsletters(mail, folder_name="Newsletters"):
    mail.select("inbox")
    # Search for emails with common newsletter keywords
    status, messages = mail.search(None, '(OR SUBJECT "newsletter" SUBJECT "promotion")')
    email_ids = messages[0].split()

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

    unsubscribe_data = {}

    for email_id in email_ids:
        status, data = mail.fetch(email_id, "(RFC822)")
        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)

        # Get the email subject and sender
        subject = msg["subject"]
        sender = msg["from"]

        # Extract the email body
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    html_content = part.get_payload(decode=True).decode()
        else:
            html_content = msg.get_payload(decode=True).decode()

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

    return unsubscribe_data

# Write unsubscribe links to a CSV file
def write_to_csv(unsubscribe_data, output_file="unsubscribe_links.csv"):
    with open(output_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Company/Newsletter", "Unsubscribe Link"])
        for company, link in unsubscribe_data.items():
            writer.writerow([company, link])

# Main function
def main():
    mail = connect_to_email()
    try:
        folder_name = filter_newsletters(mail)
        unsubscribe_data = extract_unsubscribe_links(mail, folder_name)
        write_to_csv(unsubscribe_data)
        print(f"Unsubscribe links have been saved to 'unsubscribe_links.csv'.")
    finally:
        mail.logout()

if __name__ == "__main__":
    main()
