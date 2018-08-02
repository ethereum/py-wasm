
(module
  (import "mod1" "f0" (func (param i32) (result i32)))
  (func (;1;) (result i32)
    i32.const 1
    call 0)
  (export "f1" (func 1))
)

