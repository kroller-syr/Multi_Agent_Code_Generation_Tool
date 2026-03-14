import math
import sys
from typing import Optional, Tuple


def parse_integer(value: str) -> int:
    """Parse and validate exactly one integer from a string.

    Args:
        value: The raw input string.

    Returns:
        The parsed integer.

    Raises:
        ValueError: If the input is empty, contains multiple tokens,
            or is not a valid integer.
    """
    cleaned: str = value.strip()
    if not cleaned:
        raise ValueError("Error: No input provided. Please enter exactly one integer.")

    parts = cleaned.split()
    if len(parts) != 1:
        raise ValueError("Error: Please enter exactly one integer.")

    token = parts[0]
    try:
        return int(token)
    except ValueError as exc:
        raise ValueError("Error: Invalid input. Please enter a valid integer.") from exc


def calculate_square_and_sqrt(number: int) -> Tuple[int, Optional[float], Optional[str]]:
    """Calculate the square and square root of an integer.

    For negative integers, the square root is undefined in the real numbers.

    Args:
        number: The integer to process.

    Returns:
        A tuple containing:
        - the square of the integer
        - the square root as a float for non-negative integers, otherwise None
        - an error/message for the square root when undefined, otherwise None
    """
    square: int = number * number
    if number < 0:
        return square, None, "Undefined for negative integers in real numbers."

    return square, math.sqrt(number), None


def format_square_root(value: float) -> str:
    """Format square root output for cleaner display."""
    if value.is_integer():
        return f"{int(value)}"
    return f"{value}"


def main() -> None:
    """Run the application.

    Command-line input takes precedence over interactive input.
    """
    try:
        if len(sys.argv) > 2:
            print("Error: Please provide exactly one integer input.")
            return

        if len(sys.argv) == 2:
            raw_input_value = sys.argv[1]
        else:
            raw_input_value = input("Enter an integer: ")

        number: int = parse_integer(raw_input_value)
        square, square_root, sqrt_message = calculate_square_and_sqrt(number)

        print(f"Square: {square}")
        if sqrt_message is not None:
            print(f"Square Root: {sqrt_message}")
        else:
            print(f"Square Root: {format_square_root(square_root)}")

    except ValueError as error:
        print(str(error))


if __name__ == "__main__":
    main()