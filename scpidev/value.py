import logging
import re

from . import utils


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
            logging.warning(
                "Detected a NONE typed SCPIValue. Value string = '{}'"
                .format(value_string))

    def __repr__(self):
        return (
            "<{}:{}>".format(
                repr(self._value),
                str(self._type),
        ))

    def __str__(self):
        return str(self._value)

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
    
    def __repr__(self):
        ret = "["
        for value in self:
            ret = ret + str(value) + " "
        ret = ret + "]"
        return ret
