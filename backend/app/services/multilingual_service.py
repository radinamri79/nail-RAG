"""
Multilingual service for Finnish and Swedish support
"""
from typing import Dict, Optional
from app.utils.openai_client import get_openai_client
from app.utils.prompt_loader import get_prompt
from app.config import settings
from app.logger import get_logger

logger = get_logger("multilingual_service")


class MultilingualService:
    """Service for language detection and translation."""
    
    def __init__(self):
        self.client = None
        self.supported_languages = {
            "en": "English",
            "fi": "Finnish",
            "sv": "Swedish"
        }
    
    def _get_client(self):
        """Lazy load OpenAI client."""
        if self.client is None:
            self.client = get_openai_client()
        return self.client
    
    async def detect_language(self, text: str) -> Dict[str, str]:
        """
        Detect the language of user input.
        
        Args:
            text: User input text
            
        Returns:
            Dictionary with detected_language code and language_name
        """
        try:
            # Load language detection prompt
            prompt_template = get_prompt("language_detection")
            
            prompt = f"""{prompt_template}

Text to analyze: "{text}"

Respond with ONLY the language code (en, fi, or sv) and language name on separate lines."""
            
            client = self._get_client()
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a language detection assistant. Respond with language code and name only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=50
            )
            
            result = response.choices[0].message.content.strip()
            lines = [line.strip() for line in result.split('\n') if line.strip()]
            
            # Extract language code (first line, should be 2 chars)
            detected_code = "en"  # default
            language_name = "English"
            
            for line in lines:
                line_lower = line.lower()
                if line_lower in ['en', 'fi', 'sv']:
                    detected_code = line_lower
                    language_name = self.supported_languages.get(detected_code, "English")
                    break
                elif 'finnish' in line_lower or 'suomi' in line_lower:
                    detected_code = "fi"
                    language_name = "Finnish"
                    break
                elif 'swedish' in line_lower or 'ruotsi' in line_lower:
                    detected_code = "sv"
                    language_name = "Swedish"
                    break
            
            logger.debug(f"✅ Detected language: {detected_code} ({language_name})")
            
            return {
                "detected_language": detected_code,
                "language_name": language_name
            }
            
        except Exception as e:
            logger.error(f"❌ Error detecting language: {e}")
            return {
                "detected_language": "en",
                "language_name": "English"
            }
    
    async def translate_to_english(self, text: str, source_language: str) -> str:
        """
        Translate text to English for RAG processing.
        
        Args:
            text: Text to translate
            source_language: Source language code (fi, sv, en)
            
        Returns:
            Translated text in English
        """
        if source_language == "en":
            return text
        
        try:
            prompt_template = get_prompt("translate_to_english")
            
            language_name = self.supported_languages.get(source_language, "Unknown")
            
            prompt = f"""{prompt_template}

Source language: {language_name} ({source_language})
Text to translate: "{text}"

Translate this text to English. Preserve the meaning and intent."""
            
            client = self._get_client()
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a professional translator. Translate accurately while preserving meaning."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            translated = response.choices[0].message.content.strip()
            
            logger.debug(f"✅ Translated to English: {text[:50]}... -> {translated[:50]}...")
            
            return translated
            
        except Exception as e:
            logger.error(f"❌ Error translating to English: {e}")
            return text  # Return original if translation fails
    
    async def translate_response(
        self,
        text: str,
        target_language: str
    ) -> str:
        """
        Translate English response to target language.
        
        Args:
            text: English text to translate
            target_language: Target language code (fi, sv, en)
            
        Returns:
            Translated text
        """
        if target_language == "en":
            return text
        
        try:
            prompt_template = get_prompt("translate_response")
            
            language_name = self.supported_languages.get(target_language, "Unknown")
            
            prompt = f"""{prompt_template}

Target language: {language_name} ({target_language})
English text to translate: "{text}"

Translate this text to {language_name}. Make it natural and fluent."""
            
            client = self._get_client()
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": f"You are a professional translator. Translate to {language_name} naturally and fluently."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=1000
            )
            
            translated = response.choices[0].message.content.strip()
            
            logger.debug(f"✅ Translated to {target_language}: {text[:50]}... -> {translated[:50]}...")
            
            return translated
            
        except Exception as e:
            logger.error(f"❌ Error translating response: {e}")
            return text  # Return original if translation fails
    
    async def process_multilingual_query(
        self,
        query: str
    ) -> Dict[str, str]:
        """
        Process multilingual query: detect language and translate to English.
        
        Args:
            query: User query in any supported language
            
        Returns:
            Dictionary with original_query, detected_language, and translated_query
        """
        # Detect language
        detection = await self.detect_language(query)
        detected_language = detection["detected_language"]
        
        # Translate to English if needed
        if detected_language != "en":
            translated_query = await self.translate_to_english(query, detected_language)
        else:
            translated_query = query
        
        return {
            "original_query": query,
            "detected_language": detected_language,
            "language_name": detection["language_name"],
            "translated_query": translated_query
        }


# Global instance
multilingual_service = MultilingualService()

