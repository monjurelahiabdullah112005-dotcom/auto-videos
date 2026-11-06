import os
import requests


def upload_youtube(title, desc, tags):
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    creds = Credentials(None, refresh_token=os.environ["YT_REFRESH_TOKEN"],
                        token_uri="https://oauth2.googleapis.com/token",
                        client_id=os.environ["YT_CLIENT_ID"],
                        client_secret=os.environ["YT_CLIENT_SECRET"])
    yt = build("youtube", "v3", credentials=creds)
    body = {"snippet": {"title": title[:90] + " #Shorts", "description": desc,
                        "tags": tags, "categoryId": "17"},
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}}
    media = MediaFileUpload("final.mp4", mimetype="video/mp4", resumable=True)
    res = yt.videos().insert(part="snippet,status", body=body, media_body=media).execute()
    print("YouTube done:", res.get("id"))


def upload_facebook(title, desc):
    pid = os.environ["FB_PAGE_ID"]
    with open("final.mp4", "rb") as f:
        r = requests.post(f"https://graph.facebook.com/v21.0/{pid}/videos",
                          data={"access_token": os.environ["FB_PAGE_TOKEN"],
                                "title": title, "description": desc},
                          files={"source": f}, timeout=900)
    print("Facebook:", r.text)
