import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
auth_url, _ = flow.authorization_url(prompt='consent')

print("Please go to this URL and authorize the app:\n", auth_url)
code = input("Enter the authorization code here: ")

flow.fetch_token(code=code)
creds = flow.credentials

with open("token.pickle", "wb") as token:
    pickle.dump(creds, token)

print("✅ Token saved as token.pickle")
