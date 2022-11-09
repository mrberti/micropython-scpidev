try:
    import re
except ImportError:
    import ure as re

from . import utils

VALTYPE_NONE = 0
VALTYPE_NUMERIC = 1
VALTYPE_BOOLEAN = 2
VALTYPE_DISCRETE = 3
VALTYPE_DISCRETE_N = 4
VALTYPE_ASCII_STRING = 5

class SCPIValue():
    """This class represents an SCPI value.

    An SCPIValue is basically a tuple with the following structure:
    ``(required_string, optional_string, numerical_string)``, e.g.
    ``"MAXimum"`` will be parsed into ``("MAX", "imum", "")``.
    Further, the type of the value is stored.
    """
    def __init__(self, value_string):
        self._value_string = value_string
        self._type = VALTYPE_NONE
        self._value_tuple = None

        value  = utils.findfirst(r"^<.+>$", value_string)
        if value:
            if "string" in value_string:
                # Todo: find a better way to define ASCII_STRING type
                self._type = VALTYPE_ASCII_STRING
            else:
                self._type = VALTYPE_NUMERIC
            self._value_tuple = value
        elif value_string:
            self._type = VALTYPE_DISCRETE
            req_string = utils.findfirst(r"[A-Z0-9]+", value_string)
            opt_string = utils.findfirst(r"[a-z]+[0-9]*", value_string)
            num_string = utils.findfirst(r"[a-zA-Z0-9]+(<.+>)", value_string)
            if ((req_string == "ON")
                    or (req_string == "OFF")
                    or (req_string == "1")
                    or (req_string == "0")):
                self._type = VALTYPE_BOOLEAN
            if num_string:
                self._type = VALTYPE_DISCRETE_N
            self._value_tuple = (req_string, opt_string, num_string)

    def __repr__(self):
        return ("<{!r}:{}>".format(self._value_tuple, self._type))

    def __str__(self):
        return str(self._value_tuple)

    def get_type(self):
        """Return the type of the value."""
        return self._type

    def get_value(self):
        """Return the value tuple."""
        return self._value_tuple

    def match(self, test_string):
        """Test if ``test_string`` matches the SCPIValue. Returns ``True`` for
        a match. ``False`` otherwise. A ``ValueError`` is raised if an
        unsupported type is used."""
        test_string = test_string.lower()
        type = self._type
        if type == VALTYPE_NUMERIC:
            if utils.REGEXP_NRF.match(test_string):
                return True
        elif type == VALTYPE_BOOLEAN:
            if (test_string == "ON"
                    or test_string == "OFF"
                    or test_string == "1"
                    or test_string == "0"):
                return True
        elif type == VALTYPE_DISCRETE or type == VALTYPE_DISCRETE_N:
            req_string = self._value_tuple[0].lower()
            opt_string = req_string + self._value_tuple[1].lower()
            if test_string.startswith(req_string):
                if opt_string.startswith(test_string):
                    return True
        elif type == VALTYPE_ASCII_STRING:
            raise NotImplementedError("ASCII_STRING values not yet supported")
        else:
            raise ValueError("Unknown SCPIValue type.")
        return False


class SCPIValueList(list):
    """This class represents a list of all valid SCPI values.

    To check if a concrete SCPIValue is contained in the list, you can simply
    use ``"MAX" in value_list`` where ``value_list`` is an instance of an
    SCPIValueList.
    """

    # def __init__(self, values_string):
    #     """Create a SCPIValueList from ``values_string``. ``values_string``
    #     must be a sanitized string."""
    #     list.__init__(self)
    def init(self, values_string):
        # Get inner part of {} which contains the parameter's values.
        match = re.match(r"{(.+)}", values_string)
        if match:
            inner=match.group(1)
        else:
            inner=None
        if inner:
            for val in inner.split("|"):
                self.append(SCPIValue(val))
        else:
            self.append(SCPIValue(values_string))

    def __repr__(self):
        ret = "["
        for value in self:
            ret = ret + str(value) + ", "
        ret = ret + "]"
        return ret

    def __contains__(self, val):
        for value in self:
            if value.match(val):
                return True
        return False
