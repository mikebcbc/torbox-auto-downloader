import logging
import sys
import os
import fcntl
from config import Config
from watcher import TorBoxWatcherApp
from version import __version__, __app_name__

logger = logging.getLogger(__name__)

# Lock file to prevent multiple instances
LOCK_FILE = "/tmp/torbox_watcher.lock"


def acquire_lock():
    """
    Acquire an exclusive lock to prevent multiple instances from running.
    
    Returns:
        file object if lock acquired, None otherwise
    """
    try:
        lock_file = open(LOCK_FILE, 'w')
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock_file.write(str(os.getpid()))
        lock_file.flush()
        return lock_file
    except (IOError, OSError) as e:
        logger.error(f"Another instance is already running. Exiting. ({e})")
        return None


def main():
    """Main entry point for the TorBox Watcher application.

    Initializes and runs the TorBoxWatcherApp. Handles
    configuration validation and potential startup errors.

    Raises:
        ValueError: If there is a configuration error.
        Exception: For any other application startup errors.
    """
    # Acquire lock to prevent multiple instances
    lock_file = acquire_lock()
    if lock_file is None:
        sys.exit(1)
    
    try:
        # Display version information
        logger.info("=" * 60)
        logger.info(f"{__app_name__} v{__version__}")
        logger.info("=" * 60)

        try:
            Config.validate()
            config = Config()
            watcher_app = TorBoxWatcherApp(config)

            # Run the watcher (blocking)
            logger.info("Starting watcher...")
            watcher_app.run()

        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Application startup error: {e}")
            sys.exit(1)
    finally:
        # Release lock on exit
        if lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            lock_file.close()
            try:
                os.remove(LOCK_FILE)
            except OSError:
                pass


if __name__ == "__main__":
    main()
