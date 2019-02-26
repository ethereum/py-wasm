(module
  (export "thunk" (func $thunk))
  (export "call_thunk" (func $call_thunk))
  (export "add" (func $add))
  (export "call_add" (func $call_add))

  (func $call_thunk (param i32)
    block
      get_local 0
      i32.eqz
      br_if 0
      loop
        call $thunk
        get_local 0
        i32.const 1
        i32.sub
        tee_local 0
        br_if 0
      end
    end
  )

  (func $call_add (param i32) (param i32) (param i32)
    block
      get_local 0
      i32.eqz
      br_if 0
      loop
        get_local 2
        get_local 1
        call $add
        drop
        get_local 0
        i32.const 1
        i32.sub
        tee_local 0
        br_if 0
      end
    end
  )

  (func $thunk)

  (func $add (param i32) (param i32) (result i32)
    get_local 0
    get_local 1
    i32.add
  )
)
