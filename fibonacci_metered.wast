(module
  (type (;0;) (func (param i32) (result i32)))
  (type (;1;) (func (param i32)))
  (type (;2;) (func (param i32) (result i32)))
  (type (;3;) (func (param i32 i32)))
  (type (;4;) (func (result i32)))
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
  (func (;1;) (type 1) (param i32)
    (local i32)
    get_global 0
    set_local 1
    get_global 0
    get_local 0
    i32.sub
    set_global 0
    get_global 0
    get_local 1
    i32.gt_u
    if  ;; label = @1
      get_global 1
      set_local 1
      get_global 1
      i32.const 1
      i32.sub
      set_global 1
      get_global 1
      get_local 1
      i32.gt_u
      if  ;; label = @2
        get_global 2
        set_local 1
        get_global 2
        i32.const 1
        i32.sub
        set_global 2
        get_global 2
        get_local 1
        i32.gt_u
        if  ;; label = @3
          get_global 3
          set_local 1
          get_global 3
          i32.const 1
          i32.sub
          set_global 3
          get_global 3
          get_local 1
          i32.gt_u
          if  ;; label = @4
            unreachable
          end
        end
      end
    end)
  (func (;2;) (type 2) (param i32) (result i32)
    get_local 0
    i32.const 0
    i32.eq
    if (result i32)  ;; label = @1
      get_global 0
    else
      get_local 0
      i32.const 1
      i32.eq
      if (result i32)  ;; label = @2
        get_global 1
      else
        get_local 0
        i32.const 2
        i32.eq
        if (result i32)  ;; label = @3
          get_global 2
        else
          get_global 3
        end
      end
    end)
  (func (;3;) (type 3) (param i32 i32)
    get_local 0
    i32.const 0
    i32.eq
    if  ;; label = @1
      get_local 1
      set_global 0
    else
      get_local 0
      i32.const 1
      i32.eq
      if  ;; label = @2
        get_local 1
        set_global 1
      else
        get_local 0
        i32.const 2
        i32.eq
        if  ;; label = @3
          get_local 1
          set_global 2
        else
          get_local 1
          set_global 3
        end
      end
    end)
  (func (;4;) (type 4) (result i32)
    i32.const 4)
  (table (;0;) 0 anyfunc)
  (memory (;0;) 1)
  (global (;0;) (mut i32) (i32.const 0))
  (global (;1;) (mut i32) (i32.const 0))
  (global (;2;) (mut i32) (i32.const 0))
  (global (;3;) (mut i32) (i32.const 0))
  (export "memory" (memory 0))
  (export "fib" (func 0))
  (export "get_max_cycles" (func 2))
  (export "set_max_cycles" (func 3))
  (export "get_num_max_cycles_chunks" (func 4)))
