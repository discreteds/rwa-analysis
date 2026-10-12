# Restore convenient interactive research examples

**Type:** techdebt

**Status:** OPEN

**Owner:** rwa-analysis examples / ordinary Python research interface

## Evidence

The researcher ran `uv run python -i examples/westpac_cr9.py` at the Westpac CR9
checkpoint. It exited with argparse `SystemExit: 2` because `--data-root` and
`--run-name` were required. Supplying the flags runs successfully, but `main()` keeps
the session/result/publication local, preventing the expected interactive inspection.
Existing CBA examples establish an ordinary Python interactive usage pattern.

The preceding Decimal/Literal schema-inference messages are a separate concern;
they did not cause this argument error.

## Removal objective

Make the Westpac example convenient to run and inspect interactively, consistent
with the project's existing examples. Expose the session, result, domain outputs and
reconstructed tables. Keep output locations/run names visible and intentional; preserve
retained Bronze versions. Choose the smallest concrete example change when scheduled,
without introducing an application CLI, configuration framework or generic runner.

Verify by running the documented interactive invocation and inspecting the exposed
objects. This item records the usability fix; it does not add a prerequisite to the
approved CR9 processing checkpoint or silently choose an output-overwrite policy.

See [implementation lessons](../../../00.ideation/2026-10-12-cr9-implementation-lessons.md).
