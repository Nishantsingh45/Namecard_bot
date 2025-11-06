from flask import Flask, request, jsonify,render_template
from models import db, User, ContactInfo
from services.meta_service import MetaWhatsAppService
from services.image_service import AINamecardService
from services.storage_service import SupabaseStorageService
from config import Config
import logging
from flask import jsonify, send_file
import pandas as pd
from io import BytesIO
from datetime import datetime
from services.templates import Viewproducts, Exportproducts,sendcontact
import os
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from phonenumbers import parse as parse_phone, geocoder, is_valid_number
import pycountry

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = Config.DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    with app.app_context():
        db.create_all()
    logging.basicConfig(level=logging.INFO)
    
    return app

app = create_app()
app.secret_key = 'namecard_aerochat'
serializer = URLSafeTimedSerializer(app.secret_key)

print("created")
@app.route('/webhook', methods=['GET'])
def waba_verify():
  # Webhook verification
  if request.args.get("hub.mode") == "subscribe" and request.args.get(
      "hub.challenge"):
    if not request.args.get("hub.verify_token") == 'hello':
      return "Verification token mismatch", 403
    return request.args["hub.challenge"], 200
  return "Hello world", 200

def get_country(phone_number):
    """
    Get country code from phone number
    """
    try:
        # Ensure the phone number starts with '+'
        if not phone_number.startswith('+'):
            phone_number = f"+{phone_number}"
        
        phone_obj = parse_phone(phone_number, None)
        
        # Validate phone number
        if not is_valid_number(phone_obj):
            return ''
        
        # Get country name
        country = geocoder.country_name_for_number(phone_obj, "en")
        return country
    except Exception as e:
        # Log exception if needed, for debugging
        print(f"Error parsing phone number: {e}")
        return ''
from datetime import datetime, timedelta
from services.meta_service import MetaWhatsAppService
from services.audio_service import transcribe_whatsapp_audio,save_transcript_as_docx
from services.templates import Exporttranscript
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        try:
            data = request.get_json()
            print(data)
            # Extract message details
            entry = data['entry'][0]
            changes = entry['changes'][0]
            value = changes['value']
            
            # Determine message type
            if 'messages' in value:
                message = value['messages'][0]
                message_id = message['id']
                from_number = message['from']
                contact_name = None
                country = get_country(from_number)
                if 'contacts' in value:
                    contact = value['contacts'][0]
                    contact_name = contact.get('profile', {}).get('name')
                with app.app_context():
                    user = User.query.filter_by(phone=from_number).first()
                    if not user:
                        user = User(phone=from_number,
                                    name=contact_name,
                                    country = country)
                        db.session.add(user)
                        db.session.commit()
                        MetaWhatsAppService.send_whatsapp_message(from_number, "Welcome! What would you like to do today?\nTo add a contact, simply take a photo or upload an image of a namecard.")
                        return jsonify(success=True), 200

                # Handle different message types
                if message.get('type') == 'text' or 'interactive' in message:
                    # Check if it's a reply to interactive buttons
                    MetaWhatsAppService.send_typing_indicator(from_number,message_id)
                    if 'interactive' in message:
                        interactive_type = message['interactive'].get('type')
                        
                        if interactive_type == 'button_reply':
                            button_id = message['interactive']['button_reply'].get('id')
                            
                            # Handle button selections
                            if button_id == 'export_list':
                                export_contacts(from_number)
                            elif button_id == 'add_contact':
                                last_contact = get_last_contact(from_number)
                                if last_contact:
                                    sendcontact(from_number,last_contact)
                                else:
                                    MetaWhatsAppService.send_whatsapp_message(from_number, "Please Provide your Namecard Image to get the contact details")
                            elif button_id == 'view_list':
                                token = generate_token(from_number)
                                Viewproducts(from_number,token)
                            elif button_id == 'send_image':
                                MetaWhatsAppService.send_whatsapp_message(from_number, "Please Provide your Namecard Image to get the contact details")

                    else:
                        # Initial interaction or text message
                        send_initial_interactive_menu(from_number)
                
                # Existing image processing logic
                elif message.get('type') == 'image':
                    # Your existing image processing code here
                    process_namecard_image(message, from_number)
                elif message.get('type') == 'audio':
                    audio_data = message.get('audio', {})
                    media_id = audio_data.get('id')
                    if not media_id:
                        print("no media_id")
                        return jsonify({"error": "Media ID not provided in the voice message"}), 400

                    # Download the audio file from WhatsApp
                    try:
                        transcript_text = transcribe_whatsapp_audio(media_id)
                        print(transcript_text)
                        # Save the transcript as a text file (adjust storage path as needed).
                        timestamp = datetime.now().strftime("%d %b, %-I.%M %p")  # Use %-I for removing leading zero in hour (Linux/macOS)
                        transcript_filename = f"{timestamp}.txt"

                        # For Windows compatibility (doesn't support %-I)
                        if transcript_filename.startswith("0"):
                            transcript_filename = transcript_filename[1:]
                        with open(transcript_filename, 'w', encoding="utf-8") as txt_file:
                            txt_file.write(transcript_text)
                        #transcript_filename = save_transcript_as_docx(from_number, transcript_text)
                        # Now read the transcript file data and upload it to WhatsApp.
                        with open(transcript_filename, 'rb') as file_obj:
                            file_data = file_obj.read()

                        # Upload the transcript text file using the helper function.
                        response = Exporttranscript(from_number,transcript_filename,file_data,transcript_filename)
                        # Optionally, delete the transcript file if it's no longer needed.
                        os.remove(transcript_filename)
                    except:
                        MetaWhatsAppService.send_whatsapp_message(from_number, "Sorry we are unable to Help you at the moment. Please try again later.")
                    

            return jsonify(success=True), 200
        
        except Exception as e:
            logging.error(f"Webhook Processing Error: {e}")
            return jsonify(error=str(e)), 500
def send_initial_interactive_menu(phone_number):
    """Send initial interactive menu with options"""
    interactive_message = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone_number,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": "Welcome! What would you like to do today?\nTo add a contact, simply take a photo or upload an image of a namecard."
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "export_list",
                            "title": "Export Contact List"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "view_list",
                            "title": "View Contact List"
                        }
                    }
                ]
            }
        }
    }
    
    # Use your Meta WhatsApp Service to send the message
    MetaWhatsAppService.send_whatsapp_interactive_message(phone_number,interactive_message)

def send_interactive_menu(phone_number, previous_response):
    """Send interactive menu after showing previous results"""
    interactive_message = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone_number,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": f"{previous_response}\n\nWhat would you like to do next?"
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "export_list",
                            "title": "Export Contact List"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "view_list",
                            "title": "View Contact List"
                        }
                    }
                ]
            }
        }
    }
    
    # Use your Meta WhatsApp Service to send the message
    MetaWhatsAppService.send_whatsapp_interactive_message(phone_number,interactive_message)
def send_interactive_menu_contact(phone_number, previous_response):
    """Send interactive menu after showing previous results"""
    interactive_message = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone_number,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": f"{previous_response}\n\nTo add another contact, simply take a photo or upload an image of a namecard.\n\nWhat would you like to do next?"
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "add_contact",
                            "title": "Add Contact to Phone"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "view_list",
                            "title": "View Contact List"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "export_list",
                            "title": "Export Contact List"
                        }
                    }
                ]
            }
        }
    }
    
    # Use your Meta WhatsApp Service to send the message
    MetaWhatsAppService.send_whatsapp_interactive_message(phone_number,interactive_message)
def process_namecard_image(message, from_number):
    """Process business_card image (your existing logic)"""
    media_id = message['image']['id']
    
    with app.app_context():
        user = User.query.filter_by(phone=from_number).first()
        if not user:
            user = User(phone=from_number)
            db.session.add(user)
            db.session.commit()
    
    # Download and process image
    #media_content = MetaWhatsAppService.download_media(media_id)
    card_info = AINamecardService.process_namecard_image(media_id)
    
    if card_info:
        # Create receipt entry
        result = card_info
        # Send success message
        if "message" in result:
            error_msg = result["message"]
            normal_info = AINamecardService.process_NORMAL_image(media_id)
            # Return or display the error message
            #confirmation_msg = f"Sorry , we can only process images of namecards. Please try uploading again. Thanks!."
            #send_interactive_menu(from_number, confirmation_msg)
            timestamp = datetime.now().strftime("%d %b, %-I.%M %p")  # Use %-I for removing leading zero in hour (Linux/macOS)
            transcript_filename = f"{timestamp}.txt"

            # For Windows compatibility (doesn't support %-I)
            if transcript_filename.startswith("0"):
                transcript_filename = transcript_filename[1:]
            with open(transcript_filename, 'w', encoding="utf-8") as txt_file:
                txt_file.write(normal_info)
            #transcript_filename = save_transcript_as_docx(from_number, transcript_text)
            # Now read the transcript file data and upload it to WhatsApp.
            with open(transcript_filename, 'rb') as file_obj:
                file_data = file_obj.read()

            # Upload the transcript text file using the helper function.
            confirmation_msg = f'You can download the below file to read the content of image'
            MetaWhatsAppService.send_whatsapp_message(from_number, confirmation_msg)
            response = Exporttranscript(from_number,transcript_filename,file_data,transcript_filename)
            send_interactive_menu(from_number, '')
            # Optionally, delete the transcript file if it's no longer needed.
            os.remove(transcript_filename)
            
        else:
            with app.app_context():
            # Check if a contact with the same email already exists
                if card_info.get('email'):
                    existing_contact = ContactInfo.query.filter(
                            ContactInfo.email == card_info.get('email'),
                            ContactInfo.user_id == user.id
                        ).first()
                else:
                    existing_contact = ContactInfo.query.filter(
                        ContactInfo.phone_number.op('~')(f'\\m{card_info.get("contact_number")}\\M'),
                        ContactInfo.user_id == user.id
                    ).first()


                
                if existing_contact:
                    # Set confirmation message for existing contact
                    confirmation_msg = "This contact is already present. Try uploading again with a different contact."
                    send_interactive_menu(from_number, confirmation_msg)
                else:
                    # Add new contact if email is not found
                    confirmation_msg = f"Contact Saved Successfully! \n\nName: {result.get('name', 'N/A')}\nEmail: {result.get('email', 'N/A')}\nPhone: {result.get('contact_number', 'N/A')}\nCompany: {result.get('company', 'N/A')}"
                    if 'position' in result:
                        confirmation_msg += f"\nPosition: {result['position']}"
                    if 'website' in result:
                        confirmation_msg += f"\nWebsite: {result['website']}"
                    send_interactive_menu_contact(from_number,confirmation_msg)
                    result_name = result.get('name') or result.get('company') or ""
                    new_contact = ContactInfo(
                        user_id=user.id,  # Assuming you're using Flask-Login or similar
                        name= result_name,#result.get('name', ''),
                        email=result.get('email', ''),
                        phone_number=result.get('contact_number', ''),
                        company=result.get('company', ''),
                        position = result.get('position',''),
                        website = result.get('website','')
                    )
                    db.session.add(new_contact)
                    db.session.commit()
                    # confirmation_msg = f"Contact Saved Successfully! \n\nName: {result.get('name', 'N/A')}\nEmail: {result.get('email', 'N/A')}\nPhone: {result.get('contact_number', 'N/A')}\nCompany: {result.get('company', 'N/A')}"
                    # send_interactive_menu_contact(from_number,confirmation_msg)
    else:
        MetaWhatsAppService.send_whatsapp_message(from_number, "Sorry, I couldn't process your image. Please try again.")


def get_last_contact(phone):
    user = User.query.filter_by(phone=phone).first()
    
    if not user:
        return None  # User not found
    
    # Query the last contact information for the found user based on the creation date
    last_contact = ContactInfo.query.filter_by(user_id=user.id).order_by(ContactInfo.created_at.desc()).first()
    
    return last_contact
def get_user_by_phone(phone):
    """Helper function to get user by phone number"""
    return User.query.filter_by(phone=phone).first()
def generate_token(phone):
    token = serializer.dumps(phone)
    return token
@app.route('/contacts/<token>', methods=['GET'])
def view_contacts(token):
    """
    View contacts for a given user phone number
    Returns contacts list in JSON format
    """
    try:
        # Verify the token and check expiration (2 hours = 7200 seconds)
        phone = serializer.loads(token, max_age=3600)
    except SignatureExpired:
        return render_template('error.html', error_msg='Token Expired')
    except BadSignature:
        return render_template('error.html', error_msg='Invalid Token')
    user = get_user_by_phone(phone)
    
    if not user:
        return render_template('error.html', error_msg='User not found')
    
    contacts = []
    for contact in user.contacts:
        contacts.append({
            'name': contact.name,
            'email': contact.email,
            'phone_number': contact.phone_number,
            'company': contact.company,
            'position': contact.position,
            'website': contact.website,
            'created_at': contact.created_at.isoformat()
        })
    return render_template('contacts.html', user=user, contacts=contacts)
    
    # return jsonify({
    #     'status': 'success',
    #     'data': {
    #         'user': {
    #             'name': user.name,
    #             'phone': user.phone
    #         },
    #         'contacts': contacts
    #     }
    # })

@app.route('/api/contacts/<phone>/export', methods=['GET'])
def export_contacts(phone):
    """
    Export contacts for a given user phone number
    Returns an Excel file containing all contacts
    """
    user = get_user_by_phone(phone)
    
    if not user:
        return jsonify({
            'status': 'error',
            'message': 'User not found'
        }), 404
    try:
        # Prepare data for Excel export
        contacts_data = []
        for contact in user.contacts:
            contacts_data.append({
                'Name': contact.name,
                'Email': contact.email,
                'Phone Number': contact.phone_number,
                'Company': contact.company,
                'Position': contact.position,
                'Created At': contact.created_at
            })
        
        # Create DataFrame and export to Excel
        df = pd.DataFrame(contacts_data)
        
        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Contacts')
            
            # Auto-adjust columns' width
            worksheet = writer.sheets['Contacts']
            for idx, col in enumerate(df.columns):
                series = df[col]
                max_len = max(
                    series.astype(str).map(len).max(),
                    len(str(series.name))
                ) + 1
                worksheet.set_column(idx, idx, max_len)
        
        output.seek(0)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'contacts_export_{timestamp}.xlsx'
        

        result = Exportproducts(phone,filename,output.getvalue())
        # return send_file(
        #     output,
        #     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        #     as_attachment=True,
        #     download_name=filename
        # )
        return result
    except Exception as e:
        return f"there is some error {e}"
    




from flask import Flask, request, jsonify, render_template
from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response_id = None
@app.route('/')
def index():
    global response_id
    response_id = None  # Reset on refresh or new visit
    return render_template('index.html')
# response_id = None
@app.route('/chat', methods=['POST'])
def chat():
    global response_id
    user_input = request.json.get('message')

    try:
        if response_id:
            response = client.responses.create(
                model="gpt-4.1",
                previous_response_id=response_id,
                input=user_input,
                tool_choice="required",
                tools=[
                    {
                        "type": "mcp",
                        "server_label": "shopify",
                        "server_url": "https://breadgarden.myshopify.com/api/mcp",
                        "require_approval": "never"
                    }
                ],
            )
        else:
            response = client.responses.create(
            model="gpt-4.1",
            previous_response_id=response_id,
            input=user_input,
            tool_choice="required",
            tools=[
                {
                    "type": "mcp",
                    "server_label": "shopify",
                    "server_url": "https://breadgarden.myshopify.com/api/mcp",
                    "require_approval": "never"
                }
            ],
        )

        output_text = ""
        for item in response.output:
            response_id = response.id
            if getattr(item, "role", None) == "assistant" and getattr(item, "type", None) == "message":
                for content_item in item.content:
                    if getattr(content_item, "type", None) == "output_text":
                        output_text = content_item.text
                        break

        return jsonify({"response": output_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/ecom')
def index_ecom():
    global response_id
    response_id = None  # Reset on refresh or new visit
    return render_template('index_ecom.html')
# response_id = None
@app.route('/chat_ecom', methods=['POST'])
def chat_ecom():
    global response_id
    user_input = request.json.get('message')

    try:
        if response_id:
            response = client.responses.create(
                model="gpt-4.1",
                previous_response_id=response_id,
                input=user_input,
                tool_choice="required",
                tools=[
                    {
                        "type": "mcp",
                        "server_label": "shopify",
                        "server_url": "https://ecomtestac.myshopify.com/api/mcp",
                        "require_approval": "never"
                    }
                ],
            )
        else:
            response = client.responses.create(
            model="gpt-4.1",
            previous_response_id=response_id,
            input=user_input,
            tool_choice="required",
            tools=[
                {
                    "type": "mcp",
                    "server_label": "shopify",
                    "server_url": "https://ecomtestac.myshopify.com/api/mcp",
                    "require_approval": "never"
                }
            ],
        )

        output_text = ""
        for item in response.output:
            response_id = response.id
            if getattr(item, "role", None) == "assistant" and getattr(item, "type", None) == "message":
                for content_item in item.content:
                    if getattr(content_item, "type", None) == "output_text":
                        output_text = content_item.text
                        break

        return jsonify({"response": output_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
if __name__ == '__main__':
    app.run(debug=True)
