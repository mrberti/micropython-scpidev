try:
    import re
except ImportError:
    # ATTENTION: The unix port of micropython does not support ``re.sub()``!
    import ure as re
try:
    import usocket as socket
except ImportError:
    import socket
try:
    import logging
except ImportError:
    import scpidev.logging_mockup as logging

# NR1: Integer numbers, e.g. 42
REGEXP_STRING_NR1 = r"[\+-]?[0-9]+"
# NR2: Numbers with explicit decimal point, e.g. 3.141
REGEXP_STRING_NR2 = r"[\+-]?(?:(?:[0-9]*\.[0-9]+)|(?:[0-9]+\.[0-9]*))"
# NR3: Floating point with exponential, e.g. 1e-6
REGEXP_STRING_NR3 = REGEXP_STRING_NR2 + r"[eE][\+-]?[0-9]+"
# NRf: NR1, NR2 or NR3
REGEXP_STRING_NRF = "|".join(
    [REGEXP_STRING_NR3, REGEXP_STRING_NR2, REGEXP_STRING_NR1])

# All non-ASCII characters
REGEXP_NON_ASCII_STRING = r"[^\x00-\x7f]"
# All non-ASCII printable characters (includes \n)
REGEXP_SANATIZE_BLACKLIST_STRING = r"[^\x20-\x7e]"

# Compile regexps for later use
REGEXP_NR1 = re.compile(REGEXP_STRING_NR1)
REGEXP_NR2 = re.compile(REGEXP_STRING_NR2)
REGEXP_NR3 = re.compile(REGEXP_STRING_NR3)
REGEXP_NRF = re.compile(REGEXP_STRING_NRF)
REGEXP_SANATIZE_BLACKLIST = re.compile(REGEXP_SANATIZE_BLACKLIST_STRING)
REGEXP_NON_ASCII = re.compile(REGEXP_NON_ASCII_STRING)

def findfirst(pattern, string, flags=0):
    """Return the first string of a regular expression match or an empty
    string if no result was found."""
    string_list = re.search(pattern, string, flags)
    if string_list:
        result = string_list.group(0)
    else:
        result = ""
    return result

def remove_non_ascii(string):
    return REGEXP_NON_ASCII.sub(r"", string)

def sanitize(input, remove_all_spaces=False):
    """Remove excessive and wrong characters as much as possible."""
    sanitized = str(input).strip()
    # All non-printable ASCII characters are removed
    # sanitized = REGEXP_SANATIZE_BLACKLIST.sub(r"", input)
    # Spaces at the beginning of the string.
    # sanitized = re.sub(r"(^ +)", r"", sanitized)
    if remove_all_spaces:
        sanitized = sanitized.replace(" ", "")
    else:
        # More than one space.
        # sanitized = re.sub(r" +", r" ", sanitized)
        sanitized = sanitized.replace("  ", " ")
        pass
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

def create_command_tuple(command_string):
    """Create a tuple which contains the keyword and parameter strings. The
    input is sanatized first."""
    command_string = sanitize(command_string, False)
    c = create_keyword_string(command_string)
    p = create_parameter_string(command_string)
    return (c,p)

def create_block_data_string(string):
    """Create the required format for block data. The result is in the format:
    ``#<n><XX><string>`` where ``<XX>`` is the number of bytes following and
    ``<n>`` the length of <XX>

    Sample: #211abcdefghijk
    """
    return "#{}{}{}".format(len(str(len(string))), len(string), string)


def str2int(string):
    """
    IEEE 488.2 defines #Q, #H and #B as prefix for octal, hexadecimal and binary numbers.
    This functions does as well.
    """
    if isinstance(string, str):
        string=string.replace('#b','0b')
        string=string.replace('#B','0b')
        string=string.replace('#h','0x')
        string=string.replace('#H','0x')
        string=string.replace('#q','0o')
        string=string.replace('#Q','0o')
    return int(string)


def main_test():
    print(repr(findfirst(r"asd", "aaasasd as asd")))
    print(repr(remove_non_ascii("auo")))

if __name__ == "__main__":
    main_test()
