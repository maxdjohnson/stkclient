# Changelog

## [0.3.0](https://github.com/maxdjohnson/stkclient/compare/v0.2.0...v0.3.0) (2026-10-13)

### Features

- Migrate device discovery, uploads, and document delivery to Amazon's Kindle Docs API. Delivery now includes the file size and conversion preference required by the new endpoint. ([#210](https://github.com/maxdjohnson/stkclient/pull/210))
- Replace the archived Python-RSA dependency with cryptography while preserving Amazon's signature format and saved-client compatibility. ([#209](https://github.com/maxdjohnson/stkclient/pull/209))

### Compatibility

- Calls to the low-level `stkclient.api.send_to_kindle` function must now pass the required `file_size` keyword argument. `Client.send_file` supplies it automatically and retains its existing interface. ([#210](https://github.com/maxdjohnson/stkclient/pull/210))
- `Signer.device_private_key` now uses a cryptography `RSAPrivateKey`. Use `Signer.from_device_info` to construct a signer from saved device credentials. ([#209](https://github.com/maxdjohnson/stkclient/pull/209))

### Maintenance

- Replace Poetry and Nox with uv for dependency management, builds, and direct development commands. ([#206](https://github.com/maxdjohnson/stkclient/pull/206), [#212](https://github.com/maxdjohnson/stkclient/pull/212))
- Replace the legacy linting stack with Ruff and modernize formatting and test infrastructure, including Python 3.14 and 3.15 compatibility. ([#208](https://github.com/maxdjohnson/stkclient/pull/208), [#213](https://github.com/maxdjohnson/stkclient/pull/213))
- Automate dependency updates and quarterly releases, with release validation before publishing to PyPI. ([#211](https://github.com/maxdjohnson/stkclient/pull/211))

Earlier releases are documented on the [GitHub releases page](https://github.com/maxdjohnson/stkclient/releases).
