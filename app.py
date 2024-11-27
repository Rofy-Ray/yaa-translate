import os
from flask import Flask, request, jsonify
from google.cloud import translate_v3
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

class TranslationService:
    def __init__(self):
        self.language_map = {
            'english': {
                'code': 'en-GB', 
                'full_name': 'English'
            },
            'twi': {
                'code': 'ak', 
                'full_name': 'Twi (Akan)'
            },
            'ga': {
                'code': 'gaa', 
                'full_name': 'Ga'
            },
            'ewe': {
                'code': 'ee', 
                'full_name': 'Ewe'
            }
        }
        
        self.project_id = os.getenv("PROJECT_ID")
        if not self.project_id:
            raise ValueError("PROJECT_ID environment variable must be set")
        
        self.client = translate_v3.TranslationServiceClient()
        self.parent = f"projects/{self.project_id}/locations/global"

    def translate_text(self, text: str, source_lang: str, target_lang: str) -> Dict:
        """
        Translate text between supported languages
        
        Args:
            text (str): Text to translate
            source_lang (str): Source language name (lowercase)
            target_lang (str): Target language name (lowercase)
        
        Returns:
            dict: Translation details
        """
        try:
            source_code = self.language_map[source_lang]['code']
            target_code = self.language_map[target_lang]['code']
        except KeyError:
            raise ValueError("Invalid language names")

        try:
            response = self.client.translate_text(
                contents=[text],
                target_language_code=target_code,
                source_language_code=source_code,
                parent=self.parent,
                mime_type="text/plain"
            )
            
            return {
                'original_text': text,
                'translated_text': response.translations[0].translated_text,
                'source_language': self.language_map[source_lang]['full_name'],
                'target_language': self.language_map[target_lang]['full_name']
            }
        except Exception as e:
            raise RuntimeError(f"Translation error: {str(e)}")

    def get_supported_languages(self) -> Dict[str, str]:
        """
        Get list of supported languages
        
        Returns:
            dict: Supported language names and full names
        """
        return {lang: details['full_name'] for lang, details in self.language_map.items()}

translation_service = TranslationService()

@app.route('/translate', methods=['POST'])
def translate():
    """
    Translation endpoint with flexible language input
    """
    data = request.json
    
    if not all(key in data for key in ['text', 'source_lang', 'target_lang']):
        return jsonify({
            'error': 'Missing required parameters: text, source_lang, target_lang'
        }), 400
    
    try:
        translation_result = translation_service.translate_text(
            text=data['text'], 
            source_lang=data['source_lang'].lower(), 
            target_lang=data['target_lang'].lower()
        )
        
        return jsonify(translation_result)
    
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except RuntimeError as re:
        return jsonify({'error': str(re)}), 500

@app.route('/languages', methods=['GET'])
def supported_languages():
    """
    Endpoint to retrieve supported languages
    """
    return jsonify(translation_service.get_supported_languages())

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv('PORT', 8080)))