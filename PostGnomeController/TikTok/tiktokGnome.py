import logging
import requests
import time

class tiktokGnome:
    def __init__(self, id, env_handler, git_handler, lock):
        self.id = id + 1 #So the first Gnome is not 0 but 1
        self.env_handler = env_handler
        self.git_handler = git_handler
        self.git_lock = lock #Lock for synchronizing Git operations across threads
        
    def setAT(self, access_token):
        self.access_token = access_token
        
    def setupPost(self, title, cap, mpath):
        self.title = title
        self.caption = cap
        self.mpath = mpath
    
    #Builds the url with the headers and data-raw part
    def build_post_url(self, title, cap, opt_priv):
        base_url = "https://open.tiktokapis.com/v2/post/publish/video/init/"
        
    
    #Posting function called by PGC
    def post(self, account, title, cap, mtype, utype, mpath, opt_priv, opt_dc):
        logging.info("TT_GNOME "+ str(self.id) + ": started posting process...")
        
        
    #actually post from a file
    def postFromFile(self, mpath, url):
        pass
    
    #actually post from a url
    def postFromUrl(self, mpath, url):
        pass