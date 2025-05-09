from google_auth_oauthlib.flow import InstalledAppFlow

# Replace with your own credentials file path
CLIENT_SECRET_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/drive.file']

flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)

# Run the console flow, it will give a URL to visit
creds = flow.run_console()

# Save the credentials for later use
with open('token.pickle', 'wb') as token:
    pickle.dump(creds, token)

print("Authentication successful!")
