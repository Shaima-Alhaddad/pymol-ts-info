# pymol_ts_helper.py
# Flexible PyMOL TS helper: accepts wildcards, object-names, and filesystem paths.
# Usage in PyMOL (examples):
#   run /full/path/pymol_ts_helper.py
#   parse_ts "/full/path/to/H0232_TS.txt"
#   parse_ts "/full/path/to/*.txt"               # parse multiple matching files
#   load_model_with_ts /full/path/Model.pdb      # loads PDB, auto-finds TS next to it
#   load_model_with_ts Model_H0232                # use already-open object named Model_H0232
#   load_model_with_ts "/full/path/Model.pdb", "/full/path/H0232_TS.txt"
#   attach_ts "/full/path/H0232_TS.txt", "Model_H0232"  # attach to open object (prefix match OK)
#   show_ts_info Model_H0232
#
# This script parses CASP TS files heuristically and prints trimmed metadata to PyMOL console.

from pymol import cmd
import os, re, glob
from collections import OrderedDict

_TS_META_CACHE = {}

# alias map (keeps fuzzy matching)
_KEY_ALIASES = {
    'STOICH':       ['STOICH', 'STOICHIOMETR', 'TOICH', 'STOI'],
    'SCORE':        ['SCORE', 'GDT', 'TM_SCORE', 'TM-SCORE', 'TM', 'QMEAN'],
    'METHOD':       ['METHOD', 'ETHOD'],
    'AUTHOR':       ['AUTHOR', 'UTHOR'],
    'MODEL':        ['MODEL'],
    'FORMAT':       ['FORMAT', 'FRMAT', 'FRM'],
    'TITLE':        ['TITLE', 'TITL'],
    'COMPND':       ['COMPND', 'COMPOUND', 'COMPONENT']
}

_FRIENDLY = {
    'STOICH': 'Stoichiometry',
    'SCORE':  'Score(s)',
    'METHOD': 'Method',
    'AUTHOR': 'Author',
    'MODEL':  'Model',
}

def _looks_like_coordinate_line(s):
    if not s or not s.strip():
        return False
    if re.search(r'[-+]?\d+\.\d+\s+[-+]?\d+\.\d+\s+[-+]?\d+\.\d+', s):
        return True
    if s.strip().upper().startswith(('ATOM','HETATM','TER','ENDMDL')):
        return True
    if re.match(r'^\s*\d+\s+\S+\s+\S+\s+\S+\s+\S+\s+[-+]?\d+\.\d+', s):
        return True
    return False

def _find_ts_candidate(pdb_path):
    """Search possible TS filenames next to a PDB file (same base name)."""
    base, _ = os.path.splitext(pdb_path)
    candidates = [
        base + '.ts', base + '.TS',
        base + '_TS.txt', base + '_ts.txt',
        base + '.txt'
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    d = os.path.dirname(pdb_path) or '.'
    try:
        for fn in os.listdir(d):
            if base in fn and 'TS' in fn.upper() and fn.lower().endswith(('.txt','.ts')):
                full = os.path.join(d, fn)
                if os.path.isfile(full):
                    return full
    except Exception:
        pass
    return None

def _identify_canonical_key(line_upper, left_token_upper=''):
    for canon, aliases in _KEY_ALIASES.items():
        for a in aliases:
            if a and a in line_upper:
                return canon
    if left_token_upper:
        candidate = left_token_upper + line_upper[:20]
        for canon in _KEY_ALIASES.keys():
            if canon in candidate:
                return canon
    return None

def _extract_value_from_line(original_line):
    if ':' in original_line:
        val = original_line.split(':',1)[1].strip()
        return val.strip().rstrip(' .;')
    parts = original_line.strip().split(None,1)
    if len(parts) == 2:
        return parts[1].strip().rstrip(' .;')
    return original_line.strip().rstrip(' .;')

def _clean_leading_fragment(val):
    if not val:
        return val
    vup = val.upper().lstrip()
    for aliases in _KEY_ALIASES.values():
        for a in aliases:
            if a and vup.startswith(a):
                stripped = val[len(a):].lstrip(" :-.")
                if stripped:
                    return stripped
    return val

def _collect_all_text(ts_path):
    try:
        with open(ts_path, 'r', errors='ignore') as fh:
            return fh.read()
    except Exception:
        return ''

def _find_stoich_tokens_in_text(text):
    if not text:
        return None
    tokens = re.findall(r'([A-Za-z]+)\s*[:=]?\s*(\d+)', text)
    if tokens:
        seen = []
        out = []
        for letter, num in tokens:
            key = letter.strip()
            if key not in seen:
                seen.append(key)
                out.append(f"{key}{num}")
        return ''.join(out) if out else None
    compact = re.findall(r'([A-Za-z]\d+)', text)
    if compact:
        return ''.join(compact)
    return None

def _parse_ts_metadata(ts_path, max_header_lines=2000):
    if not ts_path or not os.path.exists(ts_path):
        return None
    out = OrderedDict((k, None) for k in _KEY_ALIASES.keys())
    remarks = []
    other = OrderedDict()
    try:
        with open(ts_path, 'r', errors='ignore') as fh:
            for i, raw in enumerate(fh):
                if i > max_header_lines:
                    break
                line = raw.rstrip('\n')
                if not line.strip():
                    continue
                if _looks_like_coordinate_line(line):
                    break
                up = line.upper()
                if up.strip().startswith('REMARK'):
                    remarks.append(line.strip())
                    continue
                left_token = line.split(':',1)[0].strip().upper() if ':' in line else (line.strip().split(None,1)[0].upper() if line.strip().split(None,1) else '')
                canon = _identify_canonical_key(up, left_token)
                if canon:
                    val = _extract_value_from_line(line)
                    val = _clean_leading_fragment(val)
                    if _looks_like_coordinate_line(val) or re.match(r'^\s*\d+\s+[A-Z0-9]', val):
                        continue
                    if val:
                        out[canon] = val
                    continue
                m = re.match(r'^\s*([A-Za-z0-9_\- ]{1,60}?)\s*[:\-]\s*(.+)$', line)
                if m:
                    gk = m.group(1).strip()
                    gv = m.group(2).strip()
                    if gk and gv and gk not in other:
                        other[gk] = gv
                    continue
                if line and len(line.strip()) < 300:
                    tag = f"LINE_{i}"
                    if tag not in other:
                        other[tag] = line.strip()
    except Exception:
        pass

    # post-process stoich if missing
    if not out.get('STOICH') and not out.get('STOICHIOMETRY'):
        text = _collect_all_text(ts_path)
        found = _find_stoich_tokens_in_text(text)
        if found:
            if 'STOICH' in out:
                out['STOICH'] = found
            else:
                out['STOICHIOMETRY'] = found

    # normalize SCORE to numeric if present
    if out.get('SCORE'):
        sc = re.search(r'[-+]?\d*\.\d+|\d+', out['SCORE'])
        if sc:
            out['SCORE'] = sc.group(0)

    result = OrderedDict()
    for k in _KEY_ALIASES.keys():
        result[k] = out.get(k) or None
    result['REMARKS'] = remarks
    if other:
        result['OTHER'] = other
    return result

def _pretty_print_trimmed(key, meta):
    print(f"=== TS metadata for: {key} ===")
    if not meta:
        print("  (no TS metadata available)")
        return
    order = ['STOICH','AUTHOR','METHOD','SCORE','MODEL']
    any_printed = False
    for k in order:
        v = meta.get(k)
        if v:
            label = _FRIENDLY.get(k, k)
            print(f"{label}: {v}")
            any_printed = True
    if not any_printed:
        print("  (no recognized metadata fields found)")

# --------------------
# Public user-facing commands (flexible)
# --------------------

def parse_ts(ts_pattern):
    """
    Parse one or multiple TS files.
    Accepts exact path or shell-style wildcard (e.g. '/path/*.txt').
    Returns list of parsed dicts and caches them under basenames.
    """
    # expand wildcards
    matches = glob.glob(os.path.expanduser(ts_pattern))
    if not matches:
        # if exact file path given but not found, show help
        p = os.path.expanduser(ts_pattern)
        if os.path.exists(p):
            matches = [p]
        else:
            print("parse_ts: no files matched pattern:", ts_pattern)
            return []
    results = []
    for path in matches:
        key = os.path.splitext(os.path.basename(path))[0]
        meta = _parse_ts_metadata(path)
        _TS_META_CACHE[key] = meta
        # print trimmed output for each
        _pretty_print_trimmed(key, meta)
        results.append({'key': key, 'ts': path, 'meta': meta})
    return results

def _resolve_object_or_path(identifier):
    """
    If identifier is an existing file path return ('path', path).
    Else if it's an open PyMOL object name return ('object', objname).
    Else if identifier is a prefix matching a single object, return that object.
    Else return (None, None).
    """
    p = os.path.expanduser(str(identifier))
    if os.path.exists(p) and (p.lower().endswith('.pdb') or p.lower().endswith('.ent')):
        return ('path', p)
    # not a path -> check open objects
    objs = list(cmd.get_names())
    if identifier in objs:
        return ('object', identifier)
    # try prefix match
    matches = [n for n in objs if identifier in n]
    if len(matches) == 1:
        return ('object', matches[0])
    return (None, None)

def load_model_with_ts(pdb_or_obj, ts_path=None, quiet=1):
    """
    Load a PDB file or use an already-open object, then parse TS (if provided or auto-found).
    - pdb_or_obj: path to PDB file OR name (or prefix) of an open object.
    - ts_path: optional path to TS file. If omitted and a path was used for pdb, script searches beside pdb.
    """
    kind, val = _resolve_object_or_path(pdb_or_obj)
    if kind is None:
        print("load_model_with_ts: neither file nor open object found for:", pdb_or_obj)
        return {'object': None, 'ts': None, 'meta': None}

    if kind == 'path':
        pdb_path = val
        obj_name = os.path.splitext(os.path.basename(pdb_path))[0]
        cmd.load(pdb_path, obj_name, quiet=int(quiet))
    else:
        obj_name = val
        pdb_path = None  # we didn't load from disk

    # locate TS
    if ts_path:
        ts_path = os.path.expanduser(ts_path)
        if not os.path.exists(ts_path):
            print("load_model_with_ts: provided TS not found:", ts_path)
            ts_path = None
    if not ts_path and pdb_path:
        ts_path = _find_ts_candidate(pdb_path)

    meta = _parse_ts_metadata(ts_path) if ts_path else None
    _TS_META_CACHE[obj_name] = meta

    print("load_model_with_ts: object:", obj_name, " (pdb loaded from: {})".format(pdb_path if pdb_path else 'already-open'))
    if ts_path:
        print("TS used:", ts_path)
    else:
        print("TS file: not found (searched common candidates).")
    _pretty_print_trimmed(obj_name, meta)
    return {'object': obj_name, 'ts': ts_path, 'meta': meta}

def attach_ts(ts_path, obj_identifier):
    """
    Parse TS and attach metadata to an existing object.
    obj_identifier may be the exact object name or a short prefix.
    """
    ts_path = os.path.expanduser(ts_path)
    if not os.path.exists(ts_path):
        print("attach_ts: TS file not found:", ts_path)
        return
    # resolve object
    objs = list(cmd.get_names())
    if obj_identifier in objs:
        obj_name = obj_identifier
    else:
        # try substring match
        matches = [n for n in objs if obj_identifier in n]
        if len(matches) == 1:
            obj_name = matches[0]
        elif len(matches) > 1:
            print("attach_ts: ambiguous object identifier matched multiple objects:", matches)
            return
        else:
            print("attach_ts: object not found (available objects):", objs)
            return
    res = _parse_ts_metadata(ts_path)
    if not res:
        print("attach_ts: parsing returned no metadata.")
        return
    _TS_META_CACHE[obj_name] = res
    print("attach_ts: attached metadata from", os.path.basename(ts_path), "to object", obj_name)
    _pretty_print_trimmed(obj_name, res)

def show_ts_info(obj_or_key=None, ts_path=None):
    """
    Show TS metadata for an object name, TS basename, or explicit TS path.
    New behavior:
      - If called with no args:
          * If exactly one object is open -> use that object automatically.
          * If multiple objects are open -> print numbered list and prompt user to choose
            (enter index or object name). If input() is not available, prints the list and
            asks the user to re-run with the chosen name.
      - If called with a name, works as before (use cache or auto-find/parse TS).
      - If ts_path provided, will try to parse that TS and cache under the chosen key.
    """
    # helper to actually show/generate metadata for a chosen key
    def _show_for_key(key, explicit_ts=None):
        # if cached already, print and return
        meta = _TS_META_CACHE.get(key)
        if meta is not None:
            _pretty_print_trimmed(key, meta)
            return True
        # if explicit ts_path provided, try to use it
        if explicit_ts:
            ts_expanded = os.path.expanduser(str(explicit_ts))
            if os.path.exists(ts_expanded) and os.path.isfile(ts_expanded):
                parsed = _parse_ts_metadata(ts_expanded)
                if parsed:
                    _TS_META_CACHE[key] = parsed
                    print(f"show_ts_info: parsed and cached TS from: {ts_expanded} -> key: {key}")
                    _pretty_print_trimmed(key, parsed)
                    return True
                else:
                    print("show_ts_info: parsing failed for:", ts_expanded)
                    return False
            else:
                print("show_ts_info: provided TS path not found:", explicit_ts)
                return False

        # otherwise try to find TS files automatically (reuse original logic)
        # gather candidates from sensible dirs
        def _gather_candidates(search_dirs):
            cand = []
            for d in search_dirs:
                if not os.path.isdir(d):
                    continue
                try:
                    for fn in os.listdir(d):
                        if not fn.lower().endswith(('.txt', '.ts')):
                            continue
                        cand.append(os.path.join(d, fn))
                except Exception:
                    continue
            return cand

        cwd = os.getcwd()
        script_dir = os.path.dirname(__file__) if '__file__' in globals() else cwd
        home = os.path.expanduser('~')
        examples_dir = os.path.join(script_dir, 'examples')
        search_dirs = [cwd, examples_dir, script_dir, home]

        candidates = _gather_candidates(search_dirs)
        basematches = []
        substrmatches = []
        key_up = str(key).upper()
        for path in candidates:
            bn = os.path.splitext(os.path.basename(path))[0]
            if bn.upper() == key_up:
                basematches.append(path)
            elif key_up in os.path.basename(path).upper():
                substrmatches.append(path)

        chosen = None
        if basematches:
            chosen = basematches[0]
        elif substrmatches:
            chosen = substrmatches[0]

        # if key looks like an object in PyMOL, also try to find TS matching object name
        if chosen is None:
            objs = list(cmd.get_names())
            for n in objs:
                if key == n or key in n:
                    n_up = n.upper()
                    for path in candidates:
                        if n_up in os.path.basename(path).upper():
                            chosen = path
                            key = n  # use exact object name as cache key
                            break
                    if chosen:
                        break

        if chosen:
            parsed = _parse_ts_metadata(chosen)
            if parsed:
                _TS_META_CACHE[key] = parsed
                print(f"show_ts_info: found TS '{os.path.basename(chosen)}' -> parsed & cached under key: {key}")
                _pretty_print_trimmed(key, parsed)
                return True
            else:
                print("show_ts_info: found candidate TS but parsing failed:", chosen)
                return False

        # nothing found
        return False

    # === main entry ===
    # if user provided a name/key, use it directly
    if obj_or_key:
        key = str(obj_or_key)
        ok = _show_for_key(key, ts_path)
        if not ok:
            print("show_ts_info: no cached metadata for '%s' and no TS file found automatically." % key)
            print("Options:")
            print("  1) Run parse_ts /path/to/that_TS.txt (caches under TS basename).")
            print("  2) Call with explicit TS path to parse & attach now:")
            print("       show_ts_info <object_or_key>, /full/path/to/that_TS.txt")
        return

    # if no argument provided: decide based on number of open objects
    objs = list(cmd.get_names())
    if len(objs) == 0:
        print("show_ts_info: no open objects in PyMOL. Load a model or run parse_ts/show_ts_info <name>.")
        return

    if len(objs) == 1:
        # single model open -> use it automatically
        target = objs[0]
        print("show_ts_info: one object open, using:", target)
        ok = _show_for_key(target, ts_path)
        if not ok:
            print(f"show_ts_info: no metadata cached for '{target}' and no TS file found automatically.")
            print("You can run: parse_ts /path/to/TS.txt  OR  show_ts_info <object_name>, /path/to/TS.txt")
        return

    # multiple objects open -> present numbered list and attempt interactive selection
    print("show_ts_info: multiple objects are open. Please choose which model to show:")
    for i, n in enumerate(objs, 1):
        print(f"  {i}) {n}")
    # try to prompt user for selection
    try:
        sel = input("Enter number or exact object name (or press Enter to cancel): ").strip()
    except Exception:
        sel = None

    if not sel:
        print("show_ts_info: selection cancelled. Re-run with the chosen name, e.g.:")
        print("   show_ts_info <object_name>")
        return

    # if user entered a number, pick that index
    if sel.isdigit():
        idx = int(sel) - 1
        if 0 <= idx < len(objs):
            chosen_obj = objs[idx]
            print("show_ts_info: you selected:", chosen_obj)
            ok = _show_for_key(chosen_obj, ts_path)
            if not ok:
                print(f"show_ts_info: no metadata cached for '{chosen_obj}' and no TS file found automatically.")
                print("You can run: parse_ts /path/to/TS.txt  OR  show_ts_info <object_name>, /path/to/TS.txt")
            return
        else:
            print("show_ts_info: invalid number selection.")
            return

    # otherwise treat input as an object name (exact or substring)
    # try exact match first
    if sel in objs:
        chosen_obj = sel
    else:
        matches = [n for n in objs if sel in n]
        if len(matches) == 1:
            chosen_obj = matches[0]
        elif len(matches) > 1:
            print("show_ts_info: ambiguous name matched multiple objects:", matches)
            print("Please call show_ts_info with the exact object name.")
            return
        else:
            print("show_ts_info: no open object matched your input.")
            print("Available objects:")
            for n in objs:
                print("  ", n)
            return

    # show for chosen object
    ok = _show_for_key(chosen_obj, ts_path)
    if not ok:
        print(f"show_ts_info: no metadata cached for '{chosen_obj}' and no TS file found automatically.")
        print("You can run: parse_ts /path/to/TS.txt  OR  show_ts_info <object_name>, /path/to/TS.txt")

# Register commands with PyMOL
cmd.extend('parse_ts', parse_ts)
cmd.extend('load_model_with_ts', load_model_with_ts)
cmd.extend('attach_ts', attach_ts)
cmd.extend('show_ts_info', show_ts_info)


