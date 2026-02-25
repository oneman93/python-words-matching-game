import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from wordsGame import TextMatchingGame
import re

class TextMatchingGameGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("📖 Text Matching Game")
        self.root.geometry("1000x750")
        self.root.configure(bg='#f5f5f5')
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Customize button styles
        style.configure('Accent.TButton', font=('Arial', 11, 'bold'))
        
        # Initialize game
        self.game = TextMatchingGame("words.txt")
        
        # Current game state
        self.current_reference = None
        self.current_text = None
        self.current_test_type = None
        self.current_puzzle = None
        self.attempts = 0
        
        # Create UI
        self.create_widgets()
        
        # Start the game
        self.load_next_puzzle()
    
    def create_widgets(self):
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # Header section
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        header_frame.columnconfigure(1, weight=1)
        
        title_label = ttk.Label(header_frame, text="📖 Text Matching Game", 
                               font=('Arial', 20, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Level and progress info
        self.level_label = ttk.Label(header_frame, text="", font=('Arial', 14, 'bold'))
        self.level_label.grid(row=1, column=0, sticky=tk.W)
        
        self.progress_label = ttk.Label(header_frame, text="", font=('Arial', 12))
        self.progress_label.grid(row=1, column=1, sticky=tk.E)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(header_frame, variable=self.progress_var, 
                                           maximum=100, length=400)
        self.progress_bar.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(row=1, column=0, sticky=(tk.W, tk.E), pady=10)
        
        # Puzzle display section
        puzzle_frame = ttk.LabelFrame(main_frame, text="Puzzle", padding="15")
        puzzle_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        puzzle_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Test type indicator
        self.test_type_label = ttk.Label(puzzle_frame, text="", font=('Arial', 11, 'bold'))
        self.test_type_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        # Reference display (if applicable)
        self.reference_label = ttk.Label(puzzle_frame, text="", font=('Arial', 12, 'italic'))
        self.reference_label.grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        
        # Puzzle text display (scrollable)
        self.puzzle_text = scrolledtext.ScrolledText(puzzle_frame, height=7, width=85,
                                                     wrap=tk.WORD, font=('Courier', 13),
                                                     bg='#ffffff', relief=tk.SUNKEN, 
                                                     borderwidth=2, padx=10, pady=10)
        self.puzzle_text.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        self.puzzle_text.config(state=tk.DISABLED)
        
        # Answer input section
        answer_frame = ttk.LabelFrame(main_frame, text="Your Answer", padding="15")
        answer_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        answer_frame.columnconfigure(0, weight=1)
        
        self.answer_entry = ttk.Entry(answer_frame, font=('Arial', 13), width=60)
        self.answer_entry.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        self.answer_entry.bind('<Return>', lambda e: self.check_answer())
        
        # Buttons
        button_frame = ttk.Frame(answer_frame)
        button_frame.grid(row=1, column=0, columnspan=3)
        
        submit_btn = ttk.Button(button_frame, text="✓ Submit Answer", command=self.check_answer,
                               style='Accent.TButton', width=15)
        submit_btn.grid(row=0, column=0, padx=8)
        
        skip_btn = ttk.Button(button_frame, text="⏭ Skip Puzzle", command=self.skip_puzzle, width=15)
        skip_btn.grid(row=0, column=1, padx=8)
        
        quit_btn = ttk.Button(button_frame, text="✗ Quit Game", command=self.quit_game, width=15)
        quit_btn.grid(row=0, column=2, padx=8)
        
        # Feedback section
        feedback_frame = ttk.LabelFrame(main_frame, text="Feedback & Hints", padding="15")
        feedback_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        feedback_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        self.feedback_text = scrolledtext.ScrolledText(feedback_frame, height=7, width=85,
                                                       wrap=tk.WORD, font=('Arial', 11),
                                                       bg='#fafafa', relief=tk.SUNKEN,
                                                       borderwidth=1, padx=10, pady=10)
        self.feedback_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        feedback_frame.rowconfigure(0, weight=1)
        self.feedback_text.config(state=tk.DISABLED)
        
        # Attempts counter
        self.attempts_label = ttk.Label(main_frame, text="", font=('Arial', 10))
        self.attempts_label.grid(row=5, column=0, pady=(5, 0))
    
    def update_level_info(self):
        """Update level and progress information."""
        level_name = self.game.level_names[self.game.current_level]
        
        if self.game.current_level in [1, 2, 3]:
            hide_pct = int(self.game.hide_percentages[self.game.current_level] * 100)
            level_text = f"Level {level_name} ({hide_pct}% words hidden + reference)"
        else:
            level_text = f"Level {level_name} (reference + text)"
        
        self.level_label.config(text=level_text)
        
        # Update progress
        completed = len(self.game.completed_lines[self.game.current_level])
        total = len(self.game.lines)
        progress_pct = (completed / total * 100) if total > 0 else 0
        
        self.progress_label.config(text=f"Progress: {completed}/{total} verses")
        self.progress_var.set(progress_pct)
    
    def load_next_puzzle(self):
        """Load the next puzzle."""
        reference, text = self.game.get_available_line()
        
        if reference is None:
            # Level completed
            if self.game.current_level < 4:
                self.game.current_level += 1
                self.game.save_progress()
                self.show_message("Level Complete!", 
                                f"Congratulations! Moving to Level {self.game.level_names[self.game.current_level]}...",
                                'info')
                self.load_next_puzzle()
            else:
                # Game complete
                self.show_message("🎉 Congratulations! 🎉",
                                "You've completed all levels of the Text Matching Game!",
                                'info')
                self.root.after(2000, self.quit_game)
            return
        
        self.current_reference = reference
        self.current_text = text
        self.current_test_type = self.game.get_level_test_type(self.game.current_level, reference, text)
        self.current_puzzle = self.game.create_level_puzzle(self.game.current_level, reference, text, self.current_test_type)
        self.attempts = 0
        
        self.display_puzzle()
        self.update_level_info()
        self.clear_feedback()
        self.answer_entry.delete(0, tk.END)
        self.answer_entry.focus()
    
    def display_puzzle(self):
        """Display the current puzzle."""
        # Update test type label
        if self.current_test_type == 'reference':
            self.test_type_label.config(text="Test: Reference (provide the verse reference)", 
                                       foreground='#0066cc')
        elif self.current_test_type == 'words':
            hide_pct = int(self.game.hide_percentages[self.game.current_level] * 100)
            self.test_type_label.config(text=f"Test: Words ({hide_pct}% hidden)", 
                                       foreground='#0066cc')
        elif self.current_test_type == 'text':
            self.test_type_label.config(text="Test: Text (provide the complete verse text)", 
                                       foreground='#0066cc')
        
        # Update reference display
        if self.current_test_type == 'reference':
            self.reference_label.config(text="")
        else:
            self.reference_label.config(text=f"Reference: {self.current_reference}")
        
        # Update puzzle text
        self.puzzle_text.config(state=tk.NORMAL)
        self.puzzle_text.delete(1.0, tk.END)
        
        # Format puzzle text with better visibility
        puzzle_display = self.current_puzzle
        if self.current_test_type != 'reference':
            # Remove reference from puzzle for display (it's shown separately)
            puzzle_display = self.current_puzzle[len(self.current_reference):].strip()
        else:
            # For reference test, show the puzzle as-is
            puzzle_display = self.current_puzzle
        
        # Insert text and highlight blanks
        self.puzzle_text.insert(1.0, puzzle_display)
        
        # Highlight blanks (words starting with _)
        self.puzzle_text.tag_config("blank", foreground="#cc0000", font=('Courier', 13, 'bold'), 
                                   background="#fff3cd")
        start = "1.0"
        while True:
            # Find next blank (sequence of underscores)
            pos = self.puzzle_text.search("_", start, tk.END)
            if not pos:
                break
            # Find the end of this blank (until space or end of word)
            end_pos = pos
            while True:
                next_char = self.puzzle_text.get(end_pos, f"{end_pos}+1c")
                if next_char in [' ', '\n', '\t', '']:
                    break
                end_pos = f"{end_pos}+1c"
            # Tag the blank
            self.puzzle_text.tag_add("blank", pos, end_pos)
            start = end_pos
        
        self.puzzle_text.config(state=tk.DISABLED)
        
        # Update attempts
        self.attempts_label.config(text="")
    
    def check_answer(self):
        """Check the user's answer."""
        user_answer = self.answer_entry.get().strip()
        
        if not user_answer:
            return
        
        if user_answer.lower() == 'quit':
            self.quit_game()
            return
        
        if user_answer.lower() == 'skip':
            self.skip_puzzle()
            return
        
        # Check answer
        if self.current_test_type == 'reference':
            is_correct = self.game.check_level_answer(
                self.game.current_level, user_answer, self.current_test_type,
                self.current_puzzle, self.current_reference, self.current_text
            )
        else:
            puzzle_text = self.current_puzzle[len(self.current_reference):].strip()
            is_correct = self.game.check_level_answer(
                self.game.current_level, user_answer, self.current_test_type,
                puzzle_text, self.current_reference, self.current_text
            )
        
        if is_correct:
            self.handle_correct_answer()
        else:
            self.handle_incorrect_answer(user_answer)
    
    def handle_correct_answer(self):
        """Handle a correct answer."""
        self.attempts += 1
        
        # Mark test as completed
        verse_key = (self.current_reference, self.current_text)
        if verse_key not in self.game.level_tests_completed[self.game.current_level]:
            self.game.level_tests_completed[self.game.current_level][verse_key] = set()
        self.game.level_tests_completed[self.game.current_level][verse_key].add(self.current_test_type)
        
        # Check if all required tests are completed
        required_tests = 2
        if len(self.game.level_tests_completed[self.game.current_level][verse_key]) >= required_tests:
            self.game.completed_lines[self.game.current_level].add(verse_key)
        
        # Show success message
        self.show_feedback("✓ Correct! Well done! 🎉", 'success')
        
        # Update progress
        completed = len(self.game.completed_lines[self.game.current_level])
        total = len(self.game.lines)
        progress_text = f"📊 Progress: {completed}/{total} verses completed (all tests) ✨"
        self.append_feedback(progress_text, 'info')
        
        self.game.save_progress()
        
        # Load next puzzle after a short delay
        self.root.after(2000, self.load_next_puzzle)
    
    def handle_incorrect_answer(self, user_answer):
        """Handle an incorrect answer."""
        self.attempts += 1
        self.attempts_label.config(text=f"Attempts: {self.attempts}", foreground='#cc0000')
        
        self.show_feedback(f"✗ Incorrect. Try again! (Attempt {self.attempts})", 'error')
        
        # Show what was wrong
        if self.current_test_type == 'reference':
            self.append_feedback(f"Expected reference: {self.current_reference}", 'info')
            self.append_feedback(f"Your answer: {user_answer}", 'warning')
        else:
            puzzle_text = self.current_puzzle[len(self.current_reference):].strip()
            differences = self.get_differences_text(user_answer, puzzle_text, self.current_text)
            self.append_feedback(differences, 'info')
        
        # Clear answer field and refocus
        self.answer_entry.delete(0, tk.END)
        self.answer_entry.focus()
    
    def get_differences_text(self, user_answer, puzzle_text, correct_text):
        """Get formatted text showing differences."""
        user_filled_text = self.game.get_filled_text(user_answer, puzzle_text, correct_text)
        if user_filled_text is None:
            return "Your answer format couldn't be understood."
        
        # Check if normalized versions match
        user_normalized = self.game.normalize_text(user_answer)
        correct_normalized = self.game.normalize_text(correct_text)
        user_filled_normalized = self.game.normalize_text(user_filled_text)
        
        result = []
        result.append(f"Your filled answer: {user_filled_text}")
        result.append(f"Correct answer:     {correct_text}")
        
        if user_filled_normalized == correct_normalized or user_normalized == correct_normalized:
            result.append("Note: Your answer matches when punctuation and case are ignored.")
        else:
            # Show word-by-word differences
            user_words_norm = user_filled_normalized.split()
            correct_words_norm = correct_normalized.split()
            
            wrong_positions = []
            max_len = max(len(user_words_norm), len(correct_words_norm))
            for i in range(max_len):
                user_word = user_words_norm[i] if i < len(user_words_norm) else None
                correct_word = correct_words_norm[i] if i < len(correct_words_norm) else None
                if user_word != correct_word:
                    wrong_positions.append((i + 1, user_word or "[MISSING]", correct_word or "[EXTRA]"))
            
            if wrong_positions:
                result.append("\nWord-by-word comparison:")
                for pos, user_word, correct_word in wrong_positions[:10]:  # Limit to 10
                    result.append(f"  Position {pos}: '{user_word}' should be '{correct_word}'")
        
        return "\n".join(result)
    
    def skip_puzzle(self):
        """Skip the current puzzle."""
        self.load_next_puzzle()
    
    def quit_game(self):
        """Quit the game."""
        if messagebox.askyesno("Quit Game", "Are you sure you want to quit?"):
            self.game.save_progress()
            self.root.destroy()
    
    def show_feedback(self, message, feedback_type='info'):
        """Show feedback message."""
        self.feedback_text.config(state=tk.NORMAL)
        self.feedback_text.delete(1.0, tk.END)
        
        if feedback_type == 'success':
            color = '#006600'
        elif feedback_type == 'error':
            color = '#cc0000'
        elif feedback_type == 'warning':
            color = '#cc6600'
        else:
            color = '#000000'
        
        self.feedback_text.insert(1.0, message)
        self.feedback_text.tag_add("feedback", 1.0, tk.END)
        self.feedback_text.tag_config("feedback", foreground=color, font=('Arial', 11, 'bold'))
        self.feedback_text.config(state=tk.DISABLED)
    
    def append_feedback(self, message, feedback_type='info'):
        """Append feedback message."""
        self.feedback_text.config(state=tk.NORMAL)
        
        if feedback_type == 'info':
            color = '#0000cc'
        elif feedback_type == 'warning':
            color = '#cc6600'
        else:
            color = '#000000'
        
        self.feedback_text.insert(tk.END, "\n" + message)
        start = self.feedback_text.index(tk.END + "-1c linestart")
        end = self.feedback_text.index(tk.END + "-1c lineend")
        self.feedback_text.tag_add(f"append_{feedback_type}", start, end)
        self.feedback_text.tag_config(f"append_{feedback_type}", foreground=color)
        self.feedback_text.config(state=tk.DISABLED)
        self.feedback_text.see(tk.END)
    
    def clear_feedback(self):
        """Clear feedback area."""
        self.feedback_text.config(state=tk.NORMAL)
        self.feedback_text.delete(1.0, tk.END)
        self.feedback_text.config(state=tk.DISABLED)
    
    def show_message(self, title, message, msg_type='info'):
        """Show a message box."""
        if msg_type == 'info':
            messagebox.showinfo(title, message)
        elif msg_type == 'error':
            messagebox.showerror(title, message)
        elif msg_type == 'warning':
            messagebox.showwarning(title, message)

def main():
    root = tk.Tk()
    app = TextMatchingGameGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
