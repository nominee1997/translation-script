from typing import List
from pathlib import Path
import xml.etree.ElementTree as ET
import shutil
import csv
import argparse

"""
This script is used to help translate large collections of strings from English
to Finnish using Google Translate. The script is broken to 2 phases

First phase: 
The strings to be translated are in multiple xml files (sometimes 15+)
within a complex directory tree rooted at ../todo. First we find these .xml
files, and then move them to a flat directory in ../intermediate for 
easier handling. The old directory structure is removed. Then the files are 
aggregated to a single intermediate.csv file and some pretranslation is 
performed to improve the accuracy for technical words and project specific
words.

Manual step:
Next the strings to be translated in intermediate.csv are put through 
google translate (which can be done fast with max size of 5000 symbols per
entry), and the translated strings are saved to same file.

Second phase:
Google translate does some systematic errors with placeholder values. These
are corrected and the corrected strings are put to ../final/final.csv. The 
original .xml files are also moved to ../final. 

Manual step:
The translations are then manually corrected and the translated values 
pasted back to the appropriate .xml file (pasting done by hand since QC
needs to be done at the same time anyways). The files can then be zipped and
sent back to the appropriate stakeholder.


Usage:
python translation_script.py phase
where phase is either 1 or 2, depending on the phase the user wishes to run.

"""

def remove_systematic_errors(source: Path, target: Path) -> None:
    """
    Google translate does some systematic errors in its translations.
    Mainly a very commonly used placeholder format <x id="i"/> gets
    mapped to <x id = "i" />, where i is an indexing that increments each time 
    it is used within a single string which starts with 1. I.E. we can have i 
    values from 1 to 5 within a single string, but can't have say 1 and 4.

    Function opens the csv file at source, and a file at target and copies
    rows from source to target and applies these error corrections.
    """
    with open(target, 'w', encoding='utf-8') as target_f:
        with open(source, 'r', encoding='utf-8') as source_f:
            writer = csv.writer(target_f, delimiter="|", quoting=csv.QUOTE_NONE, 
            escapechar='\\', quotechar='')
            reader = csv.reader(source_f, delimiter="|", quoting=csv.QUOTE_NONE, 
            escapechar='\\', quotechar='')

            for row in reader:
                if len(row) == 7:
                    i = 1
                    while row[3].find('<x id = "{}" />'.format(i)) != -1:
                        row[3] = row[3].replace('<x id = "{}" />'.format(i), 
                                                    '<x id="{}"/>'.format(i))
                        i += 1

                writer.writerow(row)


def pretranslate_row(row_items: List[str]) -> List[str]:
    """
    Format of the rows:
    ID | Resource | Source | Target | Context | Glossary | Notes

    The field Target is previously None, this function fills it. It will be 
    set to the same value as Source, but words in the Glossary should be 
    changed to their Finnish translation (these are only project specific or
    very technical words!).

    This step dramatically improves google translate accuracy with both 
    consisteny and proper use of the grammatical cases.

    Note: doesn't copy the old row, but modifies original. Use case doesn't 
    require copying.
    """
    # Glossary can be None
    if row_items[5] is None:
        row_items[3] = row_items[2]
        return row_items

    # Glossary is of form 'word1 = translation1; word2 = translation2; ...'
    glossary = dict()
    for pair in row_items[5].split(";"):
        pair = [value.strip() for value in pair.split("=")]
        if len(pair) == 2:
            # Add both capitalised and uncapitalised versions to glossary dict
            glossary[pair[0]] = pair[1]
            glossary[pair[0].title()] = pair[1].title()
        else:
            pass    # Added since there were a few bad glossaries

    # Set target equal to source, and replace words using glossary if possible
    row_items[3] = " ".join([glossary[word] if word in glossary else word for   
                                  word in row_items[2].split(" ")])
    return row_items

def aggregate_xmls(paths: List[Path], target: Path) -> None:
    """
    Files are opened and the data from the rows is aggregated to a single .csv
    file. Some additional pretranslation processing has also been added.
    """
    with open(target, mode='w', encoding='utf-8') as aggregate:
        # Settings more specific to conserve original quotes.
        writer = csv.writer(aggregate, delimiter="|", quoting=csv.QUOTE_NONE, 
        escapechar='\\', quotechar='')

        # namespace to be used
        ns = {'ss':"urn:schemas-microsoft-com:office:spreadsheet"}
        for path in paths:
            # Write the name of the file on a single row
            writer.writerow([path.parts[-1]])

            # Parse the xml
            tree = ET.parse(path)
            root = tree.getroot()
            sheet = root.find("ss:Worksheet", ns)
            table = sheet.find("ss:Table", ns)
            # The first 8 rows are metadata!
            for row in table.findall("ss:Row", ns)[8:]:
                row_items = []
                for cell in row:                        
                    for data in cell:
                        row_items.append(data.text)
                writer.writerow(pretranslate_row(row_items))

def move_xml_files(source: Path, target: Path) -> None:
    """
    Moves all xml files from source to target and empties old directory tree.
    Note: Does not preserve old directory tree structure, the new is flat!
    """
    files = find_xml_files(source)
    for file in files:
        shutil.move(str(file), str(target))     # shutil requires str input!
    shutil.rmtree(str(source))
    source.mkdir()

def find_xml_files(root: Path) -> List[Path]:
    """
    Find all files which end with .xml in the directory tree rooted at root
    """
    files = list(root.glob('**/*.xml'))    # ** is for recursive
    return files

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Translation script')
    parser.add_argument('phase', metavar='phase', type=int,
                        help='the phase of the script to be run')

    args = parser.parse_args()
    
    if args.phase == 1:
        # Run first phase of the script

        # Files should be moved to a directory called intermediate
        # todo is also emptied
        todo_path = Path('../todo')
        intermediate_path = Path('../intermediate')
        move_xml_files(todo_path, intermediate_path)

        # Files should then be combined to a single .csv file
        files = find_xml_files(Path('../intermediate'))
        aggregate_xmls(files, Path('../intermediate/intermediate.csv'))

    elif args.phase == 2:
        # Run second phase of the script

        # Run systematic error check
        intermediate = Path('../intermediate')
        final = Path('../final')
        remove_systematic_errors(intermediate / "intermediate.csv", 
                                    final / "final.csv")

        # Move xml files to final (also removes intermediate.csv)
        move_xml_files(intermediate, final)

    else:
        raise ValueError("The value for phase should be one of 1, 2")