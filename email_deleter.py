import imaplib
import os

#Download and run locally
# Load email credentials from environment variables
EMAIL = #YOUR EMAIL
PASSWORD = #YOUR PASSWORD
IMAP_SERVER = "imap.gmail.com"  # Change this if using a different email provider

# Connect to the email server
def connect_to_email():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, PASSWORD)
    print("Connected to email server.")
    return mail

# Search and delete emails based on criteria
def delete_promotions_and_newsletters(mail, folder_name="inbox"):
    mail.select(folder_name)

    # Define search criteria
    search_criteria = (
        '(OR '
        'SUBJECT "newsletter" '
        'SUBJECT "promotion" '
        'SUBJECT "deal" '
        'SUBJECT "offer" '
        'SUBJECT "sale" '
        'SUBJECT "discount" '
        'SUBJECT "exclusive" '
        'SUBJECT "limited time" '
        'SUBJECT "subscribe" '
        'SUBJECT "unsubscribe" '
        'FROM "noreply@" '
        'FROM "info@" '
        'FROM "newsletter@" '
        'FROM "marketing@" '
        ')'
    )

    # Search for emails matching the criteria
    status, messages = mail.search(None, search_criteria)
    email_ids = messages[0].split()

    print(f"Found {len(email_ids)} emails matching the promotions/newsletters criteria in the '{folder_name}' folder.")

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
        delete_promotions_and_newsletters(mail, folder_name="inbox")
    finally:
        mail.logout()

if __name__ == "__main__":
    main()
