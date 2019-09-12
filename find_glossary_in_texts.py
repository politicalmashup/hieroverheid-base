import json
import re
import os
import subprocess

from util import find_key_in_line, clean_key, clear_terminal

# TODO:
# - Create continuous text detection to get description in one go and not per line
# - Add redo function
# - Possible solution: detect patterns from what user does, then ask to replicate this pattern until a different pattern is encountered

# Load the extracted texts
with open('extracted_texts.json', 'r') as f:
    extracted_texts = json.load(f)
extracted_texts = extracted_texts[0:4]

# Continue where the user last left off (TODO: make this work with topics/scp solution)
texts_to_evaluate = []
for t in extracted_texts:
    if t["name"] + ".json" not in os.listdir("glossarys/"):
        texts_to_evaluate.append(t)

def print_command_instructions():
    print("""
     Commands:
        q - identify end of glossary.
        r - redo last glossary item. (not implemented)
        d - add current line to current glossary item.
        c - print text surrounding the current line when in doubt.
        h - print these commands.
        n (or any other) - reject current text as a new glossary item. Will lead to retry.
        
        (no input) - accept current text as a new glossary item.
        
     Retry commands:
        n (or any other) - reject current text as a new glossary item. Will skip this line.
        
        (no input) - accept current text as a new glossary item.
    """)

# Start
for x in texts_to_evaluate:
    clear_terminal()
    print("wo-pdf-extraction")
    print("=" * 50, "\n")
    print("Extracting: ", x["name"], '\n')
    input("Press Enter to continue...")

    text = x["text"]
    text2 = text[len(text)//2:]

    first_occ_index = text2.find("begrippenlijst")
    if first_occ_index == -1:
        first_occ_index = text2.find("Begrippenlijst")
    begrippenlijst_text = text2[first_occ_index:]
    begrippenlijst_text = begrippenlijst_text[begrippenlijst_text.find('\n'):]

    line = 0
    glossary = {}
    new_begrip_upcoming = False
    cur_key = None
    text_available = True
    # full_glossary_text = begrippenlijst_text
    cur_text_pos = 0
    match_found = True
    while text_available:
        next_return_pos = begrippenlijst_text[cur_text_pos:].find("\n")
        r_this_line = begrippenlijst_text[cur_text_pos:cur_text_pos + next_return_pos + 1]
        this_line = r_this_line[re.search(r"[a-zA-Z0-9(\n]", r_this_line).start():]
        remaining_text = begrippenlijst_text[cur_text_pos + next_return_pos + 1:]
        # remaining_text = begrippenlijst_text[begrippenlijst_text.find("\n")+1:]

        # this_line = begrippenlijst_text[:begrippenlijst_text.find("\n")]
        # remaining_text = begrippenlijst_text[begrippenlijst_text.find("\n")+1:]
        # begrippenlijst_text = remaining_text
        # print('  ', line, this_line)

        # Store this line in a glossary item if we are filling a glossary key
        if cur_key is not None:
            cleaned_key = clean_key(cur_key)
            if glossary.get(cleaned_key) is None:
                glossary[cleaned_key] = r_this_line
            else:
                glossary[cleaned_key] += r_this_line
            if this_line == next_line:
                match_found = True

        if not new_begrip_upcoming and match_found:
            # Identify the next line as either a key OR part the description OR mark the end of the glossary
            print("")
            next_text_match = re.search("[a-zA-Z0-9(]", remaining_text)
            if next_text_match:
                next_text_match_pos = next_text_match.start() + cur_text_pos + 1
                next_text = remaining_text[next_text_match.start():]
                # next_text = begrippenlijst_text[next_text_match_pos:]
                next_line = next_text[:next_text.find("\n")+1]
                match_found = False

                context_text_start = next_text_match_pos - 200
                if context_text_start < 0:
                    context_text_start = 0
                context_text = begrippenlijst_text[context_text_start:next_text_match_pos+300]

                choice = None
                while choice == "c" or choice =="h" or choice is None:
                    clear_terminal()
                    if choice == "c":
                        print("\n\nContext:\n\n", "-" * 60, context_text, "\n")
                        print("-" * 60)
                    if choice == "h":
                        print_command_instructions()
                    print("<", next_line, ">")
                    choice = input(">>> ")


                # choice = input("Is this a new key? (Press Enter to say accept, if its part of the description enter \"d\", if you think this is the end of the begrippenlijst enter \"q\", otherwhise anything else): ")
                if choice == "":
                    new_begrip_upcoming = True
                    cur_key = None
                elif choice == "d":
                    pass
                elif choice == "q":
                    text_available = False
                else:
                    print("Retrying...")
                    next_line_key, _ = find_key_in_line(next_line)
                    print("<", next_line_key, ">")
                    choice = input(">>> ")
                    if choice == "":
                        new_begrip_upcoming = True
                        cur_key = None
            else:
                # End of text
                text_available = False


        if new_begrip_upcoming and this_line == next_line:
            # If the current line is the next glossary item, store the cleaned key (and any of the value on this line)
            if len(re.findall("[a-zA-Z0-9]+", this_line)) > 0:
                cur_key, value = find_key_in_line(this_line)
                if value:
                    cleaned_key = clean_key(cur_key)
                    glossary[cleaned_key] = value
                # remaining_text = remaining_text[len(this_line):]
                new_begrip_upcoming = False
                match_found = True
        cur_text_pos += len(this_line)
        line += 1

    print("Begrippenlijst extracted looks like: ")
    for begrip in glossary.keys():
        print(begrip, ' - ', glossary[begrip], '\n')

    glossary_container = {
        "id": int(x["id"]),
        "doc_name": x["name"],
        "pdf_url": x["url"],
        "glossary": glossary
    }


    # Use a seperate file for each document
    with open(f"glossarys/{x['name']}.json", 'w') as f:
        json.dump(glossary_container, f, indent=2)
