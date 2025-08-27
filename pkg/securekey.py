import secrets

secret = secrets.token_hex(32)
# Generate a random secret key for security purposes
print("Generated secret key:", secret)