import requests
import logging
from config import Config
import os
from io import BytesIO
import base64
class MetaWhatsAppService:
    @staticmethod
    def download_and_encode_media(media_id):
        """
        Download media from Meta WhatsApp API and convert directly to base64
        without saving to disk.
        
        :param media_id: The ID of the media to download.
        :return: Base64 encoded string if successful, None otherwise.
        """
        try:
            # Define the URL and headers
            url = f"https://graph.facebook.com/v18.0/{media_id}"
            headers = {"Authorization": f"Bearer {Config.META_WA_TOKEN}"}

            # Make the request to get the media URL
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                logging.error(f"Failed to fetch media URL: {response.status_code}")
                return None

            media_url = response.json().get('url')
            if not media_url:
                logging.error("No media URL found in the response.")
                return None

            # Stream the download to memory
            media_response = requests.get(media_url, headers=headers, stream=True)
            if media_response.status_code != 200:
                logging.error(f"Failed to download media content: {media_response.status_code}")
                return None

            # Read content directly into memory and encode to base64
            content = BytesIO()
            for chunk in media_response.iter_content(chunk_size=8192):
                if chunk:
                    content.write(chunk)
            
            # Convert to base64
            base64_encoded = base64.b64encode(content.getvalue()).decode('utf-8')
            logging.info("Successfully downloaded and encoded media")
            return base64_encoded

        except Exception as e:
            logging.error(f"Media Download and Encoding Error: {e}")
            return None

    @staticmethod
    def send_whatsapp_message(phone_number, message):
        """
        Send WhatsApp message via Meta API
        """
        try:
            url = f"https://graph.facebook.com/v18.0/{Config.META_WA_PHONE_NUMBER_ID}/messages"
            
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": phone_number,
                "type": "text",
                "text": {"body": message}
            }
            
            headers = {
                "Authorization": f"Bearer {Config.META_WA_TOKEN}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return True
        except Exception as e:
            logging.error(f"WhatsApp Message Send Error: {e}")
            return False
    @staticmethod
    def send_whatsapp_interactive_message(phone_number, interactive_message):
        """
        Send interactive WhatsApp message via Meta API
        
        :param phone_number: Recipient's phone number
        :param interactive_message: Dictionary containing interactive message details
        """
        try:
            url = f"https://graph.facebook.com/v18.0/{Config.META_WA_PHONE_NUMBER_ID}/messages"
            
            # If interactive message doesn't include messaging product, add it
            if 'messaging_product' not in interactive_message:
                interactive_message['messaging_product'] = "whatsapp"
            
            # Ensure recipient type and to fields are present
            interactive_message['recipient_type'] = "individual"
            interactive_message['to'] = phone_number
            
            headers = {
                "Authorization": f"Bearer {Config.META_WA_TOKEN}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=interactive_message, headers=headers)
            response.raise_for_status()
            
            # Log successful message send
            logging.info(f"Interactive message sent successfully to {phone_number}")
            return True
        
        except requests.exceptions.RequestException as e:
            logging.error(f"WhatsApp Interactive Message Send Error: {e}")
            logging.error(f"Response content: {e.response.text if hasattr(e, 'response') else 'No response'}")
            return False
        except Exception as e:
            logging.error(f"Unexpected WhatsApp Interactive Message Error: {e}")
            return False
    def upload_media_to_whatsapp(file_data, filename):
        """
        Upload media to WhatsApp servers and get media ID
        """
        url = f'https://graph.facebook.com/v19.0/{os.getenv("META_WA_PHONE_NUMBER_ID")}/media'
        
        files = {
            'file': (filename, file_data, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            'type': (None, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            'messaging_product': (None, 'whatsapp')
        }
        
        headers = {
            'Authorization': f'Bearer {os.getenv("META_WA_TOKEN")}'
        }
        
        response = requests.post(url, headers=headers, files=files)
        
        if response.status_code != 200:
            raise Exception(f"Failed to upload media: {response.text}")
        
        return response.json().get('id')
