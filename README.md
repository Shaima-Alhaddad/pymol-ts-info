
---

# pymol-ts-info

PyMOL helper that reads CASP TS files and prints five key metadata
fields (Stoichiometry, Author, Method, Score, Model) in the PyMOL
console.

<img width="710" height="427" alt="Screenshot 2025-09-18 at 20 30 35" src="https://github.com/user-attachments/assets/fd2dd80f-9091-43c0-8df8-7bba28b2ef82" />


------------------------------------------------------------------------

# Files

- [![Download pymol_ts_helper](https://img.shields.io/badge/Download-pymol_ts_helper.py-blue?style=for-the-badge&logo=python)](https://raw.githubusercontent.com/Shaima-Alhaddad/pymol-ts-info/main/pymol_ts_helper.py) Plugin script (run in PyMOL)

- [![Download TXT](https://img.shields.io/badge/Download-TXT-2b6cb0?style=for-the-badge&logo=)](https://github.com/Shaima-Alhaddad/pymol-ts-info/blob/main/H0232_TS.txt) Example CASP TS file.

- [![Download PDB](https://img.shields.io/badge/Download-PDB-2b6cb0?style=for-the-badge&logo=)](https://github.com/Shaima-Alhaddad/pymol-ts-info/blob/main/Model_H0232.pdb)  Example PDB model.







------------------------------------------------------------------------

# Commands to run in PyMOL.

(Quick usage, no installation is needed)

Replace <PATH_TO_YOUR_FILES> with your folder, for examples:

Mac/Linux: `/Users/yourname/Desktop/pymol_ts_helper.py`

Windows: `C:\Users\yourname\Desktop\pymol_ts_helper.py`


1.  Load the plugin (run once each PyMOL session). Type this at the
    PyMOL prompt (not inside a `python` block):


``` text
 run <PATH_TO_YOUR_FILES>/pymol_ts_helper.py
```
<img width="863" height="30" alt="Screenshot 2026-02-24 at 12 26 32" src="https://github.com/user-attachments/assets/a1629794-4b3a-4ce1-ae9e-12cc606ad6df" />



2.  Load PDB + TS together (preferred if both files available)

``` text
 load_model_with_ts <PATH_TO_YOUR_FILES>/examples/Model_H0232.pdb, <PATH_TO_YOUR_FILES>/examples/H0232_TS.txt
```
<img width="870" height="62" alt="Screenshot 2026-02-24 at 12 18 54" src="https://github.com/user-attachments/assets/4a170f9b-8223-46ef-8494-4e857b8438d5" />


An examples of the Console output, it will show the following:

=== TS metadata for: H0232_TS ===

Stoichiometry: A2B2

Author: MultiFOLD2

Method: Method text

Score(s): 0.9110 Model: 1
<img width="1892" height="784" alt="PyMol_TS" src="https://github.com/user-attachments/assets/213cbfe1-c9fb-43c7-9fba-f65107226da8" />

------------------------------------------------------------------------

# Examples of additional commands

1)  If the model is already open in PyMOL → attach TS and show

`attach_ts <PATH_TO_YOUR_FILES>/examples/H0232_TS.txt, Model_H0232 show_ts_info Model_H0232`

2)  If only TS file available (no model load in PyMOL)

`parse_ts <PATH_TO_YOUR_FILES>/examples/H0232_TS.txt show_ts_info H0232_TS`

3)  Quick show when single model is open in PyMOL. (If exactly one
    object is loaded, show_ts_info will use it automatically.)

`show_ts_info`

4)  Batch parse many TS files:

`parse_ts /<PATH_TO_YOUR_FILES>/*.txt`

------------------------------------------------------------------------

# Notes & troubleshooting

-   **Order for `load_model_with_ts`:** the first order must be the
    PDB model name, then the TS file must be second.

-   **Already open models:** if you dragged a PDB into PyMOL, find the
    object name in PyMOL.

-   **If `show_ts_info` says “no metadata cached”**: run
    `parse_ts /path/to/file.txt` or
    `attach_ts /path/to/file.txt, <object>` first.

-   **Run at the PyMOL prompt**: run, load_model_with_ts, parse_ts, etc.
    are PyMOL commands — do not type them inside a python/end block.

-   **The difference between these commands in PyMOL: parse_ts vs
    show_ts_info**

parse_ts

Purpose: Read one or more CASP TS text files.

Input: a path or wildcard (e.g. /path/H0232_TS.txt or /path/\*.txt).

Use when: you want to parse TS files (batch or single) and make their
metadata available for later commands.

show_ts_info

Purpose: Display metadata that’s already cached for an object in the
version you have, try to auto-find or parse a TS file if nothing is
cached.

Input: an object name or TS name (e.g. Model_H0232 or H0232_TS). It
works with no args (auto-uses the single open model) or accepts a second
argument giving an explicit TS path to parse-and-cache.

Output: prints the metadata for the requested object.

Use when: you want to reprint metadata for a model or a TS without
re-parsing files manually, or when you want to display the metadata
attached to an open object.

------------------------------------------------------------------------

# License

MIT
