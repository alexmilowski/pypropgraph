import string

def quote_string(v : str):

    if len(v) == 0:
        return '""'

    v = v.replace('\\', '\\\\')
    v = v.replace('"', '\\"')

    return '"{}"'.format(v)


def stringify_param_value(value):
    if isinstance(value, str):
        return quote_string(value)
    elif value is None:
        return "null"
    elif isinstance(value, (list, tuple)):
        return f'[{",".join(map(stringify_param_value, value))}]'
    elif isinstance(value, dict):
        return f'{{{",".join(f"{k}:{stringify_param_value(v)}" for k, v in value.items())}}}'
    else:
        return str(value)