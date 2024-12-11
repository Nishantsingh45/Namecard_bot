import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Meta WhatsApp API Configuration
    META_WA_TOKEN = os.getenv('META_WA_TOKEN')
    META_WA_PHONE_NUMBER_ID = os.getenv('META_WA_PHONE_NUMBER_ID')
    WEBHOOK_VERIFY_TOKEN = os.getenv('WEBHOOK_VERIFY_TOKEN')
    
    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = "gpt-4o"
    SUPABASE_URL = 'https://yraugxqmjylmrafggnqm.supabase.co'
    SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlyYXVneHFtanlsbXJhZmdnbnFtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzM3NDA3MjksImV4cCI6MjA0OTMxNjcyOX0.8F4ijY0N_f0FS4bU0C9WrTrwKvgQJRIyMprfyFdOnEU'