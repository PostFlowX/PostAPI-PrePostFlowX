from sqlite3 import PARSE_DECLTYPES
import tkinter as tk
from tkinter import ttk
import logging
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
#from numpy import character
from matplotlib import widgets
import requests
import hashlib
import random
import secrets
from typing import Optional
from urllib.parse import parse_qs, urlparse, urlencode
import json
import os
from tkinter import filedialog
from requests.models import ContentDecodingError
from tkcalendar import DateEntry
from datetime import datetime, timedelta

#Temp
CLIENT_SECRET = "Qqz48I5fgxcBBPcOOHgAwXn0oIHLWlaZ"
CLIENT_KEY = "sbawd5m0bxhlr0t24v"
REDIRECT_URI = "http://localhost:3000/auth/callback"


class TTCallbackServer(ThreadingHTTPServer):
    def __init__(self, server_address, handler_cls):
        super().__init__(server_address, handler_cls)
        self.backend: Optional["tt_UI_backend"] = None

class tt_UI_backend:
    def __init__(self, controller, ui):
        self.controller = controller
        self.ui = ui
        self.selected_accounts = []
        self.accounts = []
        self.username = None
        self.auth_code = None
        self.code_verifier = None
        self.auth_error = None
        self.state = None
        self.httpd = None

    def update_selected_accounts_label(self):
        if not self.selected_accounts:
            self.ui.selected_accounts_tt_var.set("None")
            #Debug Message
            logging.info("TT_BE: No accounts selected to display into selected_accounts_label")
        else:
            names = [acc["username"] for acc in self.selected_accounts]
            self.ui.selected_accounts_tt_var.set(", ".join(names))
            #Debug Message
            logging.info(f"TT_BE: Updated selected accounts label: {self.ui.selected_accounts_tt_var.get()}")


    def open_acount_selection(self):
        #Check if accounts are loaded
        if not self.accounts:
            logging.error("TT_BE: No accounts to select.")
            return
        
        #Toplayer window
        win = tk.Toplevel(self.ui)
        win.title("Select Accounts")
        win.geometry("600x500")
        
        logging.info("TT_BE_TL1: Opened Select Account Window")
        
        tk.Label(win, text="Select Accounts to Post", font=("Arial", 14)).pack(pady=10)
        
        # Dictionary for Checkboxes
        self.account_vars = {}
        for acc in self.accounts:
            var = tk.BooleanVar()
            cb = tk.Checkbutton(win, text=acc.get("username", "Unknown"), variable=var)
            cb.pack(anchor="w")
            self.account_vars[acc.get("username")] = var
        
        def save_selection():
            self.selected_accounts = [
                acc for acc in self.accounts
                if self.account_vars.get(acc["username"], None) and self.account_vars[acc["username"]].get()
            ]
            win.destroy()
            self.update_selected_accounts_label()
            logging.info(f"TT_BE_TL1: Selected accounts for posting: {self.selected_accounts}")
        
        #Save Button
        tk.Button(win, text="Save", command=save_selection).pack(pady=20)
        
        #Debug Message
        logging.info("TT_BE_TL1: Select Accounts Window finished and Accounts Selected")
        

    def browse_image_file(self):
            media_type = self.ui.tt_media_type.get() if hasattr(self.ui, "tt_media_type") else "video"
            if media_type == "photos":
                filetypes = [("Image files", "*.jpg *.jpeg")]
            elif media_type == "video":
                filetypes = [("Video files", "*.mp4 *.mov")]
            else:
                filetypes = [("All files", "*.*")]
            filename = filedialog.askopenfilename(title="Select File", filetypes=filetypes)
            if filename:
                self.ui.tt_media_path.set(filename)

    def update_tt_media_input(self):
        if self.ui.tt_upload_type.get() == "url":
            self.ui.frame_fileFrame.pack_forget()
            self.ui.frame_urlFrame.pack(pady=5)
        else:
            self.ui.frame_urlFrame.pack_forget()
            self.ui.frame_fileFrame.pack(pady=5)

    def update_tt_CapBox(self):
        if self.ui.tt_media_type.get() == "video":
            self.ui.frame_caption.pack_forget()
        else:
            self.ui.frame_caption.pack(pady=5)


    def _generate_code_verifier(self):
        characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~'
        result = ""
        for _ in range(len(characters)):
            result += random.choice(characters)
        logging.info(f"TT_BE: Code Verifier: {result}")
        return result

    def _compute_code_challenge(self, verifier):
        hexdigest = hashlib.sha256(verifier.encode()).hexdigest()
        logging.info(f"TT_BE: Code Challenge: {hexdigest}")
        return hexdigest

    def add_account(self):
        win = tk.Toplevel(self.ui)
        win.title("Add Account")
        win.geometry("600x500")

        content_frame = tk.Frame(win)
        content_frame.pack(pady=5, padx=5)
        
        tk.Label(content_frame, text="Add TikTok Account", font=("Arial", 14)).pack(pady=10)
        
        tk.Label(content_frame, text="Username:").pack()
        username_entry = tk.Entry(content_frame, width=30)
        username_entry.pack(pady=5, fill="x", expand=True)
        
        tk.Label(content_frame, text="Please log in in the browser window.", font=("Arial", 11)).pack(pady=10)

        logging.info("TT_BE: Opened Add Account Window")
        
        self.winCache = win
        
        def saveUsername():
            self.username = username_entry.get().strip()
            logging.info("Username saved")
        
        tk.Button(content_frame, text="Save Username", command=saveUsername).pack()
        tk.Button(win, text="Add Account via Browser", command=self.start_oauth_flow).pack()
        

    def start_oauth_flow(self, winPara=None):
        #This sets the standard value for the win since i cannot give the parameter via Button i need to do it like that
        if winPara == None:
            winPara = self.winCache
        self.auth_code = None
        self.auth_error = None
        self.state = secrets.token_urlsafe(16)

        self.code_verifier = self._generate_code_verifier()
        self.code_challenge = self._compute_code_challenge(self.code_verifier)

        logging.info("TT_BE: Started OAuth Flow")

        try:
            self.start_callback_server()
        except OSError as exc:
            logging.error(f"TT_BE: Failed to start callback server! Error: {exc}")
            winPara.destroy()
            return

        auth_url = self.build_auth_url()
        webbrowser.open(auth_url)

        self.watch_for_auth(winPara)

    def build_auth_url(self):
        client_key =  CLIENT_KEY
        redirect_uri = REDIRECT_URI
        scope = "user.info.basic,video.upload,video.publish"

        if not client_key:
            raise ValueError("TikTok Client Key is missing")

        logging.info("TT_BE: Started building the auth url")

        params = {
            "client_key": client_key,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": scope,
            "state": self.state,
            "code_challenge": self.code_challenge,
            "code_challenge_method": "S256",
        }
        return "https://www.tiktok.com/v2/auth/authorize/?" + urlencode(params)

    def start_callback_server(self):
        backend = self
        logging.info("TT_BE: Starting callback server")
        class CallbackHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                parsed = urlparse(self.path)
                query = parse_qs(parsed.query)

                backend = getattr(self.server, "backend", None)
                if backend is None:
                    logging.error("TT_BE: Callback without backend")
                    self.send_response(500)
                    self.end_headers()
                    return

                logging.info(f"TT_BE_CH: Path={parsed.path} Query={query} existing_code={backend.auth_code!r}")

                if parsed.path != "/auth/callback":
                    self.send_response(404)
                    self.end_headers()
                    return

                if backend.auth_code is not None:
                    self.send_response(200)
                    self.send_header("Content-type", "text/plain; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(b"Auth code already received. Close this window.")
                    return

                backend.auth_code = query.get("code", [None])[0]
                backend.auth_error = query.get("error", [None])[0]

                if backend.auth_code:
                    self.send_response(200)
                    self.send_header("Content-type", "text/plain; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(b"Auth successful. You can close this window.")
                    logging.info(f"TT_BE_CH: Received Auth code {backend.auth_code}")
                else:
                    self.send_response(400)
                    self.send_header("Content-type", "text/plain; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(b"Auth failed.")
                    logging.info(f"TT_BE_CH: Auth failed. Error: {backend.auth_error}")

            def log_message(self, format, *args):
                return

        server = TTCallbackServer(("127.0.0.1", 3000), CallbackHandler)
        server.backend = self
        self.httpd = server

        threading.Thread(target=server.serve_forever, daemon=True).start()

    def stop_callback_server(self):
        if self.httpd is None:
            return
        try:
            self.httpd.shutdown()
        except Exception:
            pass
        try:
            self.httpd.server_close()
        except Exception:
            pass
        self.httpd = None

    def watch_for_auth(self, win):
        if self.auth_error:
            logging.error(f"TT_BE: Auth/Login Error: {self.auth_error}")
            self.stop_callback_server()
            win.destroy()
            return

        #logging.info("TT_BE: auth code recieved, trying exchange...")

        if self.auth_code:
            logging.info("TT_BE: Auth coded recieved")
            try:
                token_data = self.exchange_code_for_token(self.auth_code)
                self.save_account(token_data)
            except Exception as exc:
                logging.error(f"TT_BE: Token exchange failed: {exc}")
                self.stop_callback_server()
                win.destroy()
                return

            self.stop_callback_server()
            win.destroy()
            return

        self.ui.after(300, lambda: self.watch_for_auth(win))

    def exchange_code_for_token(self, auth_code):
        client_key = CLIENT_KEY
        client_secret =  CLIENT_SECRET
        redirect_uri = REDIRECT_URI

        logging.info("TT_BE: Started exchange!")

        if not self.code_verifier:
            logging.error("TT_BE: Missing code_verifier for PKCE")
            raise ValueError("Missing code_verifier for PKCE")

        assert self.code_verifier is not None
        payload = {
            "client_key": client_key,
            "client_secret": client_secret,
            "code": auth_code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "code_verifier": self.code_verifier,
        }

        response = requests.post("https://open.tiktokapis.com/v2/oauth/token/", data=payload, timeout=60)
        response.raise_for_status()
        logging.info(f"TT_BE: Token exchange response: {response.json()}")
        return response.json()

    def save_account(self, token_data):
        access_token = token_data.get("data", {}).get("access_token") or token_data.get("access_token")
        refresh_token = token_data.get("data", {}).get("refresh_token") or token_data.get("refresh_token")
        exp_acct = token_data.get("data", {}).get("expires_in") or token_data.get("expires_in")
        exp_rfsh = token_data.get("data", {}).get("refresh_expires_in") or token_data.get("refresh_expires_in")
        token_type = token_data.get("data", {}).get("token_type") or token_data.get("token_type")
        if not access_token:
            raise ValueError("No access token received")

        if not self.username:
            self.username = "Unkown"

        account = {
            "username": self.username, 
            "access_token": access_token,
            "refresh_token": refresh_token,
            "acct_expires_at": exp_acct,#.isoformat(), 
            "rfsh_expires_at": exp_rfsh,#.isoformat(),
            "source": "oauth",
            "tType": token_type
        }

        self.accounts.append(account)
        
        self.controller.env_handler.load(".env_program/settings.env")
        path = self.controller.env_handler.get("ACM_TIKTOK_PATH", "")
        with open(path, "w") as f:
            logging.info(f"TT_BE: Try Saving {self.accounts} in {path}")
            json.dump(self.accounts, f, indent=4)
        
        logging.info("TT_BE: Saved TikTok account")
    
    #Loads Accounts into table on tiktok page
    def load_accounts(self):
        filepath = self.controller.env_handler.get("ACM_TIKTOK_PATH", "")
        
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                try:
                    self.accounts = json.load(f)
                    logging.info(f"TT_BE: Loaded Instagram accounts from {filepath}")
                except json.JSONDecodeError as e:
                    logging.error(f"TT_BE: Error loading accounts from {filepath}: {e}")
        else:
            logging.warning(f"TT_BE: Accounts file {filepath} not found. No accounts loaded")
            # Create Popup to create a new file
            def create_file():
                with open(filepath, "w") as f:
                    json.dump([], f, indent=4)
                self.accounts = []
                logging.info(f"UI: Created new accounts file at {filepath}")
                popup.destroy()
                self.load_accounts()  # Load file now
            
            popup = tk.Toplevel(self.ui)
            popup.title("Accounts-File is missing")
            popup.geometry("600x500")
            tk.Label(popup, text=f"The File '{filepath}' does not exist.\nCreate New File?", font=("Arial", 12)).pack(pady=20)
            tk.Button(popup, text="Yes", command=create_file).pack(side="left", padx=20)
            tk.Button(popup, text="No", command=popup.destroy).pack(side="right", padx=20)
            return        
        
                
        #Clear Table
        self.ui.account_tree_tt.delete(*self.ui.account_tree_tt.get_children())
        logging.info("UI: Cleared Account Table")
        
        #Insert loaded accounts from Json file
        for acc in self.accounts:
            self.ui.account_tree_tt.insert(
                "",
                "end",
                values=(
                    acc.get("username", "Unknown"),
                    acc.get("acct_expires_at", "Not Set"),
                    acc.get("rfsh_expires_at", "Not Set"),
                    acc.get("access_token", "No AC Token"),
                    acc.get("refresh_token", "No RF Token"),
                    acc.get("source", "Unknown"),
                    acc.get("tType", "Unknown")
                )
            )
        logging.info("TT_BE: Loaded Accounts into Tiktok table")   
        
    #Here starts the posting mechanism
    def startPostTiktok(self):
        pass
    
    def edit_account(self):
        #Check if There is an Account List
        if not self.accounts:
            logging.error("TT_BE: No accounts to edit.")
            return
        
        #Open New Window and configure it
        win = tk.Toplevel(self.ui)
        win.title("Edit Account")
        win.geometry("600x500")

        logging.info("TT_BE_TL1: Opened Edit Account Window")

        tk.Label(win, text="Edit Instagram Account", font=("Arial", 14)).pack(pady=10)

        content_frame = tk.Frame(win)
        content_frame.pack(fill="x", padx=30)

        #Combobox for Account Selection
        tk.Label(content_frame, text="Select Account:").pack()
        usernames = [acc["username"] for acc in self.accounts]
        selected_var = tk.StringVar()
        combo = ttk.Combobox(content_frame, textvariable=selected_var, values=usernames, state="readonly", width=28)
        combo.pack(pady=5, fill="x", expand=True)

        #Entry Fields
        tk.Label(content_frame, text="New Username:").pack()
        username_entry = tk.Entry(content_frame, width=30)
        username_entry.pack(pady=5, fill="x", expand=True)

        tk.Label(content_frame, text="New Instagram ID:").pack()
        ig_id_entry = tk.Entry(content_frame, width=30)
        ig_id_entry.pack(pady=5, fill="x", expand=True)

        tk.Label(content_frame, text="New Access Token:").pack()
        acc_token_entry = tk.Entry(content_frame, width=30)
        acc_token_entry.pack(pady=5, fill="x", expand=True)
        
        tk.Label(content_frame, text="New AT Expiry Date:").pack()
        acc_date_entry = DateEntry(content_frame, width=30)
        acc_date_entry.pack(pady=5, fill="x", expand=True)
        
        tk.Label(content_frame, text="New Refresh Token:").pack()
        rfsh_token_entry = tk.Entry(content_frame, width=30)
        rfsh_token_entry.pack(pady=5, fill="x", expand=True)
        
        tk.Label(content_frame, text="New RT Expiry Date:").pack()
        rfsh_date_entry = DateEntry(content_frame, width=30)
        rfsh_date_entry.pack(pady=5, fill="x", width=30)
        

        def fill_fields(event):
            idx = combo.current()
            if idx >= 0:
                username_entry.delete(0, tk.END)
                acc_token_entry.delete(0, tk.END)
                acc_date_entry.delete(0, tk.END)
                rfsh_token_entry.delete(0, tk.END)
                rfsh_date_entry.delete(0, tk.END)
                username_entry.insert(0, self.accounts[idx]["username"])
                acc_token_entry.insert(0, self.accounts[idx]["access_token"])
                acc_date_entry.insert(0, self.accounts[idx]["acct_expires_at"])
                rfsh_token_entry.insert(0, self.accounts[idx]["refresh_token"])
                rfsh_date_entry.insert(0, self.accounts[idx]["rfsh_expires_at"])
            logging.info("TT_BE_TL1: Filled fields with selected account data")
        
        combo.bind("<<ComboboxSelected>>", fill_fields)

        #Save Funcion
        def save():
            idx = combo.current()
            if idx < 0:
                logging.error("TT_BE_TL1: No Account Selected")
                tk.Label(win, text="Please Select Account", fg="red").pack()
                return
            new_username = username_entry.get().strip()
            new_acc_token = acc_token_entry.get().strip()
            new_acc_expdate = acc_date_entry.get_date()
            new_rfsh_token = rfsh_token_entry.get().strip()
            new_rfsh_expdate = rfsh_date_entry.get_date()
            if new_username or new_acc_token or new_acc_expdate or new_rfsh_token or new_rfsh_expdate:
                self.accounts[idx]["username"] = new_username
                self.accounts[idx]["access_token"] = new_acc_token
                self.accounts[idx]["acct_expires_at"] = new_acc_expdate.isoformat()
                self.accounts[idx]["refresh_token"] = new_rfsh_token
                self.accounts[idx]["rfsh_expires_at"] = new_rfsh_expdate.isoformat()
                
                with open(self.controller.env_handler.get("ACM_TIKTOK_PATH", ""), "w") as f:
                    json.dump(self.accounts, f, indent=4)
                self.load_accounts()
                win.destroy()
            else:
                logging.error("TT_BE_TL1: Some entry is empty or not accepted.")
                tk.Label(win, text="Please fill in all fields", fg="red").pack()

        #Save Button
        tk.Button(win, text="Save", command=save).pack(pady=10)
        
        #Debug Message
        logging.info("TT_BE_TL1: Add Account Window finished and New Account Saved")
        
    def delete_account(self):
        #Check if There is an Account List
        if not self.accounts:
            logging.error("TT_BE: No accounts to delete.")
            return
        
        #Open New Window and configure it
        win = tk.Toplevel(self.ui)
        win.title("Delete Account")
        win.geometry("600x500")

        logging.info("TT_BE_TL1: Opened Delete Account Window")

        tk.Label(win, text="Delete Instagram Account", font=("Arial", 14)).pack(pady=10)
        
        content_frame = tk.Frame(win)
        content_frame.pack(fill="x", padx=30)
        
        usernames = [acc["username"] for acc in self.accounts]
        selected_var = tk.StringVar()
        combo = ttk.Combobox(content_frame, textvariable=selected_var, values=usernames, state="readonly", width=28)
        combo.pack(pady=10, fill="x", expand=True)

        def delete_selected():
            idx = combo.current()
            if idx < 0:
                tk.Label(win, text="Please select an account.", fg="red").pack()
                return
            username = self.accounts[idx]["username"]
            del self.accounts[idx]
            with open(self.controller.env_handler.get("ACM_TIKTOK_PATH", ""), "w") as f:
                json.dump(self.accounts, f, indent=4)
            self.load_accounts()
            win.destroy()
            logging.info(f"TT_BE_TL1: Account '{username}' deleted.")

        #Delete Button
        tk.Button(win, text="Delete", command=delete_selected, fg="red").pack(pady=10)  

        #Debug Message
        logging.info("TT_BE_TL1: Del Account Window finished and account deleted")

