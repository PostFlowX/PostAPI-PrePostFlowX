import tkinter as tk
from tkinter import ttk
import logging
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from numpy import character
import requests
import hashlib
import random
import secrets
from typing import Optional
from urllib.parse import parse_qs, urlparse, urlencode
import json
import os

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
        self.accounts = []
        self.auth_code = None
        self.code_verifier = None
        self.auth_error = None
        self.state = None
        self.httpd = None

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

        tk.Label(win, text="Add TikTok Account", font=("Arial", 14)).pack(pady=10)
        
        tk.Label(win, text="Username:").pack()
        username_entry = tk.Entry(win, width=30)
        username_entry.pack(pady=5, fill="x", expand=True)
        
        tk.Label(win, text="Please log in in the browser window.", font=("Arial", 11)).pack(pady=10)

        logging.info("TT_BE: Opened Add Account Window")
        
        tk.Button()
        
        self.start_oauth_flow(win)

    def start_oauth_flow(self, win):
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
            win.destroy()
            return

        auth_url = self.build_auth_url()
        webbrowser.open(auth_url)

        self.watch_for_auth(win)

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
        if not access_token:
            raise ValueError("No access token received")

        account = {
            "username": "TikTok Account", #Needs fix
            "access_token": access_token,
            "refresh_token": refresh_token,
            "acct_expires_at": exp_acct, #Needs to be formatted correctly
            "rfsh_expires_at": exp_rfsh,
            "source": "oauth",
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
                    acc.get("IG_ID", "Not Set"),
                    acc.get("Status", "Not Checked"),
                    acc.get("expdate", "Not Set"),
                    acc.get("token", "No Token")
                )
            )
        logging.info("TT_BE: Loaded Accounts into Tiktok table")            