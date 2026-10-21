# Contributing to Waveform Review Kit

Thanks for helping improve this small research utility. Contributions that make waveform quality control easier, safer and more reproducible are welcome.

## Before opening a pull request

- Describe the problem and provide minimal steps to reproduce it.
- Prefer a small, focused change over a large refactor.
- Open an issue first for substantial changes to the project manifest or exported CSV schema.
- Keep the application usable without third-party runtime dependencies (Python 3.10+).
- Add or update tests for behavior changes; run `python -m unittest discover -s tests -v`.
- Check `git status` before committing and verify there is **no private research data** in the diff.

## Working locally

```bash
python app.py --project examples/demo --open
python -m unittest discover -s tests -v
```

The demo figures are synthetic. Run `python tools/generate_demo_assets.py` only if you intentionally want to regenerate them; inspect any resulting diff.

An optional browser screenshot helper is described in [README.en.md](README.en.md). It uses Playwright for screenshots only; the application itself has no extra runtime dependency.

## Bug reports

Include your operating system, Python version, browser, expected vs. actual behavior, and a minimal **synthetic** CSV or JSON reproduction. Please do not include private waveform figures, station coordinates, unpublished event catalogs, credentials or personal information.

## Suggested contributions

- Better access for keyboard-only and assistive-technology users.
- Localized interface text and documentation.
- Additional builder validation and tests.
- Safe data exchange and schema migration guidance.
- Reproducible examples of review workflows using simulated waveforms.

## Privacy and responsible disclosure

By default the application binds to `127.0.0.1` and saves annotations to browser localStorage. Do not use a publicly accessible host for confidential data. If you discover a security problem, avoid posting secret-bearing examples in public issues; contact the maintainer through a suitable private channel.

## Code of conduct

Be respectful, constructive and mindful that contributors may come from different scientific and technical backgrounds.

## License

By contributing, you agree that your contributions will be distributed under the repository's MIT license.
