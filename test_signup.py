import requests
import json

# Signup endpoint
signup_url = "http://localhost:8081/api/v1/auth/auth/signup"

# Signup data
signup_data = {
    "email": "test@example.com",
    "name": "Test User",
    "password": "testpass123",
    "phone": "1234567890",
    "city": "Test City",
    "country": "Test Country"
}

# Make the signup request
response = requests.post(signup_url, json=signup_data)

# Print the response
print("Status Code:", response.status_code)
print("Response Body:", response.text) 