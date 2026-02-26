"""
Main entry point for REST Client GUI Application.
"""

import tkinter as tk
import sys
import os
from pathlib import Path
from rest_client_gui import RestClientGUI


def get_http_file_path():
    """Get the path to the HTTP file (loads last selected or defaults to Teams.http)."""
    script_dir = Path(__file__).parent
    config_file = script_dir / '.rest_client_config.json'
    
    # Try to load last selected file
    try:
        if config_file.exists():
            import json
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                file_path = config.get('last_selected_file')
                if file_path and Path(file_path).exists():
                    return str(file_path)
    except Exception:
        pass  # Fall through to default
    
    # Default path relative to this script
    default_path = script_dir.parent / "Informatica-API-RestClient" / "API (Rest Client)" / "Teams.http"
    
    # Check if default path exists
    if default_path.exists():
        return str(default_path)
    
    # If not found, try absolute path
    absolute_path = Path(r"c:\Works\Informatica-API-RestClient\API (Rest Client)\Teams.http")
    if absolute_path.exists():
        return str(absolute_path)
    
    # If still not found, return the default path (user will get error message)
    return str(default_path)


def main():
    """Main function to start the application."""
    # Get HTTP file path
    http_file_path = get_http_file_path()
    
    # Check if file exists
    if not os.path.exists(http_file_path):
        print(f"Error: HTTP file not found at: {http_file_path}")
        print("\nPlease ensure the Teams.http file exists at the expected location.")
        print("You can also modify the path in main.py")
        sys.exit(1)
    
    # Create and run GUI
    root = tk.Tk()
    app = RestClientGUI(root, http_file_path)
    root.mainloop()


if __name__ == "__main__":
    main()
