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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def init(self, keyword_string):
        is_optional = False
        str_req = str_opt = ""

        for c in keyword_string:
            if c.isupper() or c == "*":
                str_req = str_req + c
                continue
            if c.islower():
                str_opt = str_opt + c
                continue
            if str_req:
                keyword = SCPIKeyword((str_req, str_opt), is_optional)
                self.append(keyword)
            if c == "[":
                is_optional = True
            if c == "]":
                is_optional = False
            # if c == ":":
            #     pass
            str_req = str_opt = ""

        # If we reached here and the str_req is not an empty string, all
        # characters were processed without finding any special character.
        # In other words: The keyword string only contains one word.
        if str_req:
            keyword = SCPIKeyword((str_req, str_opt), is_optional)
            self.append(keyword)
