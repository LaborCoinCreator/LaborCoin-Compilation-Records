"""Small dependency-free Ethereum Keccak-256 implementation."""
MASK=(1<<64)-1
ROT=(
  0, 1,62,28,27,
 36,44, 6,55,20,
  3,10,43,25,39,
 41,45,15,21, 8,
 18, 2,61,56,14,
)
RC=(
0x0000000000000001,0x0000000000008082,0x800000000000808A,0x8000000080008000,
0x000000000000808B,0x0000000080000001,0x8000000080008081,0x8000000000008009,
0x000000000000008A,0x0000000000000088,0x0000000080008009,0x000000008000000A,
0x000000008000808B,0x800000000000008B,0x8000000000008089,0x8000000000008003,
0x8000000000008002,0x8000000000000080,0x000000000000800A,0x800000008000000A,
0x8000000080008081,0x8000000000008080,0x0000000080000001,0x8000000080008008)

def _rol(x,n):
    if n==0:return x&MASK
    return ((x<<n)|(x>>(64-n)))&MASK

def _permute(a):
    for rc in RC:
        c=[a[x]^a[x+5]^a[x+10]^a[x+15]^a[x+20] for x in range(5)]
        d=[c[(x-1)%5]^_rol(c[(x+1)%5],1) for x in range(5)]
        for y in range(5):
            for x in range(5):a[x+5*y]^=d[x]
        b=[0]*25
        for y in range(5):
            for x in range(5):
                b[y+5*((2*x+3*y)%5)]=_rol(a[x+5*y],ROT[x+5*y])
        for y in range(5):
            row=b[5*y:5*y+5]
            for x in range(5):a[x+5*y]=row[x]^((~row[(x+1)%5])&row[(x+2)%5])
        a[0]^=rc

def keccak256(data:bytes)->bytes:
    rate=136
    padded=bytearray(data)
    padded.append(0x01)
    while len(padded)%rate != rate-1:padded.append(0)
    padded.append(0x80)
    state=[0]*25
    for off in range(0,len(padded),rate):
        block=padded[off:off+rate]
        for i in range(rate//8):state[i]^=int.from_bytes(block[8*i:8*i+8],'little')
        _permute(state)
    out=bytearray()
    while len(out)<32:
        for i in range(rate//8):
            out.extend(state[i].to_bytes(8,'little'))
            if len(out)>=32:return bytes(out[:32])
        _permute(state)
    return bytes(out[:32])

def keccak256_hex(data:bytes)->str:return '0x'+keccak256(data).hex()
