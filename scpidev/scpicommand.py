import logging
import re

def _dummy_fun(**kwargs):
    logging.debug("Called dummy function.")


class SCPIParameter():

    def __init__(self, 
            name="", 
            position=None, 
            optional="True", 
            type=None, 
            values=None, 
            default=None, 
            parameter_string=""):
        # Initialize variables.
        self._name = name
        self._position = position
        self._is_optional = optional
        #self._type = type
        self._values = values
        #self._default = default
        self._parameter_string = parameter_string

        # If a parameter string is given, try to initialize from it.
        if parameter_string:
            self.init_from_parameter_string(parameter_string)

    def init_from_parameter_string(self, parameter_string):
        # Check, if the parameter is optional. Optional parameters contain an 
        # opening square bracket.
        if "[" in parameter_string:
            is_optional = True
        else:
            is_optional = False

        # Sanatize string by removing all brackets and adding again, if the 
        # parmeter is optional.
        parameter_string_temp = re.sub(r"[\[\]]", "", parameter_string)
        if is_optional:
            self._parameter_string  = "[" + parameter_string_temp + "]"
        else:
            self._parameter_string = parameter_string_temp
        # print(repr(self._parameter_string))
        # print(is_optional

        # Get parameter name. The parameter name is surrounded by <> and 
        # outside of {}.
        name = re.findall(r"<(.+?)>{.+}", self._parameter_string)
        if name:
            name = name[0]
        # print(self._name)

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
        # print(values)

        # Finally update all class variables.
        self._name = name
        self._is_optional = is_optional
        self._values = values
        print(self)

    def is_optional(self):
        return self._is_optional

    def __str__(self):
        ret = "\n"
        for key, val in self.__dict__.items():
            ret = ret + "<" + str(key) + "> " + repr(val) + "\n"
        return str(ret)


class SCPICommand():
    _name = "Unknown name"
    _description = ""
    _scpi_string = ""
    _keyword_string = ""
    _parameter_string = ""
    _parameter_list = list()
    _callback = None
    _kwargs = dict()
    _regext = ""
    _keyword = ""

    _is_query = False

    def __init__(self, scpi_string, callback, description=""):
        self._scpi_string = scpi_string
        self._callback = callback
        self._description = description
        self._keyword_string = self.create_keyword_string()
        self._parameter_string = self.create_parameter_string()
        self._parameter_list = self.create_parameter_list()
        # logging.debug("Created new command: {}".format(repr(scpi_string)))

    def create_keyword_string(self):
        """Returns the keyword string. The keyword string is everything before 
        the first space character."""
        cmd_str = self._scpi_string.split(" ")[0]
        return cmd_str
    
    def create_parameter_string(self):
        """Returns the parameter string. The parameter string is everything 
        after the first space character. All other space characters are 
        removed."""
        parameter_string = "".join(self._scpi_string.split(" ")[1:])
        return parameter_string

    def get_parameter_list(self):
        return self._parameter_list

    def create_parameter_list(self):
        parameter_list = list()
        if not self._parameter_string:
            return parameter_list

        # First we get all optional commands.
        parameter_string = ""
        parameter_list_temp = list()
        for char in self._parameter_string:
            if "[" in char:
                if parameter_string:
                    parameter_list_temp.append(parameter_string)
                    parameter_string = ""
            parameter_string = parameter_string + char
        parameter_list_temp.append(parameter_string)

        # Sanatize the parameter string and split all non optional commands.
        parameter_string_list = list()
        for parameter in parameter_list_temp:
            if "[," in parameter:
                parameter_string_list.append(parameter.replace(",", ""))
            else:
                parameter_string_list += (parameter_string_list 
                    + parameter.split(","))

        # Finally, we create the parameter objects and store them into the 
        # parameter list
        pos = 0
        for parameter in parameter_string_list:
            pos += 1
            parameter_list.append(
                SCPIParameter(
                    position=pos,
                    parameter_string=parameter))
            # print(repr(parameter))

        return parameter_list

    def execute(self):
        logging.debug("execute command: {}".format(repr(self._scpi_string)))
        self._callback(**self._kwargs)

    def is_query(self):
        return self._is_query

    def match(self, scpi_str):
        res = False
        return res

    def add_parameter(self, 
            name, 
            type="numeric", 
            range="", 
            default=None, 
            optional="False"):
        self._parameter_list.append(
            SCPIParameter(name, optional, type, range, default))

    def __str__(self):
        ret = "\n"
        for key, val in self.__dict__.items():
            ret = ret + "<" + str(key) + "> " + repr(val) + "\n"
        return str(ret)
