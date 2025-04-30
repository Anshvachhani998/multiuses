from google_auth_oauthlib.flow import InstalledAppFlow
import pickle

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)

# Get the authorization URL
auth_url, _ = flow.authorization_url()

print("Please go to this URL and authorize the application:")
print(auth_url)

# After the user authorizes, they will receive a code to enter
code = input("Enter the authorization code: ")

# Use the code to fetch the credentials
creds = flow.fetch_token(authorization_response=code)

# Save the credentials
with open('token.pickle', 'wb') as token:
    pickle.dump(creds, token)

print("✅ Token saved as token.pickle")
