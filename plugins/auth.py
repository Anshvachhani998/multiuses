from google_auth_oauthlib.flow import InstalledAppFlow
import pickle

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)

# Old (causing error)
# creds = flow.run_local_server(port=0)

# ✅ New (Console-based, CLI-safe)
creds = flow.run_console()

with open("token.pickle", "wb") as token:
    pickle.dump(creds, token)

print("✅ Token saved as token.pickle")

