import requests

# Step 1: Login to get a fresh access token
login_url = "http://localhost:8081/api/v1/auth/auth/login"
login_data = {
    "username": "test@example.com",
    "password": "testpass123"
}
login_response = requests.post(login_url, data=login_data)

if login_response.status_code != 200:
    print("Login failed:", login_response.text)
    exit(1)

access_token = login_response.json().get("access_token")
print("Access Token:", access_token)

# Step 2: Use the token to fetch activities list (with trailing slash)
activities_url = "http://localhost:8081/api/v1/activities/activities/"
headers = {
    "Authorization": f"Bearer {access_token}"
}

response = requests.get(activities_url, headers=headers)

print("Status Code:", response.status_code)
print("Response Body:", response.text) 