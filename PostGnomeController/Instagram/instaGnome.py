import logging
import os
import shutil
import requests
import time

#Gnome Class that will exist inside each thread and executes the actual posting
class instaGnome:
    def __init__(self, id, env_handler, git_handler, lock):
        self.id = id + 1 #So the first Gnome is not 0 but 1
        self.env_handler = env_handler
        self.git_handler = git_handler
        self.git_lock = lock #Lock for synchronizing Git operations across threads

    ##Tool functions
    #Sets Picture related variables
    def setupPost(self, caption, img_path):
        self.CAPTION = caption
        self.IMAGE_URL_LOCAL = img_path

    #Set ig_id
    def setIG_ID(self, ig_id):
        self.ig_id = ig_id
    
    #Set access token
    def setAT(self, access_token):
        self.access_token = access_token

    #This Function will mvoe the picture from the UI into the git and creates (maybe return) the rawgithubusercontent link
    def uploadPicture2Git(self, filepath):
        with self.git_lock:
            self.IMAGE_URL_LOCAL = filepath
            
            #Repo Config
            self.env_handler.load(".env_program/git.env")  # Ensure the environment is loaded before initializing GitHandler
            repo_path = self.env_handler.get("REPO_PATH")
            git_username = self.env_handler.get("GIT_USERNAME")
            git_email = self.env_handler.get("GIT_EMAIL")
            filename = os.path.basename(self.IMAGE_URL_LOCAL)
            
            #Debug Message
            logging.info("IG_Gnome "+ str(self.id) + f" Loaded Values from git.env - Repo: {repo_path}, User: {git_username}, Email: {git_email}, Filename: {filename}")
            #Branch Selection not added yet
            #branch = "main"  # Default branch, can be changed if needed -> There will be an Option in UI later on

            if not repo_path or not git_username or not git_email:
                logging.error("IG_Gnome "+ str(self.id) + " REPO_PATH, GIT_USERNAME or GIT_EMAIL not found in environment variables.")
                raise ValueError("REPO_PATH, GIT_USERNAME or GIT_EMAIL not found!")
            
            #Create Target Path and copy the image into the repo
            target_path = os.path.join(repo_path, filename)
            shutil.copy2(self.IMAGE_URL_LOCAL, target_path)

            #Use Githandler Instance
            self.git_handler.set_repo_path(repo_path)
            self.git_handler.set_git_username(git_username)
            self.git_handler.set_git_email(git_email)
            self.git_handler.set_git_config() #Must be run in order to update the repo_config in git

            #Ceckout main branch or else it will be inconsistend and will not work
            self.git_handler.checkout_branch("main")

            #File should already be copied to destination
            #Add all changes, commit and push to main - Branch selection not added yet
            self.git_handler.add_all_changes()
            self.git_handler.commit_changes(f"Add image for Instagram post: {filename}")
            self.git_handler.push_changes("main")

            logging.info("IG_Gnome "+ str(self.id) + " Picture moved to Repo and pushed!")

            #Create and get Rawlink to save
            self.raw_url = self.git_handler.get_raw_url(filename)
            self.GIT_URL = self.raw_url

            #Debug Message
            self.git_handler.dump_git_status()  # Optional: Dump git status for debugging
            logging.info("IG_Gnome "+ str(self.id) + f" Uploaded Picture to Git, Raw-Link: {self.raw_url}")

    #Creates the Upload Url
    def create_Up_URL(self, media_type):
        #Create Upload Url
        url = f"https://graph.instagram.com/v24.0/{self.ig_id}/media"
        if media_type == "image":
            logging.info("IG_Gnome "+ str(self.id) + " Creating upload URL for image...")
            params = {
                "image_url": self.GIT_URL,
                "caption": self.CAPTION,
                "access_token": self.access_token
            }
        elif media_type == "video":
            logging.info("IG_Gnome "+ str(self.id) + " Creating upload URL for video...")
            params = {
                "media_type": "REELS",
                "share_to_feed": "true",
                "video_url": self.GIT_URL,
                "caption": self.CAPTION,
                "access_token": self.access_token
            }
        else:
            logging.error("IG_Gnome "+ str(self.id) + " Invalid media type specified for upload URL creation.")
            raise ValueError("Invalid media type specified. Must be 'image' or 'video'.")
        
        #Create Response returns the IG_ID
        response = requests.post(url, params=params, timeout=30)
        if response.status_code != 200:
            logging.error("IG_Gnome "+ str(self.id) + f" Error creating upload URL: {response.text}")
            raise Exception(f"Error creating upload URL: {response.text}")
        
        #Get Data from response json
        container_id = response.json().get("id")
        container_uri = response.json().get("uri")
        logging.info("IG_Gnome "+ str(self.id) + f" Created upload URL successfully. Media ID: {container_id}, URI: {container_uri}")
        return container_id, container_uri
    
    #Insert Logging operations here
    def wait_for_media_ready(self, creation_id, timeout=120, poll_interval=5):
        url = f"https://graph.instagram.com/v24.0/{creation_id}"
        params = {
            "fields": "status_code",
            "access_token": self.access_token
        }
        logging.info("IG_Gnome "+ str(self.id) + " Waiting for media to be ready...")
        #Wait until Finished or timeout
        waited = 0
        while waited < timeout:
            response = requests.get(url, params=params, timeout=30)
            data = response.json()
            status = data.get("status_code")
            if status == "FINISHED":
                return True
            elif status == "ERROR":
                logging.error("IG_Gnome "+ str(self.id) + " Media processing error.")
                raise Exception("Media processing error.")
            time.sleep(poll_interval)
            waited += poll_interval
        raise TimeoutError("Media was not ready after waiting. Media Upload may take longer or failed.")

    def postPicOnInstagram(self):
        #Prepare Upload and get media ID; media uri not needed for pictures
        container_id, conatiner_uri = self.create_Up_URL("image")
        if not container_id:
            logging.error("IG_Gnome "+ str(self.id) + " Got no Media-ID, Abortion.")
            return False

        #Status checkup
        try:
            self.wait_for_media_ready(container_id)
        except Exception as e:
            logging.error(f"Error at status checkup: {e}")
            return False

        #Publish Media
        publish_url = f"https://graph.instagram.com/v24.0/{self.ig_id}/media_publish"
        params = {
            "creation_id": container_id,
            "access_token": self.access_token
        }
        response = requests.post(publish_url, params=params, timeout=30)
        if response.status_code != 200:
            logging.error("IG_Gnome "+ str(self.id) + f" Error publishing: {response.text}")
            raise Exception(f"Error publishing: {response.text}")

        logging.info("IG_Gnome "+ str(self.id) + f" Post published successfully! (Picture) Response: {response.json()}")
        return response.json()
    
    def postReelOnInstagram(self):
        #Create Container with create_up_url ## Container_uri only needed for resumable sessions
        container_id, container_uri = self.create_Up_URL("video")
        if not container_id: #CONTAINER_URI ONLY NEEDED FOR RESUMABLE SESSION
            logging.error("IG_Gnome "+ str(self.id) + " Got no Media-ID or URI, Abortion.")
            return False
        
        #Status checkup
        try:
            self.wait_for_media_ready(container_id)
        except Exception as e:
            logging.error(f"Error at status checkup: {e}")
            return False
        
        #Publish the Reel
        publish_url = f"https://graph.instagram.com/v24.0/{self.ig_id}/media_publish"
        params = {
            "creation_id": container_id,
            "access_token": self.access_token
        }
        response = requests.post(publish_url, params=params, timeout=30)
        if response.status_code != 200:
            logging.error("IG_Gnome "+ str(self.id) + f" Error publishing: {response.text}")
            raise Exception(f"Error publishing: {response.text}")

        logging.info("IG_Gnome "+ str(self.id) + f" Reel published successfully! Response: {response.json()}")
        return response.json()

    def post(self, account, cap, media, mtype, location):
        #Posting Logic here, with use of account info etc
        logging.info("IG_Gnome "+ str(self.id) + ": Posting to Instagram account: " + str(account) + " started!")
        
        logging.info("IG_Gnome "+ str(self.id) + ": Checking posting information...")
        
        #Check cap and media
        if not cap or not media:
            logging.error("UI: Caption or Image path is empty.")
            #Fix: Create pop-up maybe with error message
            #tk.Label(self.content_frame, text="Please fill in both fields.", fg="red").pack(pady=5)
            return
        
        #Check media type
        if mtype == "image":
            if not media.lower().endswith(('.jpg', '.jpeg')):
                #Fix the same as above with pop-up
                #tk.Label(self.content_frame, text="Please select a picture that is a .jpg or .jpeg!", fg="red").pack(pady=5)
                logging.error("IG_Gnome "+ str(self.id) + ": Selected media is not a valid image file.")
                return
        elif mtype == "video":
            if not media.lower().endswith((".mp4", ".mov")):
                #Same as above again with pop-up
                #tk.Label(self.content_frame, text="Please select a video, that is a .mp4 or .mov!", fg="red").pack(pady=5)
                logging.error("IG_Gnome "+ str(self.id) + ": Selected media is not a valid video file.")
                return
        
        #Check if a valid account was given
        if not account:
            logging.warning("IG_Gnome "+ str(self.id) + f": No Accounts selected!")
            return
        
        logging.info("IG_Gnome "+ str(self.id) + f": Posting information: '{media}' with cap '{cap}' on account '{account["username"]}'. Starting posting process...")
        
        #Actual posting logic here; no posting loop needed because one gnome only posts for one account (in a thread)
        self.setIG_ID(account["IG_ID"])
        self.setAT(account["token"])
        self.uploadPicture2Git(location)
        self.setupPost(cap, media)
        if mtype == "image":
            self.postPicOnInstagram()
        elif mtype == "video":
            self.postReelOnInstagram()
            
        logging.info("IG_Gnome "+ str(self.id) + ": Posting process finished!")