# PassForge v3.0

**A Personalized Password List Generator**

## ⚠️ Disclaimer ⚠️

**This tool is intended for educational purposes and authorized security testing ONLY.** Using wordlists generated by this tool to attempt unauthorized access to accounts is **illegal and unethical**. The developers assume no liability and are not responsible for any misuse or damage caused by this tool. **Use responsibly and ethically.**

## Description

PassForge is a Python-based tool designed to generate highly personalized password wordlists based on information about a specific target individual. It takes various inputs like names, dates, usernames, and keywords, then applies a wide range of common password creation patterns and transformations (case changes, leet speak, reversal, affixing numbers/symbols/dates, common patterns, character insertion, combinations) to generate a tailored list suitable for authorized penetration testing or security awareness exercises.

## Features

* **Personalized Input:** Accepts target information via command-line arguments (first name, last name, username, nickname, birth date, partner name, pet name, company) and keywords (via CLI or file).
* **Multiple Transformations:** Applies a sequence of transformations, which can be selectively disabled:
    * Case Variations (lower, upper, capitalize, swapcase).
    * Leet Speak (simple or full substitution levels).
    * Word Reversal.
    * Character Insertions (common symbols/numbers at start/end).
    * Affixing (numbers, symbols, years, date parts as prefixes/suffixes).
    * Pattern Generation (e.g., Word+Number+Symbol combinations).
    * Combinations (pairs of base keywords, keywords + dates/years).
* **Date Processing:** Parses various date formats and uses components (YYYY, YY, MM, M, DD, D, MMDD, DDMM, etc.) in transformations.
* **Filtering:** Filters the final list by minimum and maximum password length.
* **Output Options:** Prints the unique, sorted wordlist to stdout or saves it to a file (`-o`).
* **Logging:** Configurable logging levels (`-v`, `-q`) and optional logging to file (`--log-file`).

## Requirements

* Python 3.7+
* Standard Python libraries (`argparse`, `datetime`, `itertools`, `logging`, `re`, `string`, `os`, `sys`). **No external libraries need to be installed via pip.**

## Installation

1.  Download the `passforge.py` script.
2.  Ensure you have Python 3.7+ installed.
3.  No `pip install` is required.

## Usage

```bash
python passforge.py [info options] [transformation options] [output options]
```

**Target Information Options:**

* `--first-name NAME`: Target's first name.
* `--last-name NAME`: Target's last name.
* `--username NAME`: Target's username.
* `--nickname NAME`: Target's nickname.
* `--birth-date DATE`: Target's birth date (YYYY-MM-DD, MM/DD/YY, etc.).
* `--partner-name NAME`: Target's partner's name.
* `--pet-name NAME`: Target's pet's name.
* `--company NAME`: Target's company name.
* `-k KEYWORD`, `--keyword KEYWORD`: Other keyword (hobby, city, etc.). Use multiple times.
* `-kF FILE`, `--keyword-file FILE`: File with additional keywords (one per line).

*(At least one information option or keyword file should be provided)*

**Transformation Options (Default: All Enabled except Leet='none', Reverse=False):**

* `--no-case`: Disable case transformations.
* `--leet-level {none,simple,full}`: Set leet speak level (Default: none).
* `--reverse`: Include reversed versions of words.
* `--no-numbers`: Disable adding number affixes.
* `--no-symbols`: Disable adding symbol affixes.
* `--no-dates`: Disable adding birth date variations as affixes.
* `--no-years`: Disable adding default year affixes.
* `--no-combinations`: Disable combining base words/dates.
* `--no-insertions`: Disable inserting chars at start/end.
* `--no-patterns`: Disable generating common patterns (Word+Num+Sym etc.).

**Output Options:**

* `-o FILE`, `--output-file FILE`: File to save the generated wordlist (Default: print to stdout).
* `--min-len LEN`: Minimum password length (Default: 6).
* `--max-len LEN`: Maximum password length (Default: 16).

**Logging Options:**

* `--log-file FILE`: File to write detailed logs to.
* `-v`, `--verbose`: Enable debug logging.
* `-q`, `--quiet`: Suppress info messages (show warnings/errors only).

**Examples:**

1.  **Generate list for "John Doe", born 1990-05-15, username "jdoe", pet "buddy":**
    ```bash
    python passforge.py --first-name John --last-name Doe --username jdoe --birth-date 1990-05-15 --pet-name buddy -o john_doe_list.txt
    ```

2.  **Use keywords from file, enable full leet speak and reversing, filter length:**
    ```bash
    python passforge.py -kF my_keywords.txt --leet-level full --reverse --min-len 8 --max-len 12
    ```

3.  **Generate list with only base words, case changes, and year affixes:**
    ```bash
    python passforge.py --first-name Jane --last-name Smith --leet-level none --no-reverse --no-numbers --no-symbols --no-dates --no-combinations --no-insertions --no-patterns
    ```

## Output Interpretation

* The tool outputs a list of potential password candidates based on the provided information and enabled transformations.
* The list is filtered by length and contains unique entries, sorted alphabetically.
* Check the log output (console or file) for details on the number of base words and words generated at different stages.

## Limitations

* **Pattern-Based:** Relies on common password creation patterns and transformations; may not guess truly random or highly complex passwords.
* **No Complex Rules:** Does not support advanced rule engines like Hashcat.
* **Performance:** Generating lists with many base keywords and all transformations enabled can be computationally intensive and produce very large lists.
* **Context:** Does not consider password policies (complexity requirements, length limits) of the target system.

## License

(Specify your chosen license here, e.g., MIT License)

```
[Link to LICENSE file or full license text]
```

## Contributing

(Optional: Add guidelines if you want others to contribute)

```
Contributions are welcome! Please read CONTRIBUTING.md for details.
