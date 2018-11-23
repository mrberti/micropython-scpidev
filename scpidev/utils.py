import re

# NR1: Integer numbers, e.g. 42
REGEXP_STRING_NR1 = r"[\+-]?[0-9]+"
# NR2: Numbers with explicit decimal point, e.g. 3.141
REGEXP_STRING_NR2 = r"[\+-]?(?:(?:[0-9]*\.[0-9]+)|(?:[0-9]+\.[0-9]*))"
# NR3: Floating point with exponential, e.g. 1e-6
REGEXP_STRING_NR3 = REGEXP_STRING_NR2 + r"[eE][\+-]?[0-9]+"
# Nf: NR1, NR2 or NR3
REGEXP_STRING_NF = "|".join(
    [REGEXP_STRING_NR3, REGEXP_STRING_NR2, REGEXP_STRING_NR1])

# Compile regexps for later use
REGEXP_NR1 = re.compile(REGEXP_STRING_NR1)
REGEXP_NR2 = re.compile(REGEXP_STRING_NR2)
REGEXP_NR3 = re.compile(REGEXP_STRING_NR3)
REGEXP_NF = re.compile(REGEXP_STRING_NF)

def findfirst(pattern, string, flags=0):
    """Return the first string of a regular expression match or an empty 
    string if no result was found."""
    string_list = re.findall(pattern, string, flags)
    if string_list:
        result = string_list[0]
    else:
        result = ""
    return result

def remove_non_ascii(string):
    return re.sub(r'[^\x00-\x7f]',r'', string)
