# How wordsGameGUI.py Connects to wordsGame.py

## Overview

The GUI (`wordsGameGUI.py`) is a **presentation layer** that wraps around the game logic (`wordsGame.py`). The GUI handles all visual elements and user interactions, while the game class handles all the game logic, data, and rules.

## Connection Architecture

```
┌─────────────────────────────────────┐
│   wordsGameGUI.py (GUI Layer)       │
│   - Handles UI/UX                   │
│   - User input/output               │
│   - Visual display                  │
└──────────────┬──────────────────────┘
               │
               │ Uses/Imports
               │
               ▼
┌─────────────────────────────────────┐
│   wordsGame.py (Game Logic Layer)    │
│   - Game rules & logic               │
│   - Data management                 │
│   - Answer checking                  │
│   - Progress tracking               │
└──────────────────────────────────────┘
```

## 1. Import Statement

**Line 3 in wordsGameGUI.py:**
```python
from wordsGame import TextMatchingGame
```

This imports the `TextMatchingGame` class from `wordsGame.py` so the GUI can use it.

## 2. Game Instance Creation

**Line 21 in wordsGameGUI.py:**
```python
self.game = TextMatchingGame("words.txt")
```

The GUI creates an instance of the game class, which:
- Loads the `words.txt` file
- Initializes game state (levels, progress, etc.)
- Loads saved progress from `.game_progress.json`

## 3. How the GUI Uses the Game Instance

### A. Reading Game State
The GUI reads properties from `self.game` to display information:

```python
# Get current level name
level_name = self.game.level_names[self.game.current_level]

# Get hide percentages
hide_pct = int(self.game.hide_percentages[self.game.current_level] * 100)

# Get progress
completed = len(self.game.completed_lines[self.game.current_level])
total = len(self.game.lines)
```

### B. Calling Game Methods
The GUI calls methods on `self.game` to perform game operations:

```python
# Get next puzzle
reference, text = self.game.get_available_line()

# Get test type for current verse
test_type = self.game.get_level_test_type(self.game.current_level, reference, text)

# Create puzzle
puzzle = self.game.create_level_puzzle(self.game.current_level, reference, text, test_type)

# Check answer
is_correct = self.game.check_level_answer(
    self.game.current_level, user_answer, test_type,
    puzzle_text, reference, text
)

# Get filled text for display
user_filled_text = self.game.get_filled_text(user_answer, puzzle_text, correct_text)

# Normalize text for comparison
normalized = self.game.normalize_text(text)
```

### C. Modifying Game State
The GUI updates the game's internal state:

```python
# Mark test as completed
self.game.level_tests_completed[self.game.current_level][verse_key].add(test_type)

# Mark verse as completed
self.game.completed_lines[self.game.current_level].add(verse_key)

# Advance level
self.game.current_level += 1

# Save progress
self.game.save_progress()
```

## 4. Data Flow Example

Here's how a typical user interaction flows:

```
User clicks "Submit" button
    ↓
GUI: check_answer() method
    ↓
GUI: Gets user input from entry field
    ↓
GUI: Calls self.game.check_level_answer()
    ↓
Game: Validates answer using game logic
    ↓
Game: Returns True/False
    ↓
GUI: Updates UI based on result
    ↓
GUI: Shows feedback to user
    ↓
GUI: Updates progress display
    ↓
GUI: Calls self.game.save_progress()
    ↓
Game: Saves to .game_progress.json
```

## 5. Shared Data

Both files share the same data through the game instance:

- **Progress file**: `.game_progress.json` (both CLI and GUI use the same file)
- **Words file**: `words.txt` (both load from the same file)
- **Game state**: Current level, completed verses, test completions

This means:
- ✅ You can start in CLI, quit, then continue in GUI (or vice versa)
- ✅ Progress is synchronized between both interfaces
- ✅ Same game rules apply to both

## 6. Separation of Concerns

| Component | Responsibility |
|-----------|---------------|
| **wordsGame.py** | Game logic, rules, data management, file I/O |
| **wordsGameGUI.py** | User interface, visual display, event handling |

The GUI **does NOT**:
- ❌ Contain game logic
- ❌ Know how to check answers
- ❌ Know game rules
- ❌ Manage game state directly

The GUI **only**:
- ✅ Displays information from the game
- ✅ Sends user input to the game
- ✅ Updates the visual interface based on game responses

## 7. Key Methods Called by GUI

| Game Method | Purpose | Called When |
|------------|---------|-------------|
| `get_available_line()` | Get next puzzle | Loading new puzzle |
| `get_level_test_type()` | Get current test type | Displaying puzzle |
| `create_level_puzzle()` | Generate puzzle text | Displaying puzzle |
| `check_level_answer()` | Validate user answer | User submits answer |
| `get_filled_text()` | Format user's filled answer | Showing feedback |
| `normalize_text()` | Normalize for comparison | Comparing answers |
| `save_progress()` | Save game state | After completing test/level |

## Summary

The connection is simple:
1. **Import** the game class
2. **Create** an instance: `self.game = TextMatchingGame("words.txt")`
3. **Use** the instance: `self.game.method_name()` or `self.game.property_name`
4. **Share** the same data files (progress, words)

This design allows:
- ✅ Code reusability (same game logic for CLI and GUI)
- ✅ Easy maintenance (change game logic in one place)
- ✅ Consistent behavior (same rules in both interfaces)
- ✅ Progress sharing (switch between CLI/GUI seamlessly)
