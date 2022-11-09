try:
    import re
except ImportError:
    import ure as re

from . import utils
from .value import SCPIValue, SCPIValueList


class SCPIParameter():
    def __init__(self,
            name="",
            optional="True",
            value_list=list(),
            default=None,
            parameter_string=""):
        """Todo"""
        # Initialize variables.
        self._name = name
        self._is_optional = optional
        self._value_list = value_list
        self._default = default
        self._parameter_string = parameter_string

        # If a parameter string is given, try to initialize from it.
        if parameter_string:
            self._init_from_parameter_string(parameter_string)

    def __repr__(self):
        ret = "\n"
        for key, val in self.__dict__.items():
            ret = ret + str(key) + ": " + str(val) + "\n"
        return ret

    def __str__(self):
        return self._parameter_string

    def _init_from_parameter_string(self, parameter_string):
        """The parameter parser is the heart of the package.

        TODO:
        - Notation for default parameters
        """
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
        match = re.match(r"(.+?){.+}", self._parameter_string)
        if match:
            name=match.group(1)
        else:
            name=None
            
        if name:
            name = name[0]
        self._value_list = SCPIValueList()
        self._value_list.init(parameter_string)
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
        return test_string in self.get_value_list()


class SCPIParameterList(list):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def init(self, parameter_string):
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
        for parameter in parameter_string_list:
            self.append(SCPIParameter(parameter_string=parameter))

    def __str__(self):
        ret = "["
        for value in self:
            ret = ret + str(value) + " "
        ret = ret + "]"
        return ret

    def __contains__(self, test_parameter):
        """Check if the parameterlist contains ``test_parameter``.

        Usage: ``test_parameter in parameter_list``. ``test_parameter`` must
        be a sanatized string.

        TODO:
        - The current procedure will accept test_parameters like ",MIN".
        Meaning that the prvious optional parameter is left empty. Need
        to check if this is acceptable or not. I think yes, because the user
        function must accept default parameters for optional parameters in any
        case. But it would be nice, if a default parameter feature would be
        implemented in this package.
        """
        test_para_list = test_parameter.split(",")
        if len(test_para_list) > len(self):
            # There were more parameters given than contained in this list.
            return False

        # To make this work, a new list must be created.
        parameter_list_temp = self[:]
        for test in test_para_list:
            for parameter in parameter_list_temp:
                if test == "" and parameter.is_optional():
                    break
                if parameter.match(test):
                    parameter_list_temp.pop(0)
                    break
                return False
        return True
