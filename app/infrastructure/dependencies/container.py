"""
Dependency Injection Container.

Implements the Dependency Inversion Principle by providing a centralized
container for managing application dependencies.
"""
from typing import Type, TypeVar, Callable, Any
from functools import lru_cache


T = TypeVar("T")


class DependencyContainer:
    """
    Simple dependency injection container.

    Manages singleton and factory dependencies, providing them
    when requested by the application.

    Example:
        >>> container = DependencyContainer()
        >>> container.register(IClientRepository, ClientRepository)
        >>> repo = container.resolve(IClientRepository)
    """

    def __init__(self):
        """Initialize the container with empty registries."""
        self._singletons: dict[Type, Any] = {}
        self._factories: dict[Type, Callable] = {}
        self._instances: dict[Type, Any] = {}

    def register_singleton(self, interface: Type[T], instance: T) -> None:
        """
        Register a singleton instance for an interface.

        The same instance will be returned on every resolve() call.

        Args:
            interface: The interface/abstract type
            instance: The concrete instance to register
        """
        self._singletons[interface] = instance
        self._instances[interface] = instance

    def register_factory(self, interface: Type[T], factory: Callable[..., T]) -> None:
        """
        Register a factory function for an interface.

        A new instance will be created on every resolve() call.

        Args:
            interface: The interface/abstract type
            factory: A callable that creates instances
        """
        self._factories[interface] = factory

    def register(self, interface: Type[T], implementation: Type[T]) -> None:
        """
        Register an implementation for an interface.

        Creates instances using the implementation's constructor.

        Args:
            interface: The interface/abstract type
            implementation: The concrete implementation type
        """
        self._factories[interface] = implementation

    def resolve(self, interface: Type[T], **kwargs) -> T:
        """
        Resolve a dependency by its interface.

        Args:
            interface: The interface/abstract type to resolve
            **kwargs: Additional arguments to pass to the factory

        Returns:
            An instance of the implementation

        Raises:
            KeyError: If the interface is not registered
        """
        # Check for singleton first
        if interface in self._singletons:
            return self._singletons[interface]

        # Check for factory
        if interface in self._factories:
            factory = self._factories[interface]
            instance = factory(**kwargs)
            return instance

        raise KeyError(f"No registration found for {interface}")

    def resolve_singleton(self, interface: Type[T], **kwargs) -> T:
        """
        Resolve a dependency as singleton.

        Creates the instance on first call and caches it.

        Args:
            interface: The interface/abstract type to resolve
            **kwargs: Additional arguments for the first instantiation

        Returns:
            The singleton instance
        """
        if interface not in self._instances:
            self._instances[interface] = self.resolve(interface, **kwargs)
        return self._instances[interface]

    def clear(self) -> None:
        """Clear all registrations and instances."""
        self._singletons.clear()
        self._factories.clear()
        self._instances.clear()

    def is_registered(self, interface: Type) -> bool:
        """
        Check if an interface is registered.

        Args:
            interface: The interface to check

        Returns:
            True if registered, False otherwise
        """
        return interface in self._singletons or interface in self._factories


@lru_cache()
def get_container() -> DependencyContainer:
    """
    Get the global dependency container instance.

    Uses LRU cache to ensure singleton pattern.

    Returns:
        The global DependencyContainer instance
    """
    return DependencyContainer()


# Global container instance
container = get_container()
