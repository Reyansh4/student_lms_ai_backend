import jwt

# Paste the latest token here
access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiZXhwIjoxNzQ4MzYxMTU1fQ.nV7aRDbBpMCZk70WzBBywBq8nnk2pbtTTqaKuiueA5M"

# Use the same secret and algorithm as your backend
secret = "JohnDoe"
algorithm = "HS256"

try:
    payload = jwt.decode(access_token, secret, algorithms=[algorithm])
    print("Decoded payload:", payload)
except Exception as e:
    print("Failed to decode token:", e) 