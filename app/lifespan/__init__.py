import importlib
import pkgutil
from typing import Awaitable, Callable, List


def get_all_startup_tasks() -> List[Callable[[], Awaitable[None]]]:
    """
    Automatically discovers and imports all startup tasks from module.
    Returns list of async functions to run on startup.
    Each module should contain 'startup' async function.
    Modules can optionally have PRIORITY attribute (lower = higher priority).
    """
    modules_with_tasks = []
    package_dir = __path__[0]

    for _, module_name, is_pkg in pkgutil.iter_modules([package_dir]):
        if module_name == "__init__":
            continue

        module = importlib.import_module(f".{module_name}", package=__name__)

        if hasattr(module, "startup") and callable(module.startup):
            priority = getattr(module, "PRIORITY", 50)  # Default priority is 50
            modules_with_tasks.append((priority, module.startup))

    # Sort by priority (lower number = higher priority)
    modules_with_tasks.sort(key=lambda x: x[0])

    return [task for _, task in modules_with_tasks]


def get_all_shutdown_tasks() -> List[Callable[[], Awaitable[None]]]:
    """
    Automatically discovers and imports all shutdown tasks from module.
    Returns list of async functions to run on shutdown.
    Each module should contain 'shutdown' async function.
    Modules can optionally have PRIORITY attribute (lower = higher priority).
    Shutdown runs in reverse order of startup (like a matryoshka).
    """
    modules_with_tasks = []
    package_dir = __path__[0]

    for _, module_name, is_pkg in pkgutil.iter_modules([package_dir]):
        if module_name == "__init__":
            continue

        module = importlib.import_module(f".{module_name}", package=__name__)

        if hasattr(module, "shutdown") and callable(module.shutdown):
            priority = getattr(module, "PRIORITY", 50)  # Default priority is 50
            modules_with_tasks.append((priority, module.shutdown))

    # Sort by priority in reverse order (higher priority shuts down last)
    modules_with_tasks.sort(key=lambda x: x[0], reverse=True)

    return [task for _, task in modules_with_tasks]
