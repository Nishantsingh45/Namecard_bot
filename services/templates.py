
from services.meta_service import MetaWhatsAppService

def Viewproducts(phone_number,token):
    """
    Send interactive message to view products
    """
    interactive_message = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to":phone_number,
        "type": "interactive",
        "interactive": {
            "type": "cta_url",
            "header": {
                "type": "text",
                "text": "View Contacts"
            },
            "body": {
                "text": "Click the button below to view your contacts."
            },
            "action": {
            "name": "cta_url",
            "parameters": {
                "display_text": "View Contacts",
                "url":f"https://namecard.goboxme.com/contacts/{token}"
                
            }
        }
        }
    }
    MetaWhatsAppService.send_whatsapp_interactive_message(phone_number, interactive_message)

def Exportproducts(phone_number,filename,file_data):
    """
    Send interactive message to view products
    """
    try:
        media_id = MetaWhatsAppService.upload_media_to_whatsapp(file_data,filename)
        message_payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number,
            "type": "document",
            "document": {
                #"link": f"https://namecard.goboxme.com/temp/{filename}", 
                "id": media_id, # Replace with the actual hosted file link
                "filename": filename,
                "caption": "Here are your exported contacts."
            }
        }
        MetaWhatsAppService.send_whatsapp_interactive_message(phone_number, message_payload)
        return "Message send successfully"
    except Exception as e:
        return f"error while exporting file {e}"


def sendcontact(phone_number,last_contact):
    """
    Send contact details to user
    """
    # Extract details from last_contact
    contact_name = last_contact.name
    contact_phone = last_contact.phone_number
    contact_email = last_contact.email
    contact_company = last_contact.company
    interactive_message = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "contacts",
            "contacts": [
                {
                "name": {
                    "formatted_name": contact_name,
                    "first_name": contact_name
                },
                "phones": [
                    {
                    "phone": contact_phone,
                    "type": "Mobile"
                    }
                ],
                "emails": [
                    {
                    "email": contact_email,
                    "type": "Work"
                    }
                ],
                "org": {
                    "company": contact_company
                }
                }
            ]
            }
    MetaWhatsAppService.send_whatsapp_interactive_message(phone_number, interactive_message)

    