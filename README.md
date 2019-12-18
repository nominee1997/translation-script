# translation-script
Short script written in Python used for automating some parts of a specific personal translation process.

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
```$ python translation_script.py phase```
where phase is either 1 or 2, depending on the phase the user wishes to run. 

To run the tests write
```$ pytest -vv```

Dependencies:
Only Pytest for running the tests
