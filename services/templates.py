
from services.meta_service import MetaWhatsAppService

def Viewproducts(phone_number):
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
                "text": "Clicks the button below to view your contacts."
            },
            "action": {
            "name": "cta_url",
            "parameters": {
                "display_text": "View Contacts",
                "url":f"https://namecard-bot.vercel.app/api/contacts/{phone_number}"
                
            }
        }
        }
    }
    MetaWhatsAppService.send_whatsapp_interactive_message(phone_number, interactive_message)

def Exportproducts(phone_number):
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
                "text": "Export you contacts"
            },
            "body": {
                "text": "Clicks the button below to Export your contacts."
            },
            "action": {
            "name": "cta_url",
            "parameters": {
                "display_text": "Export Contacts",
                "url":f"https://namecard-bot.vercel.app/api/contacts/{phone_number}"
                
            }
        }
        }
    }
    MetaWhatsAppService.send_whatsapp_interactive_message(phone_number, interactive_message)