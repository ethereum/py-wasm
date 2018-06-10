# <PROJECT_NAME>

[![Join the chat at https://gitter.im/ethereum/<REPO_NAME>](https://badges.gitter.im/ethereum/<REPO_NAME>.svg)](https://gitter.im/ethereum/<REPO_NAME>?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![Build Status](https://circleci.com/gh/ethereum/<REPO_NAME>.svg?style=shield)](https://circleci.com/gh/ethereum/<REPO_NAME>)
[![PyPI version](https://badge.fury.io/py/<PYPI_NAME>.svg)](https://badge.fury.io/py/<PYPI_NAME>)
[![Python versions](https://img.shields.io/pypi/pyversions/<PYPI_NAME>.svg)](https://pypi.python.org/pypi/<PYPI_NAME>)
[![Docs build](https://readthedocs.org/projects/<RTD_NAME>/badge/?version=latest)](http://<RTD_NAME>.readthedocs.io/en/latest/?badge=latest)
   

<SHORT_DESCRIPTION>

Read more in the [documentation on ReadTheDocs](https://<RTD_NAME>.readthedocs.io/). [View the change log](https://<RTD_NAME>.readthedocs.io/en/latest/releases.html).

## Quickstart

```sh
pip install <PYPI_NAME>
```

## Developer Setup

If you would like to hack on <REPO_NAME>, please check out the
[Ethereum Development Tactical Manual](https://github.com/pipermerriam/ethereum-dev-tactical-manual)
for information on how we do:

- Testing
- Pull Requests
- Code Style
- Documentation

### Development Environment Setup

You can set up your dev environment with:

```sh
git clone git@github.com:ethereum/<REPO_NAME>.git
cd <REPO_NAME>
virtualenv -p python3 venv
. venv/bin/activate
pip install -e .[dev]
```

### Testing Setup

During development, you might like to have tests run on every file save.

Show flake8 errors on file change:

```sh
# Test flake8
when-changed -v -s -r -1 <MODULE_NAME>/ tests/ -c "clear; flake8 <MODULE_NAME> tests && echo 'flake8 success' || echo 'error'"
```

Run multi-process tests in one command, but without color:

```sh
# in the project root:
pytest --numprocesses=4 --looponfail --maxfail=1
# the same thing, succinctly:
pytest -n 4 -f --maxfail=1
```

Run in one thread, with color and desktop notifications:

```sh
cd venv
ptw --onfail "notify-send -t 5000 'Test failure ⚠⚠⚠⚠⚠' 'python 3 test on <REPO_NAME> failed'" ../tests ../<MODULE_NAME>
```

### Release setup

For Debian-like systems:
```
apt install pandoc
```

To release a new version:

```sh
make release bump=$$VERSION_PART_TO_BUMP$$
```

#### How to bumpversion

The version format for this repo is `{major}.{minor}.{patch}` for stable, and
`{major}.{minor}.{patch}-{stage}.{devnum}` for unstable (`stage` can be alpha or beta).

To issue the next version in line, specify which part to bump,
like `make release bump=minor` or `make release bump=devnum`. This is typically done from the
master branch, except when releasing a beta (in which case the beta is released from master,
and the previous stable branch is released from said branch). To include changes made with each
release, update "docs/releases.rst" with the changes, and apply commit directly to master 
before release.

If you are in a beta version, `make release bump=stage` will switch to a stable.

To issue an unstable version when the current version is stable, specify the
new version explicitly, like `make release bump="--new-version 4.0.0-alpha.1 devnum"`

# Legacy 

*WARNING: This is nearing completion and still being tested.*
  

**pywebassembly.py**: Closely follows *WebAssembly Specification, Release 1.0, April 11, 2018*. Implements the following chapters.

Chapter 2 which defines the abstract syntax.

Chapter 3 which defines validation rules over the abstract syntax. These rules constrain the syntax, but provide properties such as type-safety. An almost-complete implementation is available as a feature-branch, the only thing missing is validation after opcodes such as `unreachable`.

Chapter 4 which defines execution semantics over the abstract syntax. This is implemented and passes all `assert_return` and `assert_trap` tests of the official Wasm tests, except for for tests involving floating-point which is not yet implemented.

Chapter 5 which defines a binary syntax over the abstract syntax. All functions were implemented, creating a recursive-descent parser which takes a `.wasm` file and builds a abstract syntax tree out of nested Python lists and dicts. Also implemented are inverses (up to a canonical form) back to a `.wasm` file -- this is useful to transform the syntax tree and write it back to a `.wasm` file.

Appendix which defines parts of a standard embedding, and an algorithm to validate instruction sequences. We implement most of this.

Note that functions from the specification are named with prefix `spec_`, e.g. `spec_<funcname>(...)`, and their inverses (of a canonical form) also have postfix `_inv`, e.g. `spec_<funcname>_inv(...)`.

**examples/**: Some sample uses of pywebassembly, including a metering injector.

**tests/**:  Testing of pywebassembly.



TODO:
 * Support floating point values and opcodes.
 * Support text format as described in chapter 6.
 * Finish validation.
 * Implement remaining testing opcodes, see `tests/README.md`.



