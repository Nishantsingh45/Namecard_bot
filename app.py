from flask import Flask, request, jsonify
from models import db, User, ContactInfo
from services.meta_service import MetaWhatsAppService
from services.image_service import AINamecardService
from services.storage_service import SupabaseStorageService
from config import Config
import logging

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
@app.route('/webhook', methods=['POST'])
def webhook():
    # if request.method == 'GET':
    #     # Webhook verification
    #     if request.args.get('hub.verify_token') == Config.WEBHOOK_VERIFY_TOKEN:
    #         return request.args.get('hub.challenge'), 200
    #     return 'Invalid verification token', 403

    if request.method == 'POST':
        try:
            data = request.get_json()
            
            # Extract message details
            message = data['entry'][0]['changes'][0]['value']['messages'][0]
            from_number = message['from']
            
            # Check if message contains media
            if 'type' in message and message['type'] == 'text':
                with app.app_context():
                    user = User.query.filter_by(phone=from_number).first()
                    if not user:
                        user = User(phone=from_number)
                        db.session.add(user)
                        db.session.commit()
                MetaWhatsAppService.send_whatsapp_message(from_number, "Please Provide your contact card Image to get the contact details")
            if 'type' in message and message['type'] == 'image':
                media_id = message['image']['id']
                
                # Find or create user
                with app.app_context():
                    user = User.query.filter_by(phone=from_number).first()
                    if not user:
                        user = User(phone=from_number)
                        db.session.add(user)
                        db.session.commit()
                
                # Download and process image
                media_content = MetaWhatsAppService.download_media(media_id)
                print(media_content)
                # storage_service = SupabaseStorageService()
                # image_url = storage_service.upload_image(media_content)
                # Process receipt
                card_info = AINamecardService.process_namecard_image(media_content)
                print(card_info)
                if card_info:
                    # Create receipt entry
                    result = card_info
                    with app.app_context():
                        new_contact = ContactInfo(
                        user_id=user.id,  # Assuming you're using Flask-Login or similar
                        name=result.get('name', ''),
                        email=result.get('email', ''),
                        phone_number=result.get('contact_number', ''),
                        company=result.get('company', '')
                    )
                        db.session.add(new_contact)
                        db.session.commit()
                    
                    # Send success message
                    confirmation_msg = f"🎉 Contact Saved Successfully! 🌟\n\n📇 Name: {result.get('name', 'N/A')}\n📧 Email: {result.get('email', 'N/A')}\n📞 Phone: {result.get('contact_number', 'N/A')}\n🏢 Company: {result.get('company', 'N/A')}"
                    MetaWhatsAppService.send_whatsapp_message(from_number, confirmation_msg)
                else:
                    MetaWhatsAppService.send_whatsapp_message(from_number, "Sorry, I couldn't process your image. Please try again.")
            
            return jsonify(success=True), 200
        
        except Exception as e:
            logging.error(f"Webhook Processing Error: {e}")
            return jsonify(error=str(e)), 500

if __name__ == '__main__':
    app.run(debug=True)
