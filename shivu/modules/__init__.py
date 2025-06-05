import logging
import sys
import time
import glob
from os.path import basename, dirname, isfile

StartTime = time.time()

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.FileHandler("log.txt"), logging.StreamHandler()],
    level=logging.INFO,
)
logging.getLogger("apscheduler").setLevel(logging.ERROR)
logging.getLogger("pyrate_limiter").setLevel(logging.ERROR)
LOGGER = logging.getLogger(__name__)

# Check Python version
if sys.version_info < (3, 6):
    LOGGER.error("❌ Python 3.6 or higher is required. Exiting.")
    quit(1)

# Module load control
LOAD = []       # Add module names here to load only specific modules
NO_LOAD = []    # Add module names here to skip specific modules


def __list_all_modules():
    """List all Python modules in this directory, excluding __init__.py"""
    module_files = glob.glob(dirname(__file__) + "/*.py")
    all_modules = [
        basename(f)[:-3]
        for f in module_files
        if isfile(f) and f.endswith(".py") and not f.endswith("__init__.py")
    ]

    # Filter using LOAD/NO_LOAD
    if LOAD:
        invalid = [mod for mod in LOAD if mod not in all_modules]
        if invalid:
            LOGGER.error(f"Invalid modules in LOAD: {invalid}. Exiting.")
            quit(1)
        return LOAD

    if NO_LOAD:
        LOGGER.info(f"Skipping modules: {NO_LOAD}")
        return [mod for mod in all_modules if mod not in NO_LOAD]

    return all_modules


ALL_MODULES = __list_all_modules()
__all__ = ALL_MODULES + ["ALL_MODULES"]

LOGGER.info(f"✅ Modules to load: {ALL_MODULES}")
