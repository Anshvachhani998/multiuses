import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from pyrogram import Client, filters
# Scopes and file
SCOPES = ['https://www.googleapis.com/auth/drive.file']
CLIENT_SECRET_FILE = 'plugins/credentials.json'

def generate_auth_url():
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
    flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'  # 🔥 FIXED!
    auth_url, _ = flow.authorization_url(prompt='consent')
    return auth_url


def get_token_from_code(code):
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
    flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'  # 🔥 FIXED!
    flow.fetch_token(code=code)
    creds = flow.credentials
    with open("plugins/token.pickle", "wb") as token:
        pickle.dump(creds, token)
    return True

@Client.on_message(filters.command("gdrive"))
async def send_auth_url(client, message):
    url = generate_auth_url()
    await message.reply(
        f"🔐 Visit this link to authorize:\n\n{url}\n\nThen send the code like this:\n/gcode <your-code>",
        quote=True,
        parse_mode=None)


@Client.on_message(filters.command("gcode"))
async def handle_code(client, message):
    try:
        code = message.text.split(" ", 1)[1]
    except IndexError:
        await message.reply("❌ Please provide the code.\nExample: `/gcode ABC1234xyz`", quote=True)
        return

    try:
        get_token_from_code(code)
        await message.reply("✅ Successfully authenticated and saved token!", quote=True)
    except Exception as e:
        await message.reply(f"❌ Failed to authenticate.\nError: `{e}`", quote=True)
