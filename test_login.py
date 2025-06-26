import requests
import json

# Login endpoint
login_url = "http://localhost:8081/api/v1/auth/auth/login"

# Login data
login_data = {
    "username": "test@example.com",
    "password": "testpass123"
}

# Make the login request
response = requests.post(login_url, data=login_data)

# Print the response
print("Status Code:", response.status_code)
print("Response Body:", response.text)

# If successful, save the token
if response.status_code == 200:
    token_data = response.json()
    print("\nAccess Token:", token_data.get("access_token")) 