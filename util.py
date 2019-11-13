from functools import cmp_to_key
import string

def format_code(s):
    """
    Formats a course code depending on its type.
    :param s: code
    :type s: int or str
    :return: str
    """
    if isinstance(s, int):
        return int(s)
    elif isinstance(s, str):
        return s
    else:
        raise ValueError('Code is neither an int or a str')

def sort_codes(codes):
    """
    Sorts a list of course codes in rising order and returns it.
    :param codes: course codes
    :type s: list
    :return: list
    """
    assert isinstance(codes, list)
    assert all([isinstance(i, int) or isinstance(i, str) for i in codes])

    def cmp_codes(a, b):
        def get_num_ltr(a):
            if isinstance(a, int):
                a_ltr = 0
            else:
                a_num = a.rstrip(string.ascii_uppercase)
                a_ltr = a[len(a_num):]
                a = int(a_num)
            return a, a_ltr
        a, a_ltr = get_num_ltr(a)
        b, b_ltr = get_num_ltr(b)
        if a > b:
            return 1
        elif a == b:
            if a_ltr > b_ltr:
                return 1
            elif a_ltr < b_ltr:
                return -1
            else:
                return 0
        else:
            return -1

    codes.sort(key=cmp_to_key(cmp_codes))
    return codes
