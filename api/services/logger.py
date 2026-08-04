"""
api/services/logger.py
------------------------
Sets up structured logging for the whole app.

WHY NOT JUST USE print()?
print() statements are fine for quick debugging, but in a real running
server, you need: timestamps (when did this happen?), severity levels
(is this just informational, or a real problem?), and a consistent format
you can search through later, especially once there are thousands of log
lines from real traffic. Python's built-in `logging` module gives us all
of this for free.
"""

import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


def get_logger(name: str) -> logging.Logger:
    """Each file that wants to log gets its own named logger, e.g.
    logger = get_logger(__name__) - this way log lines show exactly
    which file/module they came from, which is very useful when
    debugging a real issue in a large codebase."""
    return logging.getLogger(name)
