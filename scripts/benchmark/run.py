import argparse
import logging
from pathlib import (
    Path,
)
import sys
import time

import numpy

from wasm import (
    Runtime,
)

# From https://github.com/alexcrichton/rust-wasm-benchmark/blob/master/raw-wasm/raw.wast
BASE_DIR = Path(__file__).parent

BASIC_WASM = BASE_DIR / 'bench.wasm'

FACTORIZATION_1117_WASM = BASE_DIR / 'factorization_1117_reikna_wasm.wasm'
FACTORIZATION_9973_WASM = BASE_DIR / 'factorization_9973_reikna_wasm.wasm'
FACTORIZATION_2147483647_WASM = BASE_DIR / 'factorization_2147483647_reikna_wasm.wasm'

FIBONACCI_38_WASM = BASE_DIR / 'fibonacci_38_bigint_wasm.wasm'
FIBONACCI_17_WASM = BASE_DIR / 'fibonacci_17_bigint_wasm.wasm'
FIBONACCI_11_WASM = BASE_DIR / 'fibonacci_11_bigint_wasm.wasm'
FIBONACCI_1_WASM = BASE_DIR / 'fibonacci_1_bigint_wasm.wasm'

RECURSIVE_1_KECCAK = BASE_DIR / 'recursive_keccak_1_wasm.wasm'
RECURSIVE_10_KECCAK = BASE_DIR / 'recursive_keccak_10_wasm.wasm'
RECURSIVE_100_KECCAK = BASE_DIR / 'recursive_keccak_100_wasm.wasm'


logging.basicConfig(level=logging.INFO, format='%(message)s', stream=sys.stdout)


def _get_fn_address(runtime, module, function_name):
    for export in module.exports:
        if export.is_function and export.name == function_name:
            return export.function_address
    else:
        raise Exception(f"No function found by name: {function_name}")


def do_basic_benchmarks():
    runtime = Runtime()
    module, _ = runtime.instantiate_module(runtime.load_module(BASIC_WASM))
    runtime.register_module('bench', module)

    thunk_delta = _run_basic_bench(runtime, module, 'thunk', (), 10000)
    add_delta = _run_basic_bench(runtime, module, 'add', (numpy.uint32(1), numpy.uint32(2)), 10000)
    call_thunk_delta = _run_basic_bench(runtime, module, 'call_thunk', (numpy.uint32(10000),), 1)
    call_add_delta = _run_basic_bench(
        runtime, module, 'call_add', (numpy.uint32(10000), numpy.uint32(1), numpy.uint32(2)), 1,
    )

    logging.info(f"wrapped thunk: {call_thunk_delta / 10000:.8f} per call")
    logging.info(f"wrapped add  : {call_add_delta / 10000:.8f} per call")

    thunk_overhead = (call_thunk_delta - thunk_delta)
    add_overhead = call_add_delta - add_delta
    logging.info(f"call overhead for thunk: {thunk_overhead:.4f} ({100 * thunk_overhead / thunk_delta:.2f}%)  |   {thunk_overhead / 10000:.8f} per call")  # noqa: E501
    logging.info(f"call overhead for add  : {add_overhead:.4f} ({100 * add_overhead / add_delta:.2f}%)  |   {add_overhead / 10000:.8f} per call")  # noqa: E501


def _run_basic_bench(runtime, module, fn_name, fn_args, times):
    signature = f"{fn_name}{fn_args}"
    logging.info(f"BENCHMARKING: {signature}")
    delta = time_fn(runtime, module, fn_name, fn_args, times)
    logging.info(f"{signature.ljust(22)} x {str(times).rjust(10)}: {delta:.4f}  |  {delta / times:.4f} per-call")  # noqa: E501
    return delta


#
# Tests from https://github.com/fluencelabs/fluence/tree/master/bench/vm/tests
#
def do_factorization_benchmarks(prime):
    runtime = Runtime()

    if prime == 1117:
        module, _ = runtime.instantiate_module(runtime.load_module(FACTORIZATION_1117_WASM))
    elif prime == 9973:
        module, _ = runtime.instantiate_module(runtime.load_module(FACTORIZATION_9973_WASM))
    elif prime == 2147483647:
        module, _ = runtime.instantiate_module(runtime.load_module(FACTORIZATION_2147483647_WASM))
    else:
        raise Exception("Only 1117, 9973, 2147483647 are supported")

    logging.info(f"BENCHMARKING: factorization of {prime}")
    delta = time_fn(runtime, module, 'main', (), 1)
    logging.info(f"took: {delta:.4f}")


def do_fibonacci_bigint_benchmarks(order):
    runtime = Runtime()

    if order == 1:
        module, _ = runtime.instantiate_module(runtime.load_module(FIBONACCI_1_WASM))
    elif order == 11:
        module, _ = runtime.instantiate_module(runtime.load_module(FIBONACCI_11_WASM))
    elif order == 17:
        module, _ = runtime.instantiate_module(runtime.load_module(FIBONACCI_17_WASM))
    elif order == 38:
        module, _ = runtime.instantiate_module(runtime.load_module(FIBONACCI_38_WASM))
    else:
        raise Exception("Only 1, 11, 17, 38 are supported")

    logging.info(f"BENCHMARKING: recursive computation of fibonacci number {order} (wasm)")
    delta = time_fn(runtime, module, 'main', (), 1)
    logging.info(f"took: {delta:.4f}")


def do_recursive_keccak(depth):
    runtime = Runtime()

    if depth == 1:
        module, _ = runtime.instantiate_module(runtime.load_module(RECURSIVE_1_KECCAK))
    elif depth == 10:
        module, _ = runtime.instantiate_module(runtime.load_module(RECURSIVE_10_KECCAK))
    elif depth == 100:
        module, _ = runtime.instantiate_module(runtime.load_module(RECURSIVE_100_KECCAK))
    else:
        raise Exception("Only 1, 10, 100 are supported")

    logging.info(f"BENCHMARKING: {depth} recursive keccak hashes")
    delta = time_fn(runtime, module, 'main', (), 1)
    logging.info(f"took: {delta:.4f}")


def time_fn(runtime, module, fn_name, fn_args, times):
    func_addr = _get_fn_address(runtime, module, fn_name)
    start_at = time.perf_counter()
    for _ in range(times):
        runtime.invoke_function(func_addr, fn_args)
    end_at = time.perf_counter()
    delta = end_at - start_at
    return delta


parser = argparse.ArgumentParser(description='Py-Wasm Benchmark')
parser.add_argument(
    '--basic',
    action='store_true',
    help=("Enable basic thunk() and add(1, 2) benchmarks"),
)
parser.add_argument(
    '--fibonacci-1',
    action='store_true',
    help=(
        "Enable benchmark for computing the 1st fibonacci number using a big "
        "integer library"
    ),
)
parser.add_argument(
    '--fibonacci-11',
    action='store_true',
    help=(
        "Enable benchmark for computing the 11th fibonacci number using a big "
        "integer library"
    ),
)
parser.add_argument(
    '--fibonacci-17',
    action='store_true',
    help=(
        "Enable benchmark for computing the 17th fibonacci number using a big "
        "integer library"
    ),
)
parser.add_argument(
    '--fibonacci-38',
    action='store_true',
    help=(
        "Enable benchmark for computing the 38th fibonacci number using a big "
        "integer library"
    ),
)
parser.add_argument(
    '--factorization-1117',
    action='store_true',
    help=(
        "Enable benchmark for computing the factorization of 1117"
    ),
)
parser.add_argument(
    '--factorization-9973',
    action='store_true',
    help=(
        "Enable benchmark for computing the factorization of 9973"
    ),
)
parser.add_argument(
    '--factorization-2147483647',
    action='store_true',
    help=(
        "Enable benchmark for computing the factorization of 2147483647"
    ),
)
parser.add_argument(
    '--recursive-keccak-1',
    action='store_true',
    help=(
        "Enable benchmark for computing a singe keccak"
    ),
)
parser.add_argument(
    '--recursive-keccak-10',
    action='store_true',
    help=(
        "Enable benchmark for computing 10 levels of recursive keccak"
    ),
)
parser.add_argument(
    '--recursive-keccak-100',
    action='store_true',
    help=(
        "Enable benchmark for computing 100 levels of recursive keccak"
    ),
)


if __name__ == '__main__':
    args = parser.parse_args()
    none_selected = not any((
        args.basic,
        args.fibonacci_1,
        args.fibonacci_11,
        args.fibonacci_17,
        args.fibonacci_38,
        args.factorization_1117,
        args.factorization_9973,
        args.factorization_2147483647,
        args.recursive_keccak_1,
        args.recursive_keccak_10,
        args.recursive_keccak_100,
    ))

    if none_selected:
        logging.info("No benchmarks selected.... EXITING")
        sys.exit(0)

    if args.basic:
        do_basic_benchmarks()

    if args.fibonacci_1:
        do_fibonacci_bigint_benchmarks(1)

    if args.fibonacci_11:
        do_fibonacci_bigint_benchmarks(11)

    if args.fibonacci_17:
        do_fibonacci_bigint_benchmarks(17)

    if args.fibonacci_38:
        logging.error("This benchmark could take a REEAALLLYYYY long time to finish...")
        do_fibonacci_bigint_benchmarks(38)

    if args.factorization_1117:
        do_factorization_benchmarks(1117)

    if args.factorization_9973:
        do_factorization_benchmarks(9973)

    if args.factorization_2147483647:
        logging.error("This benchmark could take a REEAALLLYYYY long time to finish...")
        do_factorization_benchmarks(2147483647)

    if args.recursive_keccak_1:
        do_recursive_keccak(1)

    if args.recursive_keccak_10:
        do_recursive_keccak(10)

    if args.recursive_keccak_100:
        do_recursive_keccak(100)
