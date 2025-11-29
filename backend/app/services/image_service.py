"""
Image service for GPT-5.1 vision analysis of nail images
"""
from typing import Optional, Dict, Any
import base64
from io import BytesIO
from PIL import Image
from app.utils.openai_client import get_openai_client
from app.utils.prompt_loader import get_prompt
from app.config import settings
from app.logger import get_logger

logger = get_logger("image_service")


class ImageService:
    """Service for analyzing nail images using GPT-5.1 vision."""
    
    def __init__(self):
        self.client = None
        self.max_image_size = 20 * 1024 * 1024  # 20MB max
        self.supported_formats = ['JPEG', 'PNG', 'WebP']
    
    def _get_client(self):
        """Lazy load OpenAI client."""
        if self.client is None:
            self.client = get_openai_client()
        return self.client
    
    def _encode_image_to_base64(self, image: Image.Image) -> str:
        """
        Encode PIL Image to base64 string.
        
        Args:
            image: PIL Image object
            
        Returns:
            Base64 encoded string
        """
        buffered = BytesIO()
        # Convert to RGB if necessary (for JPEG)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        image.save(buffered, format="JPEG", quality=85)
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
        return img_str
    
    def _validate_image(self, image: Image.Image) -> bool:
        """
        Validate image format and size.
        
        Args:
            image: PIL Image object
            
        Returns:
            bool: True if valid
        """
        if image.format not in self.supported_formats:
            logger.warning(f"⚠️ Unsupported image format: {image.format}")
            return False
        
        # Check image size (in bytes)
        buffered = BytesIO()
        image.save(buffered, format=image.format)
        size = len(buffered.getvalue())
        
        if size > self.max_image_size:
            logger.warning(f"⚠️ Image too large: {size} bytes (max: {self.max_image_size})")
            return False
        
        return True
    
    async def analyze_nail_image(
        self,
        image_data: bytes,
        user_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze nail image using GPT-5.1 vision.
        
        Args:
            image_data: Image file bytes
            user_query: Optional user query about the image
            
        Returns:
            Dictionary with analysis results
        """
        try:
            # Load and validate image
            image = Image.open(BytesIO(image_data))
            
            if not self._validate_image(image):
                return {
                    "error": "Invalid image format or size",
                    "analysis": None
                }
            
            # Encode to base64
            base64_image = self._encode_image_to_base64(image)
            
            # Load image analysis prompt
            prompt_template = get_prompt("image_analysis")
            
            # Build analysis prompt
            if user_query:
                analysis_prompt = f"""{prompt_template}

User's question: {user_query}

Please analyze the nail image and provide detailed information about:
1. Nail shape (round, square, almond, stiletto, etc.)
2. Nail color(s) and design
3. Nail condition and health
4. Any specific style or pattern
5. Recommendations based on what you see

Provide a comprehensive analysis that can be used to answer the user's question."""
            else:
                analysis_prompt = f"""{prompt_template}

Please analyze the nail image and provide detailed information about:
1. Nail shape (round, square, almond, stiletto, etc.)
2. Nail color(s) and design
3. Nail condition and health
4. Any specific style or pattern
5. General observations and recommendations"""
            
            # Call GPT-5.1 vision
            client = self._get_client()
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": analysis_prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500,
                temperature=0.3  # Lower temperature for more factual analysis
            )
            
            analysis = response.choices[0].message.content
            
            logger.info("✅ Image analysis completed")
            
            return {
                "analysis": analysis,
                "image_format": image.format,
                "image_size": image.size,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"❌ Error analyzing image: {e}")
            return {
                "error": str(e),
                "analysis": None
            }
    
    async def analyze_nail_image_from_file(
        self,
        file_path: str,
        user_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze nail image from file path.
        
        Args:
            file_path: Path to image file
            user_query: Optional user query
            
        Returns:
            Dictionary with analysis results
        """
        try:
            with open(file_path, 'rb') as f:
                image_data = f.read()
            
            return await self.analyze_nail_image(image_data, user_query)
            
        except Exception as e:
            logger.error(f"❌ Error reading image file: {e}")
            return {
                "error": str(e),
                "analysis": None
            }
    
    def extract_key_features(self, analysis: str) -> Dict[str, str]:
        """
        Extract key features from analysis text for query enhancement.
        
        Args:
            analysis: Analysis text from GPT-5.1
            
        Returns:
            Dictionary with extracted features
        """
        features = {
            "shape": None,
            "color": None,
            "style": None,
            "condition": None
        }
        
        # Simple keyword extraction (can be enhanced with NLP)
        analysis_lower = analysis.lower()
        
        # Extract shape
        shapes = ['round', 'square', 'almond', 'stiletto', 'coffin', 'oval', 'squoval']
        for shape in shapes:
            if shape in analysis_lower:
                features["shape"] = shape
                break
        
        # Extract color (look for color words)
        colors = ['red', 'pink', 'blue', 'green', 'purple', 'black', 'white', 'nude', 'beige', 'coral', 'burgundy']
        found_colors = [color for color in colors if color in analysis_lower]
        if found_colors:
            features["color"] = ", ".join(found_colors[:3])  # Top 3 colors
        
        return features


# Global instance
image_service = ImageService()

