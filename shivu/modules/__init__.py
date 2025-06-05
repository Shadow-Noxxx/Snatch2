import logging
import sys
import time

StartTime = time.time()

# enable logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.FileHandler("log.txt"), logging.StreamHandler()],
    level=logging.INFO,
)

logging.getLogger("apscheduler").setLevel(logging.ERROR)
logging.getLogger("pyrate_limiter").setLevel(logging.ERROR)
LOGGER = logging.getLogger(__name__)

# if version < 3.6, stop bot.
if sys.version_info[0] < 3 or sys.version_info[1] < 6:
    LOGGER.error(
        "You MUST have a python version of at least 3.6! Multiple features depend on this. Bot quitting."
    )
    quit(1)

LOAD = []    # Leave empty to load all modules
NO_LOAD = [] # Add module names (without .py) to skip loading

def __list_all_modules():
    import glob
    from os.path import basename, dirname, isfile

    mod_paths = glob.glob(dirname(__file__) + "/*.py")
    all_modules = [
        basename(f)[:-3]
        for f in mod_paths
        if isfile(f) and f.endswith(".py") and not f.endswith("__init__.py")
    ]

    # Always load all modules except those in NO_LOAD
    if NO_LOAD:
        LOGGER.info("Not loading: {}".format(NO_LOAD))
        return [item for item in all_modules if item not in NO_LOAD]
    return all_modules

ALL_MODULES = __list_all_modules()
LOAD = ALL_MODULES  # Put all modules in LOAD
if "xo" not in LOAD:
    LOAD.append("xo")
LOGGER.info("Modules to load: %s", str(LOAD))
__all__ = LOAD + ["ALL_MODULES"]
