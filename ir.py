
"""
Project 1 - Stoplist
Removes the words found in a stoplist from every .txt document.
Input : data/*.txt   (text documents) + data/stoplist.txt
Output: output/*.stp (text documents without stop words)
"""
 
import os
import re
 
DATA_DIR = "data"
OUTPUT_DIR = "output"
STOPLIST_PATH = os.path.join(DATA_DIR, "stoplist.txt")
 
 
# ---------- Step 1: load the stoplist ----------
def load_stoplist(path):
    """Read the stoplist file (one word per line) into a set."""
    stopwords = set()
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            word = line.strip().lower()   # remove spaces/newline, lowercase
            if word:                      # skip empty lines
                stopwords.add(word)
    return stopwords
 
 
# ---------- Step 2: tokenize ----------
def tokenize(text):
    """Lowercase the text and split it into words (letters/digits only)."""
    text = text.lower()
    text = re.sub(r"'s\b", "", text)       # user's -> user
    return re.findall(r"[a-z0-9]+", text)  # drops punctuation: , . : ! ( ) -
 
 
# ---------- Step 3: remove stop words ----------
def remove_stopwords(tokens, stopwords):
    """Keep only the tokens that are NOT in the stoplist."""
    return [t for t in tokens if t not in stopwords]
 
 
# ---------- Step 4: process every document ----------
def process_collection(data_dir, output_dir, stopwords):
    os.makedirs(output_dir, exist_ok=True)
    stoplist_name = os.path.basename(STOPLIST_PATH)
 
    for filename in sorted(os.listdir(data_dir)):
        # only .txt documents, and skip the stoplist file itself
        if not filename.endswith(".txt") or filename == stoplist_name:
            continue
 
        in_path = os.path.join(data_dir, filename)
        out_name = os.path.splitext(filename)[0] + ".stp"   # doc1.txt -> doc1.stp
        out_path = os.path.join(output_dir, out_name)
 
        with open(in_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
 
        total_before = total_after = 0
        with open(out_path, "w", encoding="utf-8") as out:
            for line in lines:                  # keep the original line structure
                tokens = tokenize(line)
                kept = remove_stopwords(tokens, stopwords)
                total_before += len(tokens)
                total_after += len(kept)
                if kept:
                    out.write(" ".join(kept) + "\n")
 
        removed = total_before - total_after
        print(f"{filename:<12} -> {out_name:<12} "
              f"words: {total_before:>4}  kept: {total_after:>4}  removed: {removed:>4}")
 
 
if __name__ == "__main__":
    stops = load_stoplist(STOPLIST_PATH)
    print("Number of stop words:", len(stops))
    print("-" * 60)
    process_collection(DATA_DIR, OUTPUT_DIR, stops)
    print("-" * 60)
    print(f"Done. Results saved in '{OUTPUT_DIR}/'")
 

'''----------------------------------------------------------------------------------------------------------'''
"""
Project 2 - Stemming
Removes suffixes from every word using the Porter stemming algorithm (1980).
Input : output/*.stp (text documents without stop words, from Project 1)
Output: output/*.sfx (text documents without suffixes)
"""
 
import os
 
INPUT_DIR = "output"
OUTPUT_DIR = "output"
 
VOWELS = "aeiou"
 
 
# ======================================================================
#  Porter stemmer helpers
#  A word is seen as [C](VC)^m[V], where C = consonants, V = vowels.
#  m ("measure") = number of VC sequences.
#  Examples: tree, by -> m=0   trouble, oats -> m=1   private -> m=2
# ======================================================================
def is_consonant(word, i):
    """True if word[i] is a consonant. 'y' is a consonant only after a vowel
    (or at the start of the word)."""
    ch = word[i]
    if ch in VOWELS:
        return False
    if ch == "y":
        return i == 0 or not is_consonant(word, i - 1)
    return True
 
 
def measure(stem):
    """Count the number of VC sequences (m) in the stem."""
    m = 0
    i, n = 0, len(stem)
    while i < n and is_consonant(stem, i):      # skip leading consonants
        i += 1
    while i < n:
        while i < n and not is_consonant(stem, i):   # vowels
            i += 1
        if i >= n:
            break
        while i < n and is_consonant(stem, i):       # consonants
            i += 1
        m += 1
    return m
 
 
def contains_vowel(stem):
    """*v* : the stem contains a vowel."""
    return any(not is_consonant(stem, i) for i in range(len(stem)))
 
 
def ends_double_consonant(word):
    """*d : the word ends with a double consonant (e.g. -tt, -ss)."""
    return (len(word) >= 2 and word[-1] == word[-2]
            and is_consonant(word, len(word) - 1))
 
 
def ends_cvc(word):
    """*o : the word ends consonant-vowel-consonant, and the last
    consonant is not w, x or y (e.g. hop, fil)."""
    if len(word) < 3:
        return False
    return (is_consonant(word, len(word) - 3)
            and not is_consonant(word, len(word) - 2)
            and is_consonant(word, len(word) - 1)
            and word[-1] not in "wxy")
 
 
def replace_suffix(word, rules, condition):
    """Try the rules (suffix -> replacement) in order. The first suffix that
    matches is the only one considered: it is replaced if the remaining stem
    satisfies condition(stem), otherwise the word is left unchanged."""
    for suffix, replacement in rules:
        if word.endswith(suffix):
            stem = word[: len(word) - len(suffix)]
            if condition(stem):
                return stem + replacement
            return word
    return word
 
 
# ======================================================================
#  Porter steps
# ======================================================================
def step1a(word):
    # plurals: caresses -> caress, ponies -> poni, cats -> cat
    if word.endswith("sses"):
        return word[:-2]
    if word.endswith("ies"):
        return word[:-2]
    if word.endswith("ss"):
        return word
    if word.endswith("s"):
        return word[:-1]
    return word
 
 
def step1b(word):
    # past tense / -ing: agreed -> agree, plastered -> plaster, motoring -> motor
    if word.endswith("eed"):
        stem = word[:-3]
        return word[:-1] if measure(stem) > 0 else word
 
    removed = False
    for suffix in ("ed", "ing"):
        if word.endswith(suffix):
            stem = word[: -len(suffix)]
            if contains_vowel(stem):
                word = stem
                removed = True
            break
 
    if removed:
        # tidy up: conflat(ed) -> conflate, hopp(ing) -> hop, fil(ing) -> file
        if word.endswith(("at", "bl", "iz")):
            word += "e"
        elif ends_double_consonant(word) and word[-1] not in "lsz":
            word = word[:-1]
        elif measure(word) == 1 and ends_cvc(word):
            word += "e"
    return word
 
 
def step1c(word):
    # happy -> happi
    if word.endswith("y") and contains_vowel(word[:-1]):
        return word[:-1] + "i"
    return word
 
 
STEP2_RULES = [
    ("ational", "ate"), ("tional", "tion"), ("enci", "ence"), ("anci", "ance"),
    ("izer", "ize"), ("abli", "able"), ("alli", "al"), ("entli", "ent"),
    ("eli", "e"), ("ousli", "ous"), ("ization", "ize"), ("ation", "ate"),
    ("ator", "ate"), ("alism", "al"), ("iveness", "ive"), ("fulness", "ful"),
    ("ousness", "ous"), ("aliti", "al"), ("iviti", "ive"), ("biliti", "ble"),
]
 
STEP3_RULES = [
    ("icate", "ic"), ("ative", ""), ("alize", "al"), ("iciti", "ic"),
    ("ical", "ic"), ("ful", ""), ("ness", ""),
]
 
STEP4_SUFFIXES = [
    "al", "ance", "ence", "er", "ic", "able", "ible", "ant", "ement",
    "ment", "ent", "ion", "ou", "ism", "ate", "iti", "ous", "ive", "ize",
]
 
 
def step2(word):
    # relational -> relate, conditional -> condition, digitizer -> digitize
    rules = sorted(STEP2_RULES, key=lambda r: -len(r[0]))   # longest first
    return replace_suffix(word, rules, lambda s: measure(s) > 0)
 
 
def step3(word):
    # triplicate -> triplic, hopeful -> hope, goodness -> good
    rules = sorted(STEP3_RULES, key=lambda r: -len(r[0]))
    return replace_suffix(word, rules, lambda s: measure(s) > 0)
 
 
def step4(word):
    # revival -> reviv, allowance -> allow, adoption -> adopt
    for suffix in sorted(STEP4_SUFFIXES, key=len, reverse=True):
        if word.endswith(suffix):
            stem = word[: -len(suffix)]
            if measure(stem) > 1:
                if suffix == "ion":
                    if stem.endswith(("s", "t")):   # -sion / -tion only
                        return stem
                else:
                    return stem
            return word
    return word
 
 
def step5(word):
    # probate -> probat, rate -> rate, controll -> control
    if word.endswith("e"):
        stem = word[:-1]
        m = measure(stem)
        if m > 1 or (m == 1 and not ends_cvc(stem)):
            word = stem
    if measure(word) > 1 and ends_double_consonant(word) and word.endswith("l"):
        word = word[:-1]
    return word
 
 
def stem(word):
    """Apply all Porter steps to one (lowercase) word."""
    if len(word) <= 2:            # very short words are left as they are
        return word
    word = step1a(word)
    word = step1b(word)
    word = step1c(word)
    word = step2(word)
    word = step3(word)
    word = step4(word)
    word = step5(word)
    return word
 
 
# ======================================================================
#  Process every .stp document
# ======================================================================
def process_collection(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
 
    for filename in sorted(os.listdir(input_dir)):
        if not filename.endswith(".stp"):
            continue
 
        in_path = os.path.join(input_dir, filename)
        out_name = os.path.splitext(filename)[0] + ".sfx"   # doc1.stp -> doc1.sfx
        out_path = os.path.join(output_dir, out_name)
 
        with open(in_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
 
        total = changed = 0
        with open(out_path, "w", encoding="utf-8") as out:
            for line in lines:                       # keep the line structure
                words = line.split()
                stems = [stem(w) for w in words]
                total += len(words)
                changed += sum(1 for w, s in zip(words, stems) if w != s)
                if stems:
                    out.write(" ".join(stems) + "\n")
 
        print(f"{filename:<12} -> {out_name:<12} "
              f"words: {total:>4}  stemmed: {changed:>4}")
 
 
if __name__ == "__main__":
    print("Porter stemming")
    print("-" * 50)
    process_collection(INPUT_DIR, OUTPUT_DIR)
    print("-" * 50)
    print(f"Done. Results saved in '{OUTPUT_DIR}/'")