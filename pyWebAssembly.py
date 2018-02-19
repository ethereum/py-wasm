#!/usr/bin/env python



#map betwen binary and text opcodes
instrs_table_binary = {
0x00:'unreachable',
0x01:'nop',
0x02:'block',			#blocktype in* end		#begin block
0x03:'loop',			#blocktype in* end		#begin block
0x04:'if',			#blocktype in1* else? end	#begin block
0x05:'else',			#in2*				#end block & begin block
0x0b:'end',							#end block
0x0c:'br',			#labelidx			#branch
0x0d:'br_if',			#labelidx			#branch
0x0e:'br_table',		#labelidx* labelidx		#branch
0x0f:'return',							#end block
0x10:'call',			#funcidx			#branch
0x11:'call_indirect',		#typeidx 0x00			#branch

0x1a:'drop',
0x1b:'select',

0x20:'get_local',		#localidx
0x21:'set_local',		#localidx
0x22:'tee_local',		#localidx
0x23:'get_global',		#globalidx
0x24:'set_global',		#globalidx

0x28:'i32.load',		#memarg
0x29:'i64.load',		#memarg
0x2a:'f32.load',		#memarg
0x2b:'f64.load',		#memarg
0x2c:'i32.load8_s',		#memarg
0x2d:'i32.load8_u',		#memarg
0x2e:'i32.load16_s',		#memarg
0x2f:'i32.load16_u',		#memarg
0x30:'i64.load8_s',		#memarg
0x31:'i64.load8_u',		#memarg
0x32:'i64.load16_s',		#memarg
0x33:'i64.load16_u',		#memarg
0x34:'i64.load32_s',		#memarg
0x35:'i64.load32_u',		#memarg
0x36:'i32.store',		#memarg
0x37:'i64.store',		#memarg
0x38:'f32.store',		#memarg
0x39:'f64.store',		#memarg
0x3a:'i32.store8',		#memarg
0x3b:'i32.store16',		#memarg
0x3c:'i64.store8',		#memarg
0x3d:'i64.store16',		#memarg
0x3e:'i64.store32',		#memarg
0x3f:'current_memory',
0x40:'grow_memory',

0x41:'i32.const',		#i32
0x42:'i64.const',		#i64
0x43:'f32.const',		#f32
0x44:'f64.const',		#f64

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
0xbf:'f64.reinterpret/i64',
}

instrs_table_text = {}
for oc in instrs_table_binary:
  instrs_table_text[instrs_table_binary[oc]]=oc







# 2.2.3 FLOATING-POINT

N_to_signif={32:23,64:52}
signif_to_N={val:key for key,val in N_to_signif.items()}

def spec_signif(N):
  if N in N_to_signif:
    return N_to_signif[N]
  else:
    return None

def spec_signif_inv(signif):
  if signif in signif_to_N:
    return signif_to_N[signif]
  else:
    return None

N_to_expon={32:8,64:11}
expon_to_N={val:key for key,val in N_to_expon.items()}

def spec_expon(N):
  if N in N_to_expon:
    return N_to_expon[N]
  else:
    return None

def spec_expon_inv(expon):
  if expon in expon_to_N:
    return expon_to_N[expon]
  else:
    return None


# 4.3.1 REPRESENTATIONS

#TODO: check if this is correct; note little-endian; 
#floating-point values are encoded directly by their IEEE 754-2008 bit pattern in little endian byte order
def spec_bytes_fN_inv(bstar,N):
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



# 4.3.2 INTEGER OPERATIONS

def spec_signediN(N,i):
  if 0<=i<2**(N-1):
    return i
  elif 2**(N-1)<=i<2**N:
    return i-2**N
  else:
    return None

def spec_signed_iN_inv(N,i):
  if 0<=i<2**(N-1):
    return i
  elif -1*(2**(N-1))<=i<0:
    return i+2**N
  else:
    return None


# 5.1.3 VECTORS

def spec_vec(raw,idx,B):
  idx,n=spec_uN(raw,idx,32)
  xn = []
  for i in range(n):
    idx,x = B(raw,idx)
    xn+=[x]
  return idx,xn

def spec_vec_inv(mynode,myfunc):
  n_bytes=spec_uN_inv(len(mynode),32) 
  xn_bytes=bytearray()
  for x in mynode:
    xn_bytes+=myfunc(x)
  return n_bytes+xn_bytes 


############
# 5.2 VALUES
############

# 5.2.1 BYTES

def spec_byte(raw,idx):
  return idx+1,raw[idx]

def spec_byte_inv(node):
  return bytearray([node])

# 5.2.2 INTEGERS
#TODO: check things on pg 87

#unsigned
def spec_uN(raw,idx,N):
  idx,n=spec_byte(raw,idx)
  if n<2**7 and n<2**N:
    return idx,n
  elif n>=2**7 and N>7:
    idx,m=spec_uN(raw,idx,N-7)
    return idx, (2**7)*m+(n-2**7)
  else:
    return idx,None #error

def spec_uN_inv(k,N):
  #print("spec_uN_inv(",k,N,")")
  if k<2**7 and k<2**N:
    return bytearray([k])
  elif k>=2**7 and N>7:
    return bytearray([k%(2**7)+2**7])+spec_uN_inv(k//(2**7),N-7)
  else:
    return None

def spec_uN_inv_old(n,N):
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
def spec_sN(raw,idx,N):
  n=int(raw[idx])
  idx+=1
  if n<2**6 and n<2**(N-1):
    return idx,n
  elif 2**6<=n<2**7 and n>=2**7-2**(N-1):
    return idx,n-2**7
  elif n>=2**7 and N>7:
    idx,m=spec_sN(raw,idx,N-7)
    return idx,2**7*m+(n-2**7)
  else:
    return idx,None #error

def spec_sN_inv(k,N):
  if 0<=k<2**6 and k<2**N:
    return bytearray([k])
  elif 2**6<=k+2**7<2**7: # and k+2**7>=2**7-2**(N-1):
    return bytearray([k+2**7])
  elif (k>=2**6 or k<2**6) and N>7: #(k<0 and k+2**7>=2**6)) and N>7:
    return bytearray([k%(2**7)+2**7])+spec_sN_inv((k//(2**7)),N-7)
  else:
    return None

#uninterpretted integers
def spec_iN(raw,idx,N):
  idx,n=spec_sN(raw,idx,N)
  i = spec_signed_iN_inv(N,n)
  return idx, i

def spec_iN_inv(i,N):
  return spec_sN_inv(spec_signediN(N,i),N)



# 5.2.3 FLOATING-POINT

#fN::= b*:byte^{N/8} => bytes_{fN}^{-1}(b*)
def spec_fN(raw,idx,N):
  bstar = []
  for i in range(N//8):
    bstar+=[raw[idx]]
    idx+=1
  return idx, bytearray(bstar)

def spec_fN_inv(node,N):
  if len(node)==N/8:
    return node
  else:
    return None
  

# 5.2.4 NAMES

#name as UTF-8 codepoints
def spec_name(raw,idx):
  idx,bstar = spec_vec(raw,idx,spec_byte)
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
    c=2**6*(b1-0xc0) + (b2-0x80)
    if 0x80<=c<0x800:
      name+=[c]
      continue
    b3=bstar[bstaridx]
    bstaridx+=1
    c=2**12*(b1-0xc0) + 2**6*(b2-0x80) + (b3-0x80)
    if 0x800<=c<0x10000:
      name+=[c]
      continue
    b4=bstar[bstaridx+4]
    bstaridx+=1
    c=2**18*(b1-0xc0) + 2**12*(b2-0x80) + 2**6*(b3-0x80) + (b4-0x80)
    if 0x10000<=c<0x110000:
      name+=[c]
    else:
      break  #return idx, None #error
  #convert each codepoint to utf8 character
  nametxt = ""
  for b in name:
    nametxt+=chr(b)
  return idx,nametxt

def spec_name_inv(chars):
  name_bytes=bytearray()
  for c in chars:
    c = ord(c)
    if c<0x80:
      name_bytes += bytes([c])
    elif 0x80<=c<0x800:
      name_bytes += bytes([(c>>6)+0xc0,(c&0b111111)+0x80])
    elif 0x800<=c<0x10000:
      name_bytes += bytes([(c>>12)+0xc0,((c>>6)&0b111111)+0x80,(c&0b111111)+0x80])
    elif 0x10000<=c<0x110000:
      name_bytes += bytes([(c>>18)+0xc0,((c>>12)&0b111111)+0x80,((c>>6)&0b111111)+0x80,(c&0b111111)+0x80])
    else:
      return None #error
  return bytearray([len(name_bytes)])+name_bytes


###########
# 5.3 TYPES
###########

# 5.3.1 VALUE TYPES

valtype2bin={"i32":0x7f,"i64":0x7e,"f32":0x7d,"f64":0x7c}
bin2valtype={val:key for key,val in valtype2bin.items()}

def spec_valtype(raw,idx):
  if raw[idx] in bin2valtype:
    return idx+1,bin2valtype[raw[idx]]
  else:
    return idx,None

def spec_valtype_inv(node):
  if node in valtype2bin:
    return bytearray([valtype2bin[node]])
  else:
    return bytearray([])

# 5.3.2 RESULT TYPES

def spec_blocktype(raw,idx):
  if raw[idx]==0x40:
    return idx+1,None
  idx,t=spec_valtype(raw,idx)
  return idx, t

def spec_blocktype_inv(node):
  if node==None:
    return bytearray([0x40])
  else:
    return spec_valtype_inv(node)


# 5.3.3 FUNCTION TYPES

def spec_functype(raw,idx):
  if raw[idx]!=0x60:
    return idx, None #error
  idx+=1
  idx,t1star=spec_vec(raw,idx,spec_valtype)
  idx,t2star=spec_vec(raw,idx,spec_valtype)
  return idx,(t1star,t2star)

def spec_functype_inv(node):
  return bytearray([0x60])+spec_vec_inv(node[0],spec_valtype_inv)+spec_vec_inv(node[1],spec_valtype_inv)


# 5.3.4 LIMITS

def spec_limits(raw,idx):
  if raw[idx]==0x00:
    idx,n = spec_uN(raw,idx+1,32)
    return idx,{"min":n,"max":None}
  elif raw[idx]==0x01:
    idx,n = spec_uN(raw,idx+1,32)
    idx,m = spec_uN(raw,idx,32)
    return idx,{"min":n,"max":m}
  else:
    return idx,None #error
    
def spec_limits_inv(node):
  if node["max"]==None:
    return bytearray([0x00])+spec_uN_inv(node["min"],32)
  else:
    return bytearray([0x01])+spec_uN_inv(node["min"],32)+spec_uN_inv(node["max"],32)

  
# 5.3.5 MEMORY TYPES

def spec_memtype(raw,idx):
  return spec_limits(raw,idx)

def spec_memtype_inv(node):
  return spec_limits_inv(node)


# 5.3.6 TABLE TYPES

def spec_tabletype(raw,idx):
  idx,et = spec_elemtype(raw,idx)
  idx,lim = spec_limits(raw,idx)
  return idx,(lim,et)

def spec_elemtype(raw,idx):
  if raw[idx]==0x70:
    return idx+1,"anyfunc"
  else:
    return idx,None #error

def spec_tabletype_inv(node):
  return spec_elemtype_inv(node[1])+spec_limits_inv(node[0])

def spec_elemtype_inv(node):
  return bytearray([0x70])


# 5.3.7 GLOBAL TYPES

def spec_globaltype(raw,idx):
  idx,t = spec_valtype(raw,idx)
  idx,m = spec_mut(raw,idx)
  return idx,(m,t)

def spec_mut(raw,idx):
  if raw[idx]==0x00:
    return idx+1,"const"
  elif raw[idx]==0x01:
    return idx+1,"var"
  else:
    return idx, None #error

def spec_globaltype_inv(node):
  return spec_valtype_inv(node[1])+spec_mut_inv(node[0])

def spec_mut_inv(node):
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

def spec_memarg(raw,idx):
  idx,a=spec_uN(raw,idx,32)
  idx,o=spec_uN(raw,idx,32)
  return idx,{"align":a,"offset":o}

def spec_memarg_inv(node):
  return spec_uN_inv(node["align"],32) + spec_uN_inv(node["offset"],32)

def spec_instr(raw,idx):
  if raw[idx] not in instrs_table_binary:
    return idx, None #error
  instr_binary = raw[idx]
  instr_text = instrs_table_binary[instr_binary]
  idx+=1
  if instr_text in {"block","loop","if"}:      #block, loop, if
    idx,rt=spec_blocktype(raw,idx)
    instar=[]
    if instr_text=="if":
      instar2=[]
      while raw[idx] not in {0x05,0x0b}:
        idx,ins=spec_instr(raw,idx)
        instar+=[ins]
      if raw[idx]==0x05: #if with else
        idx+=1
        while raw[idx] not in {0x0b}:
          idx,ins=spec_instr(raw,idx)
          instar2+=[ins]
        return idx+1, ("if",rt,instar,instar2) #+[("end",)]
      return idx+1, ("if",rt,instar) #+[("end",)]
    else: 
      while raw[idx]!=0x0b:
        idx,ins=spec_instr(raw,idx)
        instar+=[ins]
      return idx+1, (instr_text,rt,instar) #+[("end",)]
  elif instr_text in {"br","br_if"}:           # br, br_if
    idx,l = spec_labelidx(raw,idx)
    return idx, (instr_text,l)
  elif instr_text == "br_table":               # br_table
    idx,lstar=spec_vec(raw,idx,spec_labelidx)
    idx,lN=spec_labelidx(raw,idx)
    return idx, ("br_table",lstar,lN)
  elif instr_text in {"call","call_indirect"}: # call, call_indirect
    if instr_text=="call":
      idx,x=spec_funcidx(raw,idx)
    if instr_text=="call_indirect":
      idx,x=spec_typeidx(raw,idx)
      if raw[idx]!=0x00: return idx,None #error
      idx+=1
    return idx, (instr_text,x)
  elif 0x20<=instr_binary<=0x22:               # get_local, etc
    idx,x=spec_localidx(raw,idx)
    return idx, (instr_text,x)
  elif 0x23<=instr_binary<=0x24:               # get_global, etc
    idx,x=spec_globalidx(raw,idx)
    return idx, (instr_text,x)
  elif 0x28<=instr_binary<=0x3e:               # i32.load, i64.store, etc
    idx,m = spec_memarg(raw,idx)
    return idx, (instr_text,m)
  elif 0x3f<=instr_binary<=0x40:               # urrent_memory, grow_memory
    if raw[idx]!=0x00: return idx,None #error
    return idx+1, (instr_text,)
  elif 0x41<=instr_binary<=0x42:               # i32.const, etc
    n=0
    if instr_text=="i32.const":
      idx,n = spec_iN(raw,idx,32)
    if instr_text=="i64.const":
      idx,n = spec_iN(raw,idx,64)
    return idx, (instr_text,n)
  elif 0x43<=instr_binary<=0x44:               # f32.const, etc
    z=0
    if instr_text=="f32.const":
      idx,z = spec_fN(raw,idx,32)
    if instr_text=="f64.const":
      idx,z = spec_fN(raw,idx,64)
    return idx, (instr_text,z)
  else:
    #otherwise no immediate
    return idx, (instr_text,)


def spec_instr_inv(node):
  instr_bytes = bytearray()
  #print("spec_instr_inv(",node,")")
  if type(node[0])==str:
    instr_bytes+=bytearray([instrs_table_text[node[0]]])
  #the rest is for immediates
  if node[0] in {"block","loop"}:              #block, loop
    instr_bytes+=spec_blocktype_inv(node[1])
    instar_bytes=bytearray()
    for n in node[2]:
      instar_bytes+=spec_instr_inv(n)
    instar_bytes+=bytes([0x0b])
    instr_bytes+=instar_bytes
  elif node[0]=="if":                          #if
    instr_bytes+=spec_blocktype_inv(node[1])
    instar_bytes=bytearray()
    for n in node[2]:
      instar_bytes+=spec_instr_inv(n)
    if len(node)==4: #TODO: test this
      instar_bytes+=bytearray([0x05])
      for n in node[3]:
        instar_bytes+=spec_instr_inv(n)
    instar_bytes+=bytes([0x0b])
    instr_bytes+=instar_bytes
  elif node[0] in {"br","br_if"}:              #br, br_if
    instr_bytes+=spec_labelidx_inv(node[1])
  elif node[0] == "br_table":                   #br_table
    instr_bytes+=spec_vec_inv(node[1],spec_labelidx_inv)
    instr_bytes+=spec_labelidx_inv(node[2])
  elif node[0] == "call":                       #call
    instr_bytes+=spec_funcidx_inv(node[1])
  elif node[0] == "call_indirect":              #call_indirect
    instr_bytes+=spec_typeidx_inv(node[1])
    instr_bytes+=bytearray([0x00])
  elif 0x20<=instrs_table_text[node[0]]<=0x24:  #get_local, set_local, tee_local
    instr_bytes+=spec_localidx_inv(node[1])
  elif 0x20<=instrs_table_text[node[0]]<=0x24:  #get_global, set_global
    instr_bytes+=spec_globalidx_inv(node[1])
  elif 0x28<=instrs_table_text[node[0]]<=0x3e:  #i32.load, i32.load8_s, i64.store, etc
    instr_bytes+=spec_memarg_inv(node[1])
  elif 0x3f<=instrs_table_text[node[0]]<=0x40:  #current_memory, grow_memory
    instr_bytes+=bytearray([0x00])
  elif node[0]=="i32.const":                    #i32.const
    instr_bytes+=spec_iN_inv(node[1],32)
  elif node[0]=="i64.const":                    #i64.const
    instr_bytes+=spec_iN_inv(node[1],64)
  elif node[0]=="f32.const":                    #i64.const
    instr_bytes+=spec_fN_inv(node[1],32)
  elif node[0]=="f64.const":                    #i64.const
    instr_bytes+=spec_fN_inv(node[1],64)
  return instr_bytes



# 5.4.6 EXPRESSIONS

def spec_expr(raw,idx):
  instar = []
  while raw[idx] != 0x0b: 
    idx,ins = spec_instr(raw,idx)
    instar+=[ins]
  if raw[idx] != 0x0b: return idx,None #error
  return idx+1, instar #+[('end',)]

def spec_expr_inv(node):
  instar_bytes=bytearray()
  for n in node:
    instar_bytes+=spec_instr_inv(n)
  instar_bytes+=bytes([0x0b])
  return instar_bytes






#############
# 5.5 MODULES
#############

# 5.5.1 INDICES

def spec_typeidx(raw,idx):
  idx, x = spec_uN(raw,idx,32)
  return idx,x

def spec_typeidx_inv(node):
  return spec_uN_inv(node,32)

def spec_funcidx(raw,idx):
  idx,x = spec_uN(raw,idx,32)
  return idx,x

def spec_funcidx_inv(node):
  return spec_uN_inv(node,32)

def spec_tableidx(raw,idx):
  idx,x = spec_uN(raw,idx,32)
  return idx,x

def spec_tableidx_inv(node):
  return spec_uN_inv(node,32)

def spec_memidx(raw,idx):
  idx,x = spec_uN(raw,idx,32)
  return idx,x

def spec_memidx_inv(node):
  return spec_uN_inv(node,32)

def spec_globalidx(raw,idx):
  idx,x = spec_uN(raw,idx,32)
  return idx,x

def spec_globalidx_inv(node):
  return spec_uN_inv(node,32)

def spec_localidx(raw,idx):
  idx,x = spec_uN(raw,idx,32)
  return idx,x

def spec_localidx_inv(node):
  return spec_uN_inv(node,32)

def spec_labelidx(raw,idx):
  idx,l = spec_uN(raw,idx,32)
  return idx,l

def spec_labelidx_inv(node):
  return spec_uN_inv(node,32)



# 5.5.2 SECTIONS

def spec_sectionN(raw,idx,N,B,skip):
  if idx>=len(raw) or raw[idx]!=N:
    return idx, []  #skip since this sec not included
  idx+=1
  idx,size = spec_uN(raw,idx,32)
  if skip:
    return idx+size,[]
  if N!=8: #not start:
    return spec_vec(raw,idx,B)
  else:
    return B(raw,idx)

def spec_sectionN_inv(cont,Binv,N):
  if cont==None or cont==[]:
    return bytearray([])
  N_bytes=bytearray([N])
  cont_bytes=bytearray()
  if N==8: #startsec
    cont_bytes=Binv(cont)
  else:
    cont_bytes=spec_vec_inv(cont,Binv)
  size_bytes=spec_uN_inv(len(cont_bytes),32) 
  return N_bytes+size_bytes+cont_bytes


# 5.5.3 CUSTOM SECTION

def spec_customsec(raw,idx,skip=1):
  idx,size = spec_uN(raw,idx,32)
  endidx = idx+size
  #TODO: not a vec(), so should adjust sectionN()
  return endidx,None #return spec_sectionN(raw,idx,0,spec_custom,skip) 

def spec_custom(raw,idx):
  idx,name = spec_name(raw,idx)
  #TODO: what is stopping condition for bytestar?
  idx,bytestar = spec_byte(raw,idx)
  return name,bytestar

def spec_customsec_inv(node):
  return spec_sectionN_inv(node,spec_custom_inv)
  
def spec_custom_inv(node):
  return spec_name_inv(node[0]) + spec_byte_inv(node[1]) #TODO: check this


# 5.5.4 TYPE SECTION

def spec_typesec(raw,idx,skip=0):
  return spec_sectionN(raw,idx,1,spec_functype,skip)

def spec_typesec_inv(node):
  return spec_sectionN_inv(node,spec_functype_inv,1)


# 5.5.5 IMPORT SECTION

def spec_importsec(raw,idx,skip=0):
  return spec_sectionN(raw,idx,2,spec_import,skip)

def spec_import(raw,idx):
  idx,mod = spec_name(raw,idx)
  idx,nm = spec_name(raw,idx)
  idx,d = spec_importdesc(raw,idx)
  return idx,{"module":mod,"name":nm,"desc":d}

def spec_importdesc(raw,idx):
  if raw[idx]==0x00:
    idx,x=spec_typeidx(raw,idx+1)
    return idx,{"func":x}
  elif raw[idx]==0x01:
    idx,tt=spec_tabletype(raw,idx+1)
    return idx,{"table":tt}
  elif raw[idx]==0x02:
    idx,mt=spec_memtype(raw,idx+1)
    return idx,{"mem":mt}
  elif raw[idx]==0x03:
    idx,gt=spec_globaltype(raw,idx+1)
    return idx,{"global":gt}
  else:
    return idx,None #error

def spec_importsec_inv(node):
  return spec_sectionN_inv(node,spec_import_inv,2)

def spec_import_inv(node):
  return spec_name_inv(node["module"]) + spec_name_inv(node["name"]) + spec_importdesc_inv(node["desc"])

def spec_importdesc_inv(node):
  key=list(node.keys())[0]
  if key=="func":
    return bytearray([0x00]) + spec_typeidx_inv(node[key])
  elif key=="table":
    return bytearray([0x01]) + spec_tabletype_inv(node[key])
  elif key=="mem":
    return bytearray([0x02]) + spec_memtype_inv(node[key])
  elif key=="global":
    return bytearray([0x03]) + spec_globaltype_inv(node[key])
  else:
    return bytearray()
  

# 5.5.6 FUNCTION SECTION

def spec_funcsec(raw,idx,skip=0):
  return spec_sectionN(raw,idx,3,spec_typeidx,skip)

def spec_funcsec_inv(node):
  return spec_sectionN_inv(node,spec_typeidx_inv,3)


# 5.5.7 TABLE SECTION

def spec_tablesec(raw,idx,skip=0):
  return spec_sectionN(raw,idx,4,spec_table,skip)

def spec_table(raw,idx):
  idx,tt=spec_tabletype(raw,idx)
  return idx,{"type":tt}

def spec_tablesec_inv(node):
  return spec_sectionN_inv(node,spec_table_inv,4)
  
def spec_table_inv(node):
  return spec_tabletype_inv(node["type"])


# 5.5.8 MEMORY SECTION

def spec_memsec(raw,idx,skip=0):
  return spec_sectionN(raw,idx,5,spec_mem,skip)

def spec_mem(raw,idx):
  idx,mt = spec_memtype(raw,idx)
  return idx,{"type":mt}

def spec_memsec_inv(node):
  return spec_sectionN_inv(node,spec_mem_inv,5)
  
def spec_mem_inv(node):
  return spec_memtype_inv(node["type"])


# 5.5.9 GLOBAL SECTION

def spec_globalsec(raw,idx,skip=0):
  return spec_sectionN(raw,idx,6,spec_global,skip)

def spec_global(raw,idx):
  idx,gt=spec_globaltype(raw,idx)
  idx,e=spec_expr(raw,idx)
  return idx,{"type":gt,"init":e}

def spec_globalsec_inv(node):
  return spec_sectionN_inv(node,spec_global_inv,6)
  
def spec_global_inv(node):
  return spec_globaltype_inv(node["type"]) + spec_expr_inv(node["init"])


# 5.5.10 EXPORT SECTION

def spec_exportsec(raw,idx,skip=0):
  return spec_sectionN(raw,idx,7,spec_export,skip)

def spec_export(raw,idx):
  idx,nm = spec_name(raw,idx)
  idx,d = spec_exportdesc(raw,idx)
  return idx,{"name":nm,"desc":d}

def spec_exportdesc(raw,idx):
  if raw[idx]==0x00:
    idx,x=spec_funcidx(raw,idx+1)
    return idx,{"func":x}
  elif raw[idx]==0x01:
    idx,x=spec_tableidx(raw,idx+1)
    return idx,{"table":x}
  elif raw[idx]==0x02:
    idx,x=spec_memidx(raw,idx+1)
    return idx,{"mem":x}
  elif raw[idx]==0x03:
    idx,x=spec_globalidx(raw,idx+1)
    return idx,{"global":x}
  else:
    return idx,None #error

def spec_exportsec_inv(node):
  return spec_sectionN_inv(node,spec_export_inv,7)

def spec_export_inv(node):
  return spec_name_inv(node["name"]) + spec_exportdesc_inv(node["desc"])

def spec_exportdesc_inv(node):
  key=list(node.keys())[0]
  if key=="func":
    return bytearray([0x00]) + spec_funcidx_inv(node[key])
  elif key=="table":
    return bytearray([0x01]) + spec_tableidx_inv(node[key])
  elif key=="mem":
    return bytearray([0x02]) + spec_memidx_inv(node[key])
  elif key=="global":
    return bytearray([0x03]) + spec_globalidx_inv(node[key])
  else:
    return bytearray()


# 5.5.11 START SECTION

def spec_startsec(raw,idx,skip=0):
  #TODO: st has ?
  return spec_sectionN(raw,idx,8,spec_start,skip)

def spec_start(raw,idx):
  idx,x=spec_funcidx(raw,idx)
  return idx,{"func":x}

def spec_startsec_inv(node):
  if node==[]:
    return bytearray()
  else:
    return spec_sectionN_inv(node,spec_start_inv,8)

def spec_start_inv(node):
  key=list(node.keys())[0]
  if key=="func":
    return spec_funcidx_inv(node[key])
  else:
    return bytearray()


# 5.5.12 ELEMENT SECTION

def spec_elemsec(raw,idx,skip=0):
  #TODO: typo? on pg 97 seg doesnt have star
  return spec_sectionN(raw,idx,9,spec_elem,skip)

def spec_elem(raw,idx):
  idx,x=spec_tableidx(raw,idx)
  idx,e=spec_expr(raw,idx)
  idx,ystar=spec_vec(raw,idx,spec_funcidx)
  return idx,{"table":x,"offset":e,"init":ystar}

def spec_elemsec_inv(node):
  return spec_sectionN_inv(node,spec_elem_inv,9)
  
def spec_elem_inv(node):
  return spec_tableidx_inv(node["table"]) + spec_expr_inv(node["offset"]) + spec_vec_inv(node["init"],spec_funcidx_inv)


# 5.5.13 CODE SECTION

def spec_codesec(raw,idx,skip=0):
  return spec_sectionN(raw,idx,10,spec_code,skip)

def spec_code(raw,idx):
  idx,size=spec_uN(raw,idx,32)
  idx,code_=spec_func(raw,idx)
  #TODO: check whether size==|code|; note size is only useful for validation and skipping
  return idx,code_

def spec_func(raw,idx):
  idx,tstarstar=spec_vec(raw,idx,spec_locals)
  idx,e=spec_expr(raw,idx)
  #TODO: check |concat((t*)*)|<2^32?
  #TODO: Typo: why is return e*?
  #concattstarstar=[e for t in tstarstar for e in t] #note: I did not concatenate the t*'s, is makes it easier for printing
  return idx, (tstarstar,e)

def spec_locals(raw,idx):
  idx,n=spec_uN(raw,idx,32)
  idx,t=spec_valtype(raw,idx)
  tn=[t]*n
  return idx,tn

def spec_codesec_inv(node):
  return spec_sectionN_inv(node,spec_code_inv,10)
  
def spec_code_inv(node):
  func_bytes = spec_func_inv(node)
  return spec_uN_inv(len(func_bytes),32) + func_bytes

def spec_func_inv(node):
  return spec_vec_inv(node[0],spec_locals_inv) + spec_expr_inv(node[1]) 

def spec_locals_inv(node):
  return spec_uN_inv(len(node),32) + (spec_valtype_inv(node[0]) if len(node)>0 else bytearray())
  

# 5.5.13 DATA SECTION

def spec_datasec(raw,idx,skip=0):
  #TODO: typo pg 99 seg doesnt have star
  return spec_sectionN(raw,idx,11,spec_data,skip)

def spec_data(raw,idx):
  idx,x=spec_memidx(raw,idx)
  idx,e=spec_expr(raw,idx)
  idx,bstar=spec_vec(raw,idx,spec_byte)
  return idx, {"data":x,"offset":e,"init":bstar}

def spec_datasec_inv(node):
  return spec_sectionN_inv(node,spec_data_inv,11)
  
def spec_data_inv(node):
  return spec_memidx_inv(node["data"]) + spec_expr_inv(node["offset"]) + spec_vec_inv(node["init"],spec_byte_inv)


# 5.5.15 MODULES

def spec_module(raw):
  idx=0
  magic=[0x00,0x61,0x73,0x6d]
  if magic!=[x for x in raw[idx:idx+4]]:
    return None
  idx+=4
  version=[0x01,0x00,0x00,0x00]
  if version!=[x for x in raw[idx:idx+4]]:
    return None
  idx+=4
  idx,functypestar=spec_typesec(raw,idx,0)
  idx,importstar=spec_importsec(raw,idx,0)
  idx,typeidxn=spec_funcsec(raw,idx,0)
  idx,tablestar=spec_tablesec(raw,idx,0)
  idx,memstar=spec_memsec(raw,idx,0)
  idx,globalstar=spec_globalsec(raw,idx,0)
  idx,exportstar=spec_exportsec(raw,idx,0)
  idx,startq=spec_startsec(raw,idx,0)
  idx,elemstar=spec_elemsec(raw,idx,0)
  idx,coden=spec_codesec(raw,idx,0)
  idx,datastar=spec_datasec(raw,idx,0)
  funcn=[]
  if typeidxn and coden and len(typeidxn)==len(coden):
    for i in range(len(typeidxn)):
      funcn+=[{"type":typeidxn[i], "locals":coden[i][0], "body":coden[i][1]}]
  mod = {"types":functypestar, "funcs":funcn, "tables":tablestar, "mems":memstar, "globals":globalstar, "elem": elemstar, "data":datastar, "start":startq, "imports":importstar, "exports":exportstar}
  return mod


def spec_module_inv_to_file(mod,filename):
  f = open(filename, 'wb')
  magic=bytes([0x00,0x61,0x73,0x6d])
  version=bytes([0x01,0x00,0x00,0x00])
  f.write(magic)
  f.write(version)
  f.write(spec_typesec_inv(mod["types"]))
  f.write(spec_importsec_inv(mod["imports"]))
  f.write(spec_funcsec_inv([e["type"] for e in mod["funcs"]]))
  f.write(spec_tablesec_inv(mod["tables"]))
  f.write(spec_memsec_inv(mod["mems"]))
  f.write(spec_globalsec_inv(mod["globals"]))
  f.write(spec_exportsec_inv(mod["exports"]))
  f.write(spec_startsec_inv(mod["start"]))
  f.write(spec_elemsec_inv(mod["elem"]))
  f.write(spec_codesec_inv([(f["locals"],f["body"]) for f in mod["funcs"]]))
  f.write(spec_datasec_inv(mod["data"]))
  f.close()









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
      print(" "*indent+"(end)")
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




def parse_wasm(filename):
  with open(filename, 'rb') as f:
    wasm = memoryview(f.read())
    mod = spec_module(wasm)
    #print_tree(mod)
    #print_sections(mod)
    #print_tree(mod["funcs"])
    #print_sections(mod)
    spec_module_inv_to_file(mod,filename.split('.')[0]+"_generated.wasm") 






if __name__ == "__main__":
  import sys
  if len(sys.argv)!=2:
    print("Argument should be <filename>.wasm")
  else:
    parse_wasm(sys.argv[1])
