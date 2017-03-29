def replace_multiple(string, replacements):
    # Place longer ones first to keep shorter substrings from matching where the longer ones should take place
    # For instance given the replacements {'ab': 'AB', 'abc': 'ABC'} against the string 'hey abc', it should produce
    # 'hey ABC' and not 'hey ABc'
    subs = sorted(replacements, key=len, reverse=True)

    # Create a big OR regex that matches any of the substrings to replace
    regexp = re.compile('|'.join(map(re.escape, subs)))

    # For each match, look up the new string in the replacements
    return regexp.sub(lambda match: replacements[match.group(0)], string)


def process_run_file(arguments):
    # process run file, if any
    if arguments.run_file != '':
        assert (os.path.isfile(arguments.run_file)), "Run file not found."
        with open(arguments.run_file, 'r') as f:
            re_obj = re.compile(
                r"""^\s*([^\s!#]*)\s*==?\s*(((\\"|\\'|\\!|\\#|\\\\|[^\\!#"'\s])+\s*|(["'])(\\\5|\\\\|[^"'\\])*\5\s*)*)"""
            )
            for l in f.readlines():
                m = re_obj.match(l)
                if m is not None:
                    # overwrite arguments on the args object
                    d = {'\\!': '!', '\\#': '#', '\\\\': '\\', '\\\'': '\'', '\\"': '"'}
                    if m.group(1) in arguments:
                        t = type(getattr(arguments, m.group(1)))
                    else:
                        t = str
                    s = replace_multiple(m.group(2).strip(), d)
                    if (s.startswith('"') and s.endswith('"')) or (s.startswith('\'') and s.endswith('\'')):
                        s = s[1:-1]

                    if t is bool:
                        b = s in ['true', 'yes', '1']
                        setattr(arguments, m.group(1), b)
                    else:
                        setattr(arguments, m.group(1), t(s))
