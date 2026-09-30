#Stop the freeze breeze with threading. Each PostGnome has its own thread
import threading

#import the GNOMESS
import PostGnomeController.Instagram.instaGnome as instaGnome
import PostGnomeController.TikTok.tiktokGnome as tiktokGnome

#import env and git handler so we can create one instance for one thread
from utils.env_handler import EnvHandler
from utils.git_handler import GitHandler

#Logging imports
import logging

class postGnomeController:
    def __init__(self):
        self.git_lock = threading.Lock() #Lock for synchronizing access to Git functions (maybe helps the threads to run parallel)
        self.env_handlers = []
        self.git_handlers = []
        self.threads = []
        self.thread_status = {} #Dictionary to keep track of thread statuses, e.g., {thread_id: "running" or "finished"}
        
        '''
        Quick note for the statuses and later representation in UI:
        "0" = waiting;  "."
        "1" = running;  "~"
        "2" = finished; "✔"
        "3" = error;    "✖"
        '''
    #Creates the Gnome that executes the posting process for Instagram
    def postingGnomeInsta(self, number, account, envH, gitH, cap, media, mtype, location):
        self.thread_status[number] = "1" # Set status to running
        gnome = instaGnome.instaGnome(number, envH, gitH, self.git_lock) #Give the lock as parameter so every
        try:
            gnome.post(account, cap, media, mtype, location)
            self.thread_status[number] = "2" #Status finished after post is done
        except Exception as e:
            logging.error(f"PGCtr: Error in thread {number} for account {account}: {e}")
            self.thread_status[number] = "3" #Status error if an exception occurs
        
        
    #Called by UI to start the multiposting process for Instagram, creates threads for each posting gnome
    def multipost_instagram(self, accounts, cap, media, mtype, location):
        #numerate accs in list and setup new instances of env and git handler for the gnome
        for idx, acc in enumerate(accounts):
            env_handler = EnvHandler(".env_program/settings.env")
            if env_handler is not None:
                env_handler.load(".env_program/git.env")  # Ensure the environment is loaded before initializing GitHandler
            else:
                logging.error("PGCtr: EnvHandler is not initialized before GitHandler!")
                raise RuntimeError("EnvHandler must be initialized before GitHandler.")
        
            git_handler = GitHandler(
                env_handler.get("GIT_USERNAME"),
                env_handler.get("GIT_EMAIL"),
                env_handler.get("REPO_PATH")
            )
            self.env_handlers.append(env_handler)
            self.git_handlers.append(git_handler)
            
            #Set thread status
            self.thread_status[idx] = "0" # waiting
            
            #Create and start the thread
            t = threading.Thread(
                target=self.postingGnomeInsta,
                args=(idx, acc, env_handler, git_handler, cap, media, mtype, location)
            )
            t.start()
            self.threads.append(t)
            logging.info(f"PGCtr: Started thread {idx} for account {acc}")

    def postingGnomeTikTok(self, number, account, envH, gitH, title, cap, mtype, utype, mpath, opt_priv, opt_dc):
        self.thread_status[number] = "1" # Set status to running
        gnome = tiktokGnome.tiktokGnome(number, envH, gitH, self.git_lock) #Give the lock as parameter so every
        try:
            gnome.post(account, title, cap, mtype, utype, mpath, opt_priv, opt_dc)
            self.thread_status[number] = "2" #Status finished after post is done
        except Exception as e:
            logging.error(f"PGCtr: Error in thread {number} for account {account}: {e}")
            self.thread_status[number] = "3" #Status error if an exception occurs

    def multipost_tiktok(self, accounts, mtype, utype, mpath, title, cap, opt_dc):
        #numerate accs in list and setup new instances of env and git handler for the gnome
        for idx, acc in enumerate(accounts):
            env_handler = EnvHandler(".env_program/settings.env")
            if env_handler is not None:
                env_handler.load(".env_program/git.env")  # Ensure the environment is loaded before initializing GitHandler
            else:
                logging.error("PGCtr: EnvHandler is not initialized before GitHandler!")
                raise RuntimeError("EnvHandler must be initialized before GitHandler.")
        
            git_handler = GitHandler(
                env_handler.get("GIT_USERNAME"),
                env_handler.get("GIT_EMAIL"),
                env_handler.get("REPO_PATH")
            )
            self.env_handlers.append(env_handler)
            self.git_handlers.append(git_handler)
            
            #Set thread status
            self.thread_status[idx] = "0" # waiting
            
            #Create and start the thread
            t = threading.Thread(
                target=self.postingGnomeInsta,
                args=(idx, acc, env_handler, git_handler, title, cap, mtype, utype, mpath, opt_dc)
            )
            t.start()
            self.threads.append(t)
            logging.info(f"PGCtr: Started thread {idx} for account {acc}")

    #Returns true or false wether there are still threads running, must be called by UI main window
    #tk_root is needed so we can update UI and the checking interval is in ms
    def wait_for_threads(self, callback=None, interval = 500, tk_root=None):
        alive = any(t.is_alive() for t in self.threads)
        if alive: # Will be true if any thread is alive
            if tk_root:
                tk_root.after(interval, lambda: self.wait_for_threads(interval, tk_root)) # Check again after the specified interval
        else:
            logging.info("PGCtr: All threads have finished.")
            #Save Clear all the handlers and threads
            self.env_handlers.clear()
            self.git_handlers.clear()
            self.threads.clear()
            if callback:
                callback() # Call the callback function if provided
            