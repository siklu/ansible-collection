"""
Custom exception classes for Siklu EH collection.

This module defines the exception hierarchy for error handling across
the Siklu EH Ansible collection modules and plugins.
"""

from typing import Any


class SikluError(Exception):
    """
    Base exception class for all Siklu EH collection errors.

    All custom exceptions in this collection should inherit from this class
    to allow for unified error handling and filtering.
    """

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """
        Initialize base Siklu exception.

        Args:
            message: Human-readable error message
            details: Optional dictionary with additional error context
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        """Return formatted error message with details if available."""
        if self.details:
            detail_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({detail_str})"
        return self.message


class SikluConnectionError(SikluError):
    """
    Exception raised for device connection failures.

    Raised when unable to establish or maintain SSH connection to device,
    or when connection is lost unexpectedly.

    Examples:
        - SSH connection timeout
        - Authentication failure
        - Connection reset by peer
        - Socket errors
    """

    def __init__(
            self,
            message: str,
            *,
            host: str | None = None,
            port: int | None = None,
            details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize connection error.

        Args:
            message: Error description
            host: Target device hostname/IP
            port: Target SSH port
            details: Additional context
        """
        connection_details = details or {}
        if host:
            connection_details["host"] = host
        if port:
            connection_details["port"] = port
        super().__init__(message, connection_details)


class SikluCommandError(SikluError):
    """
    Exception raised when command execution fails on device.

    Raised when a command sent to the device returns an error response
    or produces unexpected output.

    Examples:
        - Invalid command syntax
        - Command not found
        - Insufficient privileges
        - Command timeout
    """

    def __init__(
            self,
            message: str,
            *,
            command: str | None = None,
            output: str | None = None,
            details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize command error.

        Args:
            message: Error description
            command: The command that failed
            output: Device response/error output
            details: Additional context
        """
        command_details = details or {}
        if command:
            command_details["command"] = command
        if output:
            # Truncate very long output
            command_details["output"] = (
                output[:200] + "..." if len(output) > 200 else output
            )
        super().__init__(message, command_details)


class SikluConfigError(SikluError):
    """
    Exception raised for configuration operation failures.

    Raised when configuration changes cannot be applied, validated,
    or saved on the device.

    Examples:
        - Invalid configuration syntax
        - Configuration conflicts
        - Rollback failure
        - Save configuration failure
        - Validation errors
    """

    def __init__(
            self,
            message: str,
            *,
            config_lines: list[str] | None = None,
            validation_error: str | None = None,
            details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize configuration error.

        Args:
            message: Error description
            config_lines: Configuration lines that failed
            validation_error: Validation error message from device
            details: Additional context
        """
        config_details = details or {}
        if config_lines:
            config_details["config_lines"] = config_lines
        if validation_error:
            config_details["validation_error"] = validation_error
        super().__init__(message, config_details)


class SikluParseError(SikluError):
    """
    Exception raised when parsing device output fails.

    Raised when command output cannot be parsed into expected structure,
    or when required fields are missing from device response.

    Examples:
        - Unexpected output format
        - Missing required fields
        - Invalid data types
        - Malformed response
    """

    def __init__(
            self,
            message: str,
            *,
            raw_output: str | None = None,
            expected_format: str | None = None,
            details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize parse error.

        Args:
            message: Error description
            raw_output: The output that failed to parse
            expected_format: Description of expected format
            details: Additional context
        """
        parse_details = details or {}
        if raw_output:
            # Truncate very long output
            parse_details["raw_output"] = (
                raw_output[:200] + "..." if len(raw_output) > 200 else raw_output
            )
        if expected_format:
            parse_details["expected_format"] = expected_format
        super().__init__(message, parse_details)


class SikluValidationError(SikluError):
    """
    Exception raised for input validation failures.

    Raised when module parameters or arguments fail validation
    before being sent to the device.

    Examples:
        - Invalid parameter value
        - Missing required parameter
        - Parameter type mismatch
        - Value out of range
    """

    def __init__(
            self,
            message: str,
            *,
            parameter: str | None = None,
            value: Any = None,
            valid_values: list[Any] | None = None,
            details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize validation error.

        Args:
            message: Error description
            parameter: Parameter name that failed validation
            value: Invalid value provided
            valid_values: List of acceptable values
            details: Additional context
        """
        validation_details = details or {}
        if parameter:
            validation_details["parameter"] = parameter
        if value is not None:
            validation_details["value"] = str(value)
        if valid_values:
            validation_details["valid_values"] = valid_values
        super().__init__(message, validation_details)


class SikluTimeoutError(SikluError):
    """
    Exception raised when an operation times out.

    Raised when a command or operation exceeds its timeout threshold
    without completing.

    Examples:
        - Command execution timeout
        - Rollback timeout
        - Configuration save timeout
        - Connection establishment timeout
    """

    def __init__(
            self,
            message: str,
            *,
            timeout_seconds: int | None = None,
            operation: str | None = None,
            details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize timeout error.

        Args:
            message: Error description
            timeout_seconds: Timeout value that was exceeded
            operation: Operation that timed out
            details: Additional context
        """
        timeout_details = details or {}
        if timeout_seconds:
            timeout_details["timeout_seconds"] = timeout_seconds
        if operation:
            timeout_details["operation"] = operation
        super().__init__(message, timeout_details)
