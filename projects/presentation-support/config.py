import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    UPLOAD_FOLDER = 'uploads'
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 16777216))  # 16MB
    ALLOWED_EXTENSIONS = {'pdf', 'ppt', 'pptx'}
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')

    @staticmethod
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS
