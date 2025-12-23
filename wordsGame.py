import random
import re
import json
import os
import sys
from typing import List, Tuple, Optional

# ANSI color codes
class Colors:
    RESET = '\033[0m'
    CYAN = '\033[96m'  # Bright cyan for prompts
    YELLOW = '\033[93m'  # Yellow for user input
    RED = '\033[91m'  # Red for errors
    GREEN = '\033[92m'  # Green for success
    BLUE = '\033[94m'  # Blue for hints

class TextMatchingGame:
    def __init__(self, filename: str = "words.txt"):
        self.filename = filename
        self.save_file = ".game_progress.json"
        self.lines = self.load_lines()
        self.current_level = 1
        self.completed_lines = {level: set() for level in range(1, 5)}
        self.hide_percentages = {
            1: 0.20,  # 20%
            2: 0.40,  # 40%
            3: 0.70   # 70%
            # Level 4 doesn't use percentages - it has special two-test behavior
        }
        self.level_names = {
            1: "Basic",
            2: "Intermediate",
            3: "Advanced",
            4: "Royal Priesthood"
        }
        # For level 1, track which test (words or reference) has been completed for each verse
        self.level1_tests_completed = {}  # {(reference, text): set(['words', 'reference'])}
        # For level 4, track text test completion
        self.level4_tests_completed = {}  # {(reference, text): set(['text'])}
        # Load previous progress if available
        self.load_progress()
    
    def load_lines(self) -> List[Tuple[str, str]]:
        """Load lines from file and extract reference and text. Handles multi-line verses."""
        lines = []
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                file_lines = f.readlines()
            
            current_reference = None
            current_text_parts = []
            
            for line in file_lines:
                stripped_line = line.rstrip()  # Remove trailing newline but preserve leading spaces for continuation
                
                # Check if this line starts a new verse (starts with ( or [)
                verse_match = re.match(r'^[\(\[]([^)\]]+)[\)\]](.*)$', stripped_line)
                if verse_match:
                    # Save previous verse if we have one
                    if current_reference and current_text_parts:
                        text = ' '.join(current_text_parts).strip()
                        if text:
                            lines.append((current_reference, text))
                    
                    # Start new verse
                    ref_content = verse_match.group(1)
                    # Determine if it started with ( or [
                    if stripped_line.startswith('('):
                        current_reference = f"({ref_content})"
                    else:
                        current_reference = f"[{ref_content}]"
                    current_text_parts = [verse_match.group(2).strip()] if verse_match.group(2).strip() else []
                elif current_reference is not None:
                    # This is a continuation line of the current verse
                    if stripped_line:  # Only add non-empty continuation lines
                        current_text_parts.append(stripped_line.strip())
            
            # Don't forget the last verse
            if current_reference and current_text_parts:
                text = ' '.join(current_text_parts).strip()
                if text:
                    lines.append((current_reference, text))
                    
        except FileNotFoundError:
            print(f"Error: File '{self.filename}' not found.")
            return []
        
        return lines
    
    def save_progress(self):
        """Save current game progress to file."""
        try:
            # Convert sets to lists for JSON serialization
            completed_lines_dict = {
                str(level): [list(line) for line in completed_set]
                for level, completed_set in self.completed_lines.items()
            }
            
            # Convert level1_tests_completed for JSON serialization
            level1_tests_dict = {
                f"{ref}|{text}": list(tests) for (ref, text), tests in self.level1_tests_completed.items()
            }
            
            # Convert level4_tests_completed for JSON serialization
            level4_tests_dict = {
                f"{ref}|{text}": list(tests) for (ref, text), tests in self.level4_tests_completed.items()
            }
            
            progress = {
                "current_level": self.current_level,
                "completed_lines": completed_lines_dict,
                "level1_tests_completed": level1_tests_dict,
                "level4_tests_completed": level4_tests_dict
            }
            
            with open(self.save_file, 'w', encoding='utf-8') as f:
                json.dump(progress, f, indent=2)
        except Exception as e:
            # Silently fail if we can't save (e.g., permission issues)
            pass
    
    def load_progress(self):
        """Load previous game progress from file."""
        if not os.path.exists(self.save_file):
            return
        
        try:
            with open(self.save_file, 'r', encoding='utf-8') as f:
                progress = json.load(f)
            
            # Restore current level
            if "current_level" in progress:
                saved_level = progress["current_level"]
                if 1 <= saved_level <= 4:
                    self.current_level = saved_level
            
            # Restore completed lines
            if "completed_lines" in progress:
                for level_str, completed_list in progress["completed_lines"].items():
                    level = int(level_str)
                    if 1 <= level <= 4:
                        # Convert lists back to tuples
                        self.completed_lines[level] = {
                            (ref, text) for ref, text in completed_list
                        }
            
            # Restore level 1 tests completed
            if "level1_tests_completed" in progress:
                for key, tests_list in progress["level1_tests_completed"].items():
                    ref, text = key.split("|", 1)
                    self.level1_tests_completed[(ref, text)] = set(tests_list)
            
            # Restore level 4 tests completed
            if "level4_tests_completed" in progress:
                for key, tests_list in progress["level4_tests_completed"].items():
                    ref, text = key.split("|", 1)
                    self.level4_tests_completed[(ref, text)] = set(tests_list)
            
            # Check if all current words are completed at level 1
            # If new words were added, reset to level 1 but keep already completed verses
            all_current_lines = set(self.lines)
            if 1 in self.completed_lines:
                completed_level1 = self.completed_lines[1]
                if completed_level1 != all_current_lines:
                    # Not all current words are completed at level 1
                    # Reset to level 1, but keep verses that were already completed and still exist
                    self.current_level = 1
                    # For each level, keep only verses that exist in current word list
                    for level in range(1, 5):
                        self.completed_lines[level] = self.completed_lines[level] & all_current_lines
                    # Clean up level 1 tests for verses that no longer exist
                    self.level1_tests_completed = {
                        (ref, text): tests for (ref, text), tests in self.level1_tests_completed.items()
                        if (ref, text) in all_current_lines
                    }
                    # Clean up level 4 tests for verses that no longer exist
                    self.level4_tests_completed = {
                        (ref, text): tests for (ref, text), tests in self.level4_tests_completed.items()
                        if (ref, text) in all_current_lines
                    }
                    # Save the updated progress
                    self.save_progress()
            else:
                # No level 1 progress exists, but check if we need to clean up other levels
                # Keep only verses that exist in current word list for all levels
                for level in range(1, 5):
                    self.completed_lines[level] = self.completed_lines[level] & all_current_lines
                # Clean up level 1 tests for verses that no longer exist
                self.level1_tests_completed = {
                    (ref, text): tests for (ref, text), tests in self.level1_tests_completed.items()
                    if (ref, text) in all_current_lines
                }
                # Clean up level 4 tests for verses that no longer exist
                self.level4_tests_completed = {
                    (ref, text): tests for (ref, text), tests in self.level4_tests_completed.items()
                    if (ref, text) in all_current_lines
                }
        except Exception as e:
            # Silently fail if we can't load (e.g., corrupted file)
            # Start fresh
            pass
    
    def get_words_to_hide(self, words: List[str], level: int) -> set:
        """Calculate which words to hide based on level."""
        hide_percentage = self.hide_percentages[level]
        
        # Filter out words that are only punctuation/symbols (no alphanumeric characters)
        valid_word_indices = []
        normalized_words = []
        for i, word in enumerate(words):
            word_clean = re.sub(r'[^\w]', '', word)
            if word_clean:  # Only include words that have at least one alphanumeric character
                valid_word_indices.append(i)
                normalized_words.append(word_clean.lower())
        
        if not valid_word_indices:
            return set()  # No valid words to hide
        
        num_words_to_hide = max(1, int(len(valid_word_indices) * hide_percentage))
        selected_indices = set(random.sample(range(len(valid_word_indices)), num_words_to_hide))
        words_to_hide_normalized = {normalized_words[i] for i in selected_indices}
        return words_to_hide_normalized
    
    def hide_words(self, text: str, words_to_hide: set) -> str:
        """Hide specified words in the text."""
        words = text.split()
        hidden_text = []
        for word in words:
            # Remove punctuation for comparison but keep it in display
            word_clean = re.sub(r'[^\w]', '', word).lower()
            if word_clean in words_to_hide:
                hidden_text.append("_" * len(word))
            else:
                hidden_text.append(word)
        return " ".join(hidden_text)
    
    def create_puzzle(self, reference: str, text: str, level: int) -> str:
        """Create a puzzle by hiding words based on level."""
        if level == 4:
            # Level 4 has special behavior handled separately
            raise ValueError("Level 4 requires create_level4_puzzle method")
        words = text.split()
        words_to_hide = self.get_words_to_hide(words, level)
        hidden_text = self.hide_words(text, words_to_hide)
        return f"{reference} {hidden_text}"
    
    def create_level4_puzzle(self, reference: str, text: str, test_type: str) -> str:
        """Create a level 4 puzzle. test_type is 'text' (hide text, show reference)."""
        if test_type == 'text':
            # Show reference, hide text (show blanks for all words)
            words = text.split()
            hidden_text = " ".join("_" * len(word) for word in words)
            return f"{reference} {hidden_text}"
        else:
            raise ValueError("test_type must be 'text'")
    
    def get_level1_test_type(self, reference: str, text: str) -> Optional[str]:
        """Get which test type (words or reference) needs to be done for this verse at level 1."""
        verse_key = (reference, text)
        completed_tests = self.level1_tests_completed.get(verse_key, set())
        
        if 'words' not in completed_tests:
            return 'words'
        elif 'reference' not in completed_tests:
            return 'reference'
        else:
            return None  # Both tests completed
    
    def create_level1_puzzle(self, reference: str, text: str, test_type: str) -> str:
        """Create a level 1 puzzle. test_type can be 'words' (20% hiding) or 'reference' (hide reference)."""
        if test_type == 'words':
            # Test 1: 20% words hidden (normal puzzle)
            words = text.split()
            words_to_hide = self.get_words_to_hide(words, 1)
            hidden_text = self.hide_words(text, words_to_hide)
            return f"{reference} {hidden_text}"
        elif test_type == 'reference':
            # Test 2: Show text, hide reference
            return f"____ {text}"
        else:
            raise ValueError("test_type must be 'words' or 'reference'")
    
    def get_level4_test_type(self, reference: str, text: str) -> Optional[str]:
        """Get which test type (text) needs to be done for this verse at level 4."""
        verse_key = (reference, text)
        completed_tests = self.level4_tests_completed.get(verse_key, set())
        
        if 'text' not in completed_tests:
            return 'text'
        else:
            return None  # Test completed
    
    def normalize_text(self, text: str) -> str:
        """Normalize text for comparison (lowercase, remove punctuation, remove extra spaces)."""
        # Remove punctuation and normalize
        text_normalized = re.sub(r'[^\w\s]', '', text.lower())
        return " ".join(text_normalized.split())
    
    def extract_words_from_answer(self, user_answer: str) -> List[str]:
        """Extract words from user answer, handling punctuation."""
        # Split by whitespace, preserving words as user typed them (including hyphens)
        words = user_answer.split()
        # Return words as-is for display, but they'll be normalized for comparison
        return words
    
    def fill_puzzle_blanks(self, puzzle_text: str, user_words: List[str], original_text: str) -> str:
        """Fill blanks in puzzle with user's words to show their complete answer."""
        puzzle_words = puzzle_text.split()
        original_words = original_text.split()
        filled_words = []
        user_word_index = 0
        
        # Since puzzle is created by replacing words with blanks, positions align
        for i, puzzle_word in enumerate(puzzle_words):
            # Check if this is a blank (starts with underscore)
            if puzzle_word.startswith('_'):
                if user_word_index < len(user_words):
                    # Use user's word as-is to show what they actually provided
                    filled_words.append(user_words[user_word_index])
                    user_word_index += 1
                else:
                    # Not enough words provided, keep the blank
                    filled_words.append(puzzle_word)
            else:
                # Keep the word from puzzle (which is same as original at this position)
                filled_words.append(puzzle_word)
        
        return " ".join(filled_words)
    
    def get_available_line(self) -> Tuple[str, str]:
        """Get a random line that hasn't been completed at current level."""
        if self.current_level == 1:
            # Level 1: verse is available if not both tests (words and reference) are completed
            available_lines = [
                (ref, text) for ref, text in self.lines
                if self.get_level1_test_type(ref, text) is not None
            ]
        elif self.current_level == 4:
            # Level 4: verse is available if text test is not completed
            available_lines = [
                (ref, text) for ref, text in self.lines
                if self.get_level4_test_type(ref, text) is not None
            ]
        else:
            # Other levels: verse is available if not in completed_lines
            available_lines = [
                (ref, text) for ref, text in self.lines
                if (ref, text) not in self.completed_lines[self.current_level]
            ]
        
        if not available_lines:
            # All lines completed at this level, move to next level
            return None, None
        
        return random.choice(available_lines)
    
    def get_filled_text(self, user_answer: str, puzzle_text: str, original_text: str) -> Optional[str]:
        """Get the filled text from user's answer and puzzle. Returns None if invalid."""
        # First try: if user provided complete text, return normalized version
        user_normalized = self.normalize_text(user_answer)
        if len(user_normalized.split()) >= len(self.normalize_text(puzzle_text.replace('_', ' ')).split()) * 0.8:
            # User likely provided complete text
            return user_normalized
        
        # Second try: fill in blanks with user's words
        user_words = self.extract_words_from_answer(user_answer)
        if not user_words:
            return None
        
        filled_text = self.fill_puzzle_blanks(puzzle_text, user_words, original_text)
        return filled_text
    
    def verify_user_words(self, user_answer: str, puzzle_text: str, correct_text: str) -> bool:
        """Verify that user's words match the hidden words in the puzzle."""
        user_words = self.extract_words_from_answer(user_answer)
        if not user_words:
            return False
        
        puzzle_words = puzzle_text.split()
        original_words = correct_text.split()
        original_normalized = [re.sub(r'[^\w]', '', word).lower() for word in original_words]
        
        user_word_index = 0
        for i, puzzle_word in enumerate(puzzle_words):
            if puzzle_word.startswith('_'):
                if user_word_index >= len(user_words):
                    return False  # Not enough words
                # Normalize user word the same way (remove punctuation, lowercase)
                user_word_normalized = re.sub(r'[^\w]', '', user_words[user_word_index]).lower()
                if i >= len(original_normalized):
                    return False
                if user_word_normalized != original_normalized[i]:
                    return False  # Word doesn't match
                user_word_index += 1
        
        # Check if we used all user words
        return user_word_index == len(user_words)
    
    def check_answer(self, user_answer: str, puzzle_text: str, correct_text: str) -> bool:
        """Check if user's answer matches the correct text by filling in blanks."""
        # First try: if user provided complete text, check it directly
        user_normalized = self.normalize_text(user_answer)
        correct_normalized = self.normalize_text(correct_text)
        if user_normalized == correct_normalized:
            return True
        
        # Second try: verify user's words match the hidden words
        return self.verify_user_words(user_answer, puzzle_text, correct_text)
    
    def check_level1_answer(self, user_answer: str, test_type: str, puzzle_text: str, correct_reference: str, correct_text: str) -> bool:
        """Check level 1 answer. test_type: 'words' uses normal checking, 'reference' checks if user provided correct reference."""
        if test_type == 'words':
            # Use normal answer checking for words test
            # puzzle_text already has the reference removed, so use it directly
            return self.check_answer(user_answer, puzzle_text, correct_text)
        elif test_type == 'reference':
            # Check if user's answer matches the reference (with or without parentheses/brackets)
            # Remove parentheses/brackets and normalize for comparison
            ref_clean = re.sub(r'[\(\)\[\]]', '', correct_reference).strip()
            user_clean = re.sub(r'[\(\)\[\]]', '', user_answer).strip()
            return user_clean.lower() == ref_clean.lower()
        else:
            return False
    
    def check_level4_answer(self, user_answer: str, test_type: str, correct_reference: str, correct_text: str) -> bool:
        """Check level 4 answer. test_type: 'text' checks if user provided correct text."""
        if test_type == 'text':
            # Check if user's answer matches the text
            user_normalized = self.normalize_text(user_answer)
            correct_normalized = self.normalize_text(correct_text)
            return user_normalized == correct_normalized
        else:
            return False
    
    def show_differences(self, user_answer: str, puzzle_text: str, correct_text: str):
        """Show what was wrong in the user's answer."""
        user_filled_text = self.get_filled_text(user_answer, puzzle_text, correct_text)
        if user_filled_text is None:
            print(f"{Colors.RED}Your answer format couldn't be understood.{Colors.RESET}")
            return
        
        # Check if user provided full sentence by comparing normalized versions
        user_normalized = self.normalize_text(user_answer)
        correct_normalized = self.normalize_text(correct_text)
        user_filled_normalized = self.normalize_text(user_filled_text)
        
        # If normalized versions match, they're the same (just punctuation/case differences)
        if user_filled_normalized == correct_normalized or user_normalized == correct_normalized:
            # The answers match when normalized - no need to show word-by-word differences
            print(f"\n{Colors.BLUE}Your filled answer:{Colors.RESET} {user_filled_text}")
            print(f"{Colors.BLUE}Correct answer:    {Colors.RESET} {correct_text}")
            print(f"{Colors.YELLOW}Note: Your answer matches when punctuation and case are ignored.{Colors.RESET}")
            return
        
        # Show the filled text as-is (with proper formatting)
        print(f"\n{Colors.BLUE}Your filled answer:{Colors.RESET} {user_filled_text}")
        print(f"{Colors.BLUE}Correct answer:    {Colors.RESET} {correct_text}")
        
        # Check if user likely provided full sentence (80% or more of words)
        user_word_count = len(self.normalize_text(user_answer).split())
        correct_word_count = len(correct_normalized.split())
        if user_word_count >= correct_word_count * 0.8:
            # User provided full sentence, compare word-by-word in order
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
                print(f"\n{Colors.BLUE}Word-by-word comparison:{Colors.RESET}")
                for pos, user_word, correct_word in wrong_positions[:20]:  # Limit to first 20 differences
                    print(f"  Position {pos}: {Colors.RED}'{user_word}'{Colors.RESET} should be {Colors.GREEN}'{correct_word}'{Colors.RESET}")
        else:
            # User provided just missing words, compare to hidden words
            user_words_list = self.extract_words_from_answer(user_answer)
            puzzle_words = puzzle_text.split()
            original_words = correct_text.split()
            original_normalized = [re.sub(r'[^\w]', '', word).lower() for word in original_words]
            
            # Find hidden words and compare with user words
            hidden_words_normalized = []
            user_word_index = 0
            wrong_words_info = []
            
            for i, puzzle_word in enumerate(puzzle_words):
                if puzzle_word.startswith('_'):
                    if user_word_index < len(user_words_list) and i < len(original_normalized):
                        user_word_norm = re.sub(r'[^\w]', '', user_words_list[user_word_index]).lower()
                        original_word_norm = original_normalized[i]
                        hidden_words_normalized.append(original_word_norm)
                        if user_word_norm != original_word_norm:
                            wrong_words_info.append((user_word_index + 1, user_words_list[user_word_index], original_words[i]))
                        user_word_index += 1
                    elif i < len(original_normalized):
                        hidden_words_normalized.append(original_normalized[i])
            
            # Show comparison of hidden words
            if wrong_words_info:
                print(f"\n{Colors.BLUE}Your provided words vs. correct hidden words:{Colors.RESET}")
                for pos, user_word, correct_word in wrong_words_info:
                    print(f"  Position {pos}: {Colors.RED}'{user_word}'{Colors.RESET} should be {Colors.GREEN}'{correct_word}'{Colors.RESET}")
            
            if user_word_index < len(user_words_list):
                extra_words = user_words_list[user_word_index:]
                print(f"{Colors.YELLOW}Extra words provided: {', '.join(extra_words)}{Colors.RESET}")
            
            if len(user_words_list) < len(hidden_words_normalized):
                missing_count = len(hidden_words_normalized) - len(user_words_list)
                print(f"{Colors.YELLOW}{missing_count} word(s) missing{Colors.RESET}")
    
    def play(self):
        """Main game loop."""
        if not self.lines:
            print("No valid lines found in the file.")
            return
        
        print("=" * 60)
        print("Welcome to the Text Matching Game!")
        print("=" * 60)
        print(f"Total lines to complete: {len(self.lines)}")
        print("Game rules:")
        print("- Level Basic: 2 tests per verse (20% words hidden + reference test)")
        print("- Level Intermediate: 40% of words hidden")
        print("- Level Advanced: 70% of words hidden")
        print("- Level Royal Priesthood: text test (reference shown, all words hidden)")
        print("- Complete all lines at each level to progress!")
        print("=" * 60)
        print()
        
        while self.current_level <= 4:
            print(f"\n{'=' * 60}")
            if self.current_level == 1:
                print(f"LEVEL {self.level_names[self.current_level]} (2 tests per verse: words + reference)")
            elif self.current_level == 4:
                print(f"LEVEL {self.level_names[self.current_level]} (text test)")
            else:
                print(f"LEVEL {self.level_names[self.current_level]} ({int(self.hide_percentages[self.current_level] * 100)}% words hidden)")
            print(f"{'=' * 60}")
            
            reference, text = self.get_available_line()
            
            if reference is None:
                print(f"\nCongratulations! You've completed all lines at Level {self.level_names[self.current_level]}!")
                self.current_level += 1
                self.save_progress()  # Save progress after advancing level
                if self.current_level <= 4:
                    print(f"Moving to Level {self.level_names[self.current_level]}...")
                    continue
                else:
                    break
            
            attempts = 0
            while True:
                # Handle level 1 and 4 special tests
                if self.current_level == 1:
                    test_type = self.get_level1_test_type(reference, text)
                    puzzle = self.create_level1_puzzle(reference, text, test_type)
                    if test_type == 'reference':
                        print(f"\nPuzzle: {puzzle}")
                        print(f"{Colors.CYAN}Test: Reference (provide the verse reference){Colors.RESET}")
                        prompt = f"\n{Colors.CYAN}Enter the reference (e.g., (1Pe 2:9) or [1Sam 12:21]) (or 'quit' to exit, 'skip' to skip): {Colors.YELLOW}"
                    else:  # words test
                        puzzle_text = puzzle[len(reference):].strip()
                        print(f"\nPuzzle: {puzzle}")
                        print(f"Reference: {reference}")
                        print(f"{Colors.CYAN}Test: Words (20% hidden){Colors.RESET}")
                        prompt = f"\n{Colors.CYAN}Enter the complete text or just the missing words (or 'quit' to exit, 'skip' to skip): {Colors.YELLOW}"
                elif self.current_level == 4:
                    test_type = self.get_level4_test_type(reference, text)
                    puzzle = self.create_level4_puzzle(reference, text, test_type)
                    puzzle_text = puzzle[len(reference):].strip()
                    print(f"\nPuzzle: {puzzle}")
                    print(f"Reference: {reference}")
                    print(f"{Colors.CYAN}Test: Text (provide the complete verse text){Colors.RESET}")
                    prompt = f"\n{Colors.CYAN}Enter the complete text (or 'quit' to exit, 'skip' to skip): {Colors.YELLOW}"
                else:
                    # Levels 2-3: normal puzzle
                    puzzle = self.create_puzzle(reference, text, self.current_level)
                    puzzle_text = puzzle[len(reference):].strip()
                    print(f"\nPuzzle: {puzzle}")
                    print(f"Reference: {reference}")
                    prompt = f"\n{Colors.CYAN}Enter the complete text or just the missing words (or 'quit' to exit, 'skip' to skip this line): {Colors.YELLOW}"
                
                sys.stdout.flush()  # Flush stdout before input to fix Git Bash hanging issue
                user_answer = input(prompt).strip()
                print(Colors.RESET, end='')  # Reset color after input
                sys.stdout.flush()  # Flush after input as well
                
                if user_answer.lower() == 'quit':
                    print("\nThanks for playing!")
                    return
                
                if user_answer.lower() == 'skip':
                    print("Skipping this line...")
                    break
                
                # Show user's answer in yellow
                print(f"{Colors.YELLOW}Your answer: {user_answer}{Colors.RESET}")
                
                # Check answer based on level
                is_correct = False
                if self.current_level == 1:
                    if test_type == 'reference':
                        is_correct = self.check_level1_answer(user_answer, 'reference', puzzle, reference, text)
                    else:  # words test
                        puzzle_text = puzzle[len(reference):].strip()
                        is_correct = self.check_level1_answer(user_answer, 'words', puzzle_text, reference, text)
                elif self.current_level == 4:
                    puzzle_text = puzzle[len(reference):].strip()
                    is_correct = self.check_level4_answer(user_answer, 'text', reference, text)
                else:
                    is_correct = self.check_answer(user_answer, puzzle_text, text)
                
                if is_correct:
                    print(f"\n{Colors.GREEN}✓ ✅ Correct! Well done! 🎉{Colors.RESET}")
                    
                    # Mark test as completed
                    if self.current_level == 1:
                        verse_key = (reference, text)
                        if verse_key not in self.level1_tests_completed:
                            self.level1_tests_completed[verse_key] = set()
                        self.level1_tests_completed[verse_key].add(test_type)
                        
                        # Check if both tests are completed
                        if len(self.level1_tests_completed[verse_key]) == 2:
                            self.completed_lines[1].add(verse_key)
                        print(f"{Colors.GREEN}📊 Progress at Level {self.level_names[1]}: {len(self.completed_lines[1])}/{len(self.lines)} verses completed (both tests) ✨{Colors.RESET}")
                    elif self.current_level == 4:
                        verse_key = (reference, text)
                        if verse_key not in self.level4_tests_completed:
                            self.level4_tests_completed[verse_key] = set()
                        self.level4_tests_completed[verse_key].add('text')
                        self.completed_lines[4].add(verse_key)
                        print(f"{Colors.GREEN}📊 Progress at Level {self.level_names[4]}: {len(self.completed_lines[4])}/{len(self.lines)} verses completed ✨{Colors.RESET}")
                    else:
                        self.completed_lines[self.current_level].add((reference, text))
                        print(f"{Colors.GREEN}📊 Progress at Level {self.level_names[self.current_level]}: {len(self.completed_lines[self.current_level])}/{len(self.lines)} lines completed ✨{Colors.RESET}")
                    
                    self.save_progress()  # Save progress after completing a line
                    break
                else:
                    attempts += 1
                    print(f"\n{Colors.RED}✗ Incorrect. Try again! (Attempt {attempts}){Colors.RESET}")
                    # Show what was wrong (only for text/words tests, not reference tests)
                    if self.current_level == 1 and test_type != 'reference':
                        puzzle_text = puzzle[len(reference):].strip()
                        self.show_differences(user_answer, puzzle_text, text)
                    elif self.current_level == 4:
                        puzzle_text = puzzle[len(reference):].strip()
                        self.show_differences(user_answer, puzzle_text, text)
                    elif self.current_level not in [1, 4]:
                        self.show_differences(user_answer, puzzle_text, text)
                    elif self.current_level == 1 and test_type == 'reference':
                        # For reference test, show what was expected
                        ref_clean = re.sub(r'[\(\)\[\]]', '', reference).strip()
                        user_clean = re.sub(r'[\(\)\[\]]', '', user_answer).strip()
                        print(f"{Colors.BLUE}Expected reference: {Colors.GREEN}{reference}{Colors.RESET}")
                        print(f"{Colors.BLUE}Your answer: {Colors.YELLOW}{user_answer}{Colors.RESET}")
        
        print("\n" + "=" * 60)
        print(f"{Colors.GREEN}🎉 CONGRATULATIONS! 🎉{Colors.RESET}")
        print(f"{Colors.GREEN}You've completed all levels of the Text Matching Game!{Colors.RESET}")
        print("=" * 60)

if __name__ == "__main__":
    game = TextMatchingGame("words.txt")
    game.play()

