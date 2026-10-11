"""Complete ordered source-payload comparison with precise mismatch paths."""


def assert_golden(actual: dict, expected: dict) -> None:
    def compare(actual, expected, path):
        assert type(actual) is type(expected), (
            f"{path}: type {type(actual)} != {type(expected)}"
        )
        if isinstance(expected, dict):
            for key in expected.keys() - actual.keys():
                raise AssertionError(f"{path + '.' if path else ''}{key}: missing key")
            for key in actual.keys() - expected.keys():
                raise AssertionError(f"{path + '.' if path else ''}{key}: unknown key")
            for key in expected:
                compare(actual[key], expected[key], f"{path}.{key}" if path else key)
        elif isinstance(expected, (list, tuple)):
            assert len(actual) == len(expected), (
                f"{path}: length {len(actual)} != {len(expected)}"
            )
            for i, (a, e) in enumerate(zip(actual, expected)):
                compare(a, e, f"{path}[{i}]")
        else:
            assert actual == expected, f"{path}: {actual!r} != {expected!r}"

    compare(actual, expected, "")
