
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


def format_value(string):
    """
    This will format all output value
    """
    if isinstance(string, str):
        if string[-1] == ' ':
            return string.rstrip(string[-1])
        else:
            return string
    return round(string, 2)
