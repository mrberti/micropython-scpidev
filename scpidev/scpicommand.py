import logging
import re


class SCPIKeyword():
    def __init__(self, keyword_tuple, is_optional=False):
        self._keyword_tuple = keyword_tuple
        self._is_optional = is_optional

    def __str__(self):
        if self.is_optional():
            return "[{}]".format(repr(self._keyword_tuple))
        else:
            return "{}".format(repr(self._keyword_tuple))

    def __getitem__(self, key):
        return self._keyword_tuple[key]

    def is_optional(self):
        return self._is_optional


class SCPIKeywordList(list):
    def __init__(self, keyword_string):
        super().__init__()

        is_optional = False
        str_req = str_opt = ""

        for c in keyword_string:
            if c.isupper():
                str_req = str_req + c
                continue
            if c.islower():
                str_opt = str_opt + c
                continue
            if str_req:
                keyword = SCPIKeyword((str_req, str_opt), is_optional)
                self.append(keyword)
            str_req = str_opt = ""

            if c is "[":
                is_optional = True
            if c is "]":
                is_optional = False
            # if c is ":":
            #     pass


class SCPIParameter():

    def __init__(self, 
            name="", 
            position=None, 
            optional="True", 
            values=None, 
            default=None, 
            parameter_string=""):
        """Todo"""
        # Initialize variables.
        self._name = name
        self._position = position
        self._is_optional = optional
        self._values = values
        self._default = default
        self._parameter_string = parameter_string

        # If a parameter string is given, try to initialize from it.
        if parameter_string:
            self._init_from_parameter_string(parameter_string)

    def __str__(self):
        ret = "\n"
        for key, val in self.__dict__.items():
            ret = ret + "<" + str(key) + "> " + repr(val) + "\n"
        return str(ret)

    def _init_from_parameter_string(self, parameter_string):
        # Check, if the parameter is optional. Optional parameters contain an 
        # opening square bracket.
        if "[" in parameter_string:
            is_optional = True
        else:
            is_optional = False

        # Sanatize string by removing all brackets and adding again, if the 
        # parameter is optional.
        parameter_string_temp = re.sub(r"[\[\]]", "", parameter_string)
        if is_optional:
            self._parameter_string  = "[" + parameter_string_temp + "]"
        else:
            self._parameter_string = parameter_string_temp

        # Get parameter name. The parameter name is surrounded by <> and 
        # outside of {}.
        name = re.findall(r"<(.+?)>{.+}", self._parameter_string)
        if name:
            name = name[0]

        # Get inner part of {} which contains the parameter's values.
        inner = re.findall(r"{(.+)}", parameter_string_temp)
        if inner:
            values = inner[0].split("|")
            for val in values:
                # If there is no name given previously, we try to get one from 
                # the parameter's value list or finally try make one up on our 
                # own.
                if not name:
                    name = re.findall(r"^<(.+?)>$", val)
                if not name:
                    name = "p{}".format(str(self._position))
        else:
            # In case that no values are given, the parameter value is assumed 
            # to be a numeric value.
            values = list(name)

        # Finally update all class variables.
        self._name = name
        self._is_optional = is_optional
        self._values = values

    def get_parameter_string(self):
        return self._parameter_string

    def is_optional(self):
        return self._is_optional

    def match(self, parameter_string):
        """Return ``True`` if ``parameter_string`` matches the parameter's 
        syntax. ``False`` otherwise."""
        match = False
        return match


class SCPIParameterList(list):
    def __init__(self, parameter_string):
        super().__init__()

        # Get all optional commands.
        parameter_temp_string = ""
        parameter_list_temp = list()
        for char in parameter_string:
            if "[" in char:
                if parameter_temp_string:
                    parameter_list_temp.append(parameter_temp_string)
                    parameter_temp_string = ""
            parameter_temp_string = parameter_temp_string + char
        parameter_list_temp.append(parameter_temp_string)

        # Sanitize the parameter string and split all non optional commands.
        parameter_string_list = list()
        for parameter in parameter_list_temp:
            if "[," in parameter:
                parameter_string_list.append(parameter.replace(",", ""))
            else:
                parameter_string_list += (parameter_string_list 
                    + parameter.split(","))

        # Create the parameter objects and store them into the parameter list.
        pos = 0
        for parameter in parameter_string_list:
            pos += 1
            self.append(
                SCPIParameter(
                    position=pos,
                    parameter_string=parameter))


class SCPICommand():
    """Todo..."""

    def __init__(self, scpi_string, callback, name="", description=""):
        self._scpi_string = self._sanitize(scpi_string)
        self._callback = callback
        self._description = description
        self._keyword_string = self._create_keyword_string(self._scpi_string)
        self._keyword_list = SCPIKeywordList(self._keyword_string)
        self._parameter_string = self._create_parameter_string(self._scpi_string)
        self._parameter_list = SCPIParameterList(self._parameter_string)
        if name:
            self._name = name
        else:
            self.name = self._keyword_string
        self._is_query = self._keyword_string.endswith("?")

    def __str__(self):
        ret = "\n"
        for key, val in self.__dict__.items():
            ret = ret + "<" + str(key) + "> " + repr(val) + "\n"
        return str(ret)

    def _sanitize(self, input):
        """Remove excessive and wrong characters as much as possible."""
        sanitized = input
        # Control characters which appear often in source code, e.g. new-line 
        # characters in multi-line python strings.
        sanitized = re.sub(r"[\n\t]", r"", sanitized)
        # Spaces at the beginning of the string.
        sanitized = re.sub(r"(^ +)", r"", sanitized)
        # More than one space.
        sanitized = re.sub(r" +", r" ", sanitized)
        return sanitized

    def _create_keyword_string(self, command_string):
        """Creates the keyword string. The keyword string is everything before 
        the first space character."""
        cmd_str = command_string.split(" ")[0]
        return cmd_str
    
    def _create_parameter_string(self, command_string):
        """Create the parameter string. The parameter string is everything 
        after the first space character. All other space characters are 
        removed."""
        parameter_string = "".join(command_string.split(" ")[1:])
        return parameter_string

    def get_keyword_string(self):
        return self._keyword_string

    def get_keyword_list(self):
        return self._keyword_list

    def get_parameter_string(self):
        return self._parameter_string
    
    def get_parameter_list(self):
        return self._parameter_list

    def get_parameter_string_list(self):
        parameter_string_list = list()
        for parameter in self.get_parameter_list():
            parameter_string_list.append(parameter.get_parameter_string())
        return parameter_string_list

    def add_parameter(self, 
            name, 
            optional="False", 
            values="", 
            default=None, 
            parameter_string=""):
        """Add a parameter at the end of the parameter list."""
        position = len(self._parameter_list) + 1
        self._parameter_list.append(
            SCPIParameter(
                name=name, 
                position=position, 
                optional=optional, 
                values=values, 
                default=default, 
                parameter_string=parameter_string,
        ))

    def execute(self, *args, **kwargs):
        logging.debug("execute command: {}".format(repr(self._scpi_string)))
        return self._callback(*args, **kwargs)

    def is_query(self):
        return self._is_query

    def match(self, command_string):
        """Return ``True`` if ``command_string`` matches the instance's 
        keyword and parameters. ``False`` otherwise."""
        keyword_string = self._create_keyword_string(command_string)
        parameter_string = self._create_parameter_string(command_string)
        matches_keyword = self.match_keyword(keyword_string)
        matches_parameter = self.match_parameters(parameter_string)
        return matches_keyword and matches_parameter

    def match_keyword(self, keyword_string):
        """Return ``True`` if ``keyword_string`` matches the instances 
        keyword. ``False`` otherwise."""
        keyword_string = keyword_string.lower()
        # Check if the command is a query. If True, remove the trailing '?'.
        if keyword_string.endswith("?"):
            if self.is_query():
                keyword_string = keyword_string.replace("?", "")
            else:
                logging.debug(
                    "This command is not a query, but the keyword ended with "
                    "'?'.")
                return False
        elif self.is_query():
            logging.debug(
                "This command is a query, but the keyword did not end with '?'"
                ".")
            return False

        # Split keywords into a test string list against which each keyword 
        # will be tested.
        test_string_list = keyword_string.split(":")

        # Iterate over all keywords. Leave the procedure as soon as a mismatch 
        # is detected. When the loop finishes ordinarily, the matching was 
        # succesful.
        keyword_i = 0
        for keyword in self.get_keyword_list():
            if keyword_i >= len(test_string_list):
                if not keyword.is_optional():
                    logging.debug(
                        "Mismatch: Expected more non-optional keywords to "
                        "follow.")
                    return False
                continue
            test_string = test_string_list[keyword_i]
            req_string = keyword[0].lower()
            opt_string = req_string + keyword[1].lower()
            logging.debug(
                "Testing '{}' in '{}'?"
                .format(test_string, keyword))
            if not test_string.startswith(req_string):
                if keyword.is_optional():
                    continue
                else:
                    logging.debug(
                        "Mismatch: Required keyword '{}' not found. Got: '{}'"
                        .format(req_string.upper(), test_string.upper()))
                    return False
            if not opt_string.startswith(test_string):
                logging.debug(
                    "Mismatch: Trailing characters not correct: '{}' =!= '{}'"
                    .format(test_string, opt_string))
                return False
            keyword_i += 1
        logging.debug("Matching OK.")
        return True

    def match_parameters(self, parameter_string):
        match = False
        cmd_parameter_list = SCPIParameterList(parameter_string)
        for parameter in cmd_parameter_list:
            match = match and parameter.match(parameter_string)
        return match
