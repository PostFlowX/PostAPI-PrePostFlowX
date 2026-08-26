#Imports
#Thread Matrix Monitor
from Ui.ThreadMatrix import ThreadMatrix
import math

#Logging, os and file stuff
import logging
import os
import json
from utils.tokenChecker import TokenChecker

#Tkinter
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkcalendar import DateEntry
from datetime import datetime, timedelta

#Backend Class for Instagram
class ig_UI_backend: 
    def __init__(self, controller, ui):
        self.controller = controller
        self.ui = ui
        self.token_checker_already_run = False
        self.selected_accounts = []
    
    def startPostInsta(self):
        #Deactivate the post button for spam prevention
        self.ui.post_button.config(state="disabled")  # Button deaktivieren
        #Strip all the needed data from the UI
        insta_cap = self.ui.ig_caption_entry.get().strip()
        insta_media = self.ui.ig_image_path.get().strip()
        media_type = self.ui.media_type.get()
        filepath = self.ui.ig_image_path.get()
        selected_accounts = self.selected_accounts
        
        self.controller.PGC.multipost_instagram(selected_accounts, insta_cap, insta_media, media_type, filepath)
        # Matrix-Fenster öffnen
        num_threads = len(selected_accounts)
        rows = math.ceil(num_threads ** 0.5)
        cols = math.ceil(num_threads / rows)
        self.matrix_window = ThreadMatrix(self, self.controller.PGC, rows=rows, cols=cols)
        
    #File Selection
    def browse_image_file(self):
        media_type = self.ui.media_type.get() if hasattr(self, "media_type") else "image"
        if media_type == "image":
            filetypes = [("Image files", "*.jpg *.jpeg")]
        elif media_type == "video":
            filetypes = [("Video files", "*.mp4 *.mov")]
        else:
            filetypes = [("All files", "*.*")]
        filename = filedialog.askopenfilename(title="Select File", filetypes=filetypes)
        if filename:
            self.ui.ig_image_path.set(filename)

    #Loads the Accounts from the accounts.json file
    def load_accounts(self):
        filepath = self.controller.env_handler.get("ACM_INSTA_PATH", "")
        old_status = {}
        
        #Save the old statuses pre loading
        if hasattr(self, "accounts"):
            for acc in self.accounts:
                old_status[acc.get("username")] = acc.get("Status", "Not Checked")

        #Load Instagram Accounts File
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                try:
                    self.accounts = json.load(f)
                    logging.info(f"UI: Loaded Instagram accounts from {filepath}")
                except json.JSONDecodeError as e:
                    logging.error(f"UI: Error loading accounts from {filepath}: {e}")
        else:
            logging.warning(f"UI: Accounts file {filepath} not found. No accounts loaded.")
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

        #Here the list should be loaded 
        for acc in self.accounts:
            username = acc.get("username")
            if username in old_status:
                acc["Status"] = old_status[username]
            else:
                acc["Status"] = "Not Checked"
        
        #Clear Table
        self.ui.account_tree_inst.delete(*self.ui.account_tree_inst.get_children())
        logging.info("UI: Cleared Account Table")
        
        #Insert loaded accounts from Json file
        for acc in self.accounts:
            self.ui.account_tree_inst.insert(
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
        logging.info("UI: Loaded Accounts into Table")
        
    #Runs the checker, should be run 
    def run_token_checker(self):
        #Now lets run the token checker
        logging.info("UI: Starting TokenChecker for loaded accounts")
        #callback func
        def update_status_in_tree_inst(idx, is_valid):
            def update():
                try:
                    children = self.ui.account_tree_inst.get_children()
                    if idx < len(children):
                        item_id = children[idx]
                        symbol = "✔" if is_valid else "✖"
                        self.ui.account_tree_inst.set(item_id, "Status", symbol) #directly into treeview
                        self.accounts[idx]["Status"] = symbol #also update in list
                except Exception as e:
                    logging.error(f"UI: Error updating token status in treeview for index {idx}: {e}")
            self.ui.after(0, update)  # Schedule the update in the main thread
        checker = TokenChecker(self.accounts, update_status_in_tree_inst)
        checker.check_all_tokens()

    #Update the selected accounts label
    def update_selected_accounts_label(self):
        if not self.selected_accounts:
            self.ui.selected_accounts_var.set("None")
            #Debug Message
            logging.info("UI: No accounts selected to display into selected_accounts_label")
        else:
            names = [acc["username"] for acc in self.selected_accounts]
            self.ui.selected_accounts_var.set(", ".join(names))
            #Debug Message
            logging.info(f"UI: Updated selected accounts label: {self.ui.selected_accounts_var.get()}")        

    # Opens a new window to select accounts for posting
    def open_account_selection(self):
        # Check if accounts are loaded
        if not self.accounts:
            logging.error("UI: No accounts to select.")
            return
        
        # Create a new window for account selection
        win = tk.Toplevel(self.ui)
        win.title("Select Accounts")
        win.geometry("600x500")

        logging.info("UI_TL1: Opened Select Account Window")

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
            logging.info(f"UI_TL1: Selected accounts for posting: {self.selected_accounts}")

        #Save Button
        tk.Button(win, text="Save", command=save_selection).pack(pady=20)

        #Debug Message
        logging.info("UI_TL1: Select Accounts Window finished and Accounts Selected")

    #Opens a second window to add an Account to the instagram accounts file
    #Later we want to add a parameter so we can add tiktok accounts and tokens too
    def add_account(self):
        #Open Window and configure it
        win = tk.Toplevel(self.ui)
        win.title("Add Account")
        win.geometry("600x500")

        logging.info("UI_TL1: Opened Add Account Window")

        tk.Label(win, text="Add Instagram Account", font=("Arial", 14)).pack(pady=10)
        
        content_frame = tk.Frame(win)
        content_frame.pack(fill="x", padx=30)
        
        tk.Label(content_frame, text="Username:").pack()
        username_entry = tk.Entry(content_frame, width=30)
        username_entry.pack(pady=5, fill="x", expand=True)

        tk.Label(content_frame, text="Instagram ID:").pack()
        ig_id_entry = tk.Entry(content_frame, width=30)
        ig_id_entry.pack(pady=5, fill="x", expand=True)

        tk.Label(content_frame, text="Access Token:").pack()
        token_entry = tk.Entry(content_frame, width=30)
        token_entry.pack(pady=5, fill="x", expand=True)
        
        tk.Label(content_frame, text="Expiry Date:").pack()
        date_entry = DateEntry(content_frame, width=30)
        date_entry.pack(pady=5, fill="x", expand=True)

        #Define Save for inside the window
        def save():
            username = username_entry.get().strip()
            ig_id = ig_id_entry.get().strip()
            token = token_entry.get().strip()
            expdate = date_entry.get_date()
            if not expdate:
                expdate = "Not set"
            else:
                expdate = expdate.isoformat()
            
            if username and token:
                # Add the new account to the accounts list
                self.accounts.append({"username": username, "IG_ID": ig_id, "token": token, "expdate": expdate})
                # Save the updated accounts to the file
                with open(self.controller.env_handler.get("ACM_INSTA_PATH", ""), "w") as f:
                    json.dump(self.accounts, f, indent=4)
                # Reload accounts in the main window
                self.load_accounts()
                win.destroy()
            else:
                logging.error("UI_TL1: Username or Token is empty or not accepted.")
                tk.Label(win, text="Please fill in both fields.", fg="red").pack(pady=5)
        
        #Save Button
        tk.Button(win, text="Save", command=save).pack(pady=10)

        #Debug Message
        logging.info("UI_TL1: Add Account Window finished and New Account Saved")

    #Opens a second window to edit an Account from the instagram accounts file
    def edit_account(self):
        #Check if There is an Account List
        if not self.accounts:
            logging.error("UI: No accounts to edit.")
            return
        
        #Open New Window and configure it
        win = tk.Toplevel(self.ui)
        win.title("Edit Account")
        win.geometry("600x500")

        logging.info("UI_TL1: Opened Edit Account Window")

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
        token_entry = tk.Entry(content_frame, width=30)
        token_entry.pack(pady=5, fill="x", expand=True)
        
        tk.Label(content_frame, text="New Expiry Date:").pack()
        date_entry = DateEntry(content_frame, width=30)
        date_entry.pack(pady=5, fill="x", expand=True)

        def fill_fields(event):
            idx = combo.current()
            if idx >= 0:
                username_entry.delete(0, tk.END)
                ig_id_entry.delete(0, tk.END)
                token_entry.delete(0, tk.END)
                date_entry.delete(0, tk.END)
                username_entry.insert(0, self.accounts[idx]["username"])
                ig_id_entry.insert(0, self.accounts[idx]["IG_ID"])
                token_entry.insert(0, self.accounts[idx]["token"])
                date_entry.insert(0, self.accounts[idx]["expdate"])
            logging.info("UI_TL1: Filled fields with selected account data")
        
        combo.bind("<<ComboboxSelected>>", fill_fields)

        #Save Funcion
        def save():
            idx = combo.current()
            if idx < 0:
                logging.error("UI_TL1: No Account Selected")
                tk.Label(win, text="Please Select Account", fg="red").pack()
                return
            new_username = username_entry.get().strip()
            new_ig_id = ig_id_entry.get().strip()
            new_token = token_entry.get().strip()
            new_expdate = date_entry.get_date()
            if new_username or new_token or new_expdate:
                self.accounts[idx]["username"] = new_username
                self.accounts[idx]["IG_ID"] = new_ig_id
                self.accounts[idx]["token"] = new_token
                self.accounts[idx]["expdate"] = new_expdate.isoformat()
                with open(self.controller.env_handler.get("ACM_INSTA_PATH", ""), "w") as f:
                    json.dump(self.accounts, f, indent=4)
                self.load_accounts()
                win.destroy()
            else:
                logging.error("UI_TL1: Username or Token is empty or not accepted.")
                tk.Label(win, text="Please fill both fields", fg="red").pack()

        #Save Button
        tk.Button(win, text="Save", command=save).pack(pady=10)
        
        #Debug Message
        logging.info("UI_TL1: Add Account Window finished and New Account Saved")

    def delete_account(self):
        #Check if There is an Account List
        if not self.accounts:
            logging.error("UI: No accounts to delete.")
            return
        
        #Open New Window and configure it
        win = tk.Toplevel(self.ui)
        win.title("Delete Account")
        win.geometry("600x500")

        logging.info("UI_TL1: Opened Delete Account Window")

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
            with open(self.controller.env_handler.get("ACM_INSTA_PATH", ""), "w") as f:
                json.dump(self.accounts, f, indent=4)
            self.load_accounts()
            win.destroy()
            logging.info(f"UI_TL1: Account '{username}' deleted.")

        #Delete Button
        tk.Button(win, text="Delete", command=delete_selected, fg="red").pack(pady=10)  

        #Debug Message
        logging.info("UI_TL1: Del Account Window finished and account deleted")

    def renew_tokens(self):
        logging.info("UI: Starting TokenChecker for renewing tokens")
        def message(idx, is_renewed, data):
            #Send log message
            def post():
                if is_renewed:
                    logging.info(f"UI: Token of index {idx} is renewed!")
                else:
                    logging.info(f"UI: Token of indes {idx} is not renewed or something went wrong!")
            self.ui.after(0, post)
            
            #Collect data
            logging.info(f"UI: API response data: Type: {data.get('token_type')}; Expires in: {data.get('expires_in')} seconds; Token: {data.get('access_token')}")
            
            #Convert the seconds from data to date
            seconds = data.get("expires_in")
            start_date = datetime.now()
            end_date = start_date + timedelta(seconds=seconds)
            
            #Save to accounts.json
            def save():
                self.accounts[idx]["expdate"] = end_date.isoformat()
                with open(self.controller.env_handler.get("ACM_INSTA_PATH", ""), "w") as f:
                    json.dump(self.accounts, f, indent=4)
            self.ui.after(0, save)
            self.load_accounts()
            
        checker = TokenChecker(self.accounts, message)
        checker.renew_all_tokens()