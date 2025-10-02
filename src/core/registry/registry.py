from typing import Type, Callable
from dataclasses import dataclass, field


@dataclass
class ModuleRegistry:
    name: str = "DefaultRegistry"
    _classes: list[Type] = field(default_factory=list)
    _aliases: dict[str, Type] = field(default_factory=dict)

    def register(self, *aliases: str) -> Callable[[Type], Type]:
        """
        Decorator to register a module class with aliases,
        automatically adding the class's own name as an alias.
        """

        def decorator(cls: Type) -> Type:
            if cls not in self._classes:
                self._classes.append(cls)

            all_aliases = set(alias.lower() for alias in aliases)
            all_aliases.add(cls.__name__.lower())

            for alias in all_aliases:
                if alias in self._aliases:
                    raise ValueError(
                        f"Alias '{alias}' already registered for {self._aliases[alias]}"
                    )
                self._aliases[alias] = cls

            return cls

        return decorator

    def get(self, alias: str) -> Type:
        cls = self._aliases.get(alias.lower())
        if cls is None:
            raise ValueError(f"Unknown module alias: '{alias}'")
        return cls

    def list_registered(self) -> list[Type]:
        return self._classes

    def list_aliases(self) -> dict[str, str]:
        return {alias: cls.__name__ for alias, cls in self._aliases.items()}


MODULE_REGISTRY = ModuleRegistry()
