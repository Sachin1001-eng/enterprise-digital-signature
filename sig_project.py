from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

print("--- DIGITAL SIGNATURE SYSTEM INITIALIZED ---")

# 1. Key Generation
print("\n[1] Generating RSA Key Pair (Private & Public Keys)...")
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_key = private_key.public_key()
print("-> Key pair generated successfully.")

# 2. Original Message / Document
message = b"Confidential Document: Project Report Data 2026."
print(f"\n[2] Original Message: {message.decode()}")

# 3. Signing the Message
print("\n[3] Signing the message using the Private Key...")
signature = private_key.sign(
    message,
    padding.PSS(
        mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
    ),
    hashes.SHA256(),
)
print(f"-> Signature Generated (Hex): {signature.hex()[:50]}...")

# 4. Verifying the Signature with Authentic Data
print("\n[4] Verifying signature with the authentic message...")
try:
  public_key.verify(
      signature,
      message,
      padding.PSS(
          mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
      ),
      hashes.SHA256(),
  )
  print(
      "-> SUCCESS: Signature is VALID! The document is authentic and"
      " unmodified."
  )
except InvalidSignature:
  print("-> FAILED: Signature verification failed!")

# 5. Tampering Test
print("\n[5] Tampering Test: Simulating an unauthorized modification...")
tampered_message = (
    b"Confidential Document: Project Report Data 2026. [MODIFIED]"
)
print(f"Modified Message: {tampered_message.decode()}")

try:
  public_key.verify(
      signature,
      tampered_message,
      padding.PSS(
          mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
      ),
      hashes.SHA256(),
  )
  print("-> SUCCESS: (This should not appear)")
except InvalidSignature:
  print(
      "-> ALERT: TAMPERING DETECTED! The message was modified, so the signature"
      " is invalid."
  )

print("\n--- DIGITAL SIGNATURE DEMO COMPLETED ---")