import os
import random
from urllib.parse import urlencode

import requests


class tiktokGnome:
    """TikTok OAuth and content posting helper aligned with the official docs."""

    AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
    OAUTH_TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
    UPLOAD_URL = "https://open.tiktokapis.com/v2/video/upload/"
    PUBLISH_URL = "https://open.tiktokapis.com/v2/video/publish/"

    def __init__(
        self,
        id=0,
        env_handler=None,
        git_handler=None,
        lock=None,
        client_id=None,
        client_secret=None,
        redirect_uri=None,
        scope="user.info.basic,video.upload,video.publish",
        state=None,
    ):
        self.id = id + 1  # So the first Gnome is not 0 but 1
        self.env_handler = env_handler
        self.git_handler = git_handler
        self.git_lock = lock

        self.client_id = client_id or self._get_env_value("TIKTOK_CLIENT_KEY")
        self.client_secret = client_secret or self._get_env_value("TIKTOK_CLIENT_SECRET")
        self.redirect_uri = redirect_uri or self._get_env_value(
            "TIKTOK_REDIRECT_URI",
            "http://localhost:3000/auth/callback",
        )
        self.scope = scope
        self.state = state or self._generate_random_string(16)

        self.CAPTION = ""
        self.IMAGE_URL_LOCAL = None

    def _get_env_value(self, key, default=None):
        if self.env_handler is not None:
            value = self.env_handler.get(key)
            if value is not None:
                return value
        return os.getenv(key, default)

    def _generate_random_string(self, length=16):
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
        return "".join(random.choice(chars) for _ in range(length))

    def build_auth_url(self):
        if not self.client_id:
            raise ValueError("TIKTOK_CLIENT_KEY is not configured")

        params = {
            "client_key": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": self.scope,
            "state": self.state,
        }
        return f"{self.AUTH_URL}?{urlencode(params)}"

    def exchange_code_for_token(self, auth_code):
        if not self.client_id or not self.client_secret:
            raise ValueError("TIKTOK_CLIENT_KEY or TIKTOK_CLIENT_SECRET is not configured")

        payload = {
            "client_key": self.client_id,
            "client_secret": self.client_secret,
            "code": auth_code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
        }
        response = requests.post(self.OAUTH_TOKEN_URL, data=payload, timeout=60)
        response.raise_for_status()

        data = response.json()
        return data.get("data", {}).get("access_token") or data.get("access_token")

    def upload_video(self, video_path, access_token, caption=""):
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        with open(video_path, "rb") as video_file:
            files = {"video": (os.path.basename(video_path), video_file, "video/mp4")}
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.post(self.UPLOAD_URL, headers=headers, files=files, timeout=120)
            response.raise_for_status()

        payload = response.json()
        return payload.get("data", {}).get("video_id") or payload.get("video_id")

    def publish_video(self, video_id, access_token, caption=""):
        payload = {
            "video_id": video_id,
            "description": caption or self.CAPTION,
        }
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.post(self.PUBLISH_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()

    def post_video(self, video_path, access_token, caption=""):
        video_id = self.upload_video(video_path, access_token, caption=caption)
        return self.publish_video(video_id, access_token, caption=caption)

    def setupPost(self, caption, img_path):
        self.CAPTION = caption
        self.IMAGE_URL_LOCAL = img_path
        return {"caption": caption, "img_path": img_path}


TikTokPoster = tiktokGnome
