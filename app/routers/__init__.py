import pkgutil
import importlib
from typing import List
from fastapi import APIRouter


def get_all_routers() -> List[APIRouter]:
    """
    Automatically discovers and imports all routers from module.
    Returns list of APIRouter objects.
    Each router file should contain 'router' variable of APIRouter type.
    Routers should have prefix, tags and dependencies set up.
    """
    routers = []
    package_dir = __path__[0]

    for _, module_name, is_pkg in pkgutil.iter_modules([package_dir]):
        if module_name == "__init__":
            continue

        module = importlib.import_module(f".{module_name}", package=__name__)

        if hasattr(module, "router") and isinstance(module.router, APIRouter):
            routers.append(module.router)

    return routers
