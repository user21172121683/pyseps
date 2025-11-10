# SPDX-License-Identifier: AGPL-3.0-or-later

from typing import Type, Callable
from dataclasses import dataclass, field
from abc import ABCMeta, ABC
import inspect
import logging


logger = logging.getLogger(__name__)


@dataclass
class ModuleRegistry:
    name: str = "DefaultRegistry"
    _classes: dict[type, list[type]] = field(default_factory=dict)
    _aliases: dict[str, type] = field(default_factory=dict)
    _specs: dict[type, type] = field(default_factory=dict)

    def register(
        self, *aliases: str, spec_cls: type | None = None
    ) -> Callable[[type], type]:
        """
        Decorator to register a class with aliases, index it under
        its abstract bases, and optionally store its spec class.
        """

        def decorator(cls: type) -> type:
            all_aliases = set(alias.lower() for alias in aliases)
            all_aliases.add(cls.__name__.lower())

            for alias in all_aliases:
                if alias in self._aliases:
                    raise ValueError(
                        f"Alias '{alias}' already registered for {self._aliases[alias]}"
                    )
                self._aliases[alias] = cls

            # Index under ABCs
            indexed_bases = []
            for base in inspect.getmro(cls)[1:]:
                if base in (object, ABC):
                    continue
                if isinstance(base, ABCMeta) and inspect.isabstract(base):
                    if base not in self._classes:
                        self._classes[base] = []
                    if cls not in self._classes[base]:
                        self._classes[base].append(cls)
                    indexed_bases.append(base.__name__)

            # Store spec class
            if spec_cls is not None:
                self._specs[cls] = spec_cls

            # Single merged debug message
            logger.debug(
                "Registered class %s | aliases: %s%s | indexed under bases: %s",
                cls.__name__,
                ", ".join(all_aliases),
                f" | spec class: {spec_cls.__name__}" if spec_cls else "",
                ", ".join(indexed_bases) if indexed_bases else "None",
            )

            return cls

        return decorator

    def get(self, alias: str) -> Type:
        cls = self._aliases.get(alias.lower())
        if cls is None:
            raise ValueError(f"Unknown module alias: '{alias}'")
        logger.debug("Lookup for alias '%s': found %s", alias, cls.__name__)
        return cls

    def get_by_base(self, base_class: Type) -> list[Type]:
        return self._classes.get(base_class, [])

    def list_aliases(self) -> dict[str, str]:
        return {alias: cls.__name__ for alias, cls in self._aliases.items()}

    def get_spec_class(self, cls: type) -> type | None:
        """Return the spec class associated with a module class."""
        return self._specs.get(cls)


MODULE_REGISTRY = ModuleRegistry()
