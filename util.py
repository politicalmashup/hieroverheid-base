import re
import os

alphabetic_regex = re.compile('[^a-zA-Z0-9\s]')

def next_new_line(text):
    new_line = text.find("\n")
    while new_line == 0:
        text = text[new_line + 1:]
        new_line = text.find("\n")
    return (text[:new_line], text[new_line:])

def clean_key(key):
    return alphabetic_regex.sub('', key).strip()

def find_key_in_line(line):
    if "\u2013" in line:
        cur_key = line.split("\u2013")[0]
        value = line.split("\u2013")[1].strip()
    elif ":" in line:
        cur_key = line.split(":")[0]
        value = line.split(":")[1].strip()
    elif re.search(r"\s{2,}", line):
        splitted = re.split(r"\s{2,}", line)
        cur_key = splitted[0]
        value = splitted[-1]
    else:
        cur_key = line
        value = None
    value += " "
    return (cur_key, value)


def clear_terminal():
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')