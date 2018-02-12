(module
  (type (;0;) (func (param i32) (result i32)))
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
  (table (;0;) 0 anyfunc)
  (memory (;0;) 1)
  (export "memory" (memory 0))
  (export "fib" (func 0)))


(;
int fib(int n){
  int a_=1,a=1;
  for(int i=0;i<n;i++){
    int tmp=a;
    a=a+a_;
    a_=tmp;
  }
  return a;  
}
;)
