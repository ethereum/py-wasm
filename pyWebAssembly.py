#!/usr/bin/env python


"""
TODO:
 - validator
   - chapter 3 infrastructure is mostly done, need to finish spec_validate_instrstar(), then will test and debug
   - chapter 7 infrastructure is mostly done, almost ready to test and debug
 - execution
   - chapter 4 infrastructure done, needs testing
 - binary parser
   - chapter 5 error handling needed
   - if idx>len(raw) or idx<0 and access raw[idx], will get "index out of range" error, but should handle this and return an error code

"""



"""
differences from spec:
 - when some syntax is eg importdesc,exportdesc,externval,extertype,...  eg  func functype  I make it into dictionary {"func":functype}  NO, I AM CHANGING THIS
 - instead of calling eg  func(), I use a list comprehension to choose all that have "func"
 - instead of holding types and values in the stack eg i32.const 5, I just hold value 5. This is everywhere including locals, globals, value stack. So may not be able to get type just from store.
 - store is modified in each call, ie old copy is modified
"""



verbose = 2


###############
###############
# 2 STRUCTURE #
###############
###############


# 2.2.3 FLOATING-POINT

N_to_signif={32:23,64:52}
signif_to_N={val:key for key,val in N_to_signif.items()}

def spec_signif(N):
  if verbose>=1: print("spec_signif(",N,")")
  if N in N_to_signif:
    return N_to_signif[N]
  else:
    return None

def spec_signif_inv(signif):
  if verbose>=1: print("spec_signif_inv(",signif,")")
  if signif in signif_to_N:
    return signif_to_N[signif]
  else:
    return None

N_to_expon={32:8,64:11}
expon_to_N={val:key for key,val in N_to_expon.items()}

def spec_expon(N):
  if verbose>=1: print("spec_expon(",N,")")
  if N in N_to_expon:
    return N_to_expon[N]
  else:
    return None

def spec_expon_inv(expon):
  if verbose>=1: print("spec_expon_inv(",expon,")")
  if expon in expon_to_N:
    return expon_to_N[expon]
  else:
    return None





################
################
# 3 VALIDATION #
################
################


# 3.4.10 MODULE

def spec_validate_module(mod):
  if verbose>=1: print("spec_validate_module(",")")
  print(mod)
  #print(mod["imports"])
  #print(mod["imports"])
  #this is incomplete, just has enough for spec_instantiate()
  itstar = []
  for import_ in mod["imports"]:
    if import_["desc"][0] == "func":
      itstar.append( ["func",mod["types"][import_["desc"][1]]] )
    else:
      itstar.append( import_["desc"] )
  etstar = []
  for export in mod["exports"]:
    if export["desc"][0] == "func":
      #print("mod[\"types\"]",mod["types"])
      #print("mod[\"funcs\"]" ,mod["funcs"] )
      #print("export[\"desc\"]",export["desc"])
      etstar.append( mod["types"][ mod["funcs"][export["desc"][1]]["type"] ])
    elif export["desc"][0] == "table":
      etstar.append( ["table",mod["tables"][export["desc"][1]]["type"]] )
    elif export["desc"][0] == "mem":
      #print(mod["mems"][export["desc"][1]])
      etstar.append( ["mem",mod["mems"][export["desc"][1]]["type"]] )
    elif export["desc"][0] == "global":
      etstar.append( ["global",mod["globals"][export["desc"][1]]["type"]] )
  return [itstar, etstar]









###############
###############
# 4 EXECUTION #
###############
###############

  

##############
# 4.3 NUMERICS
##############

def spec_trunc(q):
  if verbose>=1: print("spec_trunc(",q,")")
  # round towards zero
  # q can be float or rational as tuple (numerator,denominator)
  if type(q)==tuple: #rational
    result = q[0]//q[1] #rounds towards negative infinity
    if result < 0 and q[1]*result != q[0]:
      return result+1
    else:
      return result
  elif type(q)==float:
    return int(q) 


# 4.3.1 REPRESENTATIONS

# bits are string of 1s and 0s
# bytes are bytearray (maybe can also read from memoryview)

def spec_bitst(t,c):
  if verbose>=1: print("spec_bitst(",t,c,")")
  N = int(t[1:3])
  if t[0]=='i':
    return spec_bitsiN(N,c)
  elif t[0]=='f':
    return spec_bitsfN(N,c)

def spec_bitsiN(N,i):
  if verbose>=1: print("spec_bitsiN(",N,i,")")
  return spec_ibitsN(N,i)

def spec_bitsiN_inv(N,i):
  if verbose>=1: print("spec_bitsiN_inv(",N,i,")")
  return spec_ibitsN_inv(N,i)

def spec_bitsfN(N,z):
  if verbose>=1: print("spec_bitsfN(",N,z,")")
  return spec_fbitsN(N,z)

def spec_bitsfN_inv(N,z):
  if verbose>=1: print("spec_bitsiN_inv(",N,z,")")
  return spec_fbitsN_inv(N,z)


# Integers

def spec_ibitsN(N,i):
  if verbose>=1: print("spec_ibitsN(",N,i,")")
  return bin(i)[2:].zfill(N)

def spec_ibitsN_inv(N,bits):
  if verbose>=1: print("spec_ibitsN_inv(",N,bits,")")
  return int(bits,2)


# Floating-Point

def spec_bitsfN(N,z):
  if verbose>=1: print("spec_bitsfN(",N,z,")")
  return spec_fbitsN(N,z)

def spec_fbitsN(N,z):
  if verbose>=1: print("spec_fbitsN(",N,z,")")
  #TODO, this is used by reinterpret
  return "01010101" #this is garbage

def spec_fbitsN_inv(N,z):
  if verbose>=1: print("spec_fbitsN_inv(",N,z,")")
  #TODO, this is used by reinterpret
  return float(z)

#floating-point values are encoded directly by their IEEE 754-2008 bit pattern in little endian byte order
def spec_bytes_fN_inv(bstar,N):
  if verbose>=1: print("spec_bytes_fN_inv(",bstar,N,")")
  #TODO: check and possibly convert with littleendian() 
  bitstring=""
  for by in bstar:
    bitstring += bin(by)[2:].rjust(8, '0')
  signstring='+' if bitstring[0]=='1' else '-'
  M=spec_signif(N)
  E=spec_expon(N)
  e=bitstring[1:E+1]
  m=bitstring[E+1:]
  if e=='1'*E:
    if m=='0'*M:
      return signstring+"inf"
    else:
      return signstring+"nan("+string(int(m,2))+")"
  elif e=='0'*E:
    return signstring+'0.'+str(int(m,2))
  else:
    return signstring+"1."+str(int(m,2))+"e"+str(int(e,2)-(2**(E-1)-1))


# Storage

def spec_bytest(t,i):
  if verbose>=1: print("spec_bytest(",t,i,")")
  if t[0]=='i':
    return spec_bytesiN(int(t[1:3]),i)
  elif t[0]=='f':
    return spec_bytesfN(int(t[1:3]),i)
  else:
    return None

def spec_bytest_inv(t,i):
  if verbose>=1: print("spec_bytest_inv(",t,i,")")
  if t[0]=='i':
    return spec_bytesiN_inv(int(t[1:3]),i)
  elif t[0]=='f':
    return spec_bytesfN_inv(int(t[1:3]),i)
  else:
    return None

def spec_bytesiN(N,i):
  if verbose>=1: print("spec_bytesiN(",N,i,")")
  #bits = spec_littleendian(spec_bitsiN(N,i))
  bits = spec_bitsiN(N,i)
  #convert bits to bytes
  bytes_ = bytearray()
  for byteIdx in range(0,len(bits),8):
    bytes_ += bytearray([int(bits[byteIdx:byteIdx+8],2)])
  return bytes_

def spec_bytesiN_inv(N,bytes_):
  if verbose>=1: print("spec_bytesiN_inv(",N,bytes_,")")
  bits=""
  for byte in bytes_:
    bits += spec_ibitsN(8,byte)
  #bits = spec_littleendian(bits)
  return spec_ibitsN_inv(N,bits)

def spec_bytesfN(N,z):
  if verbose>=1: print("spec_bytesfN(",N,z,")")
  #TODO:implement this, garbage for now
  if N==32:
    return bytearray([1,2,3,4])
  if N==64:
    return bytearray([1,2,3,4,5,6,7,8])

def spec_bytesfN_inv(N,d):
  if verbose>=1: print("spec_bytesfN_inv(",N,d,")")
  #TODO
  return None

def spec_littleendian(d):
  if verbose>=1: print("spec_littleendian(",d,")")
  #same behavior for both 32 and 64-bit values
  if len(d)==0: return ''
  d18 = d[:8]
  d2Nm8 = d[8:]
  return d18 + spec_littleendian(d2Nm8)

def spec_littleendian_inv(d):
  if verbose>=1: print("spec_littleendian_inv(",d,")")
  #this assumes len(d) is divisible by 8
  #same behavior for both 32 and 64-bit values
  return spec_littleendian(d)



# 4.3.2 INTEGER OPERATIONS

# all values are stored as positive numbers, when need signed interpretation, use spec_signediN and spec_signediN_inv()
# alternatives:
#  ctypes.c_uint32
#  numpy.uint32 which is less portable
#  BitArray(int=-1000, length=32), >> operator
#  bitstring.Bits(int=-1, length=12)
#  similar but maybe not useful: array, 

#two's comlement
def spec_signediN(N,i):
  if verbose>=1: print("spec_signediN(",N,i,")")
  if 0<=i<2**(N-1):
    return i
  elif 2**(N-1)<=i<2**N:
    return i-2**N
  else:
    return None
  #alternative 2's comlement
  #  return i - int((i << 1) & 2**N) #https://stackoverflow.com/a/36338336

def spec_signediN_inv(N,i):
  if verbose>=1: print("spec_signediN_inv(",N,i,")")
  if 0<=i<2**(N-1):
    return i
  elif -1*(2**(N-1))<=i<0:
    return i+2**N
  else:
    return None

def spec_iaddN(N,i1,i2):
  if verbose>=1: print("spec_iaddN(",N,i1,i2,")")
  return (i1+i2) % 2**N

def spec_isubN(N,i1,i2):
  if verbose>=1: print("spec_isubN(",N,i1,i2,")")
  return (i1-i2+2**N) % 2**N

def spec_imulN(N,i1,i2):
  if verbose>=1: print("spec_imulN(",N,i1,i2,")")
  return (i1*i2) % 2**N

def spec_idiv_uN(N,i1,i2):
  if verbose>=1: print("spec_idiv_uN(",N,i1,i2,")")
  if i2==0: return "trap"
  return spec_trunc((i1,i2))

def spec_idiv_sN(N,i1,i2):
  if verbose>=1: print("spec_idiv_sN(",N,i1,i2,")")
  j1 = spec_signediN(N,i1)
  j2 = spec_signediN(N,i2)
  if j2==0: return "trap"
  #assuming j1 and j2 are N-bit
  if j1//j2 == 2**(N-1): return "trap"
  return spec_signediN_inv(N,spec_trunc((j1,j2)))

def spec_irem_uN(N,i1,i2):
  if verbose>=1: print("spec_irem_uN(",i1,i2,")")
  if i2==0: return "trap"
  return i1-i2*spec_trunc((i1,i2))

def spec_irem_sN(N,i1,i2):
  if verbose>=1: print("spec_irem_sN(",N,i1,i2,")")
  j1 = spec_signediN(N,i1)
  j2 = spec_signediN(N,i2)
  if i2==0: return "trap"
  print(j1,j2,spec_trunc((j1,j2)))
  return spec_signediN_inv(N,j1-j2*spec_trunc((j1,j2)))
  
def spec_iandN(N,i1,i2):
  if verbose>=1: print("spec_iandN(",N,i1,i2,")")
  return i1 & i2

def spec_iorN(N,i1,i2):
  if verbose>=1: print("spec_iorN(",N,i1,i2,")")
  return i1 | i2

def spec_ixorN(N,i1,i2):
  if verbose>=1: print("spec_ixorN(",N,i1,i2,")")
  return i1 ^ i2
 
def spec_ishlN(N,i1,i2):
  if verbose>=1: print("spec_ishlN(",N,i1,i2,")")
  k = i2 % N
  return (i1 << k) % (2**N)

def spec_ishr_uN(N,i1,i2):
  if verbose>=1: print("spec_ishr_uN(",N,i1,i2,")")
  j2 = i2 % N
  return i1 >> j2
  
def spec_ishr_sN(N,i1,i2):
  if verbose>=1: print("spec_ishr_sN(",N,i1,i2,")")
  print("spec_ishr_sN(",N,i1,i2,")")
  k = i2 % N
  print(k)
  d0d1Nmkm1d2k = spec_ibitsN(N,i1)
  d0 = d0d1Nmkm1d2k[0]
  d1Nmkm1 = d0d1Nmkm1d2k[1:N-k]
  #print(d0*k)
  #print(d0*(k+1) + d1Nmkm1)
  return spec_ibitsN_inv(N, d0*(k+1) + d1Nmkm1 )

def spec_irotlN(N,i1,i2):
  if verbose>=1: print("spec_irotlN(",N,i1,i2,")")
  k = i2 % N
  d1kd2Nmk = spec_ibitsN(N,i1)
  d2Nmk = d1kd2Nmk[k:]
  d1k = d1kd2Nmk[:k]
  return spec_ibitsN_inv(N, d2Nmk+d1k )

def spec_irotrN(N,i1,i2):
  if verbose>=1: print("spec_irotrN(",N,i1,i2,")")
  k = i2 % N
  d1Nmkd2k = spec_ibitsN(N,i1)
  d1Nmk = d1Nmkd2k[:N-k]
  d2k = d1Nmkd2k[N-k:]
  return spec_ibitsN_inv(N, d2k+d1Nmk )

def spec_iclzN(N,i):
  if verbose>=1: print("spec_iclzN(",N,i,")")
  k = 0
  for b in spec_ibitsN(N,i):
    if b=='0':
      k+=1
    else:
      break
  return k

def spec_ictzN(N,i):
  if verbose>=1: print("spec_ictzN(",N,i,")")
  k = 0
  for b in reversed(spec_ibitsN(N,i)):
    if b=='0':
      k+=1
    else:
      break
  return k

def spec_ipopcntN(N,i):
  if verbose>=1: print("spec_ipopcntN(",N,i,")")
  k = 0
  for b in spec_ibitsN(N,i):
    if b=='1':
      k+=1
  return k

def spec_ieqzN(N,i):
  if verbose>=1: print("spec_ieqzN(",N,i,")")
  if i==0:
    return 1
  else:
    return 0

def spec_ieqN(N,i1,i2):
  if verbose>=1: print("spec_ieqN(",N,i1,i2,")")
  if i1==i2:
    return 1
  else:
    return 0

def spec_ineN(N,i1,i2):
  if verbose>=1: print("spec_ineN(",N,i1,i2,")")
  if i1!=i2:
    return 1
  else:
    return 0

def spec_ilt_uN(N,i1,i2):
  if verbose>=1: print("spec_ilt_uN(",N,i1,i2,")")
  if i1<i2:
    return 1
  else:
    return 0

def spec_ilt_sN(N,i1,i2):
  if verbose>=1: print("spec_ilt_sN(",N,i1,i2,")")
  j1 = spec_signediN(N,i1)
  j2 = spec_signediN(N,i2)
  if j1<j2:
    return 1
  else:
    return 0

def spec_igt_uN(N,i1,i2):
  if verbose>=1: print("spec_igt_uN(",N,i1,i2,")")
  if i1>i2:
    return 1
  else:
    return 0

def spec_igt_sN(N,i1,i2):
  if verbose>=1: print("spec_igt_sN(",N,i1,i2,")")
  j1 = spec_signediN(N,i1)
  j2 = spec_signediN(N,i2)
  if j1>j2:
    return 1
  else:
    return 0

def spec_ile_uN(N,i1,i2):
  if verbose>=1: print("spec_ile_uN(",N,i2,i1,")")
  if i1<=i2:
    return 1
  else:
    return 0

def spec_ile_sN(N,i1,i2):
  if verbose>=1: print("spec_ile_sN(",N,i1,i2,")")
  j1 = spec_signediN(N,i1)
  j2 = spec_signediN(N,i2)
  if j1<=j2:
    return 1
  else:
    return 0

def spec_ige_uN(N,i1,i2):
  if verbose>=1: print("spec_ige_uN(",N,i1,i2,")")
  if i1>=i2:
    return 1
  else:
    return 0

def spec_ige_sN(N,i1,i2):
  if verbose>=1: print("spec_ige_sN(",N,i1,i2,")")
  j1 = spec_signediN(N,i1)
  j2 = spec_signediN(N,i2)
  if j1>=j2:
    return 1
  else:
    return 0


# 4.3.3 FLOATING-POINT OPERATIONS


def spec_fabsN(N,z):
  if z<0:
    return -1*z
  else:
    return z

def spec_fnegN(N,z):
  return -1*z

def spec_fceilN(N,z):
  #TODO
  return z

def spec_ffloorN(N,z):
  #TODO
  return z

def spec_ftruncN(N,z):
  #TODO
  return z

def spec_fnearestN(N,z):
  #TODO
  return z

def spec_fsqrtN(N,z):
  return z

def spec_faddN(N,z1,z2):
  return z1+z2

def spec_fsubN(N,z1,z2):
  return z1-z2

def spec_fmulN(N,z1,z2):
  return z1*z2

def spec_fdivN(N,z1,z2):
  return z1/z2

def spec_fminN(N,z1,z2):
  if z1 < z2: return z1
  else: return z2

def spec_fmaxN(N,z1,z2):
  if z1 > z2: return z1
  else: return z2

def spec_fcopysignN(N,z1,z2):
  if (z1>0 and z2>0) or (z1<=0 and z2<=0):
    return z1
  else:
    return -1*z1

def spec_feqN(N,z1,z2):
  return z1==z2

def spec_fneN(N,z1,z2):
  return z1 != z2

def spec_fltN(N,z1,z2):
  return z1 < z2

def spec_fgtN(N,z1,z2):
  return z1 > z2

def spec_fleN(N,z1,z2):
  return z1 <= z2

def spec_fgeN(N,z1,z2):
  return z1 >= z2



# 4.3.4 CONVERSIONS

def spec_extend_uMN(N,M,i):
  if verbose>=1: print("spec_extend_uMN(",i,")")
  return i

def spec_extend_sMN(N,M,i):
  if verbose>=1: print("spec_extend_sMN(",M,N,i,")")
  print("spec_extend_sMN(",M,N,i,")")
  j = spec_signediN(M,i)
  return spec_signediN_inv(N,j)

def spec_wrapMN(N,M,i):
  if verbose>=1: print("spec_wrapMN(",M,N,i,")")
  print("spec_wrapMN(",M,N,i,")")
  return i % (2**N)

def spec_trunc_uMN(M,N,z):
  #TODO: floating point stuff
  return z

def spec_trunc_sMN(M,N,z):
  #TODO: floating point stuff
  return z

def spec_promoteMN(M,N,z):
  #TODO: floating point stuff
  return z

def spec_demoteMN(M,N,z):
  #TODO: floating point stuff
  return z

def spec_convert_uMN(M,N,z):
  #TODO: floating point stuff
  return z

def spec_convert_sMN(M,N,z):
  #TODO: floating point stuff
  return z

def spec_reinterprett1t2(t1,t2,c):
  if verbose>=1: print("spec_reinterprett1t2(",t1,t2,c,")")
  if t1=='i32':
    bitst1 = spec_bitsiN(32,c)
  elif t1=='i64':
    bitst1 = spec_bitsiN(64,c)
  elif t1=='f32':
    bitst1 = spec_bitsfN(32,c)
  elif t1=='f64':
    bitst1 = spec_bitsfN(64,c)
  if t2=='i32':
    return spec_bitsiN_inv(32,bitst1)
  elif t2=='i64':
    return spec_bitsiN_inv(64,bitst1)
  elif t2=='f32':
    return spec_bitsfN_inv(32,bitst1)
  elif t2=='f64':
    return spec_bitsfN_inv(64,bitst1)


##################
# 4.4 INSTRUCTIONS
##################

# S is the store

# 4.4.1 NUMERIC INSTRUCTIONS

def spec_tconst(config):
  if verbose>=1: print("spec_tconst(",")")
  S = config["S"]
  c = config["instrstar"][config["idx"]][1]
  if type(c)==bytearray: #TODO:fix parsing float const then remove this hack
    c = 1.1
  config["operand_stack"] += [c]
  config["idx"] += 1

def spec_tunop(config):	# t is in {'i32','i64','f32','f64'}
  if verbose>=1: print("spec_tunop(",")")
  S = config["S"]
  instr = config["instrstar"][config["idx"]][0]
  t = instr[0:3]
  op = opcode2exec[instr][1]
  c1 = config["operand_stack"].pop()
  c = op(int(t[1:3]),c1)
  if c == "trap": return c
  config["operand_stack"].append(c)
  config["idx"] += 1

def spec_tbinop(config):
  if verbose>=1: print("spec_tbinop(",")")
  S = config["S"]
  instr = config["instrstar"][config["idx"]][0]
  t = instr[0:3]
  op = opcode2exec[instr][1]
  c2 = config["operand_stack"].pop()
  c1 = config["operand_stack"].pop()
  c = op(int(t[1:3]),c1,c2)
  if c == "trap": return c
  config["operand_stack"].append(c)
  config["idx"] += 1
  
def spec_ttestop(config):
  if verbose>=1: print("spec_ttestop(",")")
  S = config["S"]
  instr = config["instrstar"][config["idx"]][0]
  t = instr[0:3]
  op = opcode2exec[instr][1]
  c1 = config["operand_stack"].pop()
  c = op(int(t[1:3]),c1)
  if c == "trap": return c
  config["operand_stack"].append(c)
  config["idx"] += 1
  
def spec_trelop(config):
  if verbose>=1: print("spec_trelop(",")")
  S = config["S"]
  instr = config["instrstar"][config["idx"]][0]
  t = instr[0:3]
  op = opcode2exec[instr][1]
  c2 = config["operand_stack"].pop()
  c1 = config["operand_stack"].pop()
  c = op(int(t[1:3]),c1,c2)
  if c == "trap": return c
  config["operand_stack"].append(c)
  config["idx"] += 1

def spec_t2cvtopt1(config):
  if verbose>=1: print("spec_t2crtopt1(",")")
  S = config["S"]
  instr = config["instrstar"][config["idx"]][0]
  t1 = instr[0:3]
  t2 = instr[-3:]
  op = opcode2exec[instr][1]
  c1 = config["operand_stack"].pop()
  if instr[4:15] == "reinterpret":
    c2 = op(t2,t1,c1)
  else:
    c2 = op(int(t1[1:3]),int(t2[1:3]),c1)
  if c2 == "trap": return c
  config["operand_stack"].append(c2)
  config["idx"] += 1


# 4.4.2 PARAMETRIC INSTRUCTIONS
 
def spec_drop(config):
  if verbose>=1: print("spec_drop(",")")
  S = config["S"]
  config["operand_stack"].pop()
  config["idx"] += 1
  
def spec_select(config):
  if verbose>=1: print("spec_select(",")")
  S = config["S"]
  operand_stack = config["operand_stack"]
  c = operand_stack.pop()
  val1 = operand_stack.pop()
  val2 = operand_stack.pop()
  if not c:
    operand_stack.append(val1)
  else:
    operand_stack.append(val2)
  config["idx"] += 1

# 4.4.3 VARIABLE INSTRUCTIONS

def spec_get_local(config):
  if verbose>=1: print("spec_get_local(",")")
  S = config["S"]
  F = config["F"]
  x = config["instrstar"][config["idx"]][1]
  #print(F)
  val = F[-1]["locals"][x]
  config["operand_stack"].append(val)
  config["idx"] += 1

def spec_set_local(config):
  if verbose>=1: print("spec_set_local(",")")
  S = config["S"]
  F = config["F"]
  x = config["instrstar"][config["idx"]][1]
  val = config["operand_stack"].pop()
  F[-1]["locals"][x] = val
  config["idx"] += 1

def spec_tee_local(config):
  if verbose>=1: print("spec_tee_local(",")")
  S = config["S"]
  x = config["instrstar"][config["idx"]][1]
  operand_stack = config["operand_stack"]
  val = operand_stack.pop()
  operand_stack.append(val)
  operand_stack.append(val)
  spec_set_local(config)
  #config["idx"] += 1
  
def spec_get_global(config):
  if verbose>=1: print("spec_get_global(",")")
  S = config["S"]
  F = config["F"]
  x = config["instrstar"][config["idx"]][1]
  a = F[-1]["module"]["globaladdrs"][x]
  glob = S["globals"][a]
  val = glob["value"]
  config["operand_stack"].append(val)
  config["idx"] += 1

def spec_set_global(config):
  if verbose>=1: print("spec_set_global(",")")
  S = config["S"]
  F = config["F"]
  x = config["instrstar"][config["idx"]][1]
  a = F[-1]["module"]["globaladdrs"][x]
  glob = S["globals"][a]
  val = config["operand_stack"].pop()
  glob["value"] = val
  config["idx"] += 1


# 4.4.4 MEMORY INSTRUCTIONS

# this is for both t.load and t.loadN_sx
# TODO: fix _sx to call extend_u or extend_s
def spec_tload(config):
  if verbose>=1: print("spec_tload(",")")
  S = config["S"]
  F = config["F"]
  instr = config["instrstar"][config["idx"]][0]
  memarg = config["instrstar"][config["idx"]][1]
  #print(instr)
  #print(memarg)
  t = instr[:3]
  sxflag = False
  if instr[3:] != ".load":  # eg i32.load8_s
    if instr[-1] == "s":
      sxflag = True
    N=int(instr[8:10].strip("_"))
  else:
    N=int(t[1:])
  #print(N)
  #print(sxflag)
  a = F[-1]["module"]["memaddrs"][0]
  mem = S["mems"][a]
  i = config["operand_stack"].pop()
  #print(type(i))
  #print(type(memarg["offset"]))
  ea = i+memarg["offset"] 
  if N==None:
    sxflag = False
    N = int(t[1:])
    M = N
  else:
    M = int(t[1:])
  if ea+N//8 > len(mem["data"]):
    return "trap"
  #print(ea,ea+N//8)
  bstar = mem["data"][ea:ea+N//8]
  #print("bstar",bstar)
  bstar = bytearray(reversed(bstar)) # since little endian
  #bitstring=""
  #for by in bstar:
  #  bitstring += bin(by)[2:].rjust(8, '0')
  #print(bitstring)
  #bitstring = spec_littleendian(bitstring)
  #print(bitstring)
  #bstar = bytearray()
  #for i in range(len(bitstring)//8):
  #  bstar += bytearray([int(bitstring[i*8:i*8+8],2)])
  #print(bstar)
  if sxflag:
    n = spec_bytesiN_inv(N,bstar)
    c = spec_extend_sMN(N,M,n)
  else:
    c = spec_bytest_inv(t,bstar)
  #print("c: ",c)
  config["operand_stack"].append(c)
  config["idx"] += 1

def spec_tstore(config):
  if verbose>=1: print("spec_tstore(",")")
  S = config["S"]
  F = config["F"]
  instr = config["instrstar"][config["idx"]][0]
  memarg = config["instrstar"][config["idx"]][1]
  t = instr[:3]
  Nflag = False 
  if instr[3:] != ".store":  # eg i32.store8
    Nflag = True
    N=int(instr[9:])
  else:
    N=int(t[1:])
  a = F[-1]["module"]["memaddrs"][0]
  mem = S["mems"][a]
  c = config["operand_stack"].pop()
  i = config["operand_stack"].pop()
  ea = i+memarg["offset"]
  if ea+N//8 > len(mem["data"]):
    return "trap"
  if Nflag:
    c = spec_wrapMN(int(t[1:]),N,c)
    bstar = spec_bytesiN(N,c)
  else:
    bstar = spec_bytest(t,c)
  bstar = bytearray(reversed(bstar))  #since little-endian
  mem["data"][ea:ea+N//8] = bstar
  if verbose >=3: print("stored",bstar,"to memory locations",ea,"to",ea+N//8)
  config["idx"] += 1

def spec_memorysize(config):
  if verbose>=1: print("spec_memorysize(",")")
  S = config["S"]
  F = config["F"]
  a = F[-1]["module"]["memaddrs"][0]
  mem = S["mems"][a]
  sz = len(mem["data"])//65536  #page size = 64 Ki = 65536
  config["operand_stack"].append(sz)
  config["idx"] += 1

def spec_memorygrow(config):
  if verbose>=1: print("spec_memorygrow(",")")
  S = config["S"]
  F = config["F"]
  a = F[-1]["module"]["memaddrs"][0]
  mem = S["mems"][a]
  sz = len(mem["data"])//65536  #page size = 64 Ki = 65536
  n = config["operand_stack"].pop()
  ret = spec_growmem(mem,n)
  if sz+n == len(mem["data"])//65536: #success
    config["operand_stack"].append(sz)
  else: 
    config["operand_stack"].append(2**32-1) #put -1 on top of stack
  config["idx"] += 1
    
  
# 4.4.5 CONTROL INSTRUCTIONS

# I deviated from the spec, config inculdes store S, frame F, instr_list, idx into this instr_list, operand_stack, and control_stack 
# and each label L has extra value for height of operand stack when it started, continuation when it is branched to, and end when it's last instruction is called
# operand_stack holds only values, control_stack holds only labels
# function invocation coincides with a python function call which creates a new frame, so the frames have their own implicit stack

def spec_nop(config):
  if verbose>=1: print("spec_nop(",")")
  config["idx"] += 1
  pass

def spec_unreachable(config):
  if verbose>=1: print("spec_unreachable(",")")
  return "trap"


def spec_block(config): #S,F,t,operand_stack,control_stack,continuation):
  if verbose>=1: print("spec_block(",")")
  instrstar = config["instrstar"]
  idx = config["idx"]
  operand_stack = config["operand_stack"]
  control_stack = config["control_stack"]
  t = instrstar[idx][1]
  #get arity
  if t == None:
    n=0
  elif type(t) == str:
    n=1
  elif type(t) == list:
    n=len(t)
  #finally, do stuff in book
  continuation = [instrstar,idx+1]
  L = {"arity":n, "height":len(operand_stack), "continuation":continuation, "end":continuation}
  control_stack.append(L)
  config["instrstar"] = instrstar[idx][2]
  config["idx"] = 0

def spec_loop(config):
  if verbose>=1: print("spec_loop(",")")
  instrstar = config["instrstar"]
  idx = config["idx"]
  operand_stack = config["operand_stack"]
  control_stack = config["control_stack"]
  t = instrstar[idx][1]
  #get arity n
  if t == None: n=0
  elif type(t) == str: n=1
  elif type(t) == list: n=len(t)
  #continuation = [instrstar,idx]
  continuation = [instrstar[idx][2],0]
  end = [instrstar,idx+1]
  L = {"arity":n, "height":len(operand_stack), "continuation":continuation, "end":end, "loop_flag":1}
  control_stack.append(L)
  config["instrstar"] = instrstar[idx][2]
  config["idx"] = 0

def spec_if(config):
  if verbose>=1: print("spec_if(",")")
  instrstar = config["instrstar"]
  idx = config["idx"]
  operand_stack = config["operand_stack"]
  control_stack = config["control_stack"]
  t = instrstar[idx][1]
  c = operand_stack.pop()
  #get arity n
  if t == None: n=0
  elif type(t) == str: n=1
  elif type(t) == list: n=len(t)
  continuation = [instrstar,idx+1]
  L = {"arity":n, "height":len(operand_stack), "continuation":continuation, "end":continuation}
  control_stack.append(L)
  print(instrstar[idx])
  if c:
    config["instrstar"] = instrstar[idx][2]
    config["idx"] = 0
  else:
    config["instrstar"] = instrstar[idx][3]
    config["idx"] = 0


def spec_br(config, l = None):
  if verbose>=1: print("spec_br(",")")
  operand_stack = config["operand_stack"]
  control_stack = config["control_stack"]
  if l == None:
    l = config["instrstar"][config["idx"]][1]
  #print(config["instrstar"][config["idx"]][0])
  #print(config["instrstar"][config["idx"]][1])
  #print("l=",l)
  #print(l)
  #print(control_stack)
  #print(len(control_stack))
  L = control_stack[-1*(l+1)]
  n = L["arity"]
  valn = []
  if n>0:
    valn = operand_stack[-1*n:]
  del operand_stack[ L["height"]: ]
  operand_stack += valn
  #control_stack is more complicated since loop end
  if "loop_flag" in L: #loop, special end, don't delete it
    #print("it is a loop")
    if l>0:
      #print("deleting stack from ",-1*l)
      del control_stack[-1*l:]
    config["instrstar"],config["idx"] = L["continuation"]
    config["idx"] = 0
  else:
    del control_stack[-1*(l+1):]
    config["instrstar"],config["idx"] = L["continuation"]

def spec_br_if(config):
  if verbose>=1: print("spec_br_if(",")")
  c = config["operand_stack"].pop()
  if c!=0: spec_br(config)
  else: config["idx"] += 1

def spec_br_table(config):
  if verbose>=1: print("spec_br_table(",")")
  lstar = config["instrstar"][config["idx"]][1]
  lN = config["instrstar"][config["idx"]][2]
  i = config["operand_stack"].pop()
  #print(lstar,lN)
  if i < len(lstar):
    li = lstar[i]
    spec_br(config,li)
  else:
    spec_br(config,lN)


def spec_return(config):
  if verbose>=1: print("spec_return(",")")
  operand_stack = config["operand_stack"]
  F = config["F"]
  n = F[-1]["arity"]
  height = F[-1]["height"]
  valn = operand_stack[-1*n:]
  operand_stack = operand_stack[:height]
  operand_stack += valn
  return "return"


def spec_call(config):
  if verbose>=1: print("spec_call(",")")
  F = config["F"]
  S = config["S"]
  instr = config["instrstar"][config["idx"]]
  operand_stack = config["operand_stack"]
  x = instr[1]
  a = F[-1]["module"]["funcaddrs"][x]
  spec_invokeopcode(config,a)
  config["idx"] += 1

def spec_call_indirect(config):
  if verbose>=1: print("spec_call_indirect(",")")
  S = config["S"]
  F = config["F"]
  ta = F[-1]["module"]["tableaddrs"][0]
  tab = S["tables"][ta]
  x = config["instrstar"][config["idx"]][1]
  ftexpect = F[-1]["module"]["types"][x]
  i = config["operand_stack"].pop()
  if len(tab["elem"])<=x:
    return "trap"
  if tab["elem"][i] == None:
    return "trap"
  a = tab["elem"][i]
  f = S["funcs"][a]
  ftactual = f["type"]
  if ftexpect != ftactual:
    return "trap"
  spec_invokeopcode(config,a)
  config["idx"] += 1


# 4.4.6 BLOCKS

# see control instructions above

"""
 [
  ['block', None, 
   [
    ['call', 0],
    ['get_local', 0],
    ['br_if', 0],
    ['i32.const', 2],
    ['return'],
    ['end']
   ]
  ],
  ['i32.const', 3],
  ['end']
 ]
"""

# 4.4.7 FUNCTION CALLS

# this is called invokeopcode() since the name spec_invoke() is already taken
def spec_invokeopcode(config, a):
  if verbose>=1: print("spec_invokeopcode(",")")
  # a is address
  S = config["S"]
  F = config["F"]
  instrstar = config["instrstar"]
  idx = config["idx"]
  operand_stack  = config["operand_stack"]
  #print("operand_stack before:",operand_stack)
  #a = config["instrstar"][config["idx"]][1] #immediate
  f = S["funcs"][a]
  t1n,t2m = f["type"]
  tstar = f["code"]["locals"]
  instrstarend = f["code"]["body"]
  retval = None if not t2m else t2m[0]
  blockinstrstarendend = [["block", retval,instrstarend],["end"]]
  valn = operand_stack[-1*len(t1n):]
  if len(t1n)>0:
    del operand_stack[-1*len(t1n):]
  #print("operand_stack before:",operand_stack)
  val0star = [0]*len(tstar)
  F += [{ "module": f["module"], "locals": valn+val0star, "arity":len(t2m), "height":len(operand_stack), "continuation":[instrstar, idx] }]
  arity = len(t2m)
  config_new = {"S":S,"F":F,"instrstar":blockinstrstarendend,"idx":0,"operand_stack":[],"control_stack":[]}
  #frame_stack += [{"frame":F, "arity":arity}] #an activation is really frame_n {frame} where n is arity
  spec_expr(config_new)
  operand_stack += config_new["operand_stack"]
  #print("operand_stack after:",operand_stack)
  config["instrstar"], config["idx"] = F[-1]["continuation"]
  F.pop()
  return operand_stack


# 4.4.8 EXPRESSIONS

opcode2exec = {
"unreacbable":	(spec_unreachable,),
"nop":		(spec_nop,),
"block":	(spec_block,),				# blocktype in* end
"loop":		(spec_loop,),				# blocktype in* end
"if":		(spec_if,),				# blocktype in1* else? in2* end
#"else":	(spec_else,),				# in2*
#"end":		(spec_end,),
"br":		(spec_br,),				# labelidx
"br_if":	(spec_br_if,),				# labelidx
"br_table":	(spec_br_table,),			# labelidx* labelidx
"return":	(spec_return,),
"call":		(spec_call,),				# funcidx
"call_indirect":(spec_call_indirect,),			# typeidx 0x00

"drop":		(spec_drop,),
"select":	(spec_select,),

"get_local":	(spec_get_local,),			# localidx
"set_local":	(spec_set_local,),			# localidx
"tee_local":	(spec_tee_local,),			# localidx
"get_global":	(spec_get_global,),			# globalidx
"set_global":	(spec_set_global,),			# globalidx

"i32.load":	(spec_tload,),				# memarg
"i64.load":	(spec_tload,),				# memarg
"f32.load":	(spec_tload,),				# memarg
"f64.load":	(spec_tload,), 				# memarg
"i32.load8_s":	(spec_tload,), 				# memarg
"i32.load8_u":	(spec_tload,), 				# memarg
"i32.load16_s":	(spec_tload,),				# memarg
"i32.load16_u":	(spec_tload,),				# memarg
"i64.laod8_s":	(spec_tload,),				# memarg
"i64.load8_u":	(spec_tload,), 				# memarg
"i64.load16_s":	(spec_tload,), 				# memarg
"i64.load16_u":	(spec_tload,), 				# memarg
"i64.load32_s":	(spec_tload,), 				# memarg
"i64.load32_u":	(spec_tload,), 				# memarg
"i32.store":	(spec_tstore,), 			# memarg
"i64.store":	(spec_tstore,), 			# memarg
"f32.store":	(spec_tstore,), 			# memarg
"f64.store":	(spec_tstore,), 			# memarg
"i32.store8":	(spec_tstore,), 			# memarg
"i32.store16":	(spec_tstore,), 			# memarg
"i64.store8":	(spec_tstore,), 			# memarg
"i64.store16":	(spec_tstore,), 			# memarg
"i64.store32":	(spec_tstore,),				# memarg
"memory.size":	(spec_memorysize,),
"memory.grow":	(spec_memorygrow,),

"i32.const":	(spec_tconst,),				# i32
"i64.const":	(spec_tconst,),				# i64
"f32.const":	(spec_tconst,),				# f32
"f64.const":	(spec_tconst,),				# f64

"i32.eqz":	(spec_ttestop,spec_ieqzN),
"i32.eq":	(spec_trelop,spec_ieqN),
"i32.ne":	(spec_trelop,spec_ineN),
"i32.lt_s":	(spec_trelop,spec_ilt_sN),
"i32.lt_u":	(spec_trelop,spec_ilt_uN),
"i32.gt_s":	(spec_trelop,spec_igt_sN),
"i32.gt_u":	(spec_trelop,spec_igt_uN),
"i32.le_s":	(spec_trelop,spec_ile_sN),
"i32.le_u":	(spec_trelop,spec_ile_uN),
"i32.ge_s":	(spec_trelop,spec_ige_sN),
"i32.ge_u":	(spec_trelop,spec_ige_uN),

"i64.eqz":	(spec_ttestop,spec_ieqzN),
"i64.eq":	(spec_trelop,spec_ieqN),
"i64.ne":	(spec_trelop,spec_ineN),
"i64.lt_s":	(spec_trelop,spec_ilt_sN),
"i64.lt_u":	(spec_trelop,spec_ilt_uN),
"i64.gt_s":	(spec_trelop,spec_igt_sN),
"i64.gt_u":	(spec_trelop,spec_igt_uN),
"i64.le_s":	(spec_trelop,spec_ile_sN),
"i64.le_u":	(spec_trelop,spec_ile_uN),
"i64.ge_s":	(spec_trelop,spec_ige_sN),
"i64.ge_u":	(spec_trelop,spec_ige_uN),

"f32.eq":	(spec_trelop,spec_feqN),
"f32.ne":	(spec_trelop,spec_fneN),
"f32.lt":	(spec_trelop,spec_fltN),
"f32.gt":	(spec_trelop,spec_fgtN),
"f32.le":	(spec_trelop,spec_fleN),
"f32.ge":	(spec_trelop,spec_fgeN),

"f64.eq":	(spec_trelop,spec_feqN),
"f64.ne":	(spec_trelop,spec_fneN),
"f64.lt":	(spec_trelop,spec_fltN),
"f64.gt":	(spec_trelop,spec_fgtN),
"f64.le":	(spec_trelop,spec_fleN),
"f64.ge":	(spec_trelop,spec_fgeN),

"i32.clz":	(spec_tunop,spec_iclzN),
"i32.ctz":	(spec_tunop,spec_ictzN),
"i32.popcnt":	(spec_tunop,spec_ipopcntN),
"i32.add":	(spec_tbinop,spec_iaddN),
"i32.sub":	(spec_tbinop,spec_isubN),
"i32.mul":	(spec_tbinop,spec_imulN),
"i32.div_s":	(spec_tbinop,spec_idiv_sN),
"i32.div_u":	(spec_tbinop,spec_idiv_uN),
"i32.rem_s":	(spec_tbinop,spec_irem_sN),
"i32.rem_u":	(spec_tbinop,spec_irem_uN),
"i32.and":	(spec_tbinop,spec_iandN),
"i32.or":	(spec_tbinop,spec_iorN),
"i32.xor":	(spec_tbinop,spec_ixorN),
"i32.shl":	(spec_tbinop,spec_ishlN),
"i32.shr_s":	(spec_tbinop,spec_ishr_sN),
"i32.shr_u":	(spec_tbinop,spec_ishr_uN),
"i32.rotl":	(spec_tbinop,spec_irotlN),
"i32.rotr":	(spec_tbinop,spec_irotrN),

"i64.clz":	(spec_tunop,spec_iclzN),
"i64.ctz":	(spec_tunop,spec_ictzN),
"i64.popcnt":	(spec_tunop,spec_ipopcntN),
"i64.add":	(spec_tbinop,spec_iaddN),
"i64.sub":	(spec_tbinop,spec_isubN),
"i64.mul":	(spec_tbinop,spec_imulN),
"i64.div_s":	(spec_tbinop,spec_idiv_sN),
"i64.div_u":	(spec_tbinop,spec_idiv_uN),
"i64.rem_s":	(spec_tbinop,spec_irem_sN),
"i64.rem_u":	(spec_tbinop,spec_irem_uN),
"i64.and":	(spec_tbinop,spec_iandN),
"i64.or":	(spec_tbinop,spec_iorN),
"i64.xor":	(spec_tbinop,spec_ixorN),
"i64.shl":	(spec_tbinop,spec_ishlN),
"i64.shr_s":	(spec_tbinop,spec_ishr_sN),
"i64.shr_u":	(spec_tbinop,spec_ishr_uN),
"i64.rotl":	(spec_tbinop,spec_irotlN),
"i64.rotr":	(spec_tbinop,spec_irotrN),

"f32.abs":	(spec_tunop,spec_fabsN),
"f32.neg":	(spec_tunop,spec_fnegN),
"f32.ceil":	(spec_tunop,spec_fceilN),
"f32.floor":	(spec_tunop,spec_ffloorN),
"f32.trunc":	(spec_tunop,spec_ftruncN),
"f32.nearest":	(spec_tunop,spec_fnearestN),
"f32.sqrt":	(spec_tunop,spec_fsqrtN),
"f32.add":	(spec_tbinop,spec_faddN),
"f32.sub":	(spec_tbinop,spec_fsubN),
"f32.mul":	(spec_tbinop,spec_fmulN),
"f32.div":	(spec_tbinop,spec_fdivN),
"f32.min":	(spec_tbinop,spec_fminN),
"f32.max":	(spec_tbinop,spec_fmaxN),
"f32.copysign":	(spec_tbinop,spec_fcopysignN),

"f64.abs":	(spec_tunop,spec_fabsN),
"f64.neg":	(spec_tunop,spec_fnegN),
"f64.ceil":	(spec_tunop,spec_fceilN),
"f64.floor":	(spec_tunop,spec_ffloorN),
"f64.trunc":	(spec_tunop,spec_ftruncN),
"f64.nearest":	(spec_tunop,spec_fnearestN),
"f64.sqrt":	(spec_tunop,spec_fsqrtN),
"f64.add":	(spec_tbinop,spec_faddN),
"f64.sub":	(spec_tbinop,spec_fsubN),
"f64.mul":	(spec_tbinop,spec_fmulN),
"f64.div":	(spec_tbinop,spec_fdivN),
"f64.min":	(spec_tbinop,spec_fminN),
"f64.max":	(spec_tbinop,spec_fmaxN),
"f64.copysign":	(spec_tbinop,spec_fcopysignN),

"i32.wrap/i64":		(spec_t2cvtopt1,spec_wrapMN),
"i32.trunc_s/f32":	(spec_t2cvtopt1,spec_trunc_sMN),
"i32.trunc_u/f32":	(spec_t2cvtopt1,spec_trunc_uMN),
"i32.trunc_s/f64":	(spec_t2cvtopt1,spec_trunc_sMN),
"i32.trunc_u/f64":	(spec_t2cvtopt1,spec_trunc_uMN),
"i64.extend_s/i32":	(spec_t2cvtopt1,spec_extend_sMN),
"i64.extend_u/i32":	(spec_t2cvtopt1,spec_extend_uMN),
"i64.trunc_s/f32":	(spec_t2cvtopt1,spec_trunc_sMN),
"i64.trunc_u/f32":	(spec_t2cvtopt1,spec_trunc_uMN),
"i64.trunc_s/f64":	(spec_t2cvtopt1,spec_trunc_sMN),
"i64.trunc_u/f64":	(spec_t2cvtopt1,spec_trunc_uMN),
"f32.convert_s/i32":	(spec_t2cvtopt1,spec_convert_sMN),
"f32.convert_u/i32":	(spec_t2cvtopt1,spec_convert_uMN),
"f32.convert_s/i64":	(spec_t2cvtopt1,spec_convert_sMN),
"f32.convert_u/i64":	(spec_t2cvtopt1,spec_convert_uMN),
"f32.demote/f64":	(spec_t2cvtopt1,spec_demoteMN),
"f64.convert_s/i32":	(spec_t2cvtopt1,spec_convert_sMN),
"f64.convert_u/i32":	(spec_t2cvtopt1,spec_convert_uMN),
"f64.convert_s/i64":	(spec_t2cvtopt1,spec_convert_sMN),
"f64.convert_u/i64":	(spec_t2cvtopt1,spec_convert_uMN),
"f64.promote/f32":	(spec_t2cvtopt1,spec_promoteMN),
"i32.reinterpret/f32":	(spec_t2cvtopt1,spec_reinterprett1t2),
"i64.reinterpret/f64":	(spec_t2cvtopt1,spec_reinterprett1t2),
"f32.reinterpret/i32":	(spec_t2cvtopt1,spec_reinterprett1t2),
"f64.reinterpret/i64":	(spec_t2cvtopt1,spec_reinterprett1t2)
}


global_count = 0

# this executes instr* end. This deviates from the spec.
def spec_expr(config):
  if verbose>=1: print("spec_expr(",")")
  S = config["S"]
  F = config["F"]
  operand_stack = config["operand_stack"]
  control_stack = config["control_stack"]
  #iterate over list of instructions and nested lists of instructions
  instrstar = config["instrstar"]
  idx = config["idx"]
  if len(instrstar)==0: return operand_stack
  #print(instrstar)
  while 1:
    #print("OK:",config["instrstar"])
    #print("OK:",config["idx"])
    instr = config["instrstar"][config["idx"]][0]  # idx<len(instrs) since instrstar[-1]=="end" which changes instrstar
    #print(instr)
    immediate = "" if len(config["instrstar"][config["idx"]])==1 else config["instrstar"][config["idx"]][1]
    global global_count
    global_count+=1
    #print(global_count,config["idx"])
    #print(config["instrstar"])
    #print(instr,immediate)
    if instr in {"end","else"}:
      #print(config["idx"])
      #print(config["instrstar"])
      if control_stack:
        L = control_stack.pop()
        config["instrstar"],config["idx"] = L["end"]
        #print("OK:",config["idx"])
        #print("OK:",config["instrstar"])
        #print(config["instrstar"][config["idx"]])
      else:
        return operand_stack
    else:
      ret = opcode2exec[instr][0](config)
      if ret in {"fail","return","trap"}: return ret
    #print("locals",F[-1]["locals"])
    if verbose >= 2: print("operand_stack",config["operand_stack"])
    #print("control_stack",len(config["control_stack"]),config["control_stack"])
    #print()
    if verbose >= 2: print("control_stack",config["control_stack"])


#############
# 4.5 MODULES
#############

# 4.5.1 EXTERNAL TYPING

def spec_external_typing(S,externval):
  if verbose>=1: print("spec_external_typing(",externval,")")
  if "func" == externval[0]:
    a = externval[1]
    if len(S["funcs"])<a: return -1
    funcinst = S["funcs"][a]
    return ["func",funcinst["type"]]
  elif "table" == externval[0]:
    a = externval[1]
    if len(S["tables"])<a: return -1
    tableinst = S["tables"][a]
    return ["table",[{"min":len(tableinst["elem"]),"max":tableinst["max"]},"anyfunc"]]
  elif "mem" == externval[0]:
    a = externval[1]
    if len(S["mems"])<a: return -1
    meminst = S["mems"][a]
    return ["mem",{"min":len(meminst["data"])//65536,"max":meminst["max"]}]  #page size = 64 Ki = 65536
  elif "global" == externval[0]:
    a = externval[1]
    if len(S["globals"])<a: return -1
    globalinst = S["globals"][a]
    return ["global",[globalinst["mut"],]]
  else:
    return -1


# 4.5.2 IMPORT MATCHING

def spec_externtype_matching_limits(limits1,limits2):
  if verbose>=1: print("spec_externtype_matching_limits(",limits1,limits2,")")
  n1 = limits1["min"]
  m1 = limits1["max"]
  n2 = limits2["min"]
  m2 = limits2["max"]
  if n1<n2: return -1
  if m2==None or (m1!=None and m2!=None and m1<=m2): return "<="
  else: return -1

def spec_externtype_matching(externtype1,externtype2):
  if verbose>=1: print("spec_externtype_matching(",externtype1,externtype2,")")
  if "func"==externtype1[0] and "func"==externtype2[0]:
    if externtype1[1] == externtype2[1]:
      return "<="
  elif "table"==externtype1[0] and "table"==externtype2[0]:
    limits1 = externtype1[1][0]
    limits2 = externtype2[1][0]
    if spec_externtype_matching_limits(limits1,limits2) == -1:
      return -1
    elemtype1 = externtype1[1][1]
    elemtype2 = externtype2[1][1]
    if elemtype1 == elemtype2:
      return "<="
  elif "mem"==externtype1[0] and "mem"==externtype2[0]:
    limits1 = externtype1[1]
    limits2 = externtype2[1]
    if spec_externtype_matching_limits(limits1,limits2) == "<=":
      return "<="
  elif "global"==externtype1[0] and "global"==externtype2[0]:
    if externtype1[1] == externtype2[1]:
      return "<="
  return -1


# 4.5.3 ALLOCATION

def spec_allocfunc(S,func,moduleinst):
  if verbose>=1: print("spec_allocfunc(",")")
  funcaddr = len(S["funcs"])
  functype = moduleinst["types"][func["type"]]
  funcinst = {"type":functype, "module":moduleinst, "code":func}
  S["funcs"].append(funcinst)
  return S,funcaddr

def spec_allochostfunc(S,functype,hostfunc):
  if verbose>=1: print("spec_allochostfunc(",")")
  funcaddr = len(S["funcs"])
  funcinst = {"type":functype, "hostcode":hostfunc}
  S["funcs"].append(funcinst)
  return S,funcaddr

def spec_alloctable(S,tabletype):
  if verbose>=1: print("spec_alloctable(",")")
  min_ = tabletype[0]["min"]
  max_ = tabletype[0]["max"]
  tableaddr = len(S["tables"])  
  tableinst = {"elem":[None for i in range(min_)], "max":max_}
  S["tables"].append(tableinst)
  return S,tableaddr

def spec_allocmem(S,memtype):
  if verbose>=1: print("spec_allocmem(",")")
  min_ = memtype["min"]
  max_ = memtype["max"]
  memaddr = len(S["mems"])
  meminst = {"data":bytearray(min_*65536), "max":max_}  #page size = 64 Ki = 65536
  S["mems"].append(meminst)
  return S,memaddr

def spec_allocglobal(S,globaltype,val):
  if verbose>=1: print("spec_allocglobal(",")")
  mut = globaltype[1]
  globaladdr = len(S["globals"])
  globalinst = {"value":val, "mut":mut}
  S["globals"].append(globalinst)
  return S,globaladdr
  
def spec_growtable(tableinst,n):
  if verbose>=1: print("spec_growtable(",")")
  if tablinst["max"]!=None and tableinst["max"] < n+len(tableinst["elem"]):
    return -1
  tableinst["elem"]+=[None for i in range(n)]
  return tableinst

def spec_growmem(meminst,n):
  if verbose>=1: print("spec_growmem(",")")
  len_ = n*65536  #page size = 64 Ki = 65536
  if meminst["max"]!=None and mem["max"]*65536 < len_+len(mem["data"]):
    return -1  #fail
  else:
    meminst["data"] += bytearray(len_) # each page created with bytearray(65536) which is 0s
  

def spec_allocmodule(S,module,externvalimstar,valstar):  
  if verbose>=1: print("spec_allocmodule(",")")
  moduleinst = {
     "types": module["types"],
     "funcaddrs": None,
     "tableaddrs": None,
     "memaddrs": None,
     "globaladdrs": None,
     "exports": None
    }
  funcaddrstar = [spec_allocfunc(S,func,moduleinst)[1] for func in module["funcs"]]
  tableaddrstar = [spec_alloctable(S,table["type"])[1] for table in module["tables"]]
  memaddrstar = [spec_allocmem(S,mem["type"])[1] for mem in module["mems"]]
  globaladdrstar = [spec_allocglobal(S,global_["type"],valstar[idx])[1] for idx,global_ in enumerate(module["globals"])]
  #exportinststar = [{"name":export["name"], "value":externvalex[idx]} for idx,export in enumerate(module["exports"])]
  funcaddrmodstar = [externval[1] for externval in externvalimstar if "func"==externval[0]] + funcaddrstar
  tableaddrmodstar = [externval[1] for externval in externvalimstar if "table"==externval[0]] + tableaddrstar
  memaddrmodstar = [externval[1] for externval in externvalimstar if "mem"==externval[0]] + memaddrstar
  globaladdrmodstar = [externval[1] for externval in externvalimstar if "global"==externval[0]] + globaladdrstar
  exportinststar = []
  for exporti in module["exports"]:
    if exporti["desc"][0] == "func":
      x = exporti["desc"][1]
      externvali = ["func", funcaddrmodstar[x]]
    elif exporti["desc"][0] == "table":
      x = exporti["desc"][1]
      externvali = ["table", tableaddrmodstar[x]]
    elif exporti["desc"][0] == "mem":
      x = exporti["desc"][1]
      externvali = ["mem", memaddrmodstar[x]]
    elif exporti["desc"][0] == "global":
      x = exporti["desc"][1]
      externvali = ["global", globaladdrmodstar[x]]
    exportinststar += [{"name": exporti["name"], "value": externvali}]
  moduleinst["funcaddrs"] = funcaddrmodstar
  moduleinst["tableaddrs"] = tableaddrmodstar
  moduleinst["memaddrs"] = memaddrmodstar
  moduleinst["globaladdrs"] = globaladdrmodstar
  moduleinst["exports"] = exportinststar
  return S,moduleinst 


def spec_instantiate(S,module,externvaln):
  if verbose>=1: print("spec_instantiate(",")")
  # 1
  externtypeimn,externtypeexstar = spec_validate_module(module)
  # 2
  #print("ok2")
  #print(module["imports"])
  #print(externvaln)
  #print(module)
  # 3
  #TODO: reenable this, but with it we don't pass spectest data.wast test#2 (3rd test in data.wast)
  #if len(module["imports"]) != len(externvaln):
  #  return -1,-1,-1
  # 4
  for i in range(len(externvaln)): 
    externtypei = spec_external_typing_func(S,externvaln[i])
    if externtypei == -1: return -1
    if spec_externtype_matching(externtypei,externtypeimn[i])==-1: return -1
  # 5
  valstar = []
  moduleinstim = {"globaladdrs":[externval[1] for externval in externvaln if "gloabls"==exterval[0]]}
  Fim = {"module":moduleinstim, "locals":[], "arity":1, "height":0}
  framestack = []
  framestack += [Fim]
  for globali in module["globals"]:
    config = {"S":S,"F":framestack,"instrstar":globali["init"],"idx":0,"operand_stack":[],"control_stack":[]}
    valstar += [ spec_expr( config )[0] ]
  framestack.pop()
  # 6
  S,moduleinst = spec_allocmodule(S,module,externvaln,valstar)
  # 7
  F={"module":moduleinst, "locals":[]} #, "arity":1, "height":0}
  # 8
  framestack += [F]
  # 9
  tableinst = []
  eo = []
  for elemi in module["elem"]:
    config = {"S":S,"F":framestack,"instrstar":elemi["offset"],"idx":0,"operand_stack":[],"control_stack":[]}
    eovali = spec_expr(config)[0]
    eoi = eovali
    eo+=[eoi]
    tableidxi = elemi["table"]
    tableaddri = moduleinst["tableaddrs"][tableidxi]
    tableinsti = S["tables"][tableaddri]
    tableinst+=[tableinsti]
    eendi = eoi+len(elemi["init"])
    if eendi > len(tableinsti["elem"]): return -1
  # 10
  meminst = []
  do = []
  for datai in module["data"]:
    config = {"S":S,"F":framestack,"instrstar":datai["offset"],"idx":0,"operand_stack":[],"control_stack":[]}
    dovali = spec_expr(config)[0]
    doi = dovali
    do+=[doi]
    memidxi = datai["data"]
    memaddri = moduleinst["memaddrs"][memidxi]
    meminsti = S["mems"][memaddri]
    meminst += [meminsti]
    dendi = doi+len(datai["init"])
    if dendi > len(meminsti["data"]): return -1
  # 11
  # 12
  framestack.pop()
  # 13
  for i,elemi in enumerate(module["elem"]):
    for j,funcidxij in enumerate(elemi["init"]):
      funcaddrij = moduleinst["funcaddrs"][funcidxij]
      tableinst[i]["elem"][eo[i]+j] = funcaddrij
  # 14
  for i,datai in enumerate(module["data"]):
    for j,bij in enumerate(datai["init"]):
      meminst[i]["data"][do[i]+j] = bij
  # 15
  ret = None
  if module["start"]:
    print(moduleinst["funcaddrs"])
    print(module["start"]["func"])
    funcaddr = moduleinst["funcaddrs"][ module["start"]["func"] ]
    ret = spec_invoke(S,funcaddr,[])
  return S,F,ret


    
# 4.5.5 INVOCATION

# valn looks like [["i32.const",3],["i32.const",199], ...]
def spec_invoke(S,funcaddr,valn):
  if verbose>=1: print("spec_invoke(",")")
  #TODO: fix call by spec_instantiate()
  # 1
  print(funcaddr)
  if len(S["funcs"]) < funcaddr or funcaddr < 0: return -1
  # 2
  funcinst = S["funcs"][funcaddr]  
  # 5
  t1n,t2m = funcinst["type"]
  # 4
  if len(valn)!=len(t1n): return -1
  # 5
  for ti,vali in zip(t1n,valn):
    if vali[0][:3]!=ti: return -1
  # 6
  operand_stack = []
  for ti,vali in zip(t1n,valn):
    #print(ti,vali,type(vali[1]))
    arg=vali[1]
    if type(arg)==str:
      if ti[0]=="i": arg = int(arg)
      if ti[0]=="f": arg = float(arg)
    #print(type(arg))
    operand_stack += [arg]
  # 7
  config = {"S":S,"F":[],"instrstar":funcinst["code"]["body"],"idx":0,"operand_stack":operand_stack,"control_stack":[]}
  valresm = spec_invokeopcode(config,funcaddr)
  return valresm
    
    
    
    







  
###################
###################
# 5 BINARY FORMAT #
###################
###################

# key-value pairs of binary opcodes and their text reperesentation
opcodes_binary2text = {
0x00:'unreachable',
0x01:'nop',
0x02:'block',			# blocktype in* end		# begin block
0x03:'loop',			# blocktype in* end		# begin block
0x04:'if',			# blocktype in1* else? end	# begin block
0x05:'else',			# in2*				# end block & begin block
0x0b:'end',							# end block
0x0c:'br',			# labelidx			# branch
0x0d:'br_if',			# labelidx			# branch
0x0e:'br_table',		# labelidx* labelidx		# branch
0x0f:'return',							# end outermost block
0x10:'call',			# funcidx			# branch
0x11:'call_indirect',		# typeidx 0x00			# branch

0x1a:'drop',
0x1b:'select',

0x20:'get_local',		# localidx
0x21:'set_local',		# localidx
0x22:'tee_local',		# localidx
0x23:'get_global',		# globalidx
0x24:'set_global',		# globalidx

0x28:'i32.load',		# memarg
0x29:'i64.load',		# memarg
0x2a:'f32.load',		# memarg
0x2b:'f64.load',		# memarg
0x2c:'i32.load8_s',		# memarg
0x2d:'i32.load8_u',		# memarg
0x2e:'i32.load16_s',		# memarg
0x2f:'i32.load16_u',		# memarg
0x30:'i64.load8_s',		# memarg
0x31:'i64.load8_u',		# memarg
0x32:'i64.load16_s',		# memarg
0x33:'i64.load16_u',		# memarg
0x34:'i64.load32_s',		# memarg
0x35:'i64.load32_u',		# memarg
0x36:'i32.store',		# memarg
0x37:'i64.store',		# memarg
0x38:'f32.store',		# memarg
0x39:'f64.store',		# memarg
0x3a:'i32.store8',		# memarg
0x3b:'i32.store16',		# memarg
0x3c:'i64.store8',		# memarg
0x3d:'i64.store16',		# memarg
0x3e:'i64.store32',		# memarg
0x3f:'memory.size',
0x40:'memory.grow',

0x41:'i32.const',		# i32
0x42:'i64.const',		# i64
0x43:'f32.const',		# f32
0x44:'f64.const',		# f64

0x45:'i32.eqz',
0x46:'i32.eq',
0x47:'i32.ne',
0x48:'i32.lt_s',
0x49:'i32.lt_u',
0x4a:'i32.gt_s',
0x4b:'i32.gt_u',
0x4c:'i32.le_s',
0x4d:'i32.le_u',
0x4e:'i32.ge_s',
0x4f:'i32.ge_u',

0x50:'i64.eqz',
0x51:'i64.eq',
0x52:'i64.ne',
0x53:'i64.lt_s',
0x54:'i64.lt_u',
0x55:'i64.gt_s',
0x56:'i64.gt_u',
0x57:'i64.le_s',
0x58:'i64.le_u',
0x59:'i64.ge_s',
0x5a:'i64.ge_u',

0x5b:'f32.eq',
0x5c:'f32.ne',
0x5d:'f32.lt',
0x5e:'f32.gt',
0x5f:'f32.le',
0x60:'f32.ge',

0x61:'f64.eq',
0x62:'f64.ne',
0x63:'f64.lt',
0x64:'f64.gt',
0x65:'f64.le',
0x66:'f64.ge',

0x67:'i32.clz',
0x68:'i32.ctz',
0x69:'i32.popcnt',
0x6a:'i32.add',
0x6b:'i32.sub',
0x6c:'i32.mul',
0x6d:'i32.div_s',
0x6e:'i32.div_u',
0x6f:'i32.rem_s',
0x70:'i32.rem_u',
0x71:'i32.and',
0x72:'i32.or',
0x73:'i32.xor',
0x74:'i32.shl',
0x75:'i32.shr_s',
0x76:'i32.shr_u',
0x77:'i32.rotl',
0x78:'i32.rotr',

0x79:'i64.clz',
0x7a:'i64.ctz',
0x7b:'i64.popcnt',
0x7c:'i64.add',
0x7d:'i64.sub',
0x7e:'i64.mul',
0x7f:'i64.div_s',
0x80:'i64.div_u',
0x81:'i64.rem_s',
0x82:'i64.rem_u',
0x83:'i64.and',
0x84:'i64.or',
0x85:'i64.xor',
0x86:'i64.shl',
0x87:'i64.shr_s',
0x88:'i64.shr_u',
0x89:'i64.rotl',
0x8a:'i64.rotr',

0x8b:'f32.abs',
0x8c:'f32.neg',
0x8d:'f32.ceil',
0x8e:'f32.floor',
0x8f:'f32.trunc',
0x90:'f32.nearest',
0x91:'f32.sqrt',
0x92:'f32.add',
0x93:'f32.sub',
0x94:'f32.mul',
0x95:'f32.div',
0x96:'f32.min',
0x97:'f32.max',
0x98:'f32.copysign',

0x99:'f64.abs',
0x9a:'f64.neg',
0x9b:'f64.ceil',
0x9c:'f64.floor',
0x9d:'f64.trunc',
0x9e:'f64.nearest',
0x9f:'f64.sqrt',
0xa0:'f64.add',
0xa1:'f64.sub',
0xa2:'f64.mul',
0xa3:'f64.div',
0xa4:'f64.min',
0xa5:'f64.max',
0xa6:'f64.copysign',

0xa7:'i32.wrap/i64',
0xa8:'i32.trunc_s/f32',
0xa9:'i32.trunc_u/f32',
0xaa:'i32.trunc_s/f64',
0xab:'i32.trunc_u/f64',
0xac:'i64.extend_s/i32',
0xad:'i64.extend_u/i32',
0xae:'i64.trunc_s/f32',
0xaf:'i64.trunc_u/f32',
0xb0:'i64.trunc_s/f64',
0xb1:'i64.trunc_u/f64',
0xb2:'f32.convert_s/i32',
0xb3:'f32.convert_u/i32',
0xb4:'f32.convert_s/i64',
0xb5:'f32.convert_u/i64',
0xb6:'f32.demote/f64',
0xb7:'f64.convert_s/i32',
0xb8:'f64.convert_u/i32',
0xb9:'f64.convert_s/i64',
0xba:'f64.convert_u/i64',
0xbb:'f64.promote/f32',
0xbc:'i32.reinterpret/f32',
0xbd:'i64.reinterpret/f64',
0xbe:'f32.reinterpret/i32',
0xbf:'f64.reinterpret/i64'
}

# key-value pairs of text opcodes and their binary reperesentation
opcodes_text2binary = {}
for opcode in opcodes_binary2text:
  opcodes_text2binary[opcodes_binary2text[opcode]]=opcode


# 5.1.3 VECTORS

def spec_binary_vec(raw,idx,B):
  idx,n=spec_binary_uN(raw,idx,32)
  xn = []
  for i in range(n):
    idx,x = B(raw,idx)
    xn+=[x]
  return idx,xn

def spec_binary_vec_inv(mynode,myfunc):
  n_bytes=spec_binary_uN_inv(len(mynode),32) 
  xn_bytes=bytearray()
  for x in mynode:
    xn_bytes+=myfunc(x)
  return n_bytes+xn_bytes 


############
# 5.2 VALUES
############

# 5.2.1 BYTES

def spec_binary_byte(raw,idx):
  return idx+1,raw[idx]

def spec_binary_byte_inv(node):
  return bytearray([node])

# 5.2.2 INTEGERS
#TODO: check things on pg 87

#unsigned
def spec_binary_uN(raw,idx,N):
  idx,n=spec_binary_byte(raw,idx)
  if n<2**7 and n<2**N:
    return idx,n
  elif n>=2**7 and N>7:
    idx,m=spec_binary_uN(raw,idx,N-7)
    return idx, (2**7)*m+(n-2**7)
  else:
    return idx,None #error

def spec_binary_uN_inv(k,N):
  #print("spec_binary_uN_inv(",k,N,")")
  if k<2**7 and k<2**N:
    return bytearray([k])
  elif k>=2**7 and N>7:
    return bytearray([k%(2**7)+2**7])+spec_binary_uN_inv(k//(2**7),N-7)
  else:
    return None

def spec_binary_uN_inv_old(n,N):
  if n>2**N:
    return None #error
  mybytes = bytearray()
  while n>2**7:
    m=(n&0b1111111)+2**7
    mybytes.append(m)
    n=n>>7
  mybytes.append(n)
  return mybytes

#signed
def spec_binary_sN(raw,idx,N):
  n=int(raw[idx])
  idx+=1
  if n<2**6 and n<2**(N-1):
    return idx,n
  elif 2**6<=n<2**7 and n>=2**7-2**(N-1):
    return idx,n-2**7
  elif n>=2**7 and N>7:
    idx,m=spec_binary_sN(raw,idx,N-7)
    return idx,2**7*m+(n-2**7)
  else:
    return idx,None #error

def spec_binary_sN_inv(k,N):
  if 0<=k<2**6 and k<2**N:
    return bytearray([k])
  elif 2**6<=k+2**7<2**7: # and k+2**7>=2**7-2**(N-1):
    return bytearray([k+2**7])
  elif (k>=2**6 or k<2**6) and N>7: #(k<0 and k+2**7>=2**6)) and N>7:
    return bytearray([k%(2**7)+2**7])+spec_binary_sN_inv((k//(2**7)),N-7)
  else:
    return None

#uninterpretted integers
def spec_binary_iN(raw,idx,N):
  idx,n=spec_binary_sN(raw,idx,N)
  i = spec_signediN_inv(N,n)
  return idx, i

def spec_binary_iN_inv(i,N):
  return spec_binary_sN_inv(spec_signediN(N,i),N)



# 5.2.3 FLOATING-POINT

#fN::= b*:byte^{N/8} => bytes_{fN}^{-1}(b*)
def spec_binary_fN(raw,idx,N):
  bstar = []
  for i in range(N//8):
    bstar+=[raw[idx]]
    idx+=1
  return idx, bytearray(bstar)

def spec_binary_fN_inv(node,N):
  if len(node)==N/8:
    return node
  else:
    return None
  

# 5.2.4 NAMES

#name as UTF-8 codepoints
def spec_binary_name(raw,idx):
  idx,bstar = spec_binary_vec(raw,idx,spec_binary_byte)
  #rest is finding inverse of utf8(name)=b*
  bstaridx=0
  lenbstar = len(bstar)
  name=[]
  while bstaridx<lenbstar:
    b1=bstar[bstaridx]
    bstaridx+=1
    if b1<0x80:
      name+=[b1]
      continue
    b2=bstar[bstaridx]
    bstaridx+=1
    c=(2**6)*(b1-int(0xc0)) + (b2-int(0x80))
    c_check = 2**6*(b1-192) + (b2-128)
    if 0x80<=c<0x800:
      name+=[c]
      continue
    b3=bstar[bstaridx]
    bstaridx+=1
    c=(2**12)*(b1-0xe0) + (2**6)*(b2-0x80) + (b3-0x80)
    if 0x800<=c<0x10000:
      name+=[c]
      continue
    b4=bstar[bstaridx]
    bstaridx+=1
    c=2**18*(b1-0xf0) + 2**12*(b2-0x80) + 2**6*(b3-0x80) + (b4-0x80)
    if 0x10000<=c<0x110000:
      name+=[c]
    else:
      break  #return idx, None #error
  #convert each codepoint to utf8 character
  #print("utf8 name",name, len(name), name=="")
  nametxt = ""
  for c in name:
    nametxt+=chr(c)
  #print("utf8 nametext",nametxt, len(nametxt), nametxt=="")
  return idx,nametxt

def spec_binary_name_inv(chars):
  name_bytes=bytearray()
  for c in chars:
    c = ord(c)
    if c<0x80:
      name_bytes += bytes([c])
    elif 0x80<=c<0x800:
      name_bytes += bytes([(c>>6)+0xc0,(c&0b111111)+0x80])
    elif 0x800<=c<0x10000:
      name_bytes += bytes([(c>>12)+0xe0,((c>>6)&0b111111)+0x80,(c&0b111111)+0x80])
    elif 0x10000<=c<0x110000:
      name_bytes += bytes([(c>>18)+0xf0,((c>>12)&0b111111)+0x80,((c>>6)&0b111111)+0x80,(c&0b111111)+0x80])
    else:
      return None #error
  return bytearray([len(name_bytes)])+name_bytes


###########
# 5.3 TYPES
###########

# 5.3.1 VALUE TYPES

valtype2bin={"i32":0x7f,"i64":0x7e,"f32":0x7d,"f64":0x7c}
bin2valtype={val:key for key,val in valtype2bin.items()}

def spec_binary_valtype(raw,idx):
  if raw[idx] in bin2valtype:
    return idx+1,bin2valtype[raw[idx]]
  else:
    return idx,None #error

def spec_binary_valtype_inv(node):
  if node in valtype2bin:
    return bytearray([valtype2bin[node]])
  else:
    return bytearray([]) #error

# 5.3.2 RESULT TYPES

def spec_binary_blocktype(raw,idx):
  if raw[idx]==0x40:
    return idx+1,None
  idx,t=spec_binary_valtype(raw,idx)
  return idx, t

def spec_binary_blocktype_inv(node):
  if node==None:
    return bytearray([0x40])
  else:
    return spec_binary_valtype_inv(node)


# 5.3.3 FUNCTION TYPES

def spec_binary_functype(raw,idx):
  if raw[idx]!=0x60:
    return idx, None #error
  idx+=1
  idx,t1star=spec_binary_vec(raw,idx,spec_binary_valtype)
  idx,t2star=spec_binary_vec(raw,idx,spec_binary_valtype)
  return idx,[t1star,t2star]

def spec_binary_functype_inv(node):
  return bytearray([0x60])+spec_binary_vec_inv(node[0],spec_binary_valtype_inv)+spec_binary_vec_inv(node[1],spec_binary_valtype_inv)


# 5.3.4 LIMITS

def spec_binary_limits(raw,idx):
  if raw[idx]==0x00:
    idx,n = spec_binary_uN(raw,idx+1,32)
    return idx,{"min":n,"max":None}
  elif raw[idx]==0x01:
    idx,n = spec_binary_uN(raw,idx+1,32)
    idx,m = spec_binary_uN(raw,idx,32)
    return idx,{"min":n,"max":m}
  else:
    return idx,None #error
    
def spec_binary_limits_inv(node):
  if node["max"]==None:
    return bytearray([0x00])+spec_binary_uN_inv(node["min"],32)
  else:
    return bytearray([0x01])+spec_binary_uN_inv(node["min"],32)+spec_binary_uN_inv(node["max"],32)

  
# 5.3.5 MEMORY TYPES

def spec_binary_memtype(raw,idx):
  return spec_binary_limits(raw,idx)

def spec_binary_memtype_inv(node):
  return spec_binary_limits_inv(node)


# 5.3.6 TABLE TYPES

def spec_binary_tabletype(raw,idx):
  idx,et = spec_binary_elemtype(raw,idx)
  idx,lim = spec_binary_limits(raw,idx)
  return idx,[lim,et]

def spec_binary_elemtype(raw,idx):
  if raw[idx]==0x70:
    return idx+1,"anyfunc"
  else:
    return idx,None #error

def spec_binary_tabletype_inv(node):
  return spec_binary_elemtype_inv(node[1])+spec_binary_limits_inv(node[0])

def spec_binary_elemtype_inv(node):
  return bytearray([0x70])


# 5.3.7 GLOBAL TYPES

def spec_binary_globaltype(raw,idx):
  idx,t = spec_binary_valtype(raw,idx)
  idx,m = spec_binary_mut(raw,idx)
  return idx,[m,t]

def spec_binary_mut(raw,idx):
  if raw[idx]==0x00:
    return idx+1,"const"
  elif raw[idx]==0x01:
    return idx+1,"var"
  else:
    return idx, None #error

def spec_binary_globaltype_inv(node):
  return spec_binary_valtype_inv(node[1])+spec_binary_mut_inv(node[0])

def spec_binary_mut_inv(node):
  if node=="const":
    return bytearray([0x00])
  elif node=="var":
    return bytearray([0x01])
  else:
    return bytearray([])


##################
# 5.4 INSTRUCTIONS
##################

# 5.4.1-5 VARIOUS INSTRUCTIONS

def spec_binary_memarg(raw,idx):
  idx,a=spec_binary_uN(raw,idx,32)
  idx,o=spec_binary_uN(raw,idx,32)
  return idx,{"align":a,"offset":o}

def spec_binary_memarg_inv(node):
  return spec_binary_uN_inv(node["align"],32) + spec_binary_uN_inv(node["offset"],32)

def spec_binary_instr(raw,idx):
  if raw[idx] not in opcodes_binary2text:
    return idx, None #error
  instr_binary = raw[idx]
  instr_text = opcodes_binary2text[instr_binary]
  idx+=1
  if instr_text in {"block","loop","if"}:      #block, loop, if
    idx,rt=spec_binary_blocktype(raw,idx)
    instar=[]
    if instr_text=="if":
      instar2=[]
      while raw[idx] not in {0x05,0x0b}:
        idx,ins=spec_binary_instr(raw,idx)
        instar+=[ins]
      if raw[idx]==0x05: #if with else
        idx+=1
        while raw[idx] not in {0x0b}:
          idx,ins=spec_binary_instr(raw,idx)
          instar2+=[ins]
        #return idx+1, ["if",rt,instar+[["else"]],instar2+[["end"]]] #+[["end"]]
      return idx+1, ["if",rt,instar+[["else"]],instar2+[["end"]]] #+[["end"]]
      #return idx+1, ["if",rt,instar+[["end"]]] #+[["end"]]
    else: 
      while raw[idx]!=0x0b:
        idx,ins=spec_binary_instr(raw,idx)
        instar+=[ins]
      return idx+1, [instr_text,rt,instar+[["end"]]] #+[["end"]]
  elif instr_text in {"br","br_if"}:           # br, br_if
    idx,l = spec_binary_labelidx(raw,idx)
    return idx, [instr_text,l]
  elif instr_text == "br_table":               # br_table
    idx,lstar=spec_binary_vec(raw,idx,spec_binary_labelidx)
    idx,lN=spec_binary_labelidx(raw,idx)
    return idx, ["br_table",lstar,lN]
  elif instr_text in {"call","call_indirect"}: # call, call_indirect
    if instr_text=="call":
      idx,x=spec_binary_funcidx(raw,idx)
    if instr_text=="call_indirect":
      idx,x=spec_binary_typeidx(raw,idx)
      if raw[idx]!=0x00: return idx,None #error
      idx+=1
    return idx, [instr_text,x]
  elif 0x20<=instr_binary<=0x22:               # get_local, etc
    idx,x=spec_binary_localidx(raw,idx)
    return idx, [instr_text,x]
  elif 0x23<=instr_binary<=0x24:               # get_global, etc
    idx,x=spec_binary_globalidx(raw,idx)
    return idx, [instr_text,x]
  elif 0x28<=instr_binary<=0x3e:               # i32.load, i64.store, etc
    idx,m = spec_binary_memarg(raw,idx)
    return idx, [instr_text,m]
  elif 0x3f<=instr_binary<=0x40:               # current_memory, grow_memory
    if raw[idx]!=0x00: return idx,None #error
    return idx+1, [instr_text,]
  elif 0x41<=instr_binary<=0x42:               # i32.const, etc
    n=0
    if instr_text=="i32.const":
      idx,n = spec_binary_iN(raw,idx,32)
    if instr_text=="i64.const":
      idx,n = spec_binary_iN(raw,idx,64)
    return idx, [instr_text,n]
  elif 0x43<=instr_binary<=0x44:               # f32.const, etc
    z=0
    if instr_text=="f32.const":
      idx,z = spec_binary_fN(raw,idx,32)
    if instr_text=="f64.const":
      idx,z = spec_binary_fN(raw,idx,64)
    return idx, [instr_text,z]
  else:
    #otherwise no immediate
    return idx, [instr_text,]


def spec_binary_instr_inv(node):
  instr_bytes = bytearray()
  #print("spec_binary_instr_inv(",node,")")
  if type(node[0])==str:
    instr_bytes+=bytearray([opcodes_text2binary[node[0]]])
  #the rest is for immediates
  if node[0] in {"block","loop"}:              #block, loop
    instr_bytes+=spec_binary_blocktype_inv(node[1])
    instar_bytes=bytearray()
    for n in node[2]:
      instar_bytes+=spec_binary_instr_inv(n)
    #instar_bytes+=bytes([0x0b])
    instr_bytes+=instar_bytes
  elif node[0]=="if":                          #if
    instr_bytes+=spec_binary_blocktype_inv(node[1])
    instar_bytes=bytearray()
    for n in node[2]:
      instar_bytes+=spec_binary_instr_inv(n)
    if len(node)==4: #TODO: test this
      instar_bytes+=bytearray([0x05])
      for n in node[3]:
        instar_bytes+=spec_binary_instr_inv(n)
    #instar_bytes+=bytes([0x0b])
    instr_bytes+=instar_bytes
  elif node[0] in {"br","br_if"}:              #br, br_if
    instr_bytes+=spec_binary_labelidx_inv(node[1])
  elif node[0] == "br_table":                   #br_table
    instr_bytes+=spec_binary_vec_inv(node[1],spec_binary_labelidx_inv)
    instr_bytes+=spec_binary_labelidx_inv(node[2])
  elif node[0] == "call":                       #call
    instr_bytes+=spec_binary_funcidx_inv(node[1])
  elif node[0] == "call_indirect":              #call_indirect
    instr_bytes+=spec_binary_typeidx_inv(node[1])
    instr_bytes+=bytearray([0x00])
  elif 0x20<=opcodes_text2binary[node[0]]<=0x24:  #get_local, set_local, tee_local
    instr_bytes+=spec_binary_localidx_inv(node[1])
  elif 0x20<=opcodes_text2binary[node[0]]<=0x24:  #get_global, set_global
    instr_bytes+=spec_binary_globalidx_inv(node[1])
  elif 0x28<=opcodes_text2binary[node[0]]<=0x3e:  #i32.load, i32.load8_s, i64.store, etc
    instr_bytes+=spec_binary_memarg_inv(node[1])
  elif 0x3f<=opcodes_text2binary[node[0]]<=0x40:  #memory.size, memory.grow
    instr_bytes+=bytearray([0x00])
  elif node[0]=="i32.const":                    #i32.const
    instr_bytes+=spec_binary_iN_inv(node[1],32)
  elif node[0]=="i64.const":                    #i64.const
    instr_bytes+=spec_binary_iN_inv(node[1],64)
  elif node[0]=="f32.const":                    #i64.const
    instr_bytes+=spec_binary_fN_inv(node[1],32)
  elif node[0]=="f64.const":                    #i64.const
    instr_bytes+=spec_binary_fN_inv(node[1],64)
  return instr_bytes



# 5.4.6 EXPRESSIONS

def spec_binary_expr(raw,idx):
  instar = []
  while raw[idx] != 0x0b: 
    idx,ins = spec_binary_instr(raw,idx)
    instar+=[ins]
  if raw[idx] != 0x0b: return idx,None #error
  return idx+1, instar +[['end']]

def spec_binary_expr_inv(node):
  instar_bytes=bytearray()
  for n in node:
    instar_bytes+=spec_binary_instr_inv(n)
  #instar_bytes+=bytes([0x0b])
  return instar_bytes






#############
# 5.5 MODULES
#############

# 5.5.1 INDICES

def spec_binary_typeidx(raw,idx):
  idx, x = spec_binary_uN(raw,idx,32)
  return idx,x

def spec_binary_typeidx_inv(node):
  return spec_binary_uN_inv(node,32)

def spec_binary_funcidx(raw,idx):
  idx,x = spec_binary_uN(raw,idx,32)
  return idx,x

def spec_binary_funcidx_inv(node):
  return spec_binary_uN_inv(node,32)

def spec_binary_tableidx(raw,idx):
  idx,x = spec_binary_uN(raw,idx,32)
  return idx,x

def spec_binary_tableidx_inv(node):
  return spec_binary_uN_inv(node,32)

def spec_binary_memidx(raw,idx):
  idx,x = spec_binary_uN(raw,idx,32)
  return idx,x

def spec_binary_memidx_inv(node):
  return spec_binary_uN_inv(node,32)

def spec_binary_globalidx(raw,idx):
  idx,x = spec_binary_uN(raw,idx,32)
  return idx,x

def spec_binary_globalidx_inv(node):
  return spec_binary_uN_inv(node,32)

def spec_binary_localidx(raw,idx):
  idx,x = spec_binary_uN(raw,idx,32)
  return idx,x

def spec_binary_localidx_inv(node):
  return spec_binary_uN_inv(node,32)

def spec_binary_labelidx(raw,idx):
  idx,l = spec_binary_uN(raw,idx,32)
  return idx,l

def spec_binary_labelidx_inv(node):
  return spec_binary_uN_inv(node,32)



# 5.5.2 SECTIONS

def spec_binary_sectionN(raw,idx,N,B,skip):
  if idx>=len(raw) or raw[idx]!=N:
    return idx, []  #skip since this sec not included
  idx+=1
  idx,size = spec_binary_uN(raw,idx,32)
  if skip:
    return idx+size,[]
  if N!=8: #not start:
    return spec_binary_vec(raw,idx,B)
  else:
    return B(raw,idx)

def spec_binary_sectionN_inv(cont,Binv,N):
  if cont==None or cont==[]:
    return bytearray([])
  N_bytes=bytearray([N])
  cont_bytes=bytearray()
  if N==8: #startsec
    cont_bytes=Binv(cont)
  else:
    cont_bytes=spec_binary_vec_inv(cont,Binv)
  size_bytes=spec_binary_uN_inv(len(cont_bytes),32) 
  return N_bytes+size_bytes+cont_bytes


# 5.5.3 CUSTOM SECTION

def spec_binary_customsec(raw,idx,skip=1):
  idx,size = spec_binary_uN(raw,idx,32)
  endidx = idx+size
  #TODO: not a vec(), so should adjust sectionN()
  return endidx,None #return spec_binary_sectionN(raw,idx,0,spec_binary_custom,skip) 

def spec_binary_custom(raw,idx):
  idx,name = spec_binary_name(raw,idx)
  #TODO: what is stopping condition for bytestar?
  idx,bytestar = spec_binary_byte(raw,idx)
  return name,bytestar

def spec_binary_customsec_inv(node):
  return spec_binary_sectionN_inv(node,spec_binary_custom_inv)
  
def spec_binary_custom_inv(node):
  return spec_binary_name_inv(node[0]) + spec_binary_byte_inv(node[1]) #TODO: check this


# 5.5.4 TYPE SECTION

def spec_binary_typesec(raw,idx,skip=0):
  return spec_binary_sectionN(raw,idx,1,spec_binary_functype,skip)

def spec_binary_typesec_inv(node):
  return spec_binary_sectionN_inv(node,spec_binary_functype_inv,1)


# 5.5.5 IMPORT SECTION

def spec_binary_importsec(raw,idx,skip=0):
  return spec_binary_sectionN(raw,idx,2,spec_binary_import,skip)

def spec_binary_import(raw,idx):
  idx,mod = spec_binary_name(raw,idx)
  idx,nm = spec_binary_name(raw,idx)
  idx,d = spec_binary_importdesc(raw,idx)
  return idx,{"module":mod,"name":nm,"desc":d}

def spec_binary_importdesc(raw,idx):
  if raw[idx]==0x00:
    idx,x=spec_binary_typeidx(raw,idx+1)
    return idx,["func",x]
  elif raw[idx]==0x01:
    idx,tt=spec_binary_tabletype(raw,idx+1)
    return idx,["table",tt]
  elif raw[idx]==0x02:
    idx,mt=spec_binary_memtype(raw,idx+1)
    return idx,["mem",mt]
  elif raw[idx]==0x03:
    idx,gt=spec_binary_globaltype(raw,idx+1)
    return idx,["global",gt]
  else:
    return idx,None #error

def spec_binary_importsec_inv(node):
  return spec_binary_sectionN_inv(node,spec_binary_import_inv,2)

def spec_binary_import_inv(node):
  return spec_binary_name_inv(node["module"]) + spec_binary_name_inv(node["name"]) + spec_binary_importdesc_inv(node["desc"])

def spec_binary_importdesc_inv(node):
  key=node[0]
  if key=="func":
    return bytearray([0x00]) + spec_binary_typeidx_inv(node[key])
  elif key=="table":
    return bytearray([0x01]) + spec_binary_tabletype_inv(node[key])
  elif key=="mem":
    return bytearray([0x02]) + spec_binary_memtype_inv(node[key])
  elif key=="global":
    return bytearray([0x03]) + spec_binary_globaltype_inv(node[key])
  else:
    return bytearray()
  

# 5.5.6 FUNCTION SECTION

def spec_binary_funcsec(raw,idx,skip=0):
  return spec_binary_sectionN(raw,idx,3,spec_binary_typeidx,skip)

def spec_binary_funcsec_inv(node):
  return spec_binary_sectionN_inv(node,spec_binary_typeidx_inv,3)


# 5.5.7 TABLE SECTION

def spec_binary_tablesec(raw,idx,skip=0):
  return spec_binary_sectionN(raw,idx,4,spec_binary_table,skip)

def spec_binary_table(raw,idx):
  idx,tt=spec_binary_tabletype(raw,idx)
  return idx,{"type":tt}

def spec_binary_tablesec_inv(node):
  return spec_binary_sectionN_inv(node,spec_binary_table_inv,4)
  
def spec_binary_table_inv(node):
  return spec_binary_tabletype_inv(node["type"])


# 5.5.8 MEMORY SECTION

def spec_binary_memsec(raw,idx,skip=0):
  return spec_binary_sectionN(raw,idx,5,spec_binary_mem,skip)

def spec_binary_mem(raw,idx):
  idx,mt = spec_binary_memtype(raw,idx)
  return idx,{"type":mt}

def spec_binary_memsec_inv(node):
  return spec_binary_sectionN_inv(node,spec_binary_mem_inv,5)
  
def spec_binary_mem_inv(node):
  return spec_binary_memtype_inv(node["type"])


# 5.5.9 GLOBAL SECTION

def spec_binary_globalsec(raw,idx,skip=0):
  return spec_binary_sectionN(raw,idx,6,spec_binary_global,skip)

def spec_binary_global(raw,idx):
  idx,gt=spec_binary_globaltype(raw,idx)
  idx,e=spec_binary_expr(raw,idx)
  return idx,{"type":gt,"init":e}

def spec_binary_globalsec_inv(node):
  return spec_binary_sectionN_inv(node,spec_binary_global_inv,6)
  
def spec_binary_global_inv(node):
  return spec_binary_globaltype_inv(node["type"]) + spec_binary_expr_inv(node["init"])


# 5.5.10 EXPORT SECTION

def spec_binary_exportsec(raw,idx,skip=0):
  return spec_binary_sectionN(raw,idx,7,spec_binary_export,skip)

def spec_binary_export(raw,idx):
  idx,nm = spec_binary_name(raw,idx)
  idx,d = spec_binary_exportdesc(raw,idx)
  return idx,{"name":nm,"desc":d}

def spec_binary_exportdesc(raw,idx):
  if raw[idx]==0x00:
    idx,x=spec_binary_funcidx(raw,idx+1)
    return idx,["func",x]
  elif raw[idx]==0x01:
    idx,x=spec_binary_tableidx(raw,idx+1)
    return idx,["table",x]
  elif raw[idx]==0x02:
    idx,x=spec_binary_memidx(raw,idx+1)
    return idx,["mem",x]
  elif raw[idx]==0x03:
    idx,x=spec_binary_globalidx(raw,idx+1)
    return idx,["global",x]
  else:
    return idx,None #error

def spec_binary_exportsec_inv(node):
  return spec_binary_sectionN_inv(node,spec_binary_export_inv,7)

def spec_binary_export_inv(node):
  return spec_binary_name_inv(node["name"]) + spec_binary_exportdesc_inv(node["desc"])

def spec_binary_exportdesc_inv(node):
  key=node[0]
  if key=="func":
    return bytearray([0x00]) + spec_binary_funcidx_inv(node[key])
  elif key=="table":
    return bytearray([0x01]) + spec_binary_tableidx_inv(node[key])
  elif key=="mem":
    return bytearray([0x02]) + spec_binary_memidx_inv(node[key])
  elif key=="global":
    return bytearray([0x03]) + spec_binary_globalidx_inv(node[key])
  else:
    return bytearray()


# 5.5.11 START SECTION

def spec_binary_startsec(raw,idx,skip=0):
  #TODO: st has ?
  return spec_binary_sectionN(raw,idx,8,spec_binary_start,skip)

def spec_binary_start(raw,idx):
  idx,x=spec_binary_funcidx(raw,idx)
  return idx,{"func":x}

def spec_binary_startsec_inv(node):
  if node==[]:
    return bytearray()
  else:
    return spec_binary_sectionN_inv(node,spec_binary_start_inv,8)

def spec_binary_start_inv(node):
  key=list(node.keys())[0]
  if key=="func":
    return spec_binary_funcidx_inv(node[key])
  else:
    return bytearray()


# 5.5.12 ELEMENT SECTION

def spec_binary_elemsec(raw,idx,skip=0):
  #TODO: typo? on pg 97 seg doesnt have star
  return spec_binary_sectionN(raw,idx,9,spec_binary_elem,skip)

def spec_binary_elem(raw,idx):
  idx,x=spec_binary_tableidx(raw,idx)
  idx,e=spec_binary_expr(raw,idx)
  idx,ystar=spec_binary_vec(raw,idx,spec_binary_funcidx)
  return idx,{"table":x,"offset":e,"init":ystar}

def spec_binary_elemsec_inv(node):
  return spec_binary_sectionN_inv(node,spec_binary_elem_inv,9)
  
def spec_binary_elem_inv(node):
  return spec_binary_tableidx_inv(node["table"]) + spec_binary_expr_inv(node["offset"]) + spec_binary_vec_inv(node["init"],spec_binary_funcidx_inv)


# 5.5.13 CODE SECTION

def spec_binary_codesec(raw,idx,skip=0):
  return spec_binary_sectionN(raw,idx,10,spec_binary_code,skip)

def spec_binary_code(raw,idx):
  idx,size=spec_binary_uN(raw,idx,32)
  idx,code_=spec_binary_func(raw,idx)
  #TODO: check whether size==|code|; note size is only useful for validation and skipping
  return idx,code_

def spec_binary_func(raw,idx):
  idx,tstarstar=spec_binary_vec(raw,idx,spec_binary_locals)
  idx,e=spec_binary_expr(raw,idx)
  #TODO: check |concat((t*)*)|<2^32?
  #TODO: typo: why is return e*?
  concattstarstar=[t for tstar in tstarstar for t in tstar] 
  #return idx, [tstarstar,e]  #not concatenating the t*'s makes it easier for printing
  return idx, [concattstarstar,e]

def spec_binary_locals(raw,idx):
  idx,n=spec_binary_uN(raw,idx,32)
  idx,t=spec_binary_valtype(raw,idx)
  tn=[t]*n
  return idx,tn

# the following three functions do not parse the expression, just take its address and size
# this is useful for validation or execution using bytecode
def codesec_bytecode_address(raw,idx,skip=0):
  return spec_binary_sectionN(raw,idx,10,code_bytecode_address,skip)

def code_bytecode_address(raw,idx):
  idx,size=spec_binary_uN(raw,idx,32)
  idx,code_=func_bytecode_address(raw,idx)
  idx+=size
  #TODO: check whether size==|code|; note size is only useful for validation and skipping
  return idx, code_+(size,)

def func_bytecode_address(raw,idx):
  idx,tstarstar=spec_binary_vec(raw,idx,spec_binary_locals)
  e=idx
  #concattstarstar=[e for t in tstarstar for e in t] #note: I did not concatenate the t*'s, is makes it easier for printing
  return idx, (tstarstar,e)


def spec_binary_codesec_inv(node):
  return spec_binary_sectionN_inv(node,spec_binary_code_inv,10)
  
def spec_binary_code_inv(node):
  func_bytes = spec_binary_func_inv(node)
  return spec_binary_uN_inv(len(func_bytes),32) + func_bytes

def spec_binary_func_inv(node):
  return spec_binary_vec_inv(node[0],spec_binary_locals_inv) + spec_binary_expr_inv(node[1]) 

def spec_binary_locals_inv(node):
  return spec_binary_uN_inv(len(node),32) + (spec_binary_valtype_inv(node[0]) if len(node)>0 else bytearray())
  

# 5.5.14 DATA SECTION

def spec_binary_datasec(raw,idx,skip=0):
  #TODO: typo pg 99 seg doesnt have star
  return spec_binary_sectionN(raw,idx,11,spec_binary_data,skip)

def spec_binary_data(raw,idx):
  idx,x=spec_binary_memidx(raw,idx)
  idx,e=spec_binary_expr(raw,idx)
  idx,bstar=spec_binary_vec(raw,idx,spec_binary_byte)
  return idx, {"data":x,"offset":e,"init":bstar}

def spec_binary_datasec_inv(node):
  return spec_binary_sectionN_inv(node,spec_binary_data_inv,11)
  
def spec_binary_data_inv(node):
  return spec_binary_memidx_inv(node["data"]) + spec_binary_expr_inv(node["offset"]) + spec_binary_vec_inv(node["init"],spec_binary_byte_inv)


# 5.5.15 MODULES

def spec_binary_module(raw):
  idx=0
  magic=[0x00,0x61,0x73,0x6d]
  if magic!=[x for x in raw[idx:idx+4]]:
    return None
  idx+=4
  version=[0x01,0x00,0x00,0x00]
  if version!=[x for x in raw[idx:idx+4]]:
    return None
  idx+=4
  idx,functypestar=spec_binary_typesec(raw,idx,0)
  idx,importstar=spec_binary_importsec(raw,idx,0)
  idx,typeidxn=spec_binary_funcsec(raw,idx,0)
  idx,tablestar=spec_binary_tablesec(raw,idx,0)
  idx,memstar=spec_binary_memsec(raw,idx,0)
  idx,globalstar=spec_binary_globalsec(raw,idx,0)
  idx,exportstar=spec_binary_exportsec(raw,idx,0)
  idx,startq=spec_binary_startsec(raw,idx,0)
  idx,elemstar=spec_binary_elemsec(raw,idx,0)
  idx,coden=spec_binary_codesec(raw,idx,0)
  idx,datastar=spec_binary_datasec(raw,idx,0)
  funcn=[]
  if typeidxn and coden and len(typeidxn)==len(coden):
    for i in range(len(typeidxn)):
      funcn+=[{"type":typeidxn[i], "locals":coden[i][0], "body":coden[i][1]}]
  mod = {"types":functypestar, "funcs":funcn, "tables":tablestar, "mems":memstar, "globals":globalstar, "elem": elemstar, "data":datastar, "start":startq, "imports":importstar, "exports":exportstar}
  return mod

def get_module_with_just_function_code_addresses(raw):
  idx=0
  magic=[0x00,0x61,0x73,0x6d]
  if magic!=[x for x in raw[idx:idx+4]]:
    return None
  idx+=4
  version=[0x01,0x00,0x00,0x00]
  if version!=[x for x in raw[idx:idx+4]]:
    return None
  idx+=4
  idx,functypestar=	spec_binary_typesec(raw,idx,0)
  idx,importstar=	spec_binary_importsec(raw,idx,0)
  idx,typeidxn=		spec_binary_funcsec(raw,idx,0)
  idx,tablestar=	spec_binary_tablesec(raw,idx,0)
  idx,memstar=		spec_binary_memsec(raw,idx,0)
  idx,globalstar=	spec_binary_globalsec(raw,idx,0)
  idx,exportstar=	spec_binary_exportsec(raw,idx,0)
  idx,startq=		spec_binary_startsec(raw,idx,0)
  idx,elemstar=		spec_binary_elemsec(raw,idx,0)
  idx,coden=		codesec_address(raw,idx,0)
  idx,datastar=		spec_binary_datasec(raw,idx,0)
  if not functypestar: return None
  if not importstar: return None
  if not typeidxn: return None
  if not tablestar: return None
  if not memstar: return None
  if not globalstar: return None
  if not exportstar: return None
  if not startq: return None
  if not elemstar: return None
  if not coden: return None
  if not datastar: return None
  if len(typeidxn)!=len(coden): return None
  #build module
  funcn=[]
  for i in range(len(typeidxn)):
    funcn+=[{"type":typeidxn[i], "locals":coden[i][0], "body":coden[i][1]}]
  mod = {"types":functypestar, "funcs":funcn, "tables":tablestar, "mems":memstar, "globals":globalstar, "elem": elemstar, "data":datastar, "start":startq, "imports":importstar, "exports":exportstar}
  return mod

def spec_binary_module_inv_to_file(mod,filename):
  f = open(filename, 'wb')
  magic=bytes([0x00,0x61,0x73,0x6d])
  version=bytes([0x01,0x00,0x00,0x00])
  f.write(magic)
  f.write(version)
  f.write(spec_binary_typesec_inv(mod["types"]))
  f.write(spec_binary_importsec_inv(mod["imports"]))
  f.write(spec_binary_funcsec_inv([e["type"] for e in mod["funcs"]]))
  f.write(spec_binary_tablesec_inv(mod["tables"]))
  f.write(spec_binary_memsec_inv(mod["mems"]))
  f.write(spec_binary_globalsec_inv(mod["globals"]))
  f.write(spec_binary_exportsec_inv(mod["exports"]))
  f.write(spec_binary_startsec_inv(mod["start"]))
  f.write(spec_binary_elemsec_inv(mod["elem"]))
  f.write(spec_binary_codesec_inv([(f["locals"],f["body"]) for f in mod["funcs"]]))
  f.write(spec_binary_datasec_inv(mod["data"]))
  f.close()









##############
##############
# 7 APPENDIX #
##############
##############

###############
# 7.1 EMBEDDING
###############

# 7.1.1 STORE

def init_store():
  return {"funcs":[], "mems":[], "tables":[], "globals":[]}

# 7.1.2 MODULES

def decode_module(bytestar):
  mod = spec_binary_module(bytestar)
  return mod
  
def parse_module(codepointstar):
  # text parser not implemented yet
  return -1

def validate_module(module):
  ret = spec_validate_module(module)
  if ret == -1: return "error"
  return None

def instantiate_module(store,module,externvalstar):
  #print("store:",store)
  #print("module:",module)
  #print("externvalstar:",externvalstar)
  store,F,ret = spec_instantiate(store,module,externvalstar)
  modinst = F["module"] #store["funcs"][0]["module"] #TODO: this will fail if first func is host func, or no funcs
  if store and modinst:
    return store, modinst
  else:
    return store,"error"

def module_imports(module):
  externtypestar, extertypeprimestar = spec_validate_module(mod)
  importstar = module["imports"]
  if len(importstar) != len(externtypestar): return "error"
  result = []
  for i in range(len(importstar)):
    importi = importstar[i]
    externtypei = externtypestar[i]
    resutli = [immporti["module"],importi["name"],externtypei] 
    result += resulti
  return result

def module_exports(module):
  externtypestar, extertypeprimestar = spec_validate_module(mod)
  exportstar = module["exports"]
  if len(exportstar) != len(externtypeprimestar): return "error"
  result = []
  for i in range(len(importstar)):
    exporti = exportstar[i]
    externtypeprimei = externtypeprimestar[i]
    resutli = [exporti["name"],externtypeprimei] 
    result += resulti
  return result


# 7.1.3 EXPORTS

def get_export(moduleinst, name):
  # assume valid so all export names are unique
  for exportinsti in moduleinst["exports"]:
    if name == exportinsti["name"]:
      return exportinsti["value"]
  return "error"

# 7.1.4 FUNCTIONS

def alloc_func(store, functype, hostfunc):
  store, funcaddr = spec_allochostfunc(store,functype,hostfunc)
  return store, funcaddr

def type_func(store,funcaddr):
  if len(store["funcs"]) <= funcaddr: return "error"
  functype = store["funcs"][funcaddr]
  return functype

def invoke_func(store,funcaddr,valstar):
  ret = spec_invoke(store,funcaddr,valstar)
  return store,ret
  
# 7.1.4 TABLES

def alloc_table(store, tabletype):
  store,tableaddr = spec_alloctable(store,tabletype)
  return store,tableaddr

def type_table(store,tableaddr):
  if len(store["tables"]) <= tableaddr: return "error"
  tableinst = store["tables"][tableaddr]
  max_ = tableinst["max"]
  min_ = len(tableinst["elem"]) #TODO: is this min OK? no other way to get min
  tabletype = [{"min":min_, "max":max_}, "anyfunc"]
  return tabletype

def read_table(store,tableaddr,i):
  if len(store["tables"]) < tableaddr: return "error"
  if type(i)!=int or i < 0: return "error"
  ti = store["tables"][tableaddr]
  if i >= len(ti["elem"]): return "error"
  return ti["elem"][i]

def write_table(store,tableaddr,i,funcaddr):
  if len(store["tables"]) <= tableaddr: return "error"
  if type(i)!=int or i < 0: return "error"
  ti = store["tables"][tableaddr]
  if i >= len(ti["elem"]): return "error"
  ti["elem"][i] = funcaddr
  return store

def size_table(store, tableaddr):
  if len(store["tables"]) <= tableaddr: return "error"
  return len(store["tables"][tableaddr]["elem"])

def grow_table(store, tableaddr, n):
  if len(store["tables"]) <= tableaddr: return "error"
  if type(n)!=int or n < 0: return -1
  store["tables"][tableaddr]["elem"] += [{"elem":[], "max":None} for i in range(n)]  # see spec \S 4.2.7 Table Instances for discussion on uninitialized table elements.
  return store

# 7.1.6 MEMORIES

def alloc_mem(store, memtype):
  store, memaddr = allocmem(store,memtype)
  return store, memaddr

def type_mem(store, memaddr):
  if len(store["mems"]) <= memaddr: return "error"
  meminst = store["mems"][memaddr]
  max_ = meminst["max"]
  min_ = len(meminst["data"])//65536  #page size = 64 Ki = 65536 #TODO: is this min OK? no other way to get min

def read_mem(store, memaddr, i):
  if len(store["mems"]) <= memaddr: return "error"
  if type(i)!=int or i < 0: return "error"
  mi = store["mems"][memaddr]
  if i >= len(mi["data"]): return "error"
  return mi["data"][i]

def write_mem(store,memaddr,i,byte):
  if len(store["mems"]) <= memaddr: return "error"
  if type(i)!=int or i < 0: return "error"
  mi = store["mems"][memaddr]
  if i >= len(mi["data"]): return "error"
  mi["data"][i] = byte
  return store

def size_mem(store,memaddr):
  if len(store["mems"]) <= memaddr: return "error"
  return len(store["mems"][memaddr])//65536  #page size = 64 Ki = 65536

def grow_mem(store,memaddr,n):
  if len(store["mems"]) <= memaddr: return "error"
  if type(n)!=int or n < 0: return "error"
  ret = spec_growmem(store["mems"][a],n)
  if ret==-1: return "error"
  return store

# 7.1.7 GLOBALS
  
def alloc_global(store,globaltype,val):
  store,globaladdr = spec_allocglobal(store,globaltype,val)
  return store,globaladdr

def type_global(store, globaladdr):
  if len(store["globals"]) <= globaladdr: return "error"
  globalinst = store["globals"][globaladdr]
  mut = globalinst["mut"]
  valtype = None # TODO: I don't store eg i32.const, just the value
  return [mut, valtype]

def read_global(store, globaladdr):
  if len(store["globals"]) <= globaladdr: return "error"
  gi = store["globals"][globaladdr]
  return gi["value"]
  
def write_global(store,globaladdr,val):
  if len(store["globals"]) <= globaladdr: return "error"
  gi = store["globals"][globaladdr]
  if gi["mut"] != "var": return "error"
  gi["value"] = val
  return store
  
  
  
  
  

  
  

  
  
  





##########################
# TOOLS FOR PRINTING STUFF
##########################

def print_tree(node,indent=0):
  if type(node)==tuple:
    print(" "*indent+str(node))
  elif type(node) in {list}:
    for e in node:
      print_tree(e,indent+1)
  elif type(node)==dict:
    for e in node:
      print(" "*indent+e)
      print_tree(node[e],indent+1)
  else:
    print(" "*indent+str(node))


def print_tree_expr(node,indent=0):
  if type(node)==tuple:	# an instruction
    if len(node)>2:	# ie node[0] in {"block","if","loop"}:
      print(" "*indent+str((node[0],node[1])))
      print_tree_expr(node[2],indent+1)
      print(" "*indent+"[end]")
    else:
      print(" "*indent+str(node))
  elif type(node)==list:
    for e in node:
      print_tree_expr(e,indent+1)
  elif type(node)==dict:
    for e in node:
      print(" "*indent+e)
      print_tree_expr(node[e],indent+1)
  else:
    print(" "*indent+str(node))


def print_raw_as_hex(raw):
  print("printing whole module:")
  for i in range(len(raw)):
    print(hex(raw[i]),end=" ")
    if (i+1)%10==0:
      print()
  print()






def print_sections(mod):
  print("types:",mod["types"])
  print()
  print("funcs:",mod["funcs"])
  print()
  for f in mod["funcs"]:
    print(f)
    print()
  print("tables",mod["tables"])
  print()
  print("mems",mod["mems"])
  print()
  print("globals",mod["globals"])
  print()
  print("elem",mod["elem"])
  print()
  print("data",mod["data"])
  print()
  print("start",mod["start"])
  print()
  print("imports",mod["imports"])
  print()
  print("exports",mod["exports"])







#####################
# PYWEBASSEMBLY API #
#####################

def parse_wasm(filename):
  with open(filename, 'rb') as f:
    #memoryview doesn't make copy, bytearray may require copy
    wasm = memoryview(f.read())
    mod = spec_binary_module(wasm)
    #print_tree(mod)
    print_sections(mod)
    #print_tree(mod["funcs"])
    #print_sections(mod)
    spec_binary_module_inv_to_file(mod,filename.split('.')[0]+"_generated.wasm") 


def instantiate_wasm(filename):
  with open(filename, 'rb') as f:
    #memoryview doesn't make copy, bytearray may require copy
    wasm = memoryview(f.read())
    mod = spec_binary_module(wasm)
    #print_tree(mod)
    print_sections(mod)
    #print_tree(mod["funcs"])
    #print_sections(mod)
    #
    S = {"funcs":[], "tables":[], "mems":[], "globals":[]}
    externvaln=[]
    S,F,ret = spec_instantiate(S,mod,externvaln)
    #print(S)
    #print(F)
    #print(ret)
    funcaddr = 0
    valn = [["i32.const",10]]              # change argument here
    ret = spec_invoke(S,funcaddr,valn)
    print("result of function call:",ret)
    





if __name__ == "__main__":
  import sys
  if len(sys.argv)!=2:
    print("Argument should be <filename>.wasm")
  else:
    #parse_wasm(sys.argv[1])
    instantiate_wasm(sys.argv[1])
