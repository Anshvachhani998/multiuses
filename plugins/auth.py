from google_auth_oauthlib.flow import InstalledAppFlow

# Replace with your own credentials file path
CLIENT_SECRET_FILE = 'credentials.json'

# Define the API scopes you need
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Create the flow using the credentials
flow = InstalledAppFlow.from_client_secrets_file(
    CLIENT_SECRET_FILE, SCOPES)

# Run the local server to authorize
creds = flow.run_local_server(port=0)

# Save the credentials for later use
with open('token.pickle', 'wb') as token:
    pickle.dump(creds, token)

print("Authentication successful!")
