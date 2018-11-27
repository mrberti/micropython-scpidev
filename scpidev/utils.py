import re
import socket
import logging

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
    string_list = re.findall(pattern, string, flags)
    if string_list:
        result = string_list[0]
    else:
        result = ""
    return result

def remove_non_ascii(string):
    return REGEXP_NON_ASCII.sub(r"", string)

def sanitize(input, remove_all_spaces=False):
    """Remove excessive and wrong characters as much as possible."""
    # All non-printable ASCII characters are removed
    sanitized = REGEXP_SANATIZE_BLACKLIST.sub(r"", input)
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

def create_command_tuple(command_string):
    """Create a tuple which contains the keyword and parameter strings. The 
    input is sanatized first."""
    command_string = sanitize(command_string, False)
    c = create_keyword_string(command_string)
    p = create_parameter_string(command_string)
    return (c,p)

def get_local_ip(
        remote_host="1.1.1.1", remote_port=80, default_ip=""):
    """Try to find out the local ip by establishing a test connection to 
    a known remote host. Using "0.0.0.0" or an empty string will lead to 
    listening on all local addresses."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((remote_host, remote_port))
        ip = sock.getsockname()[0]
    except Exception as e:
        ip = default_ip
        logging.warning("Could not get the local IP. Using default: {}. "
            "Exception: {}".format(ip, str(e)))
    sock.close()
    return ip
