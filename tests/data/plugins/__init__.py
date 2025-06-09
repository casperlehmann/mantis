import importlib
import os
from pydantic import BaseModel

module_dir = os.path.dirname(__file__)

for filename in os.listdir(module_dir):
    if filename.endswith(".py") and filename != "__init__.py":
        # Remove the .py extension
        module_name = filename[:-3]
        importlib.import_module(f".{module_name}", package=__name__)


class Plugins:
    """
    Plugins class for import at runtime.

    from plugins import Plugins
    Plugins.my_model
    Plugins.my_other_model

    Or iterate through all registered plugins:
    for plugin Plugins.all_plugins:
        print(plugin)
    """

    all_plugins: dict[str, BaseModel] = {}

    @classmethod
    def stats(cls):
        print("The following plugins have been loaded:")
        for plugin_name, plugin in cls.all_plugins.items():
            models_in_plugin = [_ for _ in dir(plugin) if not _.startswith("_")]
            model_count = len(models_in_plugin)
            print(f"- {plugin_name} ({model_count})")


for filename in os.listdir(module_dir):
    if filename.endswith(".py") and filename != "__init__.py":
        # Remove the .py extension
        module_name = filename[:-3]
        # Set each plugin as an attribute of the Plugins class
        imported_plugin = importlib.import_module(f".{module_name}", package=__name__)
        setattr(Plugins, module_name, imported_plugin)
        Plugins.all_plugins[module_name] = imported_plugin
