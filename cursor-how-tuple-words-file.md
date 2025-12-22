# Tuple Words File Format - Q&A

## Overview
This document explains how the words file format works for the text matching game.

## Q: What is the basic structure of the words file?

**A:** Each verse consists of:
1. A reference (e.g., `(1Pe 2:9)` or `[1Sam 12:21]`)
2. The verse text following the reference

Example:
```
(1Pe 2:9) But you are a chosen people, a royal priesthood, a holy nation, a people belonging to God, that you may declare the praises of him who called you out of darkness into his wonderful light.
```

## Q: How are references formatted?

**A:** References can use two formats:
- Parentheses: `(1Pe 2:9)` - produces reference `(1Pe 2:9)`
- Square brackets: `[1Sam 12:21]` - produces reference `[1Sam 12:21]`

The reference must start at the beginning of a line.

## Q: Can verses span multiple lines?

**A:** Yes! A verse can span multiple lines. A new verse starts when a line begins with `(` or `[`. Any lines that don't start with `(` or `[` are treated as continuation of the previous verse.

Example:
```
(1Pe 2:9) But you are a chosen people, a royal priesthood, a holy nation, 
a people belonging to God, 
that you may declare the praises of him 
who called you out of darkness into his wonderful light.

(Deu 10:14) To the LORD your God belong heavens, 
even the highest heavens, the earth and everything in it.
```

This will create two verses:
- Verse 1: `(1Pe 2:9)` with text: `"But you are a chosen people, a royal priesthood, a holy nation, a people belonging to God, that you may declare the praises of him who called you out of darkness into his wonderful light."`
- Verse 2: `(Deu 10:14)` with text: `"To the LORD your God belong heavens, even the highest heavens, the earth and everything in it."`

## Q: How are multi-line verses joined?

**A:** All continuation lines are joined with spaces. The text from each line is trimmed of leading/trailing whitespace, then joined with single spaces.

## Q: Are empty lines handled?

**A:** Yes, empty lines are skipped. They don't break verse continuity.

## Q: What happens if a line starts with `(` or `[` but isn't a valid reference?

**A:** The parser uses a regex pattern `^[\(\[]([^)\]]+)[\)\]](.*)$` to match references. If the line doesn't match this pattern, it will be treated as a continuation of the previous verse.

## Q: Can I mix reference formats in the same file?

**A:** Yes, you can use both `(reference)` and `[reference]` formats in the same file.

## Q: What is the internal data structure?

**A:** Each verse is stored as a tuple: `(reference, text)`

Example:
```python
("(1Pe 2:9)", "But you are a chosen people, a royal priesthood, a holy nation, a people belonging to God, that you may declare the praises of him who called you out of darkness into his wonderful light.")
```

The game maintains a list of these tuples: `List[Tuple[str, str]]`

## Q: What characters are preserved in the text?

**A:** All characters in the verse text are preserved exactly as written, including:
- Punctuation (commas, periods, hyphens, etc.)
- Special characters
- Capitalization
- Whitespace (normalized to single spaces between words)

## Q: How does the game identify verses for progress tracking?

**A:** Verses are identified by their tuple `(reference, text)`. This means:
- Two verses with the same reference but different text are considered different
- The full text must match exactly (except for normalization during comparison)
- Progress is tracked per `(reference, text)` combination

