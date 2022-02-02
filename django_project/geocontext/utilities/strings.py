

def strip_whitespace(string):
    """
    Strip the withe space of string
    """
    if isinstance(string, str):
        if string[-1] == ' ':
            return string.rstrip(string[-1])
        else:
            return string
    return string



