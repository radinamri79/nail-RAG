"""
Prompt Loader Utility

Centralized prompt loading and caching for the Nail RAG Service.
All prompts are stored in separate files for easy maintenance.
"""
import os
from typing import Dict, Optional
from pathlib import Path
from app.config import settings
from app.logger import get_logger

logger = get_logger("prompt_loader")


class PromptLoader:
    """Utility class for loading and caching prompts from files."""
    
    def __init__(self):
        self._cache: Dict[str, str] = {}
        self._load_all_prompts()
    
    def _load_prompt_file(self, file_path: str) -> str:
        """Load a single prompt file."""
        try:
            # Resolve path relative to project root
            if not os.path.isabs(file_path):
                file_path = Path(__file__).parent.parent.parent / file_path
            
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read().strip()
                logger.debug(f"Loaded prompt from {file_path}")
                return content
        except FileNotFoundError:
            logger.error(f"Prompt file not found: {file_path}")
            return ""
        except Exception as e:
            logger.error(f"Error loading prompt from {file_path}: {e}")
            return ""
    
    def _load_all_prompts(self):
        """Load all prompts into cache."""
        prompt_configs = {
            # RAG prompts
            'rag_system': settings.prompt_rag_system,
            'image_analysis': settings.prompt_image_analysis,
            
            # Multilingual prompts
            'multilingual': settings.prompt_multilingual,
            'language_detection': settings.prompt_language_detection,
            'translate_to_english': settings.prompt_translate_to_english,
            'translate_response': settings.prompt_translate_response,
        }
        
        loaded_count = 0
        for prompt_name, file_path in prompt_configs.items():
            content = self._load_prompt_file(file_path)
            if content:
                self._cache[prompt_name] = content
                loaded_count += 1
        
        logger.info(f"✅ Loaded {loaded_count}/{len(prompt_configs)} prompts into cache")
    
    def get_prompt(self, prompt_name: str, **kwargs) -> str:
        """
        Get a prompt by name and optionally format it with variables.
        
        Args:
            prompt_name: Name of the prompt to retrieve
            **kwargs: Variables to substitute in the prompt
            
        Returns:
            Formatted prompt string
        """
        if prompt_name not in self._cache:
            logger.warning(f"Prompt '{prompt_name}' not found in cache")
            return ""
        
        prompt = self._cache[prompt_name]
        
        # Replace placeholders with provided variables
        if kwargs:
            try:
                # Replace {{variable}} style placeholders
                for key, value in kwargs.items():
                    placeholder = f"{{{{{key}}}}}"
                    prompt = prompt.replace(placeholder, str(value))
                
                # Log if any placeholders remain unreplaced
                import re
                remaining_placeholders = re.findall(r'\{\{[^}]+\}\}', prompt)
                if remaining_placeholders:
                    logger.debug(f"Unreplaced placeholders in '{prompt_name}': {remaining_placeholders}")
                    
            except Exception as e:
                logger.error(f"Error formatting prompt '{prompt_name}': {e}")
        
        return prompt
    
    def reload_prompt(self, prompt_name: str) -> bool:
        """Reload a specific prompt from file."""
        prompt_configs = {
            'rag_system': settings.prompt_rag_system,
            'image_analysis': settings.prompt_image_analysis,
            'multilingual': settings.prompt_multilingual,
            'language_detection': settings.prompt_language_detection,
            'translate_to_english': settings.prompt_translate_to_english,
            'translate_response': settings.prompt_translate_response,
        }
        
        if prompt_name in prompt_configs:
            file_path = prompt_configs[prompt_name]
            content = self._load_prompt_file(file_path)
            if content:
                self._cache[prompt_name] = content
                logger.info(f"✅ Reloaded prompt '{prompt_name}' from {file_path}")
                return True
        
        logger.error(f"❌ Failed to reload prompt '{prompt_name}'")
        return False
    
    def reload_all_prompts(self):
        """Reload all prompts from files."""
        self._cache.clear()
        self._load_all_prompts()
    
    def list_available_prompts(self) -> list:
        """Get list of available prompt names."""
        return list(self._cache.keys())


# Global instance
prompt_loader = PromptLoader()


# Convenience functions
def get_prompt(prompt_name: str, **kwargs) -> str:
    """Get a formatted prompt."""
    return prompt_loader.get_prompt(prompt_name, **kwargs)

