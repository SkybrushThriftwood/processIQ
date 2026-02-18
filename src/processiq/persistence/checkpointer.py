"""LangGraph checkpointer for conversation state persistence.

Uses SqliteSaver to persist agent state across sessions, enabling:
- Resume conversations after browser refresh
- Access conversation history
- Multi-turn interactions with state continuity

The checkpointer is a singleton - one instance per application lifetime.
"""

import logging
from pathlib import Path
from typing import Any

from processiq.config import settings

logger = logging.getLogger(__name__)

# Singleton checkpointer instance
_checkpointer: Any = None
_connection: Any = None


def get_checkpointer() -> Any:
    """Get or create the SqliteSaver checkpointer.

    The checkpointer is created lazily on first access and reused
    for the lifetime of the application.

    Returns:
        SqliteSaver instance, or None if persistence is disabled.

    Raises:
        ImportError: If langgraph-checkpoint-sqlite is not installed.
    """
    global _checkpointer, _connection

    if not settings.persistence_enabled:
        logger.debug("Persistence disabled, returning None checkpointer")
        return None

    if _checkpointer is not None:
        return _checkpointer

    try:
        from langgraph.checkpoint.sqlite import SqliteSaver
    except ImportError as e:
        logger.error(
            "langgraph-checkpoint-sqlite not installed. "
            "Install with: uv add langgraph-checkpoint-sqlite"
        )
        raise ImportError(
            "Persistence requires langgraph-checkpoint-sqlite. "
            "Install with: uv add langgraph-checkpoint-sqlite"
        ) from e

    # Ensure database directory exists
    db_path = Path(settings.persistence_db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Initializing SqliteSaver at: %s", db_path)

    # Create connection and checkpointer
    # SqliteSaver manages its own connection
    import sqlite3

    _connection = sqlite3.connect(str(db_path), check_same_thread=False)
    _checkpointer = SqliteSaver(_connection)

    # Initialize schema
    _checkpointer.setup()

    logger.info("SqliteSaver initialized successfully")
    return _checkpointer


def close_checkpointer() -> None:
    """Close the checkpointer and its database connection.

    Call this when shutting down the application to ensure
    all data is flushed and resources are released.
    """
    global _checkpointer, _connection

    if _connection is not None:
        try:
            _connection.close()
            logger.info("Checkpointer connection closed")
        except Exception as e:
            logger.warning("Error closing checkpointer connection: %s", e)
        finally:
            _connection = None
            _checkpointer = None


def get_checkpoint_history(thread_id: str, limit: int = 10) -> list[dict[str, Any]]:
    """Get checkpoint history for a thread.

    Args:
        thread_id: The thread ID to get history for.
        limit: Maximum number of checkpoints to return.

    Returns:
        List of checkpoint metadata dicts, newest first.
    """
    checkpointer = get_checkpointer()
    if checkpointer is None:
        return []

    try:
        config = {"configurable": {"thread_id": thread_id}}
        checkpoints = list(checkpointer.list(config, limit=limit))
        return [
            {
                "thread_id": cp.config["configurable"]["thread_id"],
                "checkpoint_id": cp.config["configurable"].get("checkpoint_id"),
                "checkpoint_ns": cp.config["configurable"].get("checkpoint_ns", ""),
            }
            for cp in checkpoints
        ]
    except Exception as e:
        logger.warning("Error getting checkpoint history: %s", e)
        return []


def delete_thread(thread_id: str) -> bool:
    """Delete all checkpoints for a thread.

    Args:
        thread_id: The thread ID to delete.

    Returns:
        True if deletion was successful, False otherwise.
    """
    global _connection

    if _connection is None:
        logger.warning("No connection available for deletion")
        return False

    try:
        cursor = _connection.cursor()
        # Delete from checkpoints table (SqliteSaver uses this table name)
        cursor.execute(
            "DELETE FROM checkpoints WHERE thread_id = ?",
            (thread_id,),
        )
        _connection.commit()
        deleted = bool(cursor.rowcount > 0)
        if deleted:
            logger.info("Deleted checkpoints for thread: %s", thread_id)
        return deleted
    except Exception as e:
        logger.warning("Error deleting thread: %s", e)
        return False
