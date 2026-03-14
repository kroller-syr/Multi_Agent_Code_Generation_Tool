# README

## Overview

This program accepts exactly one integer and returns:

- **Square** of the integer
- **Square root** of the integer

Behavior rules:

- For **zero and positive integers**, both results are computed and displayed.
- For **negative integers**, the square is still computed, but the square root is reported as undefined in the real number system.
- For **invalid or non-integer input**, the program returns a clear error message.

The program uses standard language/library math support only and runs in **O(1)** time.

## How to Run

Run the program using your language/runtime of choice for the implementation.

Typical flow:

1. Start the program
2. Enter one integer
3. Read the labeled results or error message

Example generic command:

```bash
run-the-program
```

If implemented as a function, call it with a single integer argument.

## Example Usage

### Valid positive integer

**Input**

```text
9
```

**Output**

```text
Square: 81
Square Root: 3
```

### Zero

**Input**

```text
0
```

**Output**

```text
Square: 0
Square Root: 0
```

### Negative integer

**Input**

```text
-4
```

**Output**

```text
Square: 16
Square Root: undefined for negative integers in real numbers
```

### Invalid input

**Input**

```text
hello
```

**Output**

```text
Error: input must be a single integer
```

## Design Notes

- Accepts **exactly one integer** as input.
- Validates input before performing calculations.
- Uses standard math functionality for square root.
- Negative inputs are handled explicitly using **real-number behavior**:
  - square is computed normally
  - square root returns a clear undefined/error message
- No external libraries are required.
- Time complexity: **O(1)**
- Space complexity: **O(1)**

## Testing

Verify the following cases:

- Positive integer input, e.g. `4` → square `16`, square root `2`
- Zero input, e.g. `0` → square `0`, square root `0`
- Negative integer input, e.g. `-9` → square `81`, square root undefined message
- Non-integer input, e.g. `abc` → validation error
- Decimal input, e.g. `3.5` → validation error
- Multiple values input, e.g. `2 3` → validation error

A correct implementation should meet all acceptance criteria:

- accepts one integer only
- labels outputs clearly
- computes square correctly
- computes square root correctly for `0` and positive integers
- clearly handles negative integers
- rejects invalid input with a clear error message