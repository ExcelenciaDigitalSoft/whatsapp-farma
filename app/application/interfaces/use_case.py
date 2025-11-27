"""Base use case interface following Clean Architecture principles."""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

# Type variables for input and output
InputDTO = TypeVar("InputDTO")
OutputDTO = TypeVar("OutputDTO")


class IUseCase(ABC, Generic[InputDTO, OutputDTO]):
    """
    Generic use case interface defining the contract for application use cases.

    Use cases encapsulate application-specific business rules and orchestrate
    the flow of data between the domain layer and external layers.

    This interface follows the Command/Query Responsibility Segregation (CQRS)
    pattern by accepting an input DTO and returning an output DTO.

    Type Parameters:
        InputDTO: The input data transfer object type
        OutputDTO: The output data transfer object type
    """

    @abstractmethod
    async def execute(self, input_dto: InputDTO) -> OutputDTO:
        """
        Execute the use case logic.

        This method orchestrates the business logic by:
        1. Validating input data
        2. Coordinating domain entities and services
        3. Persisting changes via repositories
        4. Returning structured output

        Args:
            input_dto: The input data required for the use case

        Returns:
            The result of the use case execution

        Raises:
            DomainException: If business rules are violated
            ValidationError: If input validation fails
        """
        pass


class IQueryUseCase(ABC, Generic[InputDTO, OutputDTO]):
    """
    Query use case interface for read-only operations.

    This interface is optimized for queries that don't modify state,
    following the CQRS pattern's query side.

    Type Parameters:
        InputDTO: The query parameters
        OutputDTO: The query result
    """

    @abstractmethod
    async def execute(self, query: InputDTO) -> OutputDTO:
        """
        Execute a read-only query.

        Args:
            query: The query parameters

        Returns:
            The query result
        """
        pass


class ICommandUseCase(ABC, Generic[InputDTO, OutputDTO]):
    """
    Command use case interface for state-changing operations.

    This interface is designed for commands that modify system state,
    following the CQRS pattern's command side.

    Type Parameters:
        InputDTO: The command parameters
        OutputDTO: The command result
    """

    @abstractmethod
    async def execute(self, command: InputDTO) -> OutputDTO:
        """
        Execute a state-changing command.

        Args:
            command: The command parameters

        Returns:
            The command result

        Raises:
            DomainException: If business rules prevent the command execution
        """
        pass
