from Crypto.PublicKey import RSA
    
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256

# Generate RSA key pair
key = RSA.generate(1024)
private_key = key
public_key = key.publickey()

# Message to sign
message = b"Hello, this is a message to sign!"

# Create a SHA256 hash of the message
hash_obj = SHA256.new(message)

# Sign the message with the private key
signature = pkcs1_15.new(private_key).sign(hash_obj)

# Verify the signature with the public key
try:
    pkcs1_15.new(public_key).verify(hash_obj, signature)
    print("Signature is valid.")
except (ValueError, TypeError):
    print("Signature is invalid.")

# Save keys and signature (optional)
with open("rsa_private.pem", "wb") as f:
    f.write(private_key.export_key())
with open("rsa_public.pem", "wb") as f:
    f.write(public_key.export_key())
with open("signature.bin", "wb") as f:
    f.write(signature)