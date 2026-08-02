import requests
from utils.env_handler import EnvHandler
import random

#Create Vars
CLIENT_ID = ""
CLIENT_SECRET = ""
REDIRECT_URL ="http://localhost:3000/auth/callback"
AUTHORIZE_URL ="https://www.tiktok.com/v2/auth/authorize/"

#Obtain authorizing things


#Query the creators latest info to initiate direct post to a creators account
url = "https://open.tiktokapis.com/v2/post/publish/creator_info/query/"
response = requests.post(url, )


def generateRandomString(length):
    chars ="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
    result =''.join(random.choice(chars) for _ in range(length))
    return result