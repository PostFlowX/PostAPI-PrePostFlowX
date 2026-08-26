#Tkinter
import tkinter as tk
from tkinter import ttk
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