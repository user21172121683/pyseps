# SPDX-License-Identifier: AGPL-3.0-or-later

from typing import Type, Callable
from dataclasses import dataclass, field
from abc import ABCMeta, ABC
import inspect


@dataclass
class ModuleRegistry:
    name: str = "DefaultRegistry"
    _classes: dict[Type, list[Type]] = field(default_factory=dict)
    _aliases: dict[str, Type] = field(default_factory=dict)

    def register(self, *aliases: str) -> Callable[[Type], Type]:
        """
        Decorator to register a class with aliases, and index it under
        any abstract base classes (excluding object/ABC).
        """

        def decorator(cls: Type) -> Type:
            # Register aliases
            all_aliases = set(alias.lower() for alias in aliases)
            all_aliases.add(cls.__name__.lower())

            for alias in all_aliases:
                if alias in self._aliases:
                    raise ValueError(
                        f"Alias '{alias}' already registered for {self._aliases[alias]}"
                    )
                self._aliases[alias] = cls

            for base in inspect.getmro(cls)[1:]:
                if base in (object, ABC):
                    continue

                if isinstance(base, ABCMeta) and inspect.isabstract(base):
                    if base not in self._classes:
                        self._classes[base] = []
                    if cls not in self._classes[base]:
                        self._classes[base].append(cls)

            return cls

        return decorator

    def get(self, alias: str) -> Type:
        cls = self._aliases.get(alias.lower())
        if cls is None:
            raise ValueError(f"Unknown module alias: '{alias}'")
        return cls

    def get_by_base(self, base_class: Type) -> list[Type]:
        return self._classes.get(base_class, [])

    def list_aliases(self) -> dict[str, str]:
        return {alias: cls.__name__ for alias, cls in self._aliases.items()}


MODULE_REGISTRY = ModuleRegistry()
