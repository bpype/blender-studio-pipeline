# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

# TODO: This code should be de-duplicated between here and Blender Kitsu, 
# and moved to blender-studio-utils repo, then added to this repo as a submodule.

import bpy
import sys
from pathlib import Path
import typing
import types
import importlib.util
from . import prefs
import logging

logger = logging.getLogger(__name__)


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
Hooks are stored as `_hook_rules' attribute on the function.
The MatchingRulesType is the type definition of the `_hook_rules` attribute.
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
    logger.error(f"Incorrect matching criteria {hook_criteria}, {match_query}")
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
        rules = typing.cast(MatchingRulesType, getattr(hook, '_hook_rules'))
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
            if self.matches(
                hook, merge_mode=merge_mode, merge_status=merge_status
            ):
                hook(*args, **kwargs)

    def load_hooks(self, context):
        hook_dirs = [get_production_hook_dir(), get_asset_hook_dir()] # TODO: This should be a function param.
        for hook_dir in hook_dirs:
            if not hook_dir.exists():
                logger.debug(f"Hooks directory not found: {hook_dir}")
                return
            hook_file_path = hook_dir.resolve() / "hooks.py"
            module_name = __package__ + ".production_hooks"
            try:
                spec = importlib.util.spec_from_file_location(module_name, hook_file_path)
                hooks_module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = hooks_module
                spec.loader.exec_module(hooks_module)

                self.register_hooks(hooks_module)
            except FileNotFoundError:
                logger.debug(f"No hook file found in optional location: {hook_file_path}")

        return False

    def register(self, func: HookFunction) -> None:
        logger.info(f"Registering hook: '{func.__name__}'")
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
            if not hasattr(module_item, "_hook_rules"):
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
    Decorator to add custom logic when performing certain actions.

    Hooks are used to extend the configuration that would be not part of the core logic of the tool.
    """
    rules = {
        'merge_mode': merge_mode,
        'merge_status': merge_status,
    }

    def wrapper(func: types.FunctionType) -> types.FunctionType:
        setattr(func, '_hook_rules', rules)
        return func

    return wrapper
