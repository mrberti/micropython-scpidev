import logging
import re

from . import utils
from .keyword import SCPIKeyword, SCPIKeywordList
from .parameter import SCPIParameter, SCPIParameterList


class SCPICommand():
    def __init__(self, scpi_string, callback, name="", description=""):
        scpi_string = utils.sanitize(scpi_string)
        self._callback = callback
        self._description = description
        self._keyword_string = utils.create_keyword_string(scpi_string)
        self._keyword_list = SCPIKeywordList(self._keyword_string)
        self._parameter_string = utils.create_parameter_string(scpi_string)
        self._parameter_list = SCPIParameterList(self._parameter_string)
        self._scpi_string = self._keyword_string + " " + self._parameter_string
        if name:
            self._name = name
        else:
            self.name = self._keyword_string
        self._is_query = self._keyword_string.endswith("?")

    def __repr__(self):
        ret = "\n"
        for key, val in self.__dict__.items():
            ret = ret + str(key) + ": " + str(val) + "\n"
        return str(ret)

    def __str__(self):
        return self._scpi_string

    def get_callback(self):
        return self._callback

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
            value_list=list(), 
            default=None, 
            parameter_string=""):
        """Add a parameter at the end of the parameter list."""
        self._parameter_list.append(
            SCPIParameter(
                name=name, 
                optional=optional, 
                value_list=value_list, 
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
        parameter_string = utils.sanitize(parameter_string, True)
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
        if keyword_i < len(test_string_list):
            logging.debug("Mismatch: Could not parse all keywords.")
            return False
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


class SCPICommandList(list):
    def __init__(self):
        list.__init__(self)
