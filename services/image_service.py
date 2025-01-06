import openai
import logging
from config import Config
from datetime import datetime
from openai import OpenAI
import base64
import requests, json
import os,json
from services.meta_service import MetaWhatsAppService
def encode_image(image_url):
    """
    Encode an image to base64

    Args:
        image_url (str): Path or URL of the image

    Returns:
        str: Base64 encoded image or None if error occurs
    """
    try:
        
        # Remove 'file://' prefix

        # Read and encode the file
        with open(image_url, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')


    except Exception as e:
        #logger.error(f"Error encoding image to base64: {e}")
        return None


class AINamecardService:
    @staticmethod
    def process_namecard_image(image_url):
        """
        Process Namecard image using OpenAI Vision
        """
        try:
            openai.api_key = Config.OPENAI_API_KEY
            base64_image = MetaWhatsAppService.download_and_encode_media(image_url)
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            response = client.chat.completions.create(
                response_format={"type": "json_object"},
                model=Config.OPENAI_MODEL,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": '''Extract the following information from this image: name, email, contact number, and company. Return a JSON-formatted response.
                         Note: if you think this is not a business card image, please make is_business_card to No and rest to be empty.
                             - Do not guess or infer missing parts (e.g., do not complete the domain name for an email or a phone number ).
                        {
                            "name": "Full Name Here",
                            "email": "valid_email@example.com",
                            "contact_number": "phone number of the contact",
                            "company": "Company Name",
                            "position": "Person's Job Title or Position",
                            "website": "company_website",
                            "is_business_card": "yes/no"
                           
                        }'''},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }]
            )
            
            #receipt_text = response.choices[0].message.content
            content = json.loads(response.choices[0].message.content)
            return AINamecardService._parse_card_info(content)
        except Exception as e:
            logging.error(f"OpenAI Processing Error: {e}")
            return None

    @staticmethod
    def _parse_card_info(extracted_info):
        """
        Parse OpenAI's response into structured data
        """
        try:
            if extracted_info.get('is_business_card') == 'no':
                return {
                    'message': 'This is not a business card image.'
                }
            result = {
                'name':
                extracted_info.get('name'),
                'email':
                extracted_info.get('email','') ,
                'contact_number':
                extracted_info.get('contact_number', ""),
                'company':
                extracted_info.get('company'),
                'position':
                extracted_info.get('position', ""),
                'website':
                extracted_info.get('website', "")
            }
            return result
        except Exception as e:
            logging.error(f"Image Parsing Error: {e}")
            return None

    