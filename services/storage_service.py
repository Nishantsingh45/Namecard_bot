import io
import uuid
import logging
from supabase import create_client
from config import Config

class SupabaseStorageService:
    def __init__(self):
        self.supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

    def upload_image(self, media_content, file_extension='jpg'):
        """
        Upload image to Supabase storage
        """
        try:
            # Generate unique filename
            filename = f"{uuid.uuid4()}.{file_extension}"
            
            # Storage path
            storage_path = f"Namecards/{filename}"
            
            # Upload directly 
            response = self.supabase.storage.from_('Whatsapp').upload(
                path=storage_path, 
                file=media_content,  # Use media_content directly
                file_options={"content-type": "image/jpeg"}
            )
            
            # Get public URL
            public_url = self.supabase.storage.from_('Whatsapp').get_public_url(storage_path)
            
            return public_url
        except Exception as e:
            logging.error(f"Supabase Upload Error: {e}")
            return None