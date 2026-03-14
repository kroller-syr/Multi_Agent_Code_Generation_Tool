import importlib.util
import pathlib
import sys

import pytest


def _load_target_module():
    current_test = pathlib.Path(__file__).resolve()
    for path in current_test.parent.glob("*.py"):
        if path.name.startswith("test_"):
            continue
        spec = importlib.util.spec_from_file_location("target_module", path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        if all(hasattr(module, name) for name in ("parse_integer", "calculate_square_and_sqrt", "format_square_root", "main")):
            return module
    raise RuntimeError("Could not locate target module with required functions.")


app = _load_target_module()


class TestParseInteger:
    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("0", 0),
            ("7", 7),
            ("-5", -5),
            ("   42   ", 42),
            ("\n15\t", 15),
            ("+9", 9),
        ],
    )
    def test_parse_integer_accepts_valid_single_integer(self, raw, expected):
        assert app.parse_integer(raw) == expected

    @pytest.mark.parametrize(
        "raw",
        [
            "",
            "   ",
            "\n\t  ",
        ],
    )
    def test_parse_integer_rejects_empty_input(self, raw):
        with pytest.raises(ValueError, match="Error: No input provided\\. Please enter exactly one integer\\."):
            app.parse_integer(raw)

    @pytest.mark.parametrize(
        "raw",
        [
            "1 2",
            "10 20 30",
            "4\n5",
            "8\t9",
        ],
    )
    def test_parse_integer_rejects_multiple_tokens(self, raw):
        with pytest.raises(ValueError, match="Error: Please enter exactly one integer\\."):
            app.parse_integer(raw)

    @pytest.mark.parametrize(
        "raw",
        [
            "abc",
            "3.14",
            "5.0",
            "1,000",
            "seven",
            "12a",
        ],
    )
    def test_parse_integer_rejects_non_integer_input(self, raw):
        with pytest.raises(ValueError, match="Error: Invalid input\\. Please enter a valid integer\\."):
            app.parse_integer(raw)


class TestCalculateSquareAndSqrt:
    @pytest.mark.parametrize(
        "number, expected_square, expected_sqrt",
        [
            (0, 0, 0.0),
            (1, 1, 1.0),
            (4, 16, 2.0),
            (2, 4, pytest.approx(2 ** 0.5)),
            (9, 81, 3.0),
        ],
    )
    def test_calculate_square_and_sqrt_for_non_negative_numbers(self, number, expected_square, expected_sqrt):
        square, square_root, message = app.calculate_square_and_sqrt(number)
        assert square == expected_square
        assert square_root == expected_sqrt
        assert message is None

    @pytest.mark.parametrize(
        "number, expected_square",
        [
            (-1, 1),
            (-5, 25),
            (-12, 144),
        ],
    )
    def test_calculate_square_and_sqrt_for_negative_numbers_returns_message(self, number, expected_square):
        square, square_root, message = app.calculate_square_and_sqrt(number)
        assert square == expected_square
        assert square_root is None
        assert message == "Undefined for negative integers in real numbers."


class TestFormatSquareRoot:
    @pytest.mark.parametrize(
        "value, expected",
        [
            (0.0, "0"),
            (1.0, "1"),
            (2.0, "2"),
            (10.0, "10"),
        ],
    )
    def test_format_square_root_removes_trailing_decimal_for_integer_values(self, value, expected):
        assert app.format_square_root(value) == expected

    @pytest.mark.parametrize(
        "value, expected",
        [
            (1.5, "1.5"),
            (math_sqrt := 2 ** 0.5, f"{math_sqrt}"),
            (3.25, "3.25"),
        ],
    )
    def test_format_square_root_preserves_non_integer_float_representation(self, value, expected):
        assert app.format_square_root(value) == expected


class TestMain:
    def test_main_with_command_line_argument_outputs_square_and_integer_square_root(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["prog", "16"])
        app.main()
        captured = capsys.readouterr()
        assert captured.out == "Square: 256\nSquare Root: 4\n"

    def test_main_with_command_line_argument_outputs_square_and_non_integer_square_root(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["prog", "2"])
        app.main()
        captured = capsys.readouterr()
        assert captured.out == f"Square: 4\nSquare Root: {2 ** 0.5}\n"

    def test_main_with_negative_command_line_argument_outputs_negative_sqrt_message(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["prog", "-9"])
        app.main()
        captured = capsys.readouterr()
        assert captured.out == "Square: 81\nSquare Root: Undefined for negative integers in real numbers.\n"

    def test_main_with_zero_command_line_argument_outputs_zero_results(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["prog", "0"])
        app.main()
        captured = capsys.readouterr()
        assert captured.out == "Square: 0\nSquare Root: 0\n"

    def test_main_with_too_many_command_line_arguments_prints_error_and_returns(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["prog", "1", "2"])
        app.main()
        captured = capsys.readouterr()
        assert captured.out == "Error: Please provide exactly one integer input.\n"

    def test_main_with_invalid_command_line_argument_prints_validation_error(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["prog", "abc"])
        app.main()
        captured = capsys.readouterr()
        assert captured.out == "Error: Invalid input. Please enter a valid integer.\n"

    def test_main_uses_input_when_no_command_line_argument_is_provided(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["prog"])
        monkeypatch.setattr("builtins.input", lambda prompt: "25")
        app.main()
        captured = capsys.readouterr()
        assert captured.out == "Square: 625\nSquare Root: 5\n"

    def test_main_with_invalid_interactive_input_prints_error(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["prog"])
        monkeypatch.setattr("builtins.input", lambda prompt: "3.14")
        app.main()
        captured = capsys.readouterr()
        assert captured.out == "Error: Invalid input. Please enter a valid integer.\n"

    def test_main_command_line_takes_precedence_over_input(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["prog", "5"])

        def fail_if_called(_prompt):
            raise AssertionError("input() should not be called when CLI argument is provided")

        monkeypatch.setattr("builtins.input", fail_if_called)
        app.main()
        captured = capsys.readouterr()
        assert captured.out == "Square: 25\nSquare Root: 2.23606797749979\n"