"""
Structured logging for ASHA AI
Tracks retrieval trails, errors, and performance metrics
"""

import sys
from pathlib import Path
from loguru import logger
from config import LOGS_DIR


# Remove default handler
logger.remove()

# Console handler (INFO and above)
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO"
)

# File handler for all logs
logger.add(
    LOGS_DIR / "asha_ai_{time:YYYY-MM-DD}.log",
    rotation="00:00",  # New file daily
    retention="30 days",
    compression="zip",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG"
)

# Retrieval trail handler (for explainability)
logger.add(
    LOGS_DIR / "retrieval_trail_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="90 days",
    filter=lambda record: "retrieval" in record["extra"],
    format="{time:YYYY-MM-DD HH:mm:ss} | {extra[user_id]} | {extra[query]} | {extra[results]}",
    level="INFO"
)

# Error handler
logger.add(
    LOGS_DIR / "errors_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="90 days",
    level="ERROR",
    backtrace=True,
    diagnose=True
)


def log_retrieval(user_id: str, query: str, results: list, collection: str):
    """Log retrieval event for explainability"""
    logger.bind(
        retrieval=True,
        user_id=user_id,
        query=query[:100],  # Truncate long queries
        results=len(results),
        collection=collection
    ).info(f"Retrieved {len(results)} results from {collection}")


def log_health_signal(user_id: str, signal_type: str, risk_score: float):
    """Log health signal storage"""
    logger.info(f"Health signal stored | User: {user_id[:8]}... | Type: {signal_type} | Risk: {risk_score:.2f}")


def log_asha_action(action: str, details: dict):
    """Log ASHA worker actions"""
    logger.info(f"ASHA Action: {action} | Details: {details}")
