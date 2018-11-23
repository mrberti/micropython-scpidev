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

def sanitize(input, remove_all_spaces=False):
    """Remove excessive and wrong characters as much as possible."""
    sanitized = input
    sanitized = remove_non_ascii(sanitized)
    # Control characters which appear often in source code, e.g. new-line 
    # characters in multi-line python strings.
    sanitized = re.sub(r"[\n\t]", r"", sanitized)
    # Spaces at the beginning of the string.
    sanitized = re.sub(r"(^ +)", r"", sanitized)
    if remove_all_spaces:
        sanitized = sanitized.replace(" ", "")
    else:
        # More than one space.
        sanitized = re.sub(r" +", r" ", sanitized)
    return sanitized

def create_keyword_string(command_string):
    """Creates the keyword string. The keyword string is everything before 
    the first space character."""
    cmd_str = command_string.split(" ")[0]
    return cmd_str

def create_parameter_string(command_string):
    """Create the parameter string. The parameter string is everything 
    after the first space character. All other space characters are 
    removed."""
    parameter_string = "".join(command_string.split(" ")[1:])
    return parameter_string
