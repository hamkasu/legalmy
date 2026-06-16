import logging
import re
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from app.models.case_embedding import CaseEmbedding

logger = logging.getLogger(__name__)

# Model loaded at module level
try:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('intfloat/multilingual-e5-large')
except Exception as e:
    logger.warning(f"Could not load sentence transformer model: {e}")
    model = None

def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
    """
    Split text into chunks respecting token boundaries.

    Args:
        text: Input text to chunk
        chunk_size: Target chunk size (approximate tokens)
        overlap: Overlap between chunks in tokens

    Returns:
        List of text chunks
    """
    if not text:
        return []

    # Split on sentences using regex
    sentences = re.split(r'(?<=[.!?])\s+', text)

    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        # Approximate token count (rough: 1 token per 4 chars)
        sentence_length = len(sentence) // 4

        if current_length + sentence_length > chunk_size and current_chunk:
            # Save chunk and start new one
            chunk_text = ' '.join(current_chunk)
            chunks.append(chunk_text)

            # Add overlap from previous chunk
            if len(current_chunk) > 1:
                current_chunk = current_chunk[-overlap // 50:]  # Keep last few sentences
                current_length = sum(len(s) // 4 for s in current_chunk)
            else:
                current_chunk = []
                current_length = 0

        current_chunk.append(sentence)
        current_length += sentence_length

    # Add final chunk
    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks

def embed_chunks(chunks: List[str]) -> List[List[float]]:
    """
    Generate embeddings for text chunks.

    Args:
        chunks: List of text chunks

    Returns:
        List of 1024-dimensional embedding vectors
    """
    if not chunks or model is None:
        return []

    try:
        embeddings = model.encode(chunks, convert_to_list=True)
        return embeddings
    except Exception as e:
        logger.error(f"Error embedding chunks: {e}")
        return []

async def embed_and_store_case(
    case_id: str,
    full_text: str,
    db: AsyncSession,
) -> bool:
    """
    Chunk text, generate embeddings, and store in database.

    Args:
        case_id: Case ID
        full_text: Full case text
        db: AsyncSession

    Returns:
        True if successful, False otherwise
    """
    try:
        # Chunk the text
        chunks = chunk_text(full_text)
        if not chunks:
            logger.warning(f"No chunks generated for case {case_id}")
            return False

        # Generate embeddings
        embeddings = embed_chunks(chunks)
        if not embeddings:
            logger.warning(f"No embeddings generated for case {case_id}")
            return False

        # Delete existing embeddings
        await db.execute(
            delete(CaseEmbedding).where(CaseEmbedding.case_id == case_id)
        )

        # Insert new embeddings
        for chunk_index, embedding in enumerate(embeddings):
            case_embedding = CaseEmbedding(
                case_id=case_id,
                embedding=embedding,
                chunk_index=chunk_index,
            )
            db.add(case_embedding)

        await db.commit()
        logger.info(f"Embedded and stored {len(embeddings)} chunks for case {case_id}")
        return True

    except Exception as e:
        logger.error(f"Error embedding and storing case {case_id}: {e}")
        await db.rollback()
        return False
