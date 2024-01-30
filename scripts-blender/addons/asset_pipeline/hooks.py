import sys
import pathlib
from typing import *
import bpy
import typing
import types
from collections.abc import Iterable
import importlib
from . import prefs
from pathlib import Path


class Wildcard:
    pass


class DoNotMatch:
    pass


MatchCriteriaType = typing.Union[
    str, typing.List[str], typing.Type[Wildcard], typing.Type[DoNotMatch]
]
"""
The MatchCriteriaType is a type definition for the parameters of the `hook` decorator.

The matching parameters can use multiple types to detect how the matching criteria
would work.

* `str`: would perform an exact string match.
* `typing.Iterator[str]`: would perform an exact string match with any of the given strings.
* `typing.Type[Wildcard]`: would match any type for this parameter. This would be used so a hook
  is called for any value.
* `typing.Type[DoNotMatch]`: would ignore this hook when matching the hook parameter. This is the default
  value for the matching criteria and would normally not be set directly in a
  production configuration.
"""

MatchingRulesType = typing.Dict[str, MatchCriteriaType]
"""
Hooks are stored as `_asset_pipeline_rules' attribute on the function.
The MatchingRulesType is the type definition of the `_asset_pipeline_rules` attribute.
"""

HookFunction = typing.Callable[[typing.Any], None]


def _match_hook_parameter(
    hook_criteria: MatchCriteriaType, match_query: typing.Optional[str]
) -> bool:
    if hook_criteria == None:
        return True
    if hook_criteria == DoNotMatch:
        return match_query is None
    if hook_criteria == Wildcard:
        return True
    if isinstance(hook_criteria, str):
        return match_query == hook_criteria
    if isinstance(hook_criteria, list):
        return match_query in hook_criteria
    return False


class Hooks:
    def __init__(self):
        self._hooks: typing.List[HookFunction] = []

    def matches(
        self,
        hook: HookFunction,
        merge_mode: typing.Optional[str] = None,
        merge_status: typing.Optional[str] = None,
        **kwargs: typing.Optional[str],
    ) -> bool:
        assert not kwargs
        rules = typing.cast(MatchingRulesType, getattr(hook, '_asset_pipeline_rules'))
        return all(
            (
                _match_hook_parameter(rules['merge_mode'], merge_mode),
                _match_hook_parameter(rules['merge_status'], merge_status),
            )
        )

    def filter(self, **kwargs: typing.Optional[str]) -> typing.Iterator[HookFunction]:
        for hook in self._hooks:
            if self.matches(hook=hook, **kwargs):
                yield hook

    def execute_hooks(
        self, merge_mode: str = None, merge_status: str = None, *args, **kwargs
    ) -> None:
        for hook in self._hooks:
            if self.matches(hook, merge_mode=merge_mode, merge_status=merge_status):
                hook(*args, **kwargs)

    def import_hook(self, path: List[str]) -> None:
        with SystemPathInclude(path) as _include:
            try:
                import hooks as production_hooks

                importlib.reload(production_hooks)
                self.register_hooks(production_hooks)
            except ModuleNotFoundError:
                print("Production has no `hooks.py` configuration file for assets")

    def load_hooks(self, context):
        prod_hooks = get_production_hook_dir()
        asset_hooks = get_asset_hook_dir()
        for path in [prod_hooks.resolve().__str__(), asset_hooks.resolve().__str__()]:
            self.import_hook([path])

    def register(self, func: HookFunction) -> None:
        if func not in self._hooks:
            self._hooks.append(func)

    def register_hooks(self, module: types.ModuleType) -> None:
        """
        Register all hooks inside the given module.
        """
        for module_item_str in dir(module):
            module_item = getattr(module, module_item_str)
            if not isinstance(module_item, types.FunctionType):
                continue
            if module_item.__module__ != module.__name__:
                continue
            if not hasattr(module_item, "_asset_pipeline_rules"):
                continue
            self.register(module_item)


def get_production_hook_dir() -> Path:
    root_dir = Path(prefs.project_root_dir_get())
    asset_dir = root_dir.joinpath("svn/pro/")
    if not asset_dir.exists():
        raise Exception(f"Directory {str(asset_dir)} doesn't exist")
    hook_dir = asset_dir.joinpath("config/asset_pipeline")
    hook_dir.mkdir(parents=True, exist_ok=True)
    return hook_dir


def get_asset_hook_dir() -> Path:
    return Path(bpy.data.filepath).parent


def hook(
    merge_mode: MatchCriteriaType = None,
    merge_status: MatchCriteriaType = None,
) -> typing.Callable[[types.FunctionType], types.FunctionType]:
    """
    Decorator to add custom logic when pushing/pulling an asset.

    Hooks are used to extend the configuration that would be not part of the core logic of the asset pipeline.
    """
    rules = {
        'merge_mode': merge_mode,
        'merge_status': merge_status,
    }

    def wrapper(func: types.FunctionType) -> types.FunctionType:
        setattr(func, '_asset_pipeline_rules', rules)
        return func

    return wrapper


class SystemPathInclude:
    """
    Resource class to temporary include system paths to `sys.paths`.

    Usage:
        ```
        paths = [pathlib.Path("/home/guest/my_python_scripts")]
        with SystemPathInclude(paths) as t:
            import my_module
            reload(my_module)
        ```

    It is possible to nest multiple SystemPathIncludes.
    """

    def __init__(self, paths_to_add: List[pathlib.Path]):
        # TODO: Check if all paths exist and are absolute.
        self.__paths = paths_to_add
        self.__original_sys_path: List[str] = []

    def __enter__(self):
        self.__original_sys_path = sys.path
        new_sys_path = []
        for path_to_add in self.__paths:
            # Do not add paths that are already in the sys path.
            path_to_add_str = str(path_to_add)
            if path_to_add_str in self.__original_sys_path:
                continue
            new_sys_path.append(path_to_add_str)
        new_sys_path.extend(self.__original_sys_path)
        sys.path = new_sys_path

    def __exit__(self, exc_type, exc_value, exc_traceback):
        sys.path = self.__original_sys_path
