# pymol-ts-info

PyMOL helper that reads CASP TS files and prints five key metadata fields
(Stoichiometry, Author, Method, Score, Model) in the PyMOL console.

Reference: original README uploaded by the author. 

--------------------------------------------------------------------------------------------------------------------------------

# Files (exampless)
- `pymol_ts_helper.py` — plugin script (run in PyMOL).  
- `exampless/H0232_TS.txt` — examples CASP TS file.  
- `exampless/Model_H0232.pdb` — examples PDB model.

--------------------------------------------------------------------------------------------------------------------------------

# exampless: Commands to run in PyMOL. (Quick usage, no installation is needed)
# Replace <PATH_TO_YOUR_FILES> with your folder, for examples:
#   Mac/Linux:  /Users/yourname/Desktop/pymol-ts-exampless
#   Windows:    C:\Users\yourname\Desktop\pymol-ts-exampless

# Load the plugin (run once each PyMOL session). Type this at the PyMOL prompt (not inside a `python` block):
```text
 run <PATH_TO_YOUR_FILES>/pymol_ts_helper.py
```
 
# Load PDB + TS together (preferred if both files available)
```text
 load_model_with_ts <PATH_TO_YOUR_FILES>/examples/Model_H0232.pdb, <PATH_TO_YOUR_FILES>/examples/H0232_TS.txt
```

# An examples of the Console output, it will show following:

 === TS metadata for: H0232_TS ===
 Stoichiometry: A2B2
 Author: MultiFOLD2
 Method: <long method text>
 Score(s): 0.9110
 Model: 1

--------------------------------------------------------------------------------------------------------------------------------

# exampless of additional commands 

# 1) If the model is already open in PyMOL → attach TS and show
attach_ts <PATH_TO_YOUR_FILES>/examples/H0232_TS.txt, Model_H0232
show_ts_info Model_H0232

# 2) If only TS file available (no model load in PyMOL)
parse_ts <PATH_TO_YOUR_FILES>/examples/H0232_TS.txt
show_ts_info H0232_TS

# 3) Quick show when single model is open in PyMOL. (If exactly one object is loaded, show_ts_info will use it automatically.)
show_ts_info

# 4) Batch parse many TS files:
parse_ts /<PATH_TO_YOUR_FILES>/*.txt

--------------------------------------------------------------------------------------------------------------------------------

# Notes & troubleshooting

- **Order for `load_model_with_ts`:** the first argument must be the PDB model name, then the TS file must be second.  
- **Already open models:** if you dragged a PDB into PyMOL, find the object name in PyMOL.
- **If `show_ts_info` says “no metadata cached”**: run `parse_ts /path/to/file.txt` or `attach_ts /path/to/file.txt, <object>` first.
- **Run at the PyMOL prompt**: run, load_model_with_ts, parse_ts, etc. are PyMOL commands — do not type them inside a python/end block.


- **The difference between these commands in PyMOL: parse_ts vs show_ts_info**

parse_ts

Purpose: Read one or more CASP TS text files from disk, extract metadata, print the trimmed metadata, and cache the results.

Input: a path or wildcard (e.g. /path/H0232_TS.txt or /path/*.txt).

Output: prints the parsed metadata to the PyMOL console and returns a Python list of parsed dicts; stores each parsed entry in _TS_META_CACHE under the TS basename (e.g. H0232_TS).

Use when: you want to parse TS files (batch or single) and make their metadata available for later commands.


show_ts_info

Purpose: Display metadata that’s already cached for an object/key — or, in the version you have, try to auto-find or parse a TS file if nothing is cached.

Input: an object name or TS basename (e.g. Model_H0232 or H0232_TS). In the newer plugin it also works with no args (auto-uses the single open model) or accepts a second argument giving an explicit TS path to parse-and-cache.

Output: prints the trimmed metadata for the requested key/object.

Use when: you want to reprint metadata for a model or a TS without re-parsing files manually, or when you want to display the metadata attached to an open object.

--------------------------------------------------------------------------------------------------------------------------------

# License
  MIT