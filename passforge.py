# passforge.py (v3.0)
import argparse
import sys
import os
import itertools
import logging
import re
from datetime import datetime
import string
import threading

# --- Constants ---
__version__ = "3.0"
DEFAULT_MIN_LEN = 6
DEFAULT_MAX_LEN = 16
# Common numbers/years/symbols for affixing and patterns
CURRENT_YEAR = datetime.now().year
YEARS = [str(y) for y in range(CURRENT_YEAR - 5, CURRENT_YEAR + 3)]
YEARS_YY = [y[2:] for y in YEARS] # Add 2-digit years
NUMBERS_SIMPLE = ['1', '2', '3', '12', '123', '1234', '0', '007']
NUMBERS_ALL = NUMBERS_SIMPLE + YEARS + YEARS_YY
SYMBOLS_COMMON = ['!', '@', '#', '$', '%', '*', '?'] # Reduced set for patterns/insertions
SYMBOLS_ALL = ['!', '@', '#', '$', '%', '^', '&', '*', '?', '.', '-', '_', '+', '=']
# Leet Speak mappings
LEET_MAP_SIMPLE = {'a': '@', 'e': '3', 'i': '1', 'o': '0', 's': '$'}
LEET_MAP_FULL = {'a': ['@', '4'], 'b': ['8'], 'e': ['3'], 'g': ['6', '9'], 'i': ['1', '!', '|'],
                 'l': ['1', '|'], 'o': ['0'], 's': ['$', '5'], 't': ['7'], 'z': ['2']}
DEFAULT_PREFIXES = ['admin_', 'test_', 'dev_', 'backup_', 'staging_', 'prod_', 'pw_', 'pass_']
# Extensions removed as less relevant for passwords

# --- Logging Setup ---
log = logging.getLogger('PassForge')
log.setLevel(logging.INFO)
console_handler = logging.StreamHandler(sys.stdout)
console_formatter = logging.Formatter('[%(levelname).1s] %(asctime)s %(message)s', datefmt='%H:%M:%S')
console_handler.setFormatter(console_formatter)
if not log.handlers:
    log.addHandler(console_handler)
file_handler = None

# --- Password Generator Class ---
class PasswordGenerator:
    """Generates personalized password wordlists."""

    def __init__(self, args):
        self.args = args
        self.base_words = set()
        self.date_parts = {}
        self.lock = threading.Lock()

        log.info(f"PassForge v{__version__} initialized.")
        log.info(f"Transformations: Case={not args.no_case}, Leet={args.leet_level}, Reverse={args.reverse}, Numbers={not args.no_numbers}, Symbols={not args.no_symbols}, Dates={not args.no_dates}, Combinations={not args.no_combinations}, Insertions={not args.no_insertions}, Patterns={not args.no_patterns}")
        log.info(f"Filters: MinLen={args.min_len}, MaxLen={args.max_len}")

        self._load_base_words()
        if args.birth_date:
            self._parse_birth_date(args.birth_date)

    def _load_base_words(self):
        """Loads initial keywords from args and keyword file."""
        # (Same as v2.0)
        log.info("Loading base keywords...")
        cli_words = [self.args.first_name, self.args.last_name, self.args.username, self.args.nickname, self.args.partner_name, self.args.pet_name, self.args.company]
        if self.args.keyword: cli_words.extend(self.args.keyword)        
        for word in cli_words:
            if word:
                self.base_words.add(word)
                parts = re.split(r'[\s_\-]+', word)
                if len(parts) > 1: self.base_words.update(p for p in parts if p)
        count_cli = len(self.base_words)
        log.info(f"Added {len([w for w in cli_words if w])} keywords from command line args (unique: {count_cli}).")
        if self.args.keyword_file:
            try:
                if not os.path.exists(self.args.keyword_file): log.error(f"Keyword file not found: {self.args.keyword_file}")
                else:
                    with open(self.args.keyword_file, 'r', encoding='utf-8', errors='ignore') as f: file_keywords = {line.strip() for line in f if line.strip() and not line.strip().startswith('#')}
                    self.base_words.update(file_keywords); log.info(f"Added {len(file_keywords)} keywords from file: {self.args.keyword_file}")
            except Exception as e: log.error(f"Error reading keyword file {self.args.keyword_file}: {e}")
        if not self.base_words: log.warning("No base keywords loaded. Wordlist may be small or empty.")
        else: log.info(f"Total unique base keywords: {len(self.base_words)}")


    def _parse_birth_date(self, date_str):
        """Parses birthdate and extracts components including more formats."""
        # (Same as v2.0)
        try:
            dt = None; formats = ["%Y-%m-%d", "%Y/%m/%d", "%Y%m%d", "%m-%d-%Y", "%m/%d/%Y", "%m%d%Y", "%d-%m-%Y", "%d/%m/%Y", "%d%m%Y", "%m-%d-%y", "%m/%d/%y", "%m%d%y", "%d-%m-%y", "%d/%m/%y", "%d%m%y"]
            for fmt in formats:
                 try: dt = datetime.strptime(date_str, fmt); break
                 except ValueError: continue
            if dt is None: raise ValueError("Date format not recognized.")
            self.date_parts['yyyy'] = dt.strftime('%Y'); self.date_parts['yy'] = dt.strftime('%y'); self.date_parts['mm'] = dt.strftime('%m'); self.date_parts['m'] = str(dt.month); self.date_parts['dd'] = dt.strftime('%d'); self.date_parts['d'] = str(dt.day)
            self.date_parts['mmdd'] = dt.strftime('%m%d'); self.date_parts['ddmm'] = dt.strftime('%d%m'); self.date_parts['yyyymmdd'] = dt.strftime('%Y%m%d'); self.date_parts['mmddyy'] = dt.strftime('%m%d%y'); self.date_parts['ddmmyy'] = dt.strftime('%d%m%y'); self.date_parts['yymmdd'] = dt.strftime('%y%m%d')
            self.date_parts['month_name'] = dt.strftime('%B'); self.date_parts['month_abbr'] = dt.strftime('%b')
            log.info(f"Parsed birth date: {date_str}. Extracted parts: {list(self.date_parts.values())}")
        except ValueError as e: log.error(f"Invalid birth date format '{date_str}': {e}."); self.date_parts = {}


    def _apply_case(self, words):
        """Applies case variations."""
        # (Same as v2.0)
        if not words: return set()
        log.debug("Applying case transformations...")
        variations = set()
        for word in words:
            variations.add(word); variations.add(word.lower()); variations.add(word.upper()); variations.add(word.capitalize())
            try: variations.add(word.swapcase())
            except: pass
        log.debug(f"Case variations generated: {len(variations)}")
        return variations

    def _apply_leet(self, words):
        """Applies simple or full leet speak substitutions based on level."""
        # (Same as v2.0)
        if not words or self.args.leet_level == 'none': return words
        if self.args.leet_level == 'simple': leet_map = LEET_MAP_SIMPLE; log.debug("Applying simple leet transformations...")
        elif self.args.leet_level == 'full': leet_map = LEET_MAP_FULL; log.debug("Applying full leet transformations...")
        else: return words
        variations = set(words); words_to_process = list(words)
        if self.args.leet_level == 'full':
            for word in words_to_process:
                leet_chars_in_word = [(i, c.lower()) for i, c in enumerate(word) if c.lower() in leet_map]
                if not leet_chars_in_word: continue
                char_indices = [item[0] for item in leet_chars_in_word]; char_keys = [item[1] for item in leet_chars_in_word]
                replacement_options = [leet_map[key] for key in char_keys]
                for replacements_tuple in product(*replacement_options):
                    new_word_list = list(word)
                    for i, index in enumerate(char_indices): new_word_list[index] = replacements_tuple[i]
                    variations.add("".join(new_word_list)); variations.add("".join(new_word_list).capitalize())
        elif self.args.leet_level == 'simple':
            for word in words_to_process:
                leet_word = word.lower()
                for char, leet in leet_map.items(): leet_word = leet_word.replace(char, leet)
                if leet_word != word.lower(): variations.add(leet_word); variations.add(leet_word.capitalize())
        log.debug(f"Leet variations generated: {len(variations)}")
        return variations

    def _apply_reverse(self, words):
        """Adds reversed versions of words."""
        # (Same as v2.0)
        if not words: return set()
        log.debug("Applying reverse transformation...")
        variations = set(words)
        for word in words:
             if len(word) > 1: reversed_word = word[::-1]; variations.add(reversed_word); variations.add(reversed_word.capitalize())
        log.debug(f"Reverse variations generated: {len(variations)}")
        return variations

    def _apply_insertions(self, words):
        """Inserts common symbols/numbers at the beginning/end."""
        if not words: return set()
        log.debug("Applying character insertions...")
        variations = set(words)
        insert_chars = SYMBOLS_COMMON + NUMBERS_SIMPLE # Characters to insert

        # Use a copy to iterate over while modifying variations
        words_to_modify = list(words)
        for word in words_to_modify:
             for char in insert_chars:
                  variations.add(char + word) # Prepend
                  variations.add(word + char) # Append
        log.debug(f"Insertion variations generated: {len(variations)}")
        return variations

    def _apply_affixes(self, words):
        """Adds prefixes, suffixes (numbers, years, symbols, dates)."""
        # (Same as v2.0, uses SYMBOLS_ALL)
        if not words: return set()
        log.debug("Applying affix transformations...")
        variations = set(words)
        affixes = set(NUMBERS_SIMPLE) | set(SYMBOLS_ALL) # Use all symbols here
        if not self.args.no_dates and self.date_parts: affixes.update(self.date_parts.values())
        if not self.args.no_years: affixes.update(YEARS); affixes.update(YEARS_YY)
        words_to_affix = list(words)
        for word in words_to_affix: # Suffixes
            for suffix in affixes: variations.add(word + str(suffix))
        for word in words_to_affix: # Prefixes
            for prefix in affixes: variations.add(str(prefix) + word)
            for prefix in DEFAULT_PREFIXES: variations.add(prefix + word)
        log.debug(f"Affix variations generated: {len(variations)}")
        return variations

    def _apply_patterns(self, words):
        """Generates passwords based on common patterns like Word+Num+Symbol."""
        if not words: return set()
        log.debug("Applying pattern transformations...")
        variations = set()
        # Define elements for patterns
        nums = NUMBERS_SIMPLE + (list(self.date_parts.values()) if not self.args.no_dates else []) + (YEARS if not self.args.no_years else []) + (YEARS_YY if not self.args.no_years else [])
        symbols = SYMBOLS_COMMON # Use a smaller set for patterns to avoid excessive size

        # Use a copy to iterate over
        words_to_pattern = list(words)
        for word in words_to_pattern:
             # Word + Num
             for num in nums: variations.add(word + str(num))
             # Word + Symbol
             for sym in symbols: variations.add(word + str(sym))
             # Num + Word
             for num in nums: variations.add(str(num) + word)
             # Symbol + Word
             for sym in symbols: variations.add(str(sym) + word)
             # Word + Num + Symbol
             for num in nums:
                  for sym in symbols: variations.add(word + str(num) + str(sym))
             # Word + Symbol + Num
             for sym in symbols:
                  for num in nums: variations.add(word + str(sym) + str(num))
             # Symbol + Word + Num
             for sym in symbols:
                  for num in nums: variations.add(str(sym) + word + str(num))
             # Num + Word + Symbol
             for num in nums:
                  for sym in symbols: variations.add(str(num) + word + str(sym))

        log.debug(f"Pattern variations generated: {len(variations)}")
        return variations

    def _apply_combinations(self, words):
        """Combines base words with each other and with date parts/years."""
        # (Same logic as v2.0)
        if not self.base_words or (len(self.base_words) < 2 and not self.date_parts): return set() # Use base_words
        log.debug("Applying combination transformations...")
        variations = set(); initial_bases = list(self.base_words) # Use base_words
        date_elements = list(self.date_parts.values()) if not self.args.no_dates else []
        year_elements = list(YEARS) if not self.args.no_years else []; combined_date_years = set(date_elements) | set(year_elements)
        if len(initial_bases) >= 2:
             for w1, w2 in itertools.permutations(initial_bases, 2):
                  variations.add(w1 + w2); variations.add(w1.capitalize() + w2.capitalize()); variations.add(w1 + "_" + w2); variations.add(w1 + "-" + w2)
        for word in initial_bases:
             for affix in combined_date_years:
                  affix_str = str(affix)
                  variations.add(word + affix_str); variations.add(affix_str + word); variations.add(word.capitalize() + affix_str); variations.add(affix_str + word.capitalize()); variations.add(word + "_" + affix_str); variations.add(affix_str + "_" + word)
        log.debug(f"Combination variations generated: {len(variations)}")
        return variations


    def filter_wordlist(self, words):
        """Filters the wordlist based on length constraints."""
        # (Same as v2.0)
        min_len = self.args.min_len; max_len = self.args.max_len
        if min_len is None and max_len is None: return words
        log.info(f"Applying filters: Min Length={min_len}, Max Length={max_len}")
        original_count = len(words)
        filtered_words = {word for word in words if (min_len is None or len(word) >= min_len) and (max_len is None or len(word) <= max_len)}
        log.info(f"Total words after filtering: {len(filtered_words)} (Removed: {original_count - len(filtered_words)})")
        return filtered_words

    def generate(self):
        """Generates the final wordlist by applying transformations sequentially."""
        if not self.base_words: log.warning("No base keywords loaded."); return []

        log.info(f"Starting generation with {len(self.base_words)} base words.")
        # Define the pipeline
        pipeline = [
            ('Base', lambda w: set(w), False), # Start with base (added False as placeholder)
            ('Case', self._apply_case, self.args.no_case),
            ('Leet', self._apply_leet, self.args.leet_level == 'none'),
            ('Reverse', self._apply_reverse, not self.args.reverse),
            # Apply next steps to the expanded set
            ('Insertions', self._apply_insertions, self.args.no_insertions),
            ('Affixes', self._apply_affixes, self.args.no_numbers and self.args.no_symbols and self.args.no_dates),
            ('Patterns', self._apply_patterns, self.args.no_patterns),
            ('Combinations', self._apply_combinations, self.args.no_combinations),
        ]

        current_words = set(self.base_words)
        processed_stages = set(current_words) # Keep track of all words generated so far

        for name, func, disabled_flag in pipeline:
            if name == 'Base': continue # Skip base step func
            if name == 'Combinations':
                 # Combinations use initial base words, add results to processed_stages
                 if not disabled_flag:
                      combination_words = func(self.base_words) # Use base_words instead of base_keywords
                      processed_stages.update(combination_words)
            elif not disabled_flag:
                 # Apply transformation to the words generated *up to the previous stage*
                 # to avoid applying affixes/patterns to already affixed/patterned words excessively?
                 # Or apply to *all* words generated so far (processed_stages)? Let's try all.
                 new_words = func(processed_stages)
                 processed_stages.update(new_words) # Add newly generated words

        log.info(f"Total words before filtering: {len(processed_stages)}")
        final_wordlist = self.filter_wordlist(processed_stages)
        return sorted(list(final_wordlist))


    def run_and_output(self):
        """Runs the generation and handles output."""
        # (Same as v2.0)
        final_list = self.generate()
        if not final_list: log.warning("Generated wordlist is empty."); return
        output_content = "\n".join(final_list)
        if self.args.output_file:
            log.info(f"Saving wordlist ({len(final_list)} words) to {self.args.output_file}")
            try:
                with open(self.args.output_file, 'w', encoding='utf-8') as f: f.write(output_content + "\n")
                log.info("Wordlist saved successfully.")
            except IOError as e: log.error(f"Failed to write wordlist to {self.args.output_file}: {e}")
            except Exception as e: log.error(f"Unexpected error saving wordlist: {e}")
        else: print(output_content)

    def close(self):
        """Cleans up resources."""
        log.info("PassForge finished.")


# --- Entry Point ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=f"PassForge v{__version__} - Personalized Password List Generator. Use Responsibly!",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    # Input Info Arguments
    input_group = parser.add_argument_group('Target Information')
    input_group.add_argument("--first-name", help="Target's first name")
    input_group.add_argument("--last-name", help="Target's last name")
    input_group.add_argument("--username", help="Target's username")
    input_group.add_argument("--nickname", help="Target's nickname")
    input_group.add_argument("--birth-date", help="Target's birth date (e.g., YYYY-MM-DD, MM/DD/YY)")
    input_group.add_argument("--partner-name", help="Target's partner's name")
    input_group.add_argument("--pet-name", help="Target's pet's name")
    input_group.add_argument("--company", help="Target's company name")
    input_group.add_argument("-k", "--keyword", action='append', help="Other relevant keyword(s). Use multiple times.")
    input_group.add_argument("-kF", "--keyword-file", help="File containing additional keywords (one per line)")

    # Transformation Options
    trans_group = parser.add_argument_group('Transformation Options')
    trans_group.add_argument("--no-case", action="store_true", help="Disable case transformations")
    trans_group.add_argument("--leet-level", choices=['none', 'simple', 'full'], default='none', help="Level of leet speak substitution")
    trans_group.add_argument("--reverse", action="store_true", help="Include reversed versions of words")
    trans_group.add_argument("--no-numbers", action="store_true", help="Disable adding number suffixes/prefixes")
    trans_group.add_argument("--no-symbols", action="store_true", help="Disable adding symbol suffixes/prefixes")
    trans_group.add_argument("--no-dates", action="store_true", help="Disable adding birth date variations as suffixes/prefixes")
    trans_group.add_argument("--no-years", action="store_true", help="Disable adding default year suffixes/prefixes")
    trans_group.add_argument("--no-combinations", action="store_true", help="Disable combining base words/dates")
    trans_group.add_argument("--no-insertions", action="store_true", help="Disable inserting chars at start/end") # New flag
    trans_group.add_argument("--no-patterns", action="store_true", help="Disable generating common patterns (Word+Num+Sym etc.)") # New flag


    # Output Options
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument("-o", "--output-file", help="File to save the generated wordlist (Default: print to stdout)")
    output_group.add_argument("--min-len", type=int, default=DEFAULT_MIN_LEN, help="Minimum length of passwords to include")
    output_group.add_argument("--max-len", type=int, default=DEFAULT_MAX_LEN, help="Maximum length of passwords to include")

    # Logging Arguments
    log_group = parser.add_argument_group('Logging Options')
    log_group.add_argument("-v", "--verbose", action="store_const", dest="loglevel", const=logging.DEBUG, default=logging.INFO, help="Enable verbose (debug) logging")
    log_group.add_argument("-q", "--quiet", action="store_const", dest="loglevel", const=logging.WARNING, help="Suppress informational messages (show warnings/errors only)")
    log_group.add_argument("--log-file", help="File to write detailed logs to")


    args = parser.parse_args()

    # --- Configure Logging ---
    # (Same as v2.0)
    log.setLevel(args.loglevel)
    if args.log_file:
        try:
            file_handler = logging.FileHandler(args.log_file, mode='w')
            file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
            file_handler.setFormatter(file_formatter); log.addHandler(file_handler)
            log.info(f"Logging detailed output to: {args.log_file}")
        except Exception as e: log.error(f"Failed to open log file {args.log_file}: {e}"); sys.exit(1)
    # --- End Logging Config ---

    # Validate inputs
    if not any([args.first_name, args.last_name, args.username, args.nickname,
                args.partner_name, args.pet_name, args.company, args.keyword, args.keyword_file]):
         log.warning("No personal information or keyword file provided. Wordlist may be very small or empty.")

    # Initialize and run generator
    generator = None
    try:
        generator = PasswordGenerator(args)
        generator.run_and_output()

    except ValueError as ve: log.critical(f"Initialization Error: {ve}"); sys.exit(1)
    except KeyboardInterrupt: log.warning("\nWordlist generation interrupted by user."); print("\nProcess aborted.", file=sys.stderr); sys.exit(1)
    except Exception as e: log.critical(f"An unexpected critical error occurred: {e}", exc_info=True); sys.exit(1)
    finally:
         if generator: generator.close()

