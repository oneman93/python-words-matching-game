#!/usr/bin/env python3
"""
Launcher script for Text Matching Game.
Choose between CLI and GUI versions.
"""

import sys

def main():
    print("=" * 60)
    print("Text Matching Game Launcher")
    print("=" * 60)
    print("\nChoose an interface:")
    print("1. Command Line Interface (CLI)")
    print("2. Graphical User Interface (GUI)")
    print("3. Exit")
    
    while True:
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            print("\nStarting CLI version...\n")
            from wordsGame import TextMatchingGame
            game = TextMatchingGame("words.txt")
            game.play()
            break
        elif choice == '2':
            print("\nStarting GUI version...\n")
            try:
                import tkinter as tk
                from wordsGameGUI import TextMatchingGameGUI
                root = tk.Tk()
                app = TextMatchingGameGUI(root)
                root.mainloop()
            except ImportError as e:
                print(f"Error: Could not import GUI module. {e}")
                print("Make sure tkinter is installed.")
                if sys.platform == 'darwin':  # macOS
                    print("On macOS, tkinter should be included with Python.")
                elif sys.platform.startswith('linux'):
                    print("On Linux, install tkinter: sudo apt-get install python3-tk")
                elif sys.platform == 'win32':
                    print("On Windows, tkinter should be included with Python.")
            break
        elif choice == '3':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()
