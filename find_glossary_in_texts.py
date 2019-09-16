import json
import re
import os
import subprocess

from util import find_key_in_line, find_value_in_line, clean_key, clear_terminal, guess_begrippenlijst_page_number

# TODO:
# - Create continuous text detection to get description in one go and not per line
# - Add redo function
# - Possible solution: detect patterns from what user does, then ask to replicate this pattern until a different pattern is encountered
# - Guess the pagenumber

# Load the extracted texts
with open('extracted_texts.json', 'r') as f:
    extracted_texts = json.load(f)
extracted_texts = extracted_texts[9:]

# Continue where the user last left off (TODO: make this work with topics/scp solution)
texts_to_evaluate = []
for t in extracted_texts:
    if t["name"] + ".json" not in os.listdir("glossarys/"):
        texts_to_evaluate.append(t)

def print_command_instructions():
    print("""
     Menu commands:
        y - yes.
        n - no.
        q - skip this document.
        r - redo last glossary item.
        h - print these commands.
        x - exit the program.
    
     Text evaluation commands:
        q - identify end of glossary.
        d - add current line to current glossary item.
        c - print text surrounding the current line when in doubt.
        h - print these commands.
        
        n (or any other) - reject current text as a new glossary item. Will lead to retry.
        y (or no input) - accept current text as a new glossary item.
        
     Retry commands:
        n (or any other) - reject current text as a new glossary item. Will skip this line.
        y (or no input) - accept current text as a new glossary item.
    """)

def find_first_begrippenlijst_occurence(text):
    occ_index = text.find("Begrippenlijst")
    if occ_index == -1:
        occ_index = text.find("begrippenlijst")
        if occ_index == -1:
            input('No \'Begrippenlijst\' found. Skipping...')
    return occ_index

# Start
clear_terminal()
print("wo-pdf-extraction")
print("="*50)
print(f"\nFound {len(texts_to_evaluate)} documents.")
print_command_instructions()
input("Enter to continue...")


evince_process = None
i = 0
returned = False
while i < len(texts_to_evaluate):
    x = texts_to_evaluate[i]
    i+=1
    if evince_process:
        evince_process.terminate()
        evince_process.wait()
    clear_terminal()
    print("wo-pdf-extraction")
    print("=" * 50, "\n")
    if returned:
        print("Reevaluating document", i, "/", len(texts_to_evaluate), "\n\n", x["name"], '\n\n')
        returned = False
    else:
        print("Processing document", i, "/", len(texts_to_evaluate), "\n\n", x["name"], '\n\n')
    input("Press Enter to continue...")

    text = x["text"]
    text_second_half = text[len(text) // 2:]

    # Initialize the process
    # Confirm glossary location in the text
    begrippenlijst_occ_index = find_first_begrippenlijst_occurence(text_second_half)
    if begrippenlijst_occ_index == -1:
        continue
    begrippenlijst_text = text_second_half[begrippenlijst_occ_index:]
    glos_not_confirmed = True
    glos_found_input = None
    while glos_not_confirmed:
        if glos_found_input == "c":
            clear_terminal()
            context_text = begrippenlijst_text[:250]
            print("\nContext:\n", "-" * 60, "\n", context_text, "\n")
            print("-" * 60)
        print("="*50)
        print(begrippenlijst_text[:100])
        print("="*50)
        glos_found_input = input("Does this look like the glossary of the document? (y/n/q/r/x) ").lower()
        if glos_found_input == "" or glos_found_input == "y" or glos_found_input == "r" or glos_found_input == "q" or glos_found_input == "x":
            glos_not_confirmed = False
        elif glos_found_input == "h":
            print_command_instructions()
        elif glos_found_input == "c":
            pass
        else:
            occ_index = find_first_begrippenlijst_occurence(begrippenlijst_text[14:])
            begrippenlijst_text = begrippenlijst_text[occ_index+14:]

    if glos_found_input == "q":
        continue
    elif glos_found_input == "r":
        returned = True
        i -= 2
        if i < 0:
            i = 0
        continue
    elif glos_found_input == "x":
        break

    # Cut off the first line of the begrippenlijst_text (the title "Begrippenlijst" hopefully)
    begrippenlijst_text = begrippenlijst_text[begrippenlijst_text.find('\n'):]

    # Guess the page number
    begrippenlijst_page_number = guess_begrippenlijst_page_number(text_second_half[begrippenlijst_occ_index - 25:])
    if begrippenlijst_page_number is None:
        # Could not guess pagenumber
        evince_process = subprocess.Popen(["evince", f"pdfs/{x['name']}.pdf"])
        pn_bool = input("No page number found. Does this document contain pagenumbers? (y/n) ")
        if pn_bool == "" or pn_bool == "y" or pn_bool == "Y":
            pn_entered = input(f"Please enter the pagenumber of the glossary: ")
            begrippenlijst_page_number = int(pn_entered)
        elif pn_bool == "h":
            print_command_instructions()
        elif pn_bool == "r":
            returned = True
            i -= 2
            if i < 0:
                i = 0
            continue
        elif pn_bool == "x":
            break
        else:
            glos_bool = input(f"Does this document even contain a Begrippenlijst? (y/n) ")
            if glos_bool == "" or glos_bool == "y" or glos_bool == "Y":
                pass
            else:
                continue
    else:
        # Confirm pagenumber guess
        evince_process = subprocess.Popen(["evince", "-i", str(begrippenlijst_page_number), f"pdfs/{x['name']}.pdf"])
        pn_guess = input(f"Guessed pagenumber is: {begrippenlijst_page_number}. Is this correct? (y/n) ")
        if pn_guess == "" or pn_guess == "y" or pn_guess == "Y":
            pass
        elif pn_guess == "h":
            print_command_instructions()
        elif pn_guess == "r":
            returned = True
            i -= 2
            if i < 0:
                i = 0
            continue
        elif pn_guess == "x":
            break
        else:
            pn_entered = input(f"Please enter the pagenumber of the glossary: ")
            begrippenlijst_page_number = int(pn_entered)


    # Start the process
    line = 0
    glossary = {}
    new_begrip_upcoming = False
    cur_key = None
    text_available = True
    # full_glossary_text = begrippenlijst_text
    cur_text_pos = 0
    match_found = True
    custom_key = None
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
                        print("\n\nContext:\n\n", "-" * 60, "\n", context_text, "\n")
                        print("-" * 60)
                    if choice == "h":
                        print_command_instructions()
                    next_line_key, _ = find_key_in_line(next_line)
                    print("<", next_line_key, ">")
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
                    print("Enter your own key for this item (or 'c' to print context)")
                    custom_key = None
                    while custom_key == 'c' or custom_key is None:
                        if custom_key == 'c':
                            print("\n\nContext:\n\n", "-" * 60, context_text, "\n")
                            print("-" * 60)
                        custom_key = input(">>> ")
                    cur_key = None
                    new_begrip_upcoming = True
                    pass
            else:
                # End of text
                text_available = False


        if new_begrip_upcoming and this_line == next_line:
            # If the current line is the next glossary item, store the cleaned key (and any of the value on this line)
            if len(re.findall("[a-zA-Z0-9]+", this_line)) > 0:
                if custom_key:
                    cur_key = custom_key
                    value = find_value_in_line(this_line, cur_key)
                else:
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
        "intext_pagenumber": begrippenlijst_page_number,
        "glossary": glossary
    }


    # Use a seperate file for each document
    with open(f"glossarys/{x['name']}.json", 'w') as f:
        json.dump(glossary_container, f, indent=2)
