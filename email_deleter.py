import imaplib
import email
from email.header import decode_header
import os

# Load email credentials from environment variables
EMAIL = "h4x3r.h4ck3r@gmail.com"
PASSWORD = "bgyf hjzj wphd phcw"
IMAP_SERVER = "imap.gmail.com"  # Change this if using a different email provider

# Connect to the email server
def connect_to_email():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        print("Connected to email server.")
        return mail
    except Exception as e:
        print(f"Error connecting to email server: {e}")
        exit(1)

# Function to list all available folders
def list_folders(mail):
    status, folders = mail.list()
    if status != "OK":
        print("Error fetching folder list.")
        return
    print("Available folders:")
    for folder in folders:
        print(folder.decode())

# Function to search emails by body content
def search_email_body(mail, folder_name="[Gmail]/All Mail", keywords=None):
    if keywords is None:
        keywords = ["newsletter", "promotion", "deal", "offer", "sale", "discount", "exclusive", "limited time"]

    # Ensure the folder name is properly quoted
    folder_name = f'"{folder_name}"'

    # Select the folder
    status, _ = mail.select(folder_name)
    if status != "OK":
        print(f"Error: Unable to select folder '{folder_name}'. Please check the folder name.")
        return []

    print(f"Successfully selected folder: {folder_name}")

    # Search for all emails in the folder
    status, messages = mail.search(None, "ALL")
    if status != "OK":
        print("Error searching for emails.")
        return []

    email_ids = messages[0].split()
    print(f"Found {len(email_ids)} emails in the '{folder_name}' folder.")

    matching_emails = []

    # Fetch and parse each email
    for email_id in email_ids:
        status, data = mail.fetch(email_id, "(RFC822)")
        if status != "OK":
            print(f"Error fetching email with ID {email_id}.")
            continue

        # Parse the email content
        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)

        # Get the email body
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                # Get the plain text part of the email
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        body = part.get_payload(decode=True).decode()
                    except Exception as e:
                        print(f"Error decoding email body: {e}")
        else:
            # If the email is not multipart, get the payload directly
            try:
                body = msg.get_payload(decode=True).decode()
            except Exception as e:
                print(f"Error decoding email body: {e}")

        # Check if any keyword is in the body
        if any(keyword.lower() in body.lower() for keyword in keywords):
            matching_emails.append(email_id)

    print(f"Found {len(matching_emails)} emails matching the body content criteria.")
    return matching_emails

# Function to delete emails by ID
def delete_emails(mail, email_ids, folder_name="[Gmail]/All Mail"):
    if not email_ids:
        print("No emails found to delete.")
        return

    # Confirm before deleting
    confirm = input(f"Are you sure you want to delete these {len(email_ids)} emails? (yes/no): ")
    if confirm.lower() != "yes":
        print("Deletion canceled.")
        return

    # Mark emails for deletion
    for email_id in email_ids:
        mail.store(email_id, "+FLAGS", "\\Deleted")  # Mark the email for deletion
    mail.expunge()  # Permanently delete the marked emails

    print(f"Deleted {len(email_ids)} emails from the '{folder_name}' folder.")

# Main function
def main():
    mail = connect_to_email()
    try:
        list_folders(mail)  # List all available folders
        matching_emails = search_email_body(mail, folder_name="[Gmail]/All Mail")  # Search email body
        delete_emails(mail, matching_emails, folder_name="[Gmail]/All Mail")  # Delete matching emails
    finally:
        mail.logout()

if __name__ == "__main__":
    main()
