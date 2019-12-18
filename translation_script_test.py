import pytest
import translation_script as ts
from pathlib import Path

def test_find_xml_files(tmp_path: Path):
    # To run the test, we create a mock directory structure with 2 xml files
    test1 = tmp_path / "test1.xml"
    test1.write_text(Path('./test_data/test1.xml').read_text())
    p = tmp_path / 'extra_folder'
    p.mkdir()
    test2 = p / "test2.xml"
    test2.write_text(Path('./test_data/test2.xml').read_text())
    paths = ts.find_xml_files(tmp_path)
    assert paths == [test1, test2] or paths == [test2, test1]   # No order!

def test_move_xml_files(tmp_path: Path):
    # Create a mock directory structure. Values to be moved from old to new.
    old = tmp_path / "old"
    old.mkdir()
    test1 = old / "test1.xml"
    test1.write_text(Path('./test_data/test1.xml').read_text())
    p = old / 'extra_folder'
    p.mkdir()
    test2 = p / "test2.xml"
    test2.write_text(Path('./test_data/test2.xml').read_text())
    new = tmp_path / "new"
    new.mkdir()

    # Check values have been moved and the old directory removed
    ts.move_xml_files(old, new)
    assert (new / "test1.xml").is_file() and (new / "test2.xml").is_file()
    assert old.is_dir() == True
    assert ts.find_xml_files(old) == []

def test_aggregate_xmls(tmp_path: Path):
    # Create a mock directory with the 2 test xmls
    data = tmp_path / "data"
    data.mkdir()
    test1 = data / "test1.xml"
    test1.write_text(Path('./test_data/test1.xml').read_text())
    test2 = data / "test2.xml"
    test2.write_text(Path('./test_data/test2.xml').read_text())

    # Aggregate the 2 test xmls to a single csv
    aggregate = data / "aggregate.csv"
    ts.aggregate_xmls([test1, test2], aggregate)

    # Check validity
    with open(aggregate, 'r') as f:
        assert f.readline() == "test1.xml\n"
        assert f.readline() == "|".join(["1", "NeedHelpPopUp", 
            "If you require any assistance press 'Enter'",
            "If you require any assistance press 'Enter'", "no context", 
            "", ""]) + "\n"
        f.readline()
        assert f.readline() == "test2.xml\n"
        assert f.readline() == "1|Test1|Test1|Testi|no context|Test1 = testi|\n"

def test_pretranslate_row():
    row = ['ID', 'Resource', 'No glossary', None, None, None, None]
    row = ts.pretranslate_row(row)
    assert row == ['ID', 'Resource', 'No glossary','No glossary', 
                    None, None, None]

    row = ['ID', 'Resource', 'Time to use the Glossary', 
            None, None, 'glossary = sanasto; time = aika', None]
    row = ts.pretranslate_row(row)
    assert row == ['ID', 'Resource', 'Time to use the Glossary', 
                    'Aika to use the Sanasto', None, 
                    'glossary = sanasto; time = aika', None]

def test_remove_systematic_errors(tmp_path: Path):
    test3 = tmp_path / "test3.csv"
    test3.write_text(Path('./test_data/test3.csv').read_text())
    target = tmp_path / "target.csv"
    ts.remove_systematic_errors(test3, target)
    with open(target, 'r') as f:
        assert f.readline() == "test1.xml\n"
        f.readline()
        f.readline()
        f.readline()
        assert f.readline() == "1|Test1|Test1|Testi|no context|Test1 = testi|\n"
        assert f.readline() == "|".join(["2", "Testiresurssi", 
            'For some reason <x id="1"/> and <x id="2"/> mistranslated.',
            'For some reason <x id="1"/> and <x id="2"/> mistranslated.',
            "no context", "", ""]) + "\n"

