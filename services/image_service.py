import openai
import logging
from config import Config
from datetime import datetime
from openai import OpenAI
import base64
import requests, json
import os,json

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
            base64_image = encode_image(image_url)
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

            # Step 1: Validate if the image is a business card
            validation_response = client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "you are given a image which may have business card image or related image .Is this image a business card? Respond with 'yes' or 'no'."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }]
            )

            is_business_card = validation_response.choices[0].message.content.strip().lower()
            if is_business_card != "yes":
                return {"message": "Sorry, we can only process business cards."}

            # Step 2: Extract information if the image is a business card
            response = client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": '''Extract the following information from this image: name, email, contact number, and company. Return a JSON-formatted response.
                        {
                            "name": "Full Name Here",
                            "email": "valid_email@example.com",
                            "contact_number": "phone number of the contact",
                            "company": "Company Name"
                        }'''},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }]
            )

            content = json.loads(response.choices[0].message.content)
            return AINamecardService._parse_card_info(content)
        except Exception as e:
            logging.error(f"OpenAI Processing Error: {e}")
            return {"message": "An error occurred while processing the image."}

    @staticmethod
    def _parse_card_info(extracted_info):
        """
        Parse OpenAI's response into structured data
        """
        try:
            result = {
                'name': extracted_info.get('name'),
                'email': extracted_info.get('email', ''),
                'contact_number': extracted_info.get('contact_number', ""),
                'company': extracted_info.get('company')
            }
            return result
        except Exception as e:
            logging.error(f"Image Parsing Error: {e}")
            return {"message": "An error occurred while parsing the extracted information."}
