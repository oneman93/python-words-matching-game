"""
REST Client GUI Application
Tkinter-based GUI for executing HTTP requests from Teams.http file.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import requests
import json
import base64
import os
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple, Dict
from http_parser import HttpParser, ApiEndpoint

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rest_client_gui.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RestClientGUI:
    """Main GUI application for REST Client."""
    
    def __init__(self, root: tk.Tk, http_file_path: str):
        self.root = root
        self.http_file_path = http_file_path
        self.parser: Optional[HttpParser] = None
        self.all_endpoints: List[ApiEndpoint] = []
        self.filtered_endpoints: List[ApiEndpoint] = []
        self.current_endpoint: Optional[ApiEndpoint] = None
        
        # Track last run times for endpoints
        self.last_run_times: Dict[str, str] = {}
        # Store history file in the RestClientGUI folder
        script_dir = Path(__file__).parent
        self.run_history_file = script_dir / '.rest_client_history.json'
        self.config_file = script_dir / '.rest_client_config.json'
        self.load_run_history()
        
        # ResponseTree tab is now used for expand/collapse, no need for collapse state here
        
        # Search state for TreeView
        self.tree_search_matches = []  # List of matching item IDs
        self.tree_search_current_index = -1  # Current match index
        self.tree_search_term = ""  # Current search term
        
        self.setup_ui()
        self.load_endpoints()
    
    def setup_ui(self):
        """Set up the user interface."""
        self.root.title("REST Client GUI")
        self.root.geometry("1000x700")
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(6, weight=1)
        
        # File selection button and label
        select_frame = ttk.Frame(main_frame)
        select_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        select_frame.columnconfigure(1, weight=1)
        
        select_button = ttk.Button(
            select_frame,
            text="Select",
            command=self.select_http_file,
            width=10
        )
        select_button.grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        # Label to show selected file
        self.selected_file_label = ttk.Label(
            select_frame,
            text=f"File: {Path(self.http_file_path).name}",
            font=('Arial', 9),
            foreground='blue'
        )
        self.selected_file_label.grid(row=0, column=1, sticky=tk.W)
        
        # Search filter
        ttk.Label(main_frame, text="Search Filter:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_changed)
        search_entry = ttk.Entry(main_frame, textvariable=self.search_var, width=30)
        search_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        # API Endpoint dropdown with Copy URL button
        ttk.Label(main_frame, text="API Endpoint:").grid(row=2, column=0, sticky=tk.W, pady=5)
        endpoint_frame = ttk.Frame(main_frame)
        endpoint_frame.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        endpoint_frame.columnconfigure(0, weight=1)
        
        self.endpoint_var = tk.StringVar()
        self.endpoint_combo = ttk.Combobox(
            endpoint_frame, 
            textvariable=self.endpoint_var,
            width=80,
            state="readonly"
        )
        self.endpoint_combo.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        self.endpoint_combo.bind('<<ComboboxSelected>>', self.on_endpoint_selected)
        
        # Copy URL button
        copy_url_button = ttk.Button(
            endpoint_frame,
            text="Copy URL",
            command=self.copy_url_to_clipboard,
            width=10
        )
        copy_url_button.grid(row=0, column=1, sticky=tk.W)
        
        # Description label
        self.description_label = ttk.Label(
            main_frame,
            text="",
            font=('Arial', 9),
            foreground='gray',
            wraplength=700
        )
        self.description_label.grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=5, pady=(0, 5))
        
        # Last run time label
        self.last_run_label = ttk.Label(
            main_frame,
            text="",
            font=('Arial', 8),
            foreground='gray'
        )
        self.last_run_label.grid(row=4, column=0, columnspan=2, sticky=tk.W, padx=5, pady=(0, 5))
        
        # Run button
        self.run_button = ttk.Button(
            main_frame,
            text="Run",
            command=self.run_request,
            width=15
        )
        self.run_button.grid(row=5, column=0, columnspan=2, pady=10)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Tab 1: Variables
        self.setup_variables_tab()
        
        # Tab 2: Response (Raw JSON)
        self.setup_response_tab()
        
        # Tab 3: ResponseTree (TreeView)
        self.setup_response_tree_tab()
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_bar.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
    
    def setup_variables_tab(self):
        """Set up the Variables tab."""
        variables_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(variables_frame, text="Variables")
        
        # Configure grid
        variables_frame.columnconfigure(1, weight=1)
        variables_frame.rowconfigure(2, weight=1)
        
        # File path label
        file_path_label = ttk.Label(
            variables_frame,
            text=f"File: {self.http_file_path}",
            font=('Arial', 8),
            foreground='blue',
            cursor='hand2'
        )
        file_path_label.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        # Label
        ttk.Label(
            variables_frame,
            text="Variables from HTTP file:",
            font=('Arial', 10, 'bold')
        ).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # Create treeview for variables
        tree_frame = ttk.Frame(variables_frame)
        tree_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        # Treeview with scrollbars
        tree_scroll_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        
        self.variables_tree = ttk.Treeview(
            tree_frame,
            columns=('Value', 'Status'),
            show='tree headings',
            yscrollcommand=tree_scroll_y.set,
            xscrollcommand=tree_scroll_x.set
        )
        
        tree_scroll_y.config(command=self.variables_tree.yview)
        tree_scroll_x.config(command=self.variables_tree.xview)
        
        # Configure columns
        self.variables_tree.heading('#0', text='Variable Name')
        self.variables_tree.heading('Value', text='Value')
        self.variables_tree.heading('Status', text='Status')
        self.variables_tree.column('#0', width=200, minwidth=150)
        self.variables_tree.column('Value', width=500, minwidth=200)
        self.variables_tree.column('Status', width=250, minwidth=150)
        logger.debug("Treeview columns configured: #0=Variable Name, #1=Value, #2=Status")
        
        # Grid treeview and scrollbars
        self.variables_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_scroll_y.grid(row=0, column=1, sticky=(tk.N, tk.S))
        tree_scroll_x.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Bind double-click to edit variable value
        self.variables_tree.bind('<Double-1>', self.on_variable_double_click)
        
        # Bind right-click to show context menu
        self.variables_tree.bind('<Button-3>', self.on_variable_right_click)
        self.variables_tree.bind('<Button-2>', self.on_variable_right_click)  # For Mac
        
        # Info label
        info_label = ttk.Label(
            variables_frame,
            text="Variables are automatically loaded from the HTTP file. Double-click a variable value to edit it. @graph_token is automatically updated when OAuth token is refreshed.",
            font=('Arial', 8),
            foreground='gray'
        )
        info_label.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
    
    def setup_response_tab(self):
        """Set up the Response tab with raw JSON text."""
        response_frame = ttk.Frame(self.notebook, padding="5")
        self.notebook.add(response_frame, text="Response")
        
        # Configure grid
        response_frame.columnconfigure(0, weight=1)
        response_frame.rowconfigure(0, weight=1)
        
        # Response text box with scrollbar (raw JSON only)
        self.response_text = scrolledtext.ScrolledText(
            response_frame,
            wrap=tk.WORD,
            width=80,
            height=25,
            font=('Consolas', 10)
        )
        self.response_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure highlight tags for search results
        self.response_text.tag_configure('search_highlight', background='yellow', foreground='black')
        self.response_text.tag_configure('search_current', background='orange', foreground='black')
        
        # Configure status color tags
        self.response_text.tag_configure('status_2xx', foreground='green', font=('Consolas', 10, 'bold'))
        self.response_text.tag_configure('status_3xx', foreground='blue', font=('Consolas', 10, 'bold'))
        self.response_text.tag_configure('status_4xx', foreground='red', font=('Consolas', 10, 'bold'))
        self.response_text.tag_configure('status_5xx', foreground='red', font=('Consolas', 10, 'bold'))
        self.response_text.tag_configure('status_other', foreground='orange', font=('Consolas', 10, 'bold'))
        
        # Bind Ctrl-F for search in response text
        self.response_text.bind('<Control-f>', self.show_search_dialog)
        self.response_text.bind('<Control-F>', self.show_search_dialog)
    
    def setup_response_tree_tab(self):
        """Set up the ResponseTree tab with TreeView for expand/collapse."""
        tree_frame = ttk.Frame(self.notebook, padding="5")
        self.notebook.add(tree_frame, text="ResponseTree")
        
        # Configure grid
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(1, weight=1)  # TreeView row
        
        # Search frame
        search_frame = ttk.Frame(tree_frame)
        search_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        search_frame.columnconfigure(1, weight=1)
        
        # Search label
        ttk.Label(search_frame, text="Search:").grid(row=0, column=0, padx=(0, 5))
        
        # Search entry
        self.tree_search_var = tk.StringVar()
        self.tree_search_entry = ttk.Entry(search_frame, textvariable=self.tree_search_var, width=30)
        self.tree_search_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        self.tree_search_entry.bind('<Return>', lambda e: self.search_tree_view())
        
        # Search button
        search_button = ttk.Button(search_frame, text="Search Tree View", command=self.search_tree_view)
        search_button.grid(row=0, column=2, padx=(0, 5))
        
        # Previous button
        self.tree_search_prev_button = ttk.Button(search_frame, text="◀ Previous", command=self.search_tree_previous, state='disabled')
        self.tree_search_prev_button.grid(row=0, column=3, padx=(0, 5))
        
        # Next button
        self.tree_search_next_button = ttk.Button(search_frame, text="Next ▶", command=self.search_tree_next, state='disabled')
        self.tree_search_next_button.grid(row=0, column=4, padx=(0, 5))
        
        # Clear button
        clear_button = ttk.Button(search_frame, text="Clear", command=self.clear_tree_search)
        clear_button.grid(row=0, column=5, padx=(0, 5))
        
        # Match count label
        self.tree_search_count_label = ttk.Label(search_frame, text="", foreground='gray')
        self.tree_search_count_label.grid(row=0, column=6, padx=(10, 0))
        
        # TreeView frame
        tree_container = ttk.Frame(tree_frame)
        tree_container.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_container.columnconfigure(0, weight=1)
        tree_container.rowconfigure(0, weight=1)
        
        # Create scrollbars
        tree_scroll_y = ttk.Scrollbar(tree_container, orient=tk.VERTICAL)
        tree_scroll_x = ttk.Scrollbar(tree_container, orient=tk.HORIZONTAL)
        
        # Create TreeView
        self.response_tree = ttk.Treeview(
            tree_container,
            columns=('Value',),
            show='tree',
            yscrollcommand=tree_scroll_y.set,
            xscrollcommand=tree_scroll_x.set
        )
        
        tree_scroll_y.config(command=self.response_tree.yview)
        tree_scroll_x.config(command=self.response_tree.xview)
        
        # Configure column
        self.response_tree.column('#0', width=400, minwidth=200)
        self.response_tree.column('Value', width=500, minwidth=200)
        self.response_tree.heading('#0', text='Key')
        self.response_tree.heading('Value', text='Value')
        
        # Grid treeview and scrollbars
        self.response_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_scroll_y.grid(row=0, column=1, sticky=(tk.N, tk.S))
        tree_scroll_x.grid(row=1, column=0, sticky=(tk.W, tk.E))
    
    def populate_response_tree(self, response: requests.Response):
        """Populate the TreeView with JSON response data."""
        # Clear existing items
        for item in self.response_tree.get_children():
            self.response_tree.delete(item)
        
        try:
            # Try to parse as JSON
            json_data = response.json()
            
            # Add status and headers as root items
            status_item = self.response_tree.insert('', 'end', text=f"Status: {response.status_code} {response.reason}", values=('',))
            
            headers_item = self.response_tree.insert('', 'end', text="Headers", values=('',))
            for key, value in response.headers.items():
                self.response_tree.insert(headers_item, 'end', text=key, values=(str(value),))
            
            # Add body
            body_item = self.response_tree.insert('', 'end', text="Body", values=('',))
            
            # Recursively add JSON data
            self._add_json_to_tree(body_item, json_data, "root")
            
            # Expand status and headers by default
            self.response_tree.item(status_item, open=True)
            self.response_tree.item(headers_item, open=True)
            self.response_tree.item(body_item, open=True)
            
        except (json.JSONDecodeError, ValueError):
            # Not JSON, add as text
            self.response_tree.insert('', 'end', text="Response (Not JSON)", values=('',))
            self.response_tree.insert('', 'end', text=response.text[:200] + "..." if len(response.text) > 200 else response.text, values=('',))
    
    def _add_json_to_tree(self, parent, data, key_name=""):
        """Recursively add JSON data to TreeView."""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    # Complex type - create node
                    node = self.response_tree.insert(parent, 'end', text=str(key), values=('',))
                    self._add_json_to_tree(node, value, key)
                else:
                    # Simple value
                    value_str = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
                    if len(value_str) > 100:
                        value_str = value_str[:100] + "..."
                    self.response_tree.insert(parent, 'end', text=str(key), values=(value_str,))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    # Complex type - create node
                    node = self.response_tree.insert(parent, 'end', text=f"[{i}]", values=('',))
                    self._add_json_to_tree(node, item, f"[{i}]")
                else:
                    # Simple value
                    value_str = json.dumps(item, ensure_ascii=False) if not isinstance(item, str) else item
                    if len(value_str) > 100:
                        value_str = value_str[:100] + "..."
                    self.response_tree.insert(parent, 'end', text=f"[{i}]", values=(value_str,))
        else:
            # Simple value
            value_str = json.dumps(data, ensure_ascii=False) if not isinstance(data, str) else data
            if len(value_str) > 100:
                value_str = value_str[:100] + "..."
            self.response_tree.insert(parent, 'end', text=key_name, values=(value_str,))
    
    def search_tree_view(self, event=None):
        """Search for text in TreeView and expand matching nodes."""
        search_term = self.tree_search_var.get().strip()
        
        if not search_term:
            self.clear_tree_search()
            return
        
        # Clear previous search
        self.tree_search_matches = []
        self.tree_search_current_index = -1
        self.tree_search_term = search_term.lower()
        
        # Recursively search all items
        self._search_tree_recursive('', search_term.lower())
        
        # Update UI
        match_count = len(self.tree_search_matches)
        if match_count > 0:
            self.tree_search_count_label.config(text=f"Found {match_count} match{'es' if match_count > 1 else ''}")
            self.tree_search_prev_button.config(state='normal')
            self.tree_search_next_button.config(state='normal')
            # Select first match
            self.tree_search_current_index = 0
            self._highlight_tree_match(0)
        else:
            self.tree_search_count_label.config(text="No matches found", foreground='red')
            self.tree_search_prev_button.config(state='disabled')
            self.tree_search_next_button.config(state='disabled')
    
    def _search_tree_recursive(self, parent_item, search_term):
        """Recursively search TreeView items."""
        children = self.response_tree.get_children(parent_item)
        
        for item in children:
            # Get item text and value
            item_text = self.response_tree.item(item, 'text')
            item_values = self.response_tree.item(item, 'values')
            item_value = item_values[0] if item_values else ''
            
            # Check if search term matches
            text_match = search_term in item_text.lower()
            value_match = search_term in str(item_value).lower()
            
            if text_match or value_match:
                # Found a match - expand all parents to make it visible
                self._expand_tree_parents(item)
                self.tree_search_matches.append(item)
            
            # Recursively search children
            self._search_tree_recursive(item, search_term)
    
    def _expand_tree_parents(self, item):
        """Expand all parent nodes to make an item visible."""
        parent = self.response_tree.parent(item)
        while parent:
            self.response_tree.item(parent, open=True)
            parent = self.response_tree.parent(parent)
    
    def _highlight_tree_match(self, index):
        """Highlight and scroll to a match at the given index."""
        if 0 <= index < len(self.tree_search_matches):
            item = self.tree_search_matches[index]
            
            # Clear previous selection
            self.response_tree.selection_remove(self.response_tree.selection())
            
            # Select current match
            self.response_tree.selection_set(item)
            self.response_tree.focus(item)
            
            # Expand parents and scroll to item
            self._expand_tree_parents(item)
            self.response_tree.see(item)
            
            # Update match count display
            self.tree_search_count_label.config(
                text=f"Match {index + 1} of {len(self.tree_search_matches)}",
                foreground='blue'
            )
    
    def search_tree_next(self):
        """Navigate to next search match."""
        if self.tree_search_matches:
            self.tree_search_current_index = (self.tree_search_current_index + 1) % len(self.tree_search_matches)
            self._highlight_tree_match(self.tree_search_current_index)
    
    def search_tree_previous(self):
        """Navigate to previous search match."""
        if self.tree_search_matches:
            self.tree_search_current_index = (self.tree_search_current_index - 1) % len(self.tree_search_matches)
            self._highlight_tree_match(self.tree_search_current_index)
    
    def clear_tree_search(self):
        """Clear search and reset TreeView state."""
        self.tree_search_var.set("")
        self.tree_search_matches = []
        self.tree_search_current_index = -1
        self.tree_search_term = ""
        self.tree_search_count_label.config(text="")
        self.tree_search_prev_button.config(state='disabled')
        self.tree_search_next_button.config(state='disabled')
        
        # Clear selection
        self.response_tree.selection_remove(self.response_tree.selection())
    
    def select_http_file(self):
        """Open file dialog to select an HTTP file."""
        # Get the default directory (same directory as current file or default location)
        default_dir = Path(self.http_file_path).parent if self.http_file_path else str(
            Path(__file__).parent.parent / "Informatica-API-RestClient" / "API (Rest Client)")
        
        # Open file dialog
        file_path = filedialog.askopenfilename(
            title="Select HTTP File",
            initialdir=str(default_dir),
            filetypes=[("HTTP files", "*.http"), ("All files", "*.*")]
        )
        
        if file_path:
            # Update the HTTP file path
            self.http_file_path = file_path
            
            # Save the selected file path
            self.save_selected_file_path(file_path)
            
            # Update the label
            self.selected_file_label.config(text=f"File: {Path(file_path).name}")
            
            # Clear current state
            self.current_endpoint = None
            self.search_var.set("")
            
            # Reload endpoints and variables
            self.load_endpoints()
            
            logger.info(f"Selected HTTP file: {file_path}")
    
    def save_selected_file_path(self, file_path: str):
        """Save the selected HTTP file path to config file."""
        try:
            config = {}
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            config['last_selected_file'] = file_path
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            logger.debug(f"Saved selected file path: {file_path}")
        except Exception as e:
            logger.error(f"Error saving selected file path: {e}")
    
    def load_selected_file_path(self) -> Optional[str]:
        """Load the last selected HTTP file path from config file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    file_path = config.get('last_selected_file')
                    if file_path and Path(file_path).exists():
                        logger.debug(f"Loaded selected file path: {file_path}")
                        return file_path
        except Exception as e:
            logger.error(f"Error loading selected file path: {e}")
        return None
    
    def load_endpoints(self):
        """Load endpoints from the HTTP file."""
        try:
            self.status_var.set("Loading endpoints...")
            self.parser = HttpParser(self.http_file_path)
            self.all_endpoints = self.parser.parse()
            self.filtered_endpoints = self.all_endpoints.copy()
            self.update_endpoint_dropdown(preserve_selection=False)
            # After loading, try to select the last run endpoint
            self.select_last_run_endpoint()
            self.populate_variables_tab()
            self.status_var.set(f"Loaded {len(self.all_endpoints)} endpoints")
        except FileNotFoundError:
            messagebox.showerror("Error", f"File not found: {self.http_file_path}")
            self.status_var.set("Error: File not found")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load endpoints: {str(e)}")
            self.status_var.set(f"Error: {str(e)}")
            logger.error(f"Error loading endpoints: {e}", exc_info=True)
    
    def decode_token_claims(self, token: str) -> Optional[dict]:
        """Decode JWT token and return claims."""
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return None
            
            payload = parts[1]
            padding = len(payload) % 4
            if padding:
                payload += '=' * (4 - padding)
            
            decoded_bytes = base64.urlsafe_b64decode(payload)
            return json.loads(decoded_bytes)
        except Exception:
            return None
    
    def check_token_expiration(self, token: str) -> Tuple[bool, Optional[str], Optional[datetime], Optional[dict]]:
        """
        Check if a JWT token is expired and return claims.
        Returns: (is_expired, status_message, expiration_datetime, claims)
        """
        try:
            # Decode token
            payload_data = self.decode_token_claims(token)
            if not payload_data:
                return False, "Not a valid JWT token", None, None
            
            # Get expiration time (exp is Unix timestamp)
            exp_timestamp = payload_data.get('exp')
            iat_timestamp = payload_data.get('iat')  # Issued at
            aud = payload_data.get('aud', '')
            roles = payload_data.get('roles', [])
            scp = payload_data.get('scp', '')
            
            if exp_timestamp:
                exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
                current_time = datetime.now(timezone.utc)
                
                if current_time >= exp_datetime:
                    # Token is expired
                    return True, "EXPIRED", exp_datetime, payload_data
                else:
                    # Token is still valid
                    # Calculate time until expiration
                    time_remaining = exp_datetime - current_time
                    hours = int(time_remaining.total_seconds() // 3600)
                    minutes = int((time_remaining.total_seconds() % 3600) // 60)
                    
                    # Build status message with diagnostics
                    status_parts = []
                    
                    # Get issued time if available
                    if iat_timestamp:
                        iat_datetime = datetime.fromtimestamp(iat_timestamp, tz=timezone.utc)
                        refreshed_str = iat_datetime.strftime("%Y-%m-%d %H:%M:%S UTC")
                        status_parts.append(f"refreshed: {refreshed_str}")
                    
                    # Check audience
                    if aud != 'https://graph.microsoft.com':
                        status_parts.append(f"⚠️ aud: {aud}")
                    
                    # Check permissions
                    if not roles and not scp:
                        status_parts.append("⚠️ No roles/scp")
                    elif roles:
                        status_parts.append(f"roles: {len(roles)}")
                    
                    if status_parts:
                        status = f"Valid ({', '.join(status_parts)})"
                    else:
                        status = f"Valid (expires in {hours}h {minutes}m)"
                    
                    return False, status, exp_datetime, payload_data
            
            return False, "No expiration info", None, payload_data
            
        except Exception as e:
            return False, f"Error: {str(e)[:30]}", None, None
    
    def populate_variables_tab(self):
        """Populate the Variables tab with variables from the parser."""
        logger.debug("populate_variables_tab called")
        
        # Check if tree exists
        if not hasattr(self, 'variables_tree'):
            logger.warning("variables_tree does not exist yet")
            return
        
        # Clear existing items
        existing_items = self.variables_tree.get_children()
        logger.debug(f"Clearing {len(existing_items)} existing items")
        for item in existing_items:
            self.variables_tree.delete(item)
        
        # Add variables from parser
        if self.parser and self.parser.variables:
            logger.debug(f"Found {len(self.parser.variables)} variables in parser")
            for var_name, var_value in sorted(self.parser.variables.items()):
                logger.debug(f"Adding variable: @{var_name} (value length: {len(var_value) if var_value else 0})")
                # Check if this is a token variable and validate it
                status = ""
                if var_name == 'graph_token' and var_value:
                    is_expired, status_msg, exp_datetime, claims = self.check_token_expiration(var_value)
                    status = status_msg
                    # Color code: red for expired, green for valid, orange for warnings
                    if is_expired:
                        tags = (var_name, 'expired')
                    elif '⚠️' in status_msg:
                        tags = (var_name, 'warning')
                    else:
                        tags = (var_name, 'valid')
                else:
                    tags = (var_name,)
                
                # Show full value (treeview will handle scrolling for long values)
                item_id = self.variables_tree.insert(
                    '',
                    tk.END,
                    text=f"@{var_name}",
                    values=(var_value, status),
                    tags=tags
                )
                logger.debug(f"Inserted tree item: {item_id} for variable @{var_name}")
        
        # Configure tag colors
        self.variables_tree.tag_configure('expired', foreground='red')
        self.variables_tree.tag_configure('valid', foreground='green')
        self.variables_tree.tag_configure('warning', foreground='orange')
    
    def on_variable_double_click(self, event):
        """Handle double-click on variable to edit its value."""
        logger.debug(f"Double-click event: x={event.x}, y={event.y}")
        
        # Select the item under the cursor first
        item = self.variables_tree.identify_row(event.y)
        logger.debug(f"Identified row item: {item}")
        
        if not item:
            logger.warning("No item identified at click position")
            return
        
        # Select the item
        self.variables_tree.selection_set(item)
        logger.debug(f"Selected item: {item}")
        
        # Get the column that was clicked
        try:
            region = self.variables_tree.identify_region(event.x, event.y)
            column = self.variables_tree.identify_column(event.x)
            logger.debug(f"Region: {region}, Column: {column}")
        except Exception as e:
            logger.error(f"Error identifying region/column: {e}")
            return
        
        # Only allow editing the Value column (column #1 - first data column)
        if region == 'cell' and column == '#1':
            logger.info(f"Value column clicked, opening edit dialog")
            # Get current variable name and value
            var_name_with_at = self.variables_tree.item(item, 'text')
            var_name = var_name_with_at.replace('@', '')
            values = self.variables_tree.item(item, 'values')
            logger.debug(f"Item text: {var_name_with_at}, Values: {values}")
            
            if values and len(values) > 0:
                current_value = values[0]
                logger.info(f"Editing variable: @{var_name} = {current_value[:50]}...")
                # Show edit dialog
                self.edit_variable_value(var_name, current_value, item)
            else:
                logger.warning(f"No value found for item {item}")
        else:
            logger.debug(f"Not Value column - Region: {region}, Column: {column} (expected: cell, #1)")
    
    def on_variable_right_click(self, event):
        """Handle right-click on variable to show context menu."""
        logger.debug(f"Right-click event: x={event.x}, y={event.y}")
        
        # Select the item under the cursor
        item = self.variables_tree.identify_row(event.y)
        logger.debug(f"Identified row item: {item}")
        
        if item:
            # Clear previous selection and select the clicked item
            self.variables_tree.selection_set(item)
            logger.debug(f"Selected item: {item}")
            
            # Get the column that was clicked
            try:
                region = self.variables_tree.identify_region(event.x, event.y)
                column = self.variables_tree.identify_column(event.x)
                logger.debug(f"Region: {region}, Column: {column}")
            except Exception as e:
                logger.error(f"Error identifying region/column: {e}")
                return
            
            # Only show menu for Value column (column #1 - first data column)
            if region == 'cell' and column == '#1':
                logger.info("Value column right-clicked, showing context menu")
                # Create context menu
                context_menu = tk.Menu(self.root, tearoff=0)
                context_menu.add_command(label="Edit", command=lambda: self._edit_selected_variable())
                
                # Show menu at cursor position
                try:
                    context_menu.tk_popup(event.x_root, event.y_root)
                finally:
                    context_menu.grab_release()
            else:
                logger.debug(f"Not Value column - Region: {region}, Column: {column} (expected: cell, #1)")
        else:
            logger.warning("No item identified at right-click position")
    
    def _edit_selected_variable(self):
        """Edit the currently selected variable."""
        logger.debug("_edit_selected_variable called")
        
        # Get the selected item
        selection = self.variables_tree.selection()
        logger.debug(f"Current selection: {selection}")
        
        if not selection:
            logger.warning("No item selected")
            return
        
        item = selection[0]
        logger.debug(f"Selected item: {item}")
        
        # Get current variable name and value
        var_name_with_at = self.variables_tree.item(item, 'text')
        values = self.variables_tree.item(item, 'values')
        logger.debug(f"Item text: {var_name_with_at}, Values: {values}")
        
        var_name = var_name_with_at.replace('@', '')
        
        if values and len(values) > 0:
            current_value = values[0]
            logger.info(f"Editing variable: @{var_name} = {current_value[:50]}...")
            # Show edit dialog
            self.edit_variable_value(var_name, current_value, item)
        else:
            logger.error(f"No value found for item {item}")
            messagebox.showerror("Error", f"No value found for variable {var_name_with_at}")
    
    def edit_variable_value(self, var_name: str, current_value: str, tree_item):
        """Show dialog to edit variable value and update HTTP file."""
        logger.info(f"Opening edit dialog for variable: @{var_name}")
        logger.debug(f"Current value length: {len(current_value)}")
        
        # Create edit dialog
        edit_window = tk.Toplevel(self.root)
        edit_window.title(f"Edit Variable: @{var_name}")
        edit_window.geometry("500x150")
        edit_window.transient(self.root)
        edit_window.grab_set()
        
        # Variable name label
        ttk.Label(edit_window, text=f"Variable: @{var_name}", font=('Arial', 10, 'bold')).pack(pady=10)
        
        # Value entry
        value_frame = ttk.Frame(edit_window, padding="10")
        value_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(value_frame, text="Value:").grid(row=0, column=0, sticky=tk.W, padx=5)
        value_var = tk.StringVar(value=current_value)
        value_entry = ttk.Entry(value_frame, textvariable=value_var, width=60)
        value_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        value_entry.select_range(0, tk.END)
        value_entry.focus()
        value_frame.columnconfigure(1, weight=1)
        
        # Buttons
        button_frame = ttk.Frame(edit_window)
        button_frame.pack(pady=10)
        
        def save_value():
            new_value = value_var.get().strip()
            logger.info(f"Saving variable @{var_name}: old='{current_value[:50]}...', new='{new_value[:50]}...'")
            
            if new_value != current_value:
                # Update variable in parser
                if self.parser:
                    logger.debug(f"Updating parser variable: {var_name}")
                    self.parser.variables[var_name] = new_value
                else:
                    logger.error("Parser is None, cannot update variable")
                
                # Update variable in HTTP file
                logger.debug(f"Updating variable in HTTP file: {var_name}")
                if self.update_variable_in_file(var_name, new_value):
                    logger.info(f"Successfully updated variable @{var_name} in file")
                    # Update endpoints that use this variable
                    self.update_endpoints_with_variable(var_name, new_value)
                    
                    # Refresh the variables tab
                    self.populate_variables_tab()
                    
                    # Refresh endpoint dropdown if needed
                    self.update_endpoint_dropdown()
                    
                    self.status_var.set(f"Variable @{var_name} updated successfully")
                else:
                    logger.error(f"Failed to update variable @{var_name} in file")
                    messagebox.showerror("Error", f"Failed to update variable @{var_name} in file")
            else:
                logger.debug("Value unchanged, skipping update")
            edit_window.destroy()
        
        def cancel():
            edit_window.destroy()
        
        ttk.Button(button_frame, text="Save", command=save_value).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=cancel).pack(side=tk.LEFT, padx=5)
        
        # Bind Enter key to save
        value_entry.bind('<Return>', lambda e: save_value())
        value_entry.bind('<Escape>', lambda e: cancel())
        
        # Center the window
        edit_window.update_idletasks()
        x = (edit_window.winfo_screenwidth() // 2) - (edit_window.winfo_width() // 2)
        y = (edit_window.winfo_screenheight() // 2) - (edit_window.winfo_height() // 2)
        edit_window.geometry(f"+{x}+{y}")
    
    def update_variable_in_file(self, var_name: str, new_value: str) -> bool:
        """
        Update a variable in the HTTP file.
        Returns True if successful, False otherwise.
        """
        logger.debug(f"update_variable_in_file called: var_name={var_name}, new_value length={len(new_value)}")
        logger.debug(f"HTTP file path: {self.http_file_path}")
        
        try:
            # Read the file
            logger.debug("Reading HTTP file...")
            with open(self.http_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            logger.debug(f"Read {len(lines)} lines from file")
            
            # Find and replace the variable line
            updated = False
            search_pattern = f'@{var_name}='
            logger.debug(f"Searching for pattern: {search_pattern}")
            
            for i, line in enumerate(lines):
                # Look for @variable_name= pattern
                if line.strip().startswith(search_pattern):
                    logger.debug(f"Found variable at line {i+1}: {line.strip()[:100]}")
                    # Replace the value after the = sign
                    # Preserve any comments or formatting after the value
                    if '#' in line:
                        # Has comment, preserve it
                        comment_part = line[line.find('#'):]
                        lines[i] = f"@{var_name}={new_value}{comment_part}"
                        logger.debug(f"Updated line with comment: {lines[i][:100]}")
                    else:
                        # No comment, just replace the value
                        # Preserve the newline
                        if line.endswith('\n'):
                            lines[i] = f"@{var_name}={new_value}\n"
                        else:
                            lines[i] = f"@{var_name}={new_value}"
                        logger.debug(f"Updated line: {lines[i][:100]}")
                    updated = True
                    break
            
            if not updated:
                logger.warning(f"Variable @{var_name} not found in file")
            
            if updated:
                # Write back to file
                with open(self.http_file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                return True
            else:
                # Variable line not found, try to add it after other variables
                for i, line in enumerate(lines):
                    if line.strip().startswith('@') and '=' in line:
                        # Insert after this line
                        lines.insert(i + 1, f"@{var_name}={new_value}\n")
                        updated = True
                        break
                
                if updated:
                    with open(self.http_file_path, 'w', encoding='utf-8') as f:
                        f.writelines(lines)
                    return True
            
            logger.warning(f"Variable @{var_name} not found in file, attempting to add it")
            return False
        except Exception as e:
            logger.error(f"Error updating variable in file: {e}", exc_info=True)
            return False
    
    def update_endpoints_with_variable(self, var_name: str, new_value: str):
        """Update endpoints that use the changed variable."""
        if not self.parser:
            return
        
        logger.debug(f"Updating endpoints with variable: {var_name}")
        
        # Special handling for graph_token: update Authorization headers directly
        if var_name == 'graph_token':
            # Re-parse all endpoints to get fresh headers with new token
            # This is necessary because headers are already substituted during initial parsing
            logger.info("Re-parsing endpoints to update Authorization headers with new token")
            self.all_endpoints = self.parser.parse()
            self.filtered_endpoints = self.all_endpoints.copy()
            # Update dropdown to reflect any changes
            self.update_endpoint_dropdown(preserve_selection=True)
            logger.info(f"Re-parsed {len(self.all_endpoints)} endpoints with new token")
            return
        
        # For other variables, update in-place if they still have the template
        # Re-substitute variables in all endpoints
        for endpoint in self.all_endpoints:
            # Update URL if it contains the variable
            if f'{{{{{var_name}}}}}' in endpoint.original_url:
                endpoint.url = endpoint.original_url.replace(f'{{{{{var_name}}}}}', new_value)
            
            # Update headers if they contain the variable template
            for header_name, header_value in endpoint.headers.items():
                if f'{{{{{var_name}}}}}' in header_value:
                    endpoint.headers[header_name] = header_value.replace(f'{{{{{var_name}}}}}', new_value)
            
            # Update body if it contains the variable
            if f'{{{{{var_name}}}}}' in endpoint.body:
                endpoint.body = endpoint.body.replace(f'{{{{{var_name}}}}}', new_value)
        
        # Also update filtered endpoints
        for endpoint in self.filtered_endpoints:
            if f'{{{{{var_name}}}}}' in endpoint.original_url:
                endpoint.url = endpoint.original_url.replace(f'{{{{{var_name}}}}}', new_value)
            
            for header_name, header_value in endpoint.headers.items():
                if f'{{{{{var_name}}}}}' in header_value:
                    endpoint.headers[header_name] = header_value.replace(f'{{{{{var_name}}}}}', new_value)
            
            if f'{{{{{var_name}}}}}' in endpoint.body:
                endpoint.body = endpoint.body.replace(f'{{{{{var_name}}}}}', new_value)
    
    def update_graph_token_in_file(self, new_token: str) -> bool:
        """
        Update the @graph_token variable in the HTTP file.
        Returns True if successful, False otherwise.
        """
        try:
            # Read the file
            with open(self.http_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Find and replace the graph_token line
            updated = False
            for i, line in enumerate(lines):
                # Look for @graph_token= pattern
                if line.strip().startswith('@graph_token='):
                    # Replace the value after the = sign
                    # Preserve any comments or formatting after the value
                    if '#' in line:
                        # Has comment, preserve it
                        comment_part = line[line.find('#'):]
                        lines[i] = f"@graph_token={new_token}{comment_part}"
                    else:
                        # No comment, just replace the value
                        lines[i] = f"@graph_token={new_token}\n"
                    updated = True
                    break
            
            if updated:
                # Write back to file
                with open(self.http_file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                return True
            else:
                # Token line not found, try to add it after @scope or @grant_type
                for i, line in enumerate(lines):
                    if line.strip().startswith('@scope=') or line.strip().startswith('@grant_type='):
                        # Insert after this line
                        lines.insert(i + 1, f"@graph_token={new_token}\n")
                        updated = True
                        break
                
                if updated:
                    with open(self.http_file_path, 'w', encoding='utf-8') as f:
                        f.writelines(lines)
                    return True
            
            return False
        except Exception as e:
            print(f"Error updating token in file: {e}")
            return False
    
    def on_search_changed(self, *args):
        """Handle search filter changes."""
        search_text = self.search_var.get().lower()
        
        if not search_text:
            self.filtered_endpoints = self.all_endpoints.copy()
        else:
            self.filtered_endpoints = [
                ep for ep in self.all_endpoints
                if search_text in ep.url.lower() 
                or search_text in ep.method.lower()
                or search_text in ep.description.lower()
            ]
        
        self.update_endpoint_dropdown()
    
    def update_endpoint_dropdown(self, preserve_selection: bool = True):
        """Update the endpoint dropdown with filtered endpoints.
        
        Args:
            preserve_selection: If True, try to preserve the current selection after update.
        """
        logger.debug(f"update_endpoint_dropdown called, preserve_selection={preserve_selection}")
        
        # Show original URL with variables (no last run time in dropdown)
        display_names = [ep.get_display_name() for ep in self.filtered_endpoints]
        logger.debug(f"Display names count: {len(display_names)}")
        
        # Try to preserve current selection
        current_selection = None
        if preserve_selection and self.current_endpoint:
            try:
                current_index = self.endpoint_combo.current()
                logger.debug(f"Current dropdown index: {current_index}")
                if current_index >= 0:
                    current_values = self.endpoint_combo['values']
                    if current_values and current_index < len(current_values):
                        current_display_name = current_values[current_index]
                        logger.debug(f"Current display name: {current_display_name}")
                        # Try to find the same endpoint in the new list
                        if current_display_name in display_names:
                            current_selection = display_names.index(current_display_name)
                            logger.debug(f"Found current endpoint at new index: {current_selection}")
                        else:
                            logger.debug(f"Current endpoint not found in new list, will reset to 0")
                    else:
                        # Use current_endpoint to find it in the new list
                        current_endpoint_display = self.current_endpoint.get_display_name()
                        if current_endpoint_display in display_names:
                            current_selection = display_names.index(current_endpoint_display)
                            logger.debug(f"Found current endpoint by object at index: {current_selection}")
            except (IndexError, tk.TclError) as e:
                logger.debug(f"Error preserving selection: {e}")
        
        self.endpoint_combo['values'] = display_names
        
        if display_names:
            if current_selection is not None and current_selection < len(display_names):
                logger.info(f"Preserving selection at index {current_selection}")
                self.endpoint_combo.current(current_selection)
            else:
                logger.debug(f"Resetting to index 0 (current_selection={current_selection})")
                self.endpoint_combo.current(0)
            self.on_endpoint_selected()
    
    def load_run_history(self):
        """Load endpoint run history from file."""
        try:
            if self.run_history_file.exists():
                with open(self.run_history_file, 'r', encoding='utf-8') as f:
                    self.last_run_times = json.load(f)
                logger.debug(f"Loaded {len(self.last_run_times)} entries from run history")
            else:
                logger.debug("Run history file does not exist yet")
                self.last_run_times = {}
        except Exception as e:
            logger.error(f"Error loading run history: {e}")
            self.last_run_times = {}
    
    def select_last_run_endpoint(self):
        """Select the most recently run endpoint from history."""
        if not self.last_run_times:
            logger.debug("No run history available")
            return
        
        # Find the most recently run endpoint
        most_recent_key = None
        most_recent_time = None
        
        for endpoint_key, run_time in self.last_run_times.items():
            if most_recent_time is None or run_time > most_recent_time:
                most_recent_time = run_time
                most_recent_key = endpoint_key
        
        if not most_recent_key:
            logger.debug("No recent endpoint found in history")
            return
        
        logger.info(f"Most recently run endpoint: {most_recent_key} at {most_recent_time}")
        
        # Find matching endpoint in filtered_endpoints
        for i, endpoint in enumerate(self.filtered_endpoints):
            endpoint_key = f"{endpoint.method} {endpoint.original_url}"
            if endpoint_key == most_recent_key:
                logger.info(f"Found matching endpoint at index {i}, selecting it")
                self.endpoint_combo.current(i)
                self.on_endpoint_selected()
                return
        
        logger.debug(f"Could not find matching endpoint for key: {most_recent_key}")
    
    def save_run_history(self):
        """Save endpoint run history to file."""
        try:
            with open(self.run_history_file, 'w', encoding='utf-8') as f:
                json.dump(self.last_run_times, f, indent=2)
        except Exception as e:
            print(f"Error saving run history: {e}")
    
    def record_endpoint_run(self, endpoint: ApiEndpoint):
        """Record when an endpoint was last run."""
        endpoint_key = f"{endpoint.method} {endpoint.original_url}"
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.last_run_times[endpoint_key] = current_time
        self.save_run_history()
        
        # Update last run time label without resetting dropdown selection
        if self.current_endpoint:
            endpoint_key_current = f"{self.current_endpoint.method} {self.current_endpoint.original_url}"
            if endpoint_key_current == endpoint_key:
                self.last_run_label.config(text=f"Last run: {current_time}")
    
    def copy_url_to_clipboard(self):
        """Copy the current endpoint URL to clipboard."""
        if self.current_endpoint:
            url_to_copy = self.current_endpoint.url  # Copy the actual URL (with variables substituted)
            self.root.clipboard_clear()
            self.root.clipboard_append(url_to_copy)
            self.status_var.set(f"URL copied to clipboard: {url_to_copy[:50]}...")
        else:
            messagebox.showinfo("Copy URL", "No endpoint selected")
    
    def on_endpoint_selected(self, event=None):
        """Handle endpoint selection."""
        selection = self.endpoint_combo.current()
        if selection >= 0 and selection < len(self.filtered_endpoints):
            self.current_endpoint = self.filtered_endpoints[selection]
            
            # Update description label
            if self.current_endpoint.description:
                self.description_label.config(text=self.current_endpoint.description)
            else:
                self.description_label.config(text="")
            
            # Update last run time label
            endpoint_key = f"{self.current_endpoint.method} {self.current_endpoint.original_url}"
            last_run = self.last_run_times.get(endpoint_key)
            if last_run:
                self.last_run_label.config(text=f"Last run: {last_run}")
            else:
                self.last_run_label.config(text="")
            
            self.status_var.set(f"Selected: {self.current_endpoint.method} {self.current_endpoint.original_url}")
    
    def run_request(self):
        """Execute the selected HTTP request."""
        if not self.current_endpoint:
            messagebox.showwarning("Warning", "Please select an endpoint first.")
            return
        
        try:
            self.status_var.set("Executing request...")
            self.run_button.config(state='disabled')
            self.response_text.delete(1.0, tk.END)
            
            # Prepare request
            endpoint = self.current_endpoint
            method = endpoint.method.upper()
            url = endpoint.url
            
            # Prepare headers
            headers = endpoint.headers.copy()
            
            # Prepare body
            data = None
            json_data = None
            if endpoint.body:
                # Check if Content-Type indicates form-urlencoded
                content_type = headers.get('Content-Type', '').lower()
                is_form_urlencoded = 'application/x-www-form-urlencoded' in content_type
                
                if is_form_urlencoded:
                    # Parse form-urlencoded data into dictionary
                    try:
                        # Split by & and then by = to create key-value pairs
                        form_data = {}
                        for pair in endpoint.body.strip().split('&'):
                            if '=' in pair:
                                key, value = pair.split('=', 1)
                                # URL decode if needed (basic handling)
                                form_data[key.strip()] = value.strip()
                        data = form_data
                    except Exception:
                        # Fallback to string if parsing fails
                        data = endpoint.body.strip()
                else:
                    try:
                        # Try to parse as JSON
                        json_data = json.loads(endpoint.body)
                        if 'Content-Type' not in headers:
                            headers['Content-Type'] = 'application/json'
                    except json.JSONDecodeError:
                        # Not JSON, use as raw data
                        data = endpoint.body.strip()
                        if 'Content-Type' not in headers:
                            headers['Content-Type'] = 'application/x-www-form-urlencoded'
            
            # Execute request
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=json_data,
                data=data,
                timeout=30
            )
            
            # Record that this endpoint was run
            self.record_endpoint_run(endpoint)
            
            # Format response for raw JSON display (Response tab)
            response_text = self.format_response_raw(response)
            self.response_text.delete(1.0, tk.END)
            self.response_text.insert(1.0, response_text)
            
            # Apply color to status line in response text
            status_tag = self.get_status_tag(response.status_code)
            status_line_start = "1.0"
            # Find the end of the first line (status line)
            status_line_end = "1.0 lineend"
            self.response_text.tag_add(status_tag, status_line_start, status_line_end)
            
            # Populate TreeView (ResponseTree tab)
            self.populate_response_tree(response)
            
            # Check for 401 errors and provide diagnostics
            if response.status_code == 401:
                # Try to decode token and show diagnostics
                auth_header = headers.get('Authorization', '')
                if auth_header.startswith('Bearer '):
                    token = auth_header.replace('Bearer ', '').strip()
                    claims = self.decode_token_claims(token)
                    if claims:
                        diagnostics = []
                        aud = claims.get('aud', '')
                        roles = claims.get('roles', [])
                        scp = claims.get('scp', '')
                        exp = claims.get('exp')
                        
                        if aud != 'https://graph.microsoft.com':
                            diagnostics.append(f"⚠️ Wrong audience: {aud} (expected: https://graph.microsoft.com)")
                        
                        if not roles and not scp:
                            diagnostics.append("⚠️ No roles or scp found in token")
                        elif roles:
                            diagnostics.append(f"Token has {len(roles)} role(s): {', '.join(roles[:3])}")
                        
                        if exp:
                            exp_time = datetime.fromtimestamp(exp, tz=timezone.utc)
                            current_time = datetime.now(timezone.utc)
                            if current_time >= exp_time:
                                diagnostics.append("⚠️ Token is expired")
                        
                        if diagnostics:
                            diagnostic_text = "\n\n401 Diagnostic Info:\n" + "\n".join(f"  {d}" for d in diagnostics)
                            response_text += diagnostic_text
                            self.response_text.delete(1.0, tk.END)
                            self.response_text.insert(1.0, response_text)
                            # Re-apply color to status line after re-inserting text
                            status_tag = self.get_status_tag(response.status_code)
                            self.response_text.tag_add(status_tag, "1.0", "1.0 lineend")
            
            # Check if this is OAuth token endpoint and update token if successful
            if response.status_code == 200 and 'oauth2/v2.0/token' in url.lower():
                try:
                    response_json = response.json()
                    if 'access_token' in response_json:
                        new_token = response_json['access_token']
                        # Update the graph_token variable in parser
                        if self.parser:
                            self.parser.variables['graph_token'] = new_token
                            
                            # CRITICAL: Update all endpoints with the new token
                            # This re-substitutes {{graph_token}} in URLs, headers, and bodies
                            logger.info("Updating all endpoints with new token")
                            self.update_endpoints_with_variable('graph_token', new_token)
                            
                            # Update the token in the HTTP file
                            if self.update_graph_token_in_file(new_token):
                                # Refresh the Variables tab to show updated token in green
                                self.populate_variables_tab()
                                # Show success message
                                self.status_var.set(f"Status: {response.status_code} {response.reason} - Token updated in file and all endpoints!")
                                self.update_status_bar_color(response.status_code)
                            else:
                                # Update in memory only if file update failed
                                self.populate_variables_tab()
                                self.status_var.set(f"Status: {response.status_code} {response.reason} - Token updated in memory only (file update failed)")
                                self.update_status_bar_color(response.status_code)
                        else:
                            self.status_var.set(f"Status: {response.status_code} {response.reason}")
                            self.update_status_bar_color(response.status_code)
                    else:
                        self.status_var.set(f"Status: {response.status_code} {response.reason}")
                        self.update_status_bar_color(response.status_code)
                except (json.JSONDecodeError, KeyError):
                    # Response is not JSON or doesn't have access_token
                    status_msg = f"Status: {response.status_code} {response.reason}"
                    self.status_var.set(status_msg)
                    self.update_status_bar_color(response.status_code)
                except Exception as e:
                    # Handle any other errors during token update
                    self.status_var.set(f"Status: {response.status_code} {response.reason} - Error updating token: {str(e)}")
                    self.update_status_bar_color(response.status_code)
            else:
                # Update status
                status_msg = f"Status: {response.status_code} {response.reason}"
                self.status_var.set(status_msg)
            
            # Update status bar color based on status code
            self.update_status_bar_color(response.status_code)
            
            # Switch to Response tab to show the result
            self.notebook.select(1)  # Index 1 is the Response tab
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Request Error: {str(e)}"
            self.response_text.delete(1.0, tk.END)
            self.response_text.insert(1.0, error_msg)
            # Switch to Response tab to show the error
            self.notebook.select(1)
            self.status_var.set(error_msg)
            messagebox.showerror("Request Error", str(e))
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.response_text.delete(1.0, tk.END)
            self.response_text.insert(1.0, error_msg)
            # Switch to Response tab to show the error
            self.notebook.select(1)
            self.status_var.set(error_msg)
            messagebox.showerror("Error", str(e))
        finally:
            self.run_button.config(state='normal')
    
    def format_response_raw(self, response: requests.Response) -> str:
        """Format HTTP response as raw JSON text for the Response tab."""
        lines = []
        
        # Status line
        lines.append(f"Status: {response.status_code} {response.reason}\n")
        lines.append("=" * 80 + "\n\n")
        
        # Headers
        lines.append("Headers:\n")
        for key, value in response.headers.items():
            lines.append(f"  {key}: {value}\n")
        lines.append("\n" + "=" * 80 + "\n\n")
        
        # Body
        lines.append("Body:\n")
        try:
            # Try to format as JSON
            json_data = response.json()
            
            # Count items if it's an array
            if isinstance(json_data, list):
                item_count = len(json_data)
                lines.append(f"📊 Total items: {item_count}\n\n")
            elif isinstance(json_data, dict):
                # Check if it's a dict with a common array key
                for key in ['data', 'items', 'results', 'users', 'courses', 'events']:
                    if key in json_data and isinstance(json_data[key], list):
                        item_count = len(json_data[key])
                        lines.append(f"📊 Total {key}: {item_count}\n\n")
                        break
            
            # Format JSON with pretty printing (no collapse markers)
            json_text = json.dumps(json_data, indent=2, ensure_ascii=False)
            lines.append(json_text)
        except (json.JSONDecodeError, ValueError):
            # Not JSON, display as text
            lines.append(response.text)
        
        return ''.join(lines)
    
    def format_response(self, response: requests.Response) -> str:
        """Format HTTP response for display (legacy method, kept for compatibility)."""
        return self.format_response_raw(response)
    
    def get_status_tag(self, status_code: int) -> str:
        """Get the appropriate tag name for a status code."""
        if 200 <= status_code < 300:
            return 'status_2xx'
        elif 300 <= status_code < 400:
            return 'status_3xx'
        elif 400 <= status_code < 500:
            return 'status_4xx'
        elif 500 <= status_code < 600:
            return 'status_5xx'
        else:
            return 'status_other'
    
    def update_status_bar_color(self, status_code: int):
        """Update the status bar color based on HTTP status code."""
        if 200 <= status_code < 300:
            # Success - Green
            self.status_bar.config(foreground='green')
        elif 300 <= status_code < 400:
            # Redirect - Blue
            self.status_bar.config(foreground='blue')
        elif 400 <= status_code < 500:
            # Client Error - Red
            self.status_bar.config(foreground='red')
        elif 500 <= status_code < 600:
            # Server Error - Red
            self.status_bar.config(foreground='red')
        else:
            # Other - Orange
            self.status_bar.config(foreground='orange')
    
    def show_search_dialog(self, event=None):
        """Show search dialog for response text (Ctrl-F functionality)."""
        # Create a simple search dialog
        search_window = tk.Toplevel(self.root)
        search_window.title("Find in Response")
        search_window.geometry("400x100")
        search_window.transient(self.root)
        
        # Search entry
        search_frame = ttk.Frame(search_window, padding="10")
        search_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(search_frame, text="Find:").grid(row=0, column=0, sticky=tk.W, padx=5)
        search_entry = ttk.Entry(search_frame, width=40)
        search_entry.grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E))
        search_entry.focus()
        
        # Buttons
        button_frame = ttk.Frame(search_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        def highlight_all_matches(search_text):
            """Highlight all matches in the text."""
            # Clear previous highlights
            self.response_text.tag_remove('search_highlight', 1.0, tk.END)
            self.response_text.tag_remove('search_current', 1.0, tk.END)
            
            if not search_text:
                return
            
            # Find and highlight all matches
            start_pos = 1.0
            matches = []
            while True:
                pos = self.response_text.search(
                    search_text,
                    start_pos,
                    tk.END,
                    nocase=True
                )
                if not pos:
                    break
                end_pos = f"{pos}+{len(search_text)}c"
                matches.append((pos, end_pos))
                self.response_text.tag_add('search_highlight', pos, end_pos)
                start_pos = end_pos
            
            return matches
        
        def find_next():
            search_text = search_entry.get()
            if not search_text:
                return
            
            # Highlight all matches first
            matches = highlight_all_matches(search_text)
            
            if not matches:
                messagebox.showinfo("Find", "Text not found")
                return
            
            # Get current cursor position
            current_pos = self.response_text.index(tk.INSERT)
            
            # Find next match after current position
            next_match = None
            for pos, end_pos in matches:
                if self.response_text.compare(pos, '>', current_pos):
                    next_match = (pos, end_pos)
                    break
            
            # If no match after current, wrap to first
            if not next_match:
                next_match = matches[0]
            
            # Highlight current match with different color
            pos, end_pos = next_match
            self.response_text.tag_remove('search_current', 1.0, tk.END)
            self.response_text.tag_add('search_current', pos, end_pos)
            self.response_text.mark_set(tk.INSERT, end_pos)
            self.response_text.see(pos)
        
        def find_prev():
            search_text = search_entry.get()
            if not search_text:
                return
            
            # Highlight all matches first
            matches = highlight_all_matches(search_text)
            
            if not matches:
                messagebox.showinfo("Find", "Text not found")
                return
            
            # Get current cursor position
            current_pos = self.response_text.index(tk.INSERT)
            
            # Find previous match before current position
            prev_match = None
            for pos, end_pos in reversed(matches):
                if self.response_text.compare(pos, '<', current_pos):
                    prev_match = (pos, end_pos)
                    break
            
            # If no match before current, wrap to last
            if not prev_match:
                prev_match = matches[-1]
            
            # Highlight current match with different color
            pos, end_pos = prev_match
            self.response_text.tag_remove('search_current', 1.0, tk.END)
            self.response_text.tag_add('search_current', pos, end_pos)
            self.response_text.mark_set(tk.INSERT, pos)
            self.response_text.see(pos)
        
        ttk.Button(button_frame, text="Find Next", command=find_next).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Find Previous", command=find_prev).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=search_window.destroy).pack(side=tk.LEFT, padx=5)
        
        # Bind Enter key to find next
        search_entry.bind('<Return>', lambda e: find_next())
        
        # Center the window
        search_window.update_idletasks()
        x = (search_window.winfo_screenwidth() // 2) - (search_window.winfo_width() // 2)
        y = (search_window.winfo_screenheight() // 2) - (search_window.winfo_height() // 2)
        search_window.geometry(f"+{x}+{y}")
