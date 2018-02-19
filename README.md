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

**pyWebAssembly.py**: Closely follows *WebAssembly Specification, Release 1.0, Dec 13, 2017*. Implements Chapter 5 and necessary parts of Chapters 2 and 4. The resulting recursive-descent parser takes a `.wasm` file and builds a syntax tree with nested tuples, lists, and dicts. This process is invertible back to a `.wasm` file. Functions from the specification are named `spec_<func>(...)` and their inverses (of a canonical form) are named `spec_<func>_inv(...)`.


**metering.py**: Injects a function call before each sequence of unbranching instructions, whose argument is the sum of costs of instructions in the sequence. Also injects helper functions, including the metering function which updates the cycle count and traps when a limit is exceeded.

The original C fibonacci function:

Before metering (see `fibonacci.wast` for full module, and the original fibonacci function in C).
```
  (func (;0;) (type 0) (param i32) (result i32)
    (local i32 i32 i32)
    i32.const 1
    set_local 1
    block  ;; label = @1
      get_local 0
      i32.const 1
      i32.lt_s
      br_if 0 (;@1;)
      i32.const 1
      set_local 3
      i32.const 0
      set_local 2
      loop  ;; label = @2
        get_local 2
        get_local 3
        i32.add
        set_local 1
        get_local 3
        set_local 2
        get_local 1
        set_local 3
        get_local 0
        i32.const -1
        i32.add
        tee_local 0
        br_if 0 (;@2;)
      end
    end
    get_local 1)
```


After metering (see `fibonacci_metered.wast` for full module). Notice injected `i32.const n` `call 1` where n is sum of costs of instructions until the next branch (each instruction costs one for this example). The metering function has index `1` in this example -- this index is handled automatically.
```
  (func (;0;) (type 0) (param i32) (result i32)
    (local i32 i32 i32)
    i32.const 3
    call 1
    i32.const 1
    set_local 1
    block  ;; label = @1
      i32.const 4
      call 1
      get_local 0
      i32.const 1
      i32.lt_s
      br_if 0 (;@1;)
      i32.const 5
      call 1
      i32.const 1
      set_local 3
      i32.const 0
      set_local 2
      loop  ;; label = @2
        i32.const 13
        call 1
        get_local 2
        get_local 3
        i32.add
        set_local 1
        get_local 3
        set_local 2
        get_local 1
        set_local 3
        get_local 0
        i32.const -1
        i32.add
        tee_local 0
        br_if 0 (;@2;)
      end
    end
    i32.const 1
    call 1
    get_local 1)
```


**index.html**: Demo to run any file generated by `metering.py` (e.g. `fibonacci_metered.wasm`). User specifies the `.wasm` file, function name, argument, and cycles limit. Because JavaScript doesn't support the `i64` type and we want more than 2^32 cycles, we allow arbitrary precision integers imported and exported to and from the wasm module as a sequence of `i32`s, using helper functions in both JavaScript and injected by `metering.py`. A trap occurs if the cycles limit is exceeded! To run this demo, a server is needed to serve the `.wasm` file: execute `python3 -m http.server` in this directory and visit the given URL in the browser. Notice the 46th Fibonacci numbers overflows `i32`.


**fibonacci...**: Various versions of our demo fibonacci module. The `_metered.wasm` file is generated by `metering.py`. The `.wast` versions are generated by `wasm2wast`.


TODO:

 * Floating point canonicalization code injector.
 * Interpretter as described in chapter 4.
 * Support text format as described in chapter 6.



