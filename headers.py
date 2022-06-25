import os
import sys
import requests
import pyperclip

path = os.path.dirname(os.path.abspath(__file__))
s_path = path.split('\\')
sys.path.insert(0, '\\'.join(s_path) + '\\[MySources]')


headers = pyperclip.paste()
lines = headers.split('\r\n')
parsed_headers = []
parsed_params = []
headers_mode = True
for line in lines:
    key, value = line.split(': ')
    if headers_mode:
        key = key.lower()
        if ':' in key:
            key = key.replace(':', '')
        if key == 'user-agent':
            value = 'self.user_agent'
            str_ = f"            '{key}': {value}"
            headers_mode = False
        elif key == 'cookie':
            #value = 'self.cookies_string'
            #str_ = f"            '{key}': {value}"
            continue
        else:
            str_ = f"            '{key}': '{value}'"
        parsed_headers.append(str_)
    else:
        if key.lower() == 'x-requested-with':
            str_ = f"            '{key.lower()}': '{value}'"
            parsed_headers.append(str_)
        else:
            str_ = f"            ('{key}', '{value}')"
            parsed_params.append(str_)
result = 'headers = {\n'
result += ',\n'.join(parsed_headers)
result += '\n        }\n'
params_string = ',\n'.join(parsed_params)
if parsed_params:
    result += f"""        params = [
{params_string}
        ]\n"""
params_string = 'data=params, ' if parsed_params else ''
result += f'        r = requests.post(url, {params_string}headers=headers)'
pyperclip.copy(result)