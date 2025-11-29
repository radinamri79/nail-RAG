"""
Startup Service - Initialize Weaviate, OpenAI, and warm up services
"""
from typing import Dict, Any
import time
from app.services.weaviate_service import weaviate_service
from app.models.weaviate_client import check_weaviate_health
from app.utils.openai_client import get_openai_client
from app.utils.prompt_loader import prompt_loader
from app.services.chat_service import chat_service
from app.config import settings
from app.logger import get_logger

logger = get_logger("startup_service")


class StartupService:
    """Service to handle application startup and initialization."""
    
    def __init__(self):
        self.initialization_status = {
            "weaviate_collections": False,
            "weaviate_health": False,
            "openai_client": False,
            "prompts_loaded": False,
            "chat_service": False,
            "system_ready": False
        }
    
    async def initialize_weaviate_collections(self) -> bool:
        """Initialize all required Weaviate collections."""
        try:
            logger.info("📊 Initializing Weaviate collections...")
            
            success = await weaviate_service.ensure_collections_exist()
            
            if success:
                logger.info("✅ Weaviate collections initialized successfully")
                self.initialization_status["weaviate_collections"] = True
                return True
            else:
                logger.error("❌ Failed to initialize Weaviate collections")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error initializing Weaviate collections: {e}")
            return False
    
    async def check_weaviate_health(self) -> bool:
        """Check Weaviate connection health."""
        try:
            logger.info("🔍 Checking Weaviate health...")
            
            is_healthy = check_weaviate_health()
            
            if is_healthy:
                logger.info("✅ Weaviate health check passed")
                self.initialization_status["weaviate_health"] = True
            else:
                logger.warning("⚠️ Weaviate health check failed")
            
            return is_healthy
            
        except Exception as e:
            logger.warning(f"⚠️ Weaviate health check error: {e}")
            return False
    
    async def initialize_openai_client(self) -> bool:
        """Initialize and verify OpenAI client."""
        try:
            logger.info("🤖 Initializing OpenAI client...")
            
            # Try to get client (will raise error if API key missing)
            client = get_openai_client()
            
            # Test connection with a simple call (optional, might cost credits)
            # We'll skip the actual API call to avoid costs, just verify client creation
            logger.info("✅ OpenAI client initialized successfully")
            self.initialization_status["openai_client"] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Error initializing OpenAI client: {e}")
            return False
    
    async def load_prompts(self) -> bool:
        """Load and cache all prompts."""
        try:
            logger.info("📝 Loading prompts...")
            
            # Prompts are already loaded in prompt_loader.__init__
            # Just verify they're loaded
            available = prompt_loader.list_available_prompts()
            
            if available:
                logger.info(f"✅ Loaded {len(available)} prompts: {', '.join(available)}")
                self.initialization_status["prompts_loaded"] = True
                return True
            else:
                logger.warning("⚠️ No prompts loaded")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error loading prompts: {e}")
            return False
    
    async def initialize_chat_service(self) -> bool:
        """Initialize chat service."""
        try:
            logger.info("💬 Initializing chat service...")
            
            await chat_service.initialize()
            
            logger.info("✅ Chat service initialized successfully")
            self.initialization_status["chat_service"] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Error initializing chat service: {e}")
            return False
    
    async def warm_up_services(self) -> bool:
        """Warm up services and cache frequently used data."""
        try:
            logger.info("🔥 Warming up services...")
            
            # Pre-load prompts (already done, but verify)
            await self.load_prompts()
            
            # Initialize chat service
            await self.initialize_chat_service()
            
            logger.info("✅ Service warm-up completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error during service warm-up: {e}")
            return False
    
    async def run_startup_sequence(self) -> Dict[str, Any]:
        """Run the complete startup sequence."""
        logger.info("🚀 Starting Nail RAG Service initialization sequence...")
        
        startup_results = {
            "started_at": time.time(),
            "weaviate_collections_ready": False,
            "weaviate_health_ready": False,
            "openai_ready": False,
            "prompts_ready": False,
            "chat_service_ready": False,
            "services_warmed": False,
            "total_time": 0,
            "system_ready": False
        }
        
        start_time = time.time()
        
        try:
            # Step 1: Initialize Weaviate collections
            logger.info("📊 Step 1: Initializing Weaviate collections...")
            weaviate_success = await self.initialize_weaviate_collections()
            startup_results["weaviate_collections_ready"] = weaviate_success
            
            # Step 2: Check Weaviate health
            logger.info("🔍 Step 2: Checking Weaviate health...")
            health_success = await self.check_weaviate_health()
            startup_results["weaviate_health_ready"] = health_success
            
            # Step 3: Initialize OpenAI client
            logger.info("🤖 Step 3: Initializing OpenAI client...")
            openai_success = await self.initialize_openai_client()
            startup_results["openai_ready"] = openai_success
            
            # Step 4: Load prompts
            logger.info("📝 Step 4: Loading prompts...")
            prompts_success = await self.load_prompts()
            startup_results["prompts_ready"] = prompts_success
            
            # Step 5: Warm up services
            logger.info("🔥 Step 5: Warming up services...")
            warmup_success = await self.warm_up_services()
            startup_results["chat_service_ready"] = warmup_success
            startup_results["services_warmed"] = warmup_success
            
            # Calculate total time
            total_time = time.time() - start_time
            startup_results["total_time"] = total_time
            
            # Determine if system is ready
            # System needs OpenAI and services warmed
            # Weaviate can be degraded (will retry on first request)
            system_ready = (
                openai_success and
                prompts_success and
                warmup_success
            )
            startup_results["system_ready"] = system_ready
            self.initialization_status["system_ready"] = system_ready
            
            if system_ready:
                logger.info(f"🎉 Nail RAG Service initialization completed successfully in {total_time:.2f}s")
                logger.info("✅ System Status:")
                logger.info(f"   📊 Weaviate Collections: {'✅ Ready' if weaviate_success else '❌ Failed'}")
                logger.info(f"   🔍 Weaviate Health: {'✅ Ready' if health_success else '⚠️ Warning'}")
                logger.info(f"   🤖 OpenAI: {'✅ Ready' if openai_success else '❌ Failed'}")
                logger.info(f"   📝 Prompts: {'✅ Ready' if prompts_success else '❌ Failed'}")
                logger.info(f"   💬 Chat Service: {'✅ Ready' if warmup_success else '❌ Failed'}")
                logger.info("🚀 System ready for production!")
            else:
                logger.error(f"❌ Nail RAG Service initialization failed after {total_time:.2f}s")
                logger.error("❌ System Status:")
                logger.error(f"   📊 Weaviate Collections: {'✅ Ready' if weaviate_success else '❌ Failed'}")
                logger.error(f"   🔍 Weaviate Health: {'✅ Ready' if health_success else '⚠️ Warning'}")
                logger.error(f"   🤖 OpenAI: {'✅ Ready' if openai_success else '❌ Failed'}")
                logger.error(f"   📝 Prompts: {'✅ Ready' if prompts_success else '❌ Failed'}")
                logger.error(f"   💬 Chat Service: {'✅ Ready' if warmup_success else '❌ Failed'}")
            
            return startup_results
            
        except Exception as e:
            total_time = time.time() - start_time
            startup_results["total_time"] = total_time
            logger.error(f"❌ Critical error during startup sequence: {e}")
            startup_results["error"] = str(e)
            return startup_results
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status."""
        return {
            "system_ready": self.initialization_status["system_ready"],
            "components": self.initialization_status.copy()
        }


# Global instance
startup_service = StartupService()

# Convenience functions
async def initialize_system() -> Dict[str, Any]:
    """Initialize the complete Nail RAG Service system."""
    return await startup_service.run_startup_sequence()

def is_system_ready() -> bool:
    """Check if the system is ready for operations."""
    return startup_service.get_system_status()["system_ready"]

