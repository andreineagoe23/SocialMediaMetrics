import requests

CLIENT_ID = 'XYwStgEAHmv6YEKNVi'
CLIENT_SECRET = 'vNs330TXKVv2Bhs4WvaY0BpgxsTIIEmV'
REDIRECT_URI = 'https://www.brixtonradio.com/'
AUTHORIZATION_CODE = 'ljgDfBuJGm'

# Prepare the data
data = {
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'redirect_uri': REDIRECT_URI,
    'code': AUTHORIZATION_CODE,
    'grant_type': 'authorization_code',
}

response = requests.post('https://api.mixcloud.com/oauth/access_token', data=data)

# Check the response
if response.status_code == 200:
    access_token = response.json().get('access_token')
    print("Access Token:", access_token)
else:
    print("Error:", response.status_code, response.text)
