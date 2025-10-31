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
# @app.route('/webhook', methods=['POST'])
# def webhook():
#     # if request.method == 'GET':
#     #     # Webhook verification
#     #     if request.args.get('hub.verify_token') == Config.WEBHOOK_VERIFY_TOKEN:
#     #         return request.args.get('hub.challenge'), 200
#     #     return 'Invalid verification token', 403

#     if request.method == 'POST':
#         try:
#             data = request.get_json()
            
#             # Extract message details
#             message = data['entry'][0]['changes'][0]['value']['messages'][0]
#             from_number = message['from']
            
#             # Check if message contains media
#             if 'type' in message and message['type'] == 'text':
#                 with app.app_context():
#                     user = User.query.filter_by(phone=from_number).first()
#                     if not user:
#                         user = User(phone=from_number)
#                         db.session.add(user)
#                         db.session.commit()
#                 MetaWhatsAppService.send_whatsapp_message(from_number, "Please Provide your contact card Image to get the contact details")
#             if 'type' in message and message['type'] == 'image':
#                 media_id = message['image']['id']
                
#                 # Find or create user
#                 with app.app_context():
#                     user = User.query.filter_by(phone=from_number).first()
#                     if not user:
#                         user = User(phone=from_number)
#                         db.session.add(user)
#                         db.session.commit()
                
#                 # Download and process image
#                 media_content = MetaWhatsAppService.download_media(media_id)
#                 print(media_content)
#                 # storage_service = SupabaseStorageService()
#                 # image_url = storage_service.upload_image(media_content)
#                 # Process receipt
#                 card_info = AINamecardService.process_namecard_image(media_content)
#                 print(card_info)
#                 if card_info:
#                     # Create receipt entry
#                     result = card_info
#                     with app.app_context():
#                         new_contact = ContactInfo(
#                         user_id=user.id,  # Assuming you're using Flask-Login or similar
#                         name=result.get('name', ''),
#                         email=result.get('email', ''),
#                         phone_number=result.get('contact_number', ''),
#                         company=result.get('company', '')
#                     )
#                         db.session.add(new_contact)
#                         db.session.commit()
                    
#                     # Send success message
#                     if "message" in result:
#                         error_msg = result["message"]
#                         # Return or display the error message
#                         confirmation_msg = f"❌ {error_msg}"
#                     else:
#                         confirmation_msg = f"🎉 Contact Saved Successfully! 🌟\n\n📇 Name: {result.get('name', 'N/A')}\n📧 Email: {result.get('email', 'N/A')}\n📞 Phone: {result.get('contact_number', 'N/A')}\n🏢 Company: {result.get('company', 'N/A')}"
#                     MetaWhatsAppService.send_whatsapp_message(from_number, confirmation_msg)
#                 else:
#                     MetaWhatsAppService.send_whatsapp_message(from_number, "Sorry, I couldn't process your image. Please try again.")
            
#             return jsonify(success=True), 200
        
#         except Exception as e:
#             logging.error(f"Webhook Processing Error: {e}")
#             return jsonify(error=str(e)), 500
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
            # Return or display the error message
            confirmation_msg = f"Sorry , we can only process images of namecards. Please try uploading again. Thanks!."
            send_interactive_menu(from_number, confirmation_msg)
        else:
            with app.app_context():
            # Check if a contact with the same email already exists
                existing_contact = ContactInfo.query.filter(
                        ContactInfo.email == card_info.get('email', ''),
                        ContactInfo.user_id == user.id
                    ).first()
                
                if existing_contact:
                    # Set confirmation message for existing contact
                    confirmation_msg = "This contact is already present. Try uploading again with a different contact."
                    send_interactive_menu(from_number, confirmation_msg)
                else:
                    # Add new contact if email is not found
                    confirmation_msg = f"Contact Saved Successfully! \n\nName: {result.get('name', 'N/A')}\nEmail: {result.get('email', 'N/A')}\nPhone: {result.get('contact_number', 'N/A')}\nCompany: {result.get('company', 'N/A')}"
                    send_interactive_menu_contact(from_number,confirmation_msg)
                    new_contact = ContactInfo(
                        user_id=user.id,  # Assuming you're using Flask-Login or similar
                        name=result.get('name', ''),
                        email=result.get('email', ''),
                        phone_number=result.get('contact_number', ''),
                        company=result.get('company', '')
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
if __name__ == '__main__':
    app.run(debug=True)
