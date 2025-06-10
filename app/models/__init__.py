import importlib
import os

for file in os.listdir(os.path.dirname(__file__)):
    if file.endswith(".py") and file not in ("__init__.py", "base.py"):
        module_name = f"app.models.{file[:-3]}"
        importlib.import_module(module_name)
