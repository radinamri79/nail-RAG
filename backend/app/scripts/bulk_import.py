"""
Bulk import script for nail guides dataset into Weaviate
"""
import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.models.pydantic_models import NailGuideDocument
from app.services.weaviate_service import weaviate_service
from app.constants import CollectionNames
from app.logger import get_logger

logger = get_logger("bulk_import")


async def load_dataset(file_path: str) -> Dict[str, List[Dict]]:
    """
    Load the nail guides dataset JSON file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Dictionary with category names as keys and document lists as values
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"✅ Loaded dataset from {file_path}")
        logger.info(f"📊 Found {len(data)} categories")
        
        for category, documents in data.items():
            logger.info(f"   - {category}: {len(documents)} documents")
        
        return data
        
    except Exception as e:
        logger.error(f"❌ Error loading dataset: {e}")
        raise


async def import_category(
    category_name: str,
    documents: List[Dict],
    collection_name: str
) -> Dict[str, int]:
    """
    Import all documents from a category into Weaviate.
    
    Args:
        category_name: Category name
        documents: List of document dictionaries
        collection_name: Target Weaviate collection name
        
    Returns:
        Statistics dictionary (imported, skipped, failed)
    """
    stats = {"imported": 0, "skipped": 0, "failed": 0}
    
    logger.info(f"📦 Importing {len(documents)} documents from '{category_name}' into '{collection_name}'...")
    
    for idx, doc_data in enumerate(documents, 1):
        try:
            # Create document model
            document = NailGuideDocument(**doc_data)
            
            # Check if already exists
            exists = await weaviate_service.check_document_exists(
                document.id,
                collection_name
            )
            
            if exists:
                logger.debug(f"   [{idx}/{len(documents)}] Document {document.id} already exists, skipping")
                stats["skipped"] += 1
                continue
            
            # Import document
            success = await weaviate_service.import_document(document, collection_name)
            
            if success:
                stats["imported"] += 1
                if idx % 10 == 0:
                    logger.info(f"   Progress: {idx}/{len(documents)} documents processed")
            else:
                stats["failed"] += 1
                logger.warning(f"   ⚠️ Failed to import document {document.id}")
                
        except Exception as e:
            stats["failed"] += 1
            logger.error(f"   ❌ Error processing document {doc_data.get('id', 'unknown')}: {e}")
    
    return stats


async def bulk_import(dataset_path: str = "datasets/nail_guides_final_dataset.json") -> None:
    """
    Main bulk import function.
    
    Args:
        dataset_path: Path to dataset JSON file
    """
    logger.info("🚀 Starting bulk import process...")
    
    try:
        # Ensure collections exist
        logger.info("📋 Ensuring Weaviate collections exist...")
        await weaviate_service.ensure_collections_exist()
        
        # Load dataset
        logger.info(f"📂 Loading dataset from {dataset_path}...")
        dataset = await load_dataset(dataset_path)
        
        # Category to collection mapping
        category_mapping = {
            "Color Theory & Outfit Matching (Nail + Clothes)": CollectionNames.NAIL_COLOR_THEORY,
            "Skin Tone – Nail Color Advice": CollectionNames.NAIL_SKIN_TONE,
            "Seasonal / Occasion-Based Nail Advice": CollectionNames.NAIL_SEASONAL,
            "Hand / Finger Shape – Nail Shape & Design Advice": CollectionNames.NAIL_SHAPE,
        }
        
        # Import each category
        total_stats = {"imported": 0, "skipped": 0, "failed": 0}
        
        for category_name, documents in dataset.items():
            collection_name = category_mapping.get(category_name)
            
            if not collection_name:
                logger.warning(f"⚠️ Unknown category: {category_name}, skipping")
                continue
            
            stats = await import_category(category_name, documents, collection_name)
            
            # Update totals
            for key in total_stats:
                total_stats[key] += stats[key]
            
            logger.info(f"✅ Category '{category_name}' completed: {stats}")
        
        # Final summary
        logger.info("=" * 60)
        logger.info("📊 BULK IMPORT SUMMARY")
        logger.info("=" * 60)
        logger.info(f"✅ Imported: {total_stats['imported']} documents")
        logger.info(f"⏭️  Skipped: {total_stats['skipped']} documents (already exist)")
        logger.info(f"❌ Failed: {total_stats['failed']} documents")
        logger.info(f"📈 Total: {sum(total_stats.values())} documents processed")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Bulk import failed: {e}")
        raise


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Bulk import nail guides dataset into Weaviate")
    parser.add_argument(
        "--dataset",
        type=str,
        default="datasets/nail_guides_final_dataset.json",
        help="Path to dataset JSON file"
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip documents that already exist (default: True)"
    )
    
    args = parser.parse_args()
    
    # Resolve dataset path
    dataset_path = Path(args.dataset)
    if not dataset_path.is_absolute():
        dataset_path = Path(__file__).parent.parent.parent / dataset_path
    
    if not dataset_path.exists():
        logger.error(f"❌ Dataset file not found: {dataset_path}")
        sys.exit(1)
    
    await bulk_import(str(dataset_path))


if __name__ == "__main__":
    asyncio.run(main())

