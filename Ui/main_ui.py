#from doctest import debug
#from codecs import escape_encode
#from curses.ascii import isdigit
#from pydoc import doc
#from re import A
#from struct import pack
import tkinter as tk
from tkinter import ttk

#from typing import Text
#from matplotlib.offsetbox import PaddedBox

#from datetime import datetime, timedelta
#from turtle import fill, left, right, width

#from numpy import pad
from tkinterweb import HtmlFrame

import os # For Logfile saving and path handling
import threading # for some toplayer windows like the debug window

#For Logging
import logging
from utils.tkinter_log_handler import TkinterLogHandler

#UI backends
from Ui.tiktok_backend import tt_UI_backend
from Ui.instagram_backend import ig_UI_backend
#from Ui.settings_backend import

#For Account Management and checking
import json
from utils.tokenChecker import TokenChecker

#for Select All in the Ui
def select_all(event):
        event.widget.select_range(0, 'end')
        event.widget.icursor('end')
        return 'break'

class PostAPIApp(tk.Tk):
    def __init__(self, debug_handler, controller):
        super().__init__()
        
        #Select all
        self.bind_class("Entry", "<Control-a>", select_all)
        self.bind_class("Entry", "<Control-A>", select_all)
        
        self.title("Post API App")
        self.geometry("1800x800")

        #Set the given Attributes
        self.debug_handler = debug_handler
        self.controller = controller
        
        #Setup Env Handler
        if self.controller and hasattr(self.controller, "env_handler"):
            self.controller.env_handler.load(".env_program/settings.env")
        else:
            logging.error("UI: No valid Controller or env_handler passed!")
            raise ValueError("No valid Controller or env_handler passed!")
        
        #Setup cool backends
        self.tiktok_backend = tt_UI_backend(self.controller, self)
        self.insta_backend = ig_UI_backend(self.controller, self)
        
        #Setup the cool token checker var         #self.token_checker_already_run = False
        
        # Set the icon if it exists
        icon_path = "assets/iconLIN.xbm"
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)
        else:
            logging.warning(f"UI: Icon file {icon_path} not found. Using default icon.")

        # === Main Container Frame ===
        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True)

        # === Left Menu ===
        self.menu_frame = tk.Frame(self.container, bg="#ddd", width=100)
        self.menu_frame.pack(side="left", fill="y")

        self.content_frame = tk.Frame(self.container, bg="#fff")
        self.content_frame.pack(side="right", fill="both", expand=True)

        self.build_menu()

        # === Startpage ===
        self.show_Menu()

    def build_menu(self):
        for widget in self.menu_frame.winfo_children():
            widget.destroy()
        self.buttons = []
        
        # === Menü-Buttons ===
        self.buttons = []
        menu_items = [
            ("PostAPI Menu", self.show_Menu),  # Title
            ("1. Documentation", self.show_doc),
            ("2. Settings", self.show_settings),
            ("3. Instagram", self.show_instagram),
            ("4. TikTok", self.show_tiktok),
            ("5. Client-Mode", self.show_client_mode),
            ("6. Credits", self.show_credits),
            ("7. Exit", self.exit_app)
        ]

        if self.controller.env_handler.get("DEBUG_MODE", "False").lower() in ("true", "1", "yes"):
            menu_items.append(("8. Debug", self.show_debug))

        for text, command in menu_items:
            btn = tk.Button(self.menu_frame, text=text, command=command, height=2)
            btn.pack(fill="x")
            self.buttons.append(btn)
        
        # Debug Message
        logging.info("UI: Built Menu")

    def clear_content(self):
        #Delete Logging-Handler if there is one exisiting
        if hasattr(self, "debug_handler"):
            if self.debug_handler is not None:
                self.debug_handler.set_widget(None)  # Clear the widget reference

        #Del all widgets in content_frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Debug Message
        logging.info("UI: Cleared Content Frame")

    def show_Menu(self):
        #Clear content and show the main menu
        self.clear_content()
        tk.Label(self.content_frame, text="PostAPI Menu", font=("Arial", 18)).pack(pady=10)
        tk.Label(self.content_frame, text="Please select an option from the left menu.").pack(pady=10)

        #Debug Message
        logging.info("UI: Opened Main Menu")

    def show_doc(self):
        #Clear content and create MainFrame on Page
        self.clear_content()
        tk.Label(self.content_frame, text="Documentation", font=("Arial", 18)).pack(pady=10)
        doc_frame = tk.Frame(self.content_frame)
        doc_frame.pack(fill="both", expand=True)
        
        #Create two other frames inside Mainframe for List and HTML View
        file_explo = ttk.Treeview(doc_frame)
        file_explo.pack(side="left", fill = "y", padx=10, pady=10)
        html_view = HtmlFrame(doc_frame)
        html_view.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        #Doc Path
        doc_path = "doc/"
        
        #Load Pages from the doc-directory
        def insert_items(parent, path):
            for entry in sorted(os.listdir(path)):
                if entry.lower() == "css":
                    continue
                full_path = os.path.join(path, entry)
                if os.path.isdir(full_path):
                    node = file_explo.insert(parent, "end", text=entry, open=False)
                    insert_items(node, full_path)
                elif entry.endswith(".html"):
                    file_explo.insert(parent, "end", text=entry, values=[full_path])
            logging.info("UI_DOC: Loaded elements into treeview")
        
        insert_items("", doc_path)
        
        #What Happens when selected
        def on_select(event):
            sel = file_explo.focus()
            file_path = file_explo.item(sel, "values")
            if file_path:
                with open(file_path[0], "r") as html_file:
                    html_content = html_file.read()
                    html_view.load_html(html_content)
            logging.info(f"UI_DOC: Loaded {file_path}")
        
        #Binder
        file_explo.bind("<<TreeviewSelect>>", on_select)
        
        #Debug Message
        logging.info("UI: Opened Documentation Page")

    def show_settings(self):
        #Load Existings Settings
        #Switch to git.env to load git settings
        self.controller.env_handler.load(".env_program/git.env")
        git_username = self.controller.env_handler.get("GIT_USERNAME", "")
        git_email = self.controller.env_handler.get("GIT_EMAIL", "")
        repo_path = self.controller.env_handler.get("REPO_PATH", "")
        
        #Switch Back to settings.env
        self.controller.env_handler.load(".env_program/settings.env")
        acm_instagram_path = self.controller.env_handler.get("ACM_INSTA_PATH", "")
        acm_tiktok_path = self.controller.env_handler.get("ACM_TIKTOK_PATH", "")
        debug_mode = self.controller.env_handler.get("DEBUG_MODE", "")

        #Clear content and show settings
        self.clear_content()
        tk.Label(self.content_frame, text="Settings / Config", font=("Arial", 18)).pack(pady=10)

        # Git config
        tk.Label(self.content_frame, text="Git Settings:", font=("Arial", 14)).pack()
        #Git Username
        frame_user = tk.Frame(self.content_frame) # New frame for user git settings
        frame_user.pack(pady=5)

        tk.Label(frame_user, text="Git Username:", width=40).pack(side="left")
        self.git_user_entry = tk.Entry(frame_user, width=40)
        self.git_user_entry.insert(0, git_username)  # Set existing username
        self.git_user_entry.pack(side="left", padx=5)

        #Git Email
        frame_email = tk.Frame(self.content_frame)  # New frame for email git settings
        frame_email.pack(pady=5)

        tk.Label(frame_email, text="Git Email:", width=40).pack(side="left")
        self.git_email_entry = tk.Entry(frame_email, width=40)
        self.git_email_entry.insert(0, git_email)  # Set existing email 
        self.git_email_entry.pack(side="left", padx=5)

        # Local Repo Path
        frame_path = tk.Frame(self.content_frame)  # New frame for local repo path
        frame_path.pack(pady=5)

        tk.Label(frame_path, text="Local Repo Path:", width=40).pack(side="left")
        self.local_repo_entry = tk.Entry(frame_path, width=40)
        self.local_repo_entry.insert(0, repo_path)  # Set existing local repo path
        self.local_repo_entry.pack(side="left", padx=5)

        # Save Button for Git Settings
        tk.Button(self.content_frame, text="Save Git Settings", command=self.save_settings_GIT).pack(pady=10)

        #Debug Box
        frame_debug = tk.Frame(self.content_frame)  # New frame for debug settings
        frame_debug.pack(pady=5)

        tk.Label(frame_debug, text="Debug Settings:", font=("Arial", 14)).pack()
        self.debug_var = tk.BooleanVar(value=(debug_mode == "True"))
        debug_cb = tk.Checkbutton(frame_debug, text="Activate Debug-Mode", variable=self.debug_var)
        debug_cb.pack(pady=10)

        tk.Button(self.content_frame, text="Save Debug Settings", command=self.save_settings_DEBUG).pack(pady=10)

        # ACM Settings (Account Management)
        frame_acm = tk.Frame(self.content_frame)  # New frame for ACM settings
        frame_acm.pack(pady=5)

        tk.Label(frame_acm, text="Account Management Settings:", font=("Arial", 14)).pack()
        tk.Label(frame_acm, text="Instagram:").pack()
        self.acm_instagram = tk.Entry(frame_acm, width=30)
        self.acm_instagram.insert(0, acm_instagram_path)
        self.acm_instagram.pack(pady=5, fill="x", expand=True)
        
        tk.Label(frame_acm, text="Tiktok:").pack()
        self.acm_tiktok = tk.Entry(frame_acm, width=30)
        self.acm_tiktok.insert(0, acm_tiktok_path)
        self.acm_tiktok.pack(pady=5, fill="x", expand=True)

        tk.Button(frame_acm, text="Save ACM Settings", command=self.save_settings_acm).pack(pady=10)

        #Message Box for Settings
        self.frame_message = tk.Frame(self.content_frame)  # New frame for message box
        self.frame_message.pack(pady=5)

        #Debug Message
        logging.info("UI: Opened Settings Page")

    #What i need : - List for accounts -> username_token map? ; filepath ; Caption ; 
    def show_instagram(self):
        self.clear_content()

        # Main-Frame for Instagram (left)
        frame_insert = tk.Frame(self.content_frame)
        frame_insert.pack(side="left", fill="both", expand=True, padx=20, pady=10)

        tk.Label(frame_insert, text="Instagram Post", font=("Arial", 18)).pack(pady=10)

        #Media Type Selection
        self.media_type = tk.StringVar(value="image")
        frame_media = tk.Frame(frame_insert)
        frame_media.pack(pady=5)
        tk.Label(frame_media, text="Media type:").pack(side="left")
        tk.Radiobutton(frame_media, text="Picture", variable=self.media_type, value="image").pack(side="left")
        tk.Radiobutton(frame_media, text="Reel", variable=self.media_type, value="video").pack(side="left")

        # Filepath (Local URL)
        tk.Label(frame_insert, text="Media Filepath:").pack()
        self.ig_image_path = tk.StringVar()
        frame_file = tk.Frame(frame_insert)
        frame_file.pack(pady=5)
        self.ig_image_entry = tk.Entry(frame_file, textvariable=self.ig_image_path, width=40, state="readonly")
        self.ig_image_entry.pack(side="left", padx=5)
        tk.Button(frame_file, text="Browse...", command=self.insta_backend.browse_image_file).pack(side="left")
        
        # Caption
        tk.Label(frame_insert, text="Caption:").pack()
        self.ig_caption_entry = tk.Entry(frame_insert, width=50)
        self.ig_caption_entry.pack(pady=5)

        # Account Selection
        tk.Button(frame_insert, text="Select Accounts", command=self.insta_backend.open_account_selection).pack(pady=5)

        # Post-Button, this is a object in self so we can lock it to prevent spam
        self.post_button = tk.Button(frame_insert, text="Post", command=self.insta_backend.startPostInsta)
        self.post_button.pack(pady=20)

        # Right Side: Account-Table
        frame_accounts = tk.Frame(self.content_frame)
        frame_accounts.pack(side="right", fill="y", padx=20, pady=10)

        tk.Label(frame_accounts, text="Accounts", font=("Arial", 14)).pack()

        # Table for Accounts
        self.account_tree_inst = ttk.Treeview(frame_accounts, columns=("Username", "IG_ID", "Status", "expdate","Token"), show="headings", height=10)
        self.account_tree_inst.heading("Username", text="Username")
        self.account_tree_inst.heading("IG_ID", text="Instagram ID")
        self.account_tree_inst.heading("Status", text="Status")
        self.account_tree_inst.heading("expdate", text="Expires in")
        self.account_tree_inst.heading("Token", text="Access Token")
        self.account_tree_inst.pack(pady=5)

        # Buttons for Account-management
        btn_frame = tk.Frame(frame_accounts)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Add", command=self.insta_backend.add_account).pack(side="left", padx=2)
        tk.Button(btn_frame, text="Edit", command=self.insta_backend.edit_account).pack(side="left", padx=2)
        tk.Button(btn_frame, text="Delete", command=self.insta_backend.delete_account).pack(side="left", padx=2)
        tk.Button(btn_frame, text="Renew Tokens", command=self.insta_backend.renew_tokens).pack(side="left", padx=2)
        tk.Button(btn_frame, text="Refresh Statuses", command=self.insta_backend.run_token_checker).pack(side="left", padx=2)

        # Load Accounts into table
        self.insta_backend.load_accounts()
        
        #Run the token checker but only once
        if not self.insta_backend.token_checker_already_run:
            self.insta_backend.run_token_checker()
            self.token_checker_already_run = True

        #List for Selcted Accounts
        tk.Label(frame_accounts, text="Selected Accounts:", font=("Arial", 12)).pack(pady=5)
        self.selected_accounts_var = tk.StringVar()
        self.selected_accounts_label = tk.Label(frame_accounts, textvariable=self.selected_accounts_var, fg="blue", anchor="w", justify="left")
        self.selected_accounts_label.pack(fill="x", padx=5)
        self.insta_backend.update_selected_accounts_label()

        # Debug Message
        logging.info("UI: Opened Instagram Page")

    def show_tiktok(self):
        self.clear_content()
        
        #Main Frame (left)
        frame_insert = tk.Frame(self.content_frame)
        frame_insert.pack(side="left", fill="both", expand=True, padx=20, pady=10)
        
        tk.Label(frame_insert, text="Tiktok Post", font=("Arial", 18)).pack(pady=10)
        
        #All the selections
        
        #Main Frame(right)
        frame_accounts = tk.Frame(self.content_frame)
        frame_accounts.pack(side="right", fill="y", padx=20, pady=10)
        
        tk.Label(frame_accounts, text="Accounts", font=("Arial", 14)).pack()
        
        #Another account tree
        self.account_tree_tt = ttk.Treeview(frame_accounts, columns=("Username", "ID?", "Status", "expdate", "Token"), show="headings", height=10)
        self.account_tree_tt.heading("Username", text="Username")
        self.account_tree_tt.heading("ID?", text="ID?")
        self.account_tree_tt.heading("Status", text="Status")
        self.account_tree_tt.heading("expdate", text="Expires in")
        self.account_tree_tt.heading("Token", text="Access Token")
        self.account_tree_tt.pack(pady=5)
        
        #Button frame under treeview inside accounts frame
        btn_frame = tk.Frame(frame_accounts)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Add", command=self.tiktok_backend.add_account).pack(side="left", padx=2)
        
        #Load accounts into table
        self.tiktok_backend.load_accounts()
        
        #Debug Message
        logging.info("UI: Opened TikTok Page (WIP)")

    def show_client_mode(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Client Mode (For Servers)", font=("Arial", 18)).pack(pady=10)

        #Debug Message
        logging.info("UI: Opened Client Mode Page (WIP)")

    def show_credits(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Credits", font=("Arial", 18)).pack(pady=10)
        tk.Label(self.content_frame, text="Author: Siralexus\nEmail: alexgeschaeftlich@posteo.com").pack(pady=20)

        #Debug Message
        logging.info("UI: Opened Credits Page")

    def show_debug(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Debug-Infos", font=("Arial", 18)).pack(pady=10)
        self.debug_console = tk.Text(self.content_frame, height=20, width=80, state="normal", bg="#222", fg="#0f0")
        self.debug_console.pack(pady=10, fill="both", expand=True) # Expandable to fill the space
    
        # Log-Historie anzeigen
        self.debug_console.delete("1.0", "end")
        for msg in TkinterLogHandler.log_history:
            self.debug_console.insert("end", msg + "\n")
        self.debug_console.config(state="disabled")

        #Set Debug Console as widget for logging
        if self.debug_handler is not None:
            self.debug_handler.set_widget(self.debug_console)

        # Button für Debug-Konsole im Extra-Fenster
        def open_debug_window():
            logging.info("UI: Opening Debug Console in Extra Window")
            win = tk.Toplevel(self)
            win.title("Debug Console (Extra Window)")
            win.geometry("800x400")
            debug_text = tk.Text(win, height=20, width=80, state="normal", bg="#222", fg="#0f0")
            debug_text.pack(fill="both", expand=True)
            #Show loading
            debug_text.insert("end", "Loading log history...\n")
            
            def load_log_into_thread():
                # Collect all messages so far
                all_logs = "\n".join(TkinterLogHandler.log_history)
                
                def update_ui():
                    debug_text.config(state="normal")
                    debug_text.delete("1.0", "end")
                    debug_text.insert("end", all_logs)
                    debug_text.config(state="disabled")
                    
                    if self.debug_handler is not None:
                        self.debug_handler.set_widget(debug_text)
                
                self.after(0,update_ui)
            # Starte das Laden in einem separaten Thread
            thread = threading.Thread(target=load_log_into_thread, daemon=True)
            thread.start()
        tk.Button(self.content_frame, text="Open Debug-Console in extra window", command=open_debug_window).pack(pady=10)

        logging.info("UI: Opened Debug Console")

    # === Functions ===
    def save_settings_GIT(self):
        git_username = self.git_user_entry.get()
        git_email = self.git_email_entry.get()
        local_repo_path = self.local_repo_entry.get()
        #Load env in env handler
        self.controller.env_handler.load(".env_program/git.env")  # Ensure the environment is loaded before saving settings
        if git_username and git_email and local_repo_path:
            # Update the .env file with the new Git settings; no need to check if they are already set as the function will handle that
            self.controller.env_handler.setV("GIT_USERNAME", git_username)
            self.controller.env_handler.setV("GIT_EMAIL", git_email)
            self.controller.env_handler.setV("REPO_PATH", local_repo_path)
            # Remove previous messages
            for widget in self.frame_message.winfo_children():
                widget.destroy()
            tk.Label(self.frame_message, text=f"Git settings saved:\n{git_username}\n{git_email}\n{local_repo_path}\n").pack()
        else:
            tk.Label(self.frame_message, text="Please Enter something.").pack()

        # Debug Message
        logging.info("UI: Saved Git Settings")

    def save_settings_DEBUG(self):
        debug_mode = self.debug_var.get()
        self.controller.env_handler.load(".env_program/settings.env")  # Ensure the environment is loaded before saving settings
        self.controller.env_handler.setV("DEBUG_MODE", str(debug_mode))  # Save the debug mode setting
        # Remove previous messages
        for widget in self.frame_message.winfo_children():
            widget.destroy()
        tk.Label(self.frame_message, text=f"Debug mode set to: {debug_mode}").pack()
        self.build_menu()  # Rebuild the menu to reflect changes    

        #Debug Message
        logging.info("UI: Saved Debug Settings")

    #Saves ACM Settings
    def save_settings_acm(self):
        #Remove previous message
        for widget in self.frame_message.winfo_children():
            widget.destroy()        
        acm_instagram_path = self.acm_instagram.get() 
        acm_tiktok_path = self.acm_tiktok.get()
        self.controller.env_handler.load(".env_program/settings.env")  # Ensure the environment is loaded before saving settings
        self.controller.env_handler.setV("ACM_INSTA_PATH", str(acm_instagram_path))  # Save the ACM Instagram file path
        self.controller.env_handler.setV("ACM_TIKTOK_PATH", str(acm_tiktok_path))
        tk.Label(self.frame_message, text="ACM settings saved successfully.").pack()
        self.build_menu()  # Rebuild the menu to reflect changes
        
        #Debug Message
        logging.info("UI: Saved ACM Settings")  
        
    #Exit Func
    def exit_app(self):
        logging.info("UI: Exiting Application")
        # Save log history before exiting
        TkinterLogHandler.save_log_history()
        self.quit()
    
    
'''    #File Selection
    def browse_image_file(self):
        media_type = self.media_type.get() if hasattr(self, "media_type") else "image"
        if media_type == "image":
            filetypes = [("Image files", "*.jpg *.jpeg")]
        elif media_type == "video":
            filetypes = [("Video files", "*.mp4 *.mov")]
        else:
            filetypes = [("All files", "*.*")]
        filename = filedialog.askopenfilename(title="Select File", filetypes=filetypes)
        if filename:
            self.ig_image_path.set(filename)

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

            popup = tk.Toplevel(self)
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
        self.account_tree_inst.delete(*self.account_tree_inst.get_children())
        logging.info("UI: Cleared Account Table")
        
        #Insert loaded accounts from Json file
        for acc in self.accounts:
            self.account_tree_inst.insert(
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
                    children = self.account_tree_inst.get_children()
                    if idx < len(children):
                        item_id = children[idx]
                        symbol = "✔" if is_valid else "✖"
                        self.account_tree_inst.set(item_id, "Status", symbol) #directly into treeview
                        self.accounts[idx]["Status"] = symbol #also update in list
                except Exception as e:
                    logging.error(f"UI: Error updating token status in treeview for index {idx}: {e}")
            self.after(0, update)  # Schedule the update in the main thread
        checker = TokenChecker(self.accounts, update_status_in_tree_inst)
        checker.check_all_tokens()

    #Update the selected accounts label
    def update_selected_accounts_label(self):
        if not self.selected_accounts:
            self.selected_accounts_var.set("None")
            #Debug Message
            logging.info("UI: No accounts selected to display into selected_accounts_label")
        else:
            names = [acc["username"] for acc in self.selected_accounts]
            self.selected_accounts_var.set(", ".join(names))
            #Debug Message
            logging.info(f"UI: Updated selected accounts label: {self.selected_accounts_var.get()}")        

    # Opens a new window to select accounts for posting
    def open_account_selection(self):
        # Check if accounts are loaded
        if not self.accounts:
            logging.error("UI: No accounts to select.")
            return
        
        # Create a new window for account selection
        win = tk.Toplevel(self)
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
        win = tk.Toplevel(self)
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
        win = tk.Toplevel(self)
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
        win = tk.Toplevel(self)
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
            self.after(0, post)
            
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
            self.after(0, save)
            self.load_accounts()
            
        checker = TokenChecker(self.accounts, message)
        checker.renew_all_tokens()

    #Starts the pOsting process (instagram)
    def startPostInsta(self):
        #Deactivate the post button for spam prevention
        self.post_button.config(state="disabled")  # Button deaktivieren
        #Strip all the needed data from the UI
        insta_cap = self.ig_caption_entry.get().strip()
        insta_media = self.ig_image_path.get().strip()
        media_type = self.media_type.get()
        filepath = self.ig_image_path.get()
        selected_accounts = self.selected_accounts
        
        self.controller.PGC.multipost_instagram(selected_accounts, insta_cap, insta_media, media_type, filepath)
        # Matrix-Fenster öffnen
        num_threads = len(selected_accounts)
        rows = math.ceil(num_threads ** 0.5)
        cols = math.ceil(num_threads / rows)
        self.matrix_window = ThreadMatrix(self, self.controller.PGC, rows=rows, cols=cols)
'''
    