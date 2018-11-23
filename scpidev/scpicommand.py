import logging
import re

from . import utils


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
        list.__init__(self)

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

            if c == "[":
                is_optional = True
            if c == "]":
                is_optional = False
            # if c == ":":
            #     pass


class SCPIValue():
    NONE = 0
    NUMERIC = 1
    BOOLEAN = 2
    DISCRETE = 3
    DISCRETE_N = 4
    ASCII_STRING = 5

    def __init__(self, value_string):
        self._value_string = value_string
        self._type = SCPIValue.NONE
        self._value = None
        
        value  = utils.findfirst(r"^<.+>$", value_string)
        if value:
            if "string" in value_string:
                # Todo: find a better way to define ASCII_STRING type
                self._type = SCPIValue.ASCII_STRING
            else:
                self._type = SCPIValue.NUMERIC
            self._value = value
        elif value_string:
            self._type = SCPIValue.DISCRETE
            req_string = utils.findfirst(r"[A-Z0-9]+", value_string)
            opt_string = utils.findfirst(r"[a-z]+[0-9]*", value_string)
            num_string = utils.findfirst(r"[a-zA-Z0-9]+(<.+>)", value_string)
            if ((req_string == "ON") 
                    or (req_string == "OFF") 
                    or (req_string == "1") 
                    or (req_string == "0")):
                self._type = SCPIValue.BOOLEAN
            if num_string:
                self._type = SCPIValue.DISCRETE_N
            self._value = (req_string, opt_string, num_string)
        if self._type == SCPIValue.NONE:
            logging.warning("Detected a NONE typed SCPIValue.")

    def __str__(self):
        return (
            "<{}:{}>".format(
                repr(self._value),
                str(self._type),
        ))

    def get_type(self):
        return self._type

    def get_value(self):
        return self._value

    def match(self, test_string):
        test_string = test_string.lower()
        logging.debug(
            "Testing '{}' in '{}'"
            .format(test_string, self))
        type = self.get_type()
        if type == SCPIValue.NUMERIC:
            if utils.REGEXP_NF.match(test_string):
                return True
        elif type == SCPIValue.BOOLEAN:
            if (test_string == "ON" 
                    or test_string == "OFF"
                    or test_string == "1"
                    or test_string == "0"):
                return True
        elif type == SCPIValue.DISCRETE or type == SCPIValue.DISCRETE_N:
            req_string = self.get_value()[0].lower()
            opt_string = req_string + self.get_value()[1].lower()
            if req_string.startswith(test_string):
                if opt_string.startswith(test_string):
                    return True
        elif type == SCPIValue.ASCII_STRING:
            raise NotImplementedError("ASCII_STRING values not yet supported")
        else:
            raise ValueError("Unknown SCPIValue type.")
        return False


class SCPIValueList(list):
    def __init__(self, values_string):
        list.__init__(self)
        values_string = utils.sanitize(values_string, remove_all_spaces=True)

        # Get inner part of {} which contains the parameter's values.
        inner = re.findall(r"{(.+)}", values_string)
        if inner:
            for val in inner[0].split("|"):
                self.append(SCPIValue(val))
        else:
            self.append(SCPIValue(values_string))
    
    def __str__(self):
        ret = "["
        for value in self:
            ret = ret + str(value) + " "
        ret = ret + "]"
        return ret


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
            ret = ret + str(key) + ": " + str(val) + "\n"
        return ret

    def _init_from_parameter_string(self, parameter_string):
        parameter_string = utils.sanitize(parameter_string, True)
        # Check, if the parameter is optional. Optional parameters contain an 
        # opening square bracket.
        if "[" in parameter_string:
            self._is_optional = True
        else:
            self._is_optional = False

        # Sanatize string by removing all brackets and adding again, if the 
        # parameter is optional.
        parameter_string = re.sub(r"[\[\]]", "", parameter_string)
        if self.is_optional():
            self._parameter_string  = "[" + parameter_string + "]"
        else:
            self._parameter_string = parameter_string

        # Get parameter name. The parameter name is surrounded by <> and 
        # outside of {}.
        name = re.findall(r"<(.+?)>{.+}", self._parameter_string)
        if name:
            name = name[0]
        self._value_list = SCPIValueList(parameter_string)
        self._name = name

    def get_parameter_string(self):
        return self._parameter_string
    
    def get_value_list(self):
        return self._value_list

    def is_optional(self):
        return self._is_optional

    def match(self, test_string):
        """Return ``True`` if ``test_string`` matches the parameter's 
        syntax. ``False`` otherwise."""
        logging.debug(
            "Testing '{}' in '{}'?"
            .format(test_string, self.get_parameter_string()))
        for value in self.get_value_list():
            if value.match(test_string):
                return True
        return False


class SCPIParameterList(list):
    def __init__(self, parameter_string):
        list.__init__(self)
        parameter_string = utils.sanitize(
            parameter_string, remove_all_spaces=True)

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

    def __str__(self):
        ret = "["
        for value in self:
            ret = ret + str(value) + " "
        ret = ret + "]"
        return ret


class SCPICommand():
    """Todo..."""

    def __init__(self, scpi_string, callback, name="", description=""):
        self._scpi_string = utils.sanitize(scpi_string)
        self._callback = callback
        self._description = description
        self._keyword_string = utils.create_keyword_string(self._scpi_string)
        self._keyword_list = SCPIKeywordList(self._keyword_string)
        self._parameter_string = utils.create_parameter_string(self._scpi_string)
        self._parameter_list = SCPIParameterList(self._parameter_string)
        if name:
            self._name = name
        else:
            self.name = self._keyword_string
        self._is_query = self._keyword_string.endswith("?")

    def __str__(self):
        ret = "\n"
        for key, val in self.__dict__.items():
            ret = ret + str(key) + ": " + str(val) + "\n"
        return str(ret)

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

    def execute_if_match(self, parameter_string):
        if not self.match_parameters(parameter_string):
            logging.debug("Parameter mismatch. Got '{}' but expected '{}'"
                .format(
                str(parameter_string),
                str(self.get_parameter_string())))
            return None
        return self.execute(parameter_string)

    def execute(self, parameter_string):
        args = parameter_string.split(",")
        kwargs = dict()
        logging.debug("execute command: {}".format(repr(self._scpi_string)))
        return self._callback(*args, **kwargs)

    def is_query(self):
        return self._is_query

    def match(self, command_string):
        """Return ``True`` if ``command_string`` matches the instance's 
        keyword and parameters. ``False`` otherwise."""
        keyword_string = utils.create_keyword_string(command_string)
        parameter_string = utils.create_parameter_string(command_string)
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
                "Testing '{}' in '{}'"
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

    def match_parameters(self, test_string):
        test_string = utils.sanitize(test_string, remove_all_spaces=True)
        test_parameter_string_list = test_string.split(",")
        pos = 0
        n_test_parameter = len(test_parameter_string_list)
        for parameter in self.get_parameter_list():
            if pos >= n_test_parameter:
                if not parameter.is_optional():
                    return False
                continue
            test = test_parameter_string_list[pos]
            if not parameter.match(test):
                return False
            pos += 1
        return True
