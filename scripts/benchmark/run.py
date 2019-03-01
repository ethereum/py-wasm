from pathlib import Path
import time

import numpy

from wasm import (
    Runtime,
)


# From https://github.com/alexcrichton/rust-wasm-benchmark/blob/master/raw-wasm/raw.wast
BASE_DIR = Path(__file__).parent
WASM_BENCH = BASE_DIR / 'bench.wasm'


def _get_fn_address(runtime, module, function_name):
    for export in module.exports:
        if export.is_function and export.name == function_name:
            return export.function_address
    else:
        raise Exception(f"No function found by name: {function_name}")


def bench():
    runtime = Runtime()
    module, _ = runtime.instantiate_module(runtime.load_module(WASM_BENCH))
    runtime.register_module('bench', module)

    thunk_delta = bench_fn(runtime, module, 'thunk', (), 10000)
    add_delta = bench_fn(runtime, module, 'add', (numpy.uint32(1), numpy.uint32(2)), 10000)
    call_thunk_delta = bench_fn(runtime, module, 'call_thunk', (numpy.uint32(10000),), 1)
    call_add_delta = bench_fn(
        runtime,
        module,
        'call_add',
        (numpy.uint32(10000), numpy.uint32(1), numpy.uint32(2)),
        1,
    )

    print(f"wrapped thunk: {call_thunk_delta / 10000:.8f} per call")
    print(f"wrapped add  : {call_add_delta / 10000:.8f} per call")

    thunk_overhead = (call_thunk_delta - thunk_delta)
    add_overhead = call_add_delta - add_delta
    print(f"call overhead for thunk: {thunk_overhead:.4f} ({100 * thunk_overhead / thunk_delta:.2f}%)  |   {thunk_overhead / 10000:.8f} per call")  # noqa: E501
    print(f"call overhead for add  : {add_overhead:.4f} ({100 * add_overhead / add_delta:.2f}%)  |   {add_overhead / 10000:.8f} per call")  # noqa: E501


def bench_fn(runtime, module, fn_name, fn_args, times):
    func_addr = _get_fn_address(runtime, module, fn_name)
    start_at = time.perf_counter()
    for _ in range(times):
        runtime.invoke_function(func_addr, fn_args)
    end_at = time.perf_counter()
    delta = end_at - start_at
    signature = f"{fn_name}{fn_args}"
    print(f"{signature.ljust(22)} x {str(times).rjust(10)}: {delta:.4f}  |  {delta / times:.4f} per-call")  # noqa: E501
    return delta


if __name__ == '__main__':
    bench()
