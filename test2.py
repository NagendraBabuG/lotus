from Crypto.PublicKey.RSA import generate
print(generate(1024))

from Crypto.PublicKey import RSA
keyGenerator = RSA.generate
print(RSA.generate(1024))
print(keyGenerator(1024))

import Crypto.PublicKey.RSA as Encryptor
print(Encryptor.generate(1024))

import Crypto.PublicKey.RSA;
print(Crypto.PublicKey.RSA.generate(1024))


import Crypto.PublicKey.RSA as Assym    
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256

# Generate RSA key pair
key = Assym.generate(1024)
private_key = key
public_key = key.publickey()
