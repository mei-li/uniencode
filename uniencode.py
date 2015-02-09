#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2008-2014, Mei Li Triantafylllidi.
# All rights reserved.

"""
This script changes text file encodings or recursively in directories from a
detected encoding to a given one, or to utf-8 by default. For parameters
reference do:
> python uniencode.py -h
"""
import codecs
import fnmatch
import os
import sys
import tempfile

from optparse import OptionParser, OptionGroup


CHARDET_IMPORT_ERROR_MSG = """Error: %s
Please install chardet from http://pypi.python.org/pypi/chardet.
To avoid full installation keep the chardet directory at the same directory with this script."""


try:
    import chardet
except ImportError as e:
    print CHARDET_IMPORT_ERROR_MSG % e
    sys.exit(1)


DEFAULT_TARGET_ENCODING = 'utf-8'


def is_binary(name):
    if 'win' in sys.platform:
        return False
    return os.system('file "' + name + '" | grep text > /dev/null')


def unify_encoding(file_path, target_encoding):
    with open(file_path) as fp:
        enc = chardet.detect(fp.read())

    confidence = enc['confidence']
    encoding = enc['encoding']

    if not encoding:
        print "Cannot detect file %s encoding" % file_path
        return False

    encoding = encoding.lower()

    if confidence <= 0.5:
        print "Not changing %s file from %s to %s, LOW conf (%s)" % (file_path,
                                                                     encoding,
                                                                     target_encoding,
                                                                     confidence)
        return False

    elif confidence > 0.7 and encoding != target_encoding and encoding != 'ascii':
        print "Changing %s file from %s to %s, with conf %s" % (file_path,
                                                                encoding,
                                                                target_encoding,
                                                                confidence)
        swap_files = False
        with codecs.open(file_path, 'r', encoding) as file_orig, \
                tempfile.NamedTemporaryFile(mode='w', delete=False) as file_changed:
            try:
                for line in file_orig:
                    file_changed.write(line.encode(target_encoding))
                swap_files = True
            except UnicodeEncodeError:
                print "Changing %s file from %s encoding to %s is NOT possible" % (file_path,
                                                                                   encoding,
                                                                                   target_encoding)
            except UnicodeDecodeError:
                print "Wrong encoding guess. %s file remains unchanged" % file_path
        if swap_files:
            os.remove(file_path)
            os.rename(file_changed.name, file_path)
            return True
        else:
            os.remove(file_changed.name)
            return False

    elif confidence > 0.5 and confidence <= 0.7:
        print "Changing %s file row by row to %s, with conf %s" % (file_path,
                                                                   target_encoding,
                                                                   confidence)
        problems = False
        with open(file_path) as file_orig, tempfile.NamedTemporaryFile(
                mode='w', delete=False) as file_changed:
            for line in file_orig:
                line_info = chardet.detect(line)
                if (not line_info['encoding']) or line_info['confidence'] < 0.7:
                    problems = True
                    file_changed.write(line)
                else:
                    try:
                        line_changed = unicode(line, line_info['encoding']).encode(target_encoding)
                        file_changed.write(line_changed)
                    except (UnicodeDecodeError, UnicodeEncodeError):
                        problems = True
                        file_changed.write(line)
        os.remove(file_path)
        os.rename(file_changed.name, file_path)
        if problems:
            print "Some lines of %s file had corrupted encodings and remained unchanged" % file_path
        return True


def dtstat(dtroot, pattern, target_encoding):
    changed = 0
    for path, dirs, files in os.walk(os.path.abspath(dtroot)):
        for filename in fnmatch.filter(files, pattern):
            file_path = os.path.join(path, filename)
            if os.path.islink(file_path):
                continue
            if os.path.isfile(file_path):
                if is_binary(file_path):
                    print "Ignoring binary file %s" % file_path
                    continue
                if unify_encoding(file_path, target_encoding):
                    changed += 1
    print "Changed %s files in total" % changed


def main():
    usage = "usage: %prog [options] FILE"
    description = """This script re-encodes files to utf8 or custom encoding, it works for
single files and also recursively for a directory. It avoids binary files. FIles change ONLY if
encoding is detected with HIGH confidence. Prints nothing if no actions are taken due
to compatible or ascii encoding found."""

    parser = OptionParser(usage=usage, description=description)
    parser.add_option("-r", "--recursive",
                      action="store_true", dest="directory", default=False,
                      help="Operates recursively on folder FILE")
    parser.add_option("-e", "--encoding",
                      dest="enc",
                      default=None,
                      help="Custom encoding, default encoding is utf-8. For possible values look"
                           "http://docs.python.org/library/codecs.html#standard-encodings")
    parser.add_option("-p", "--pattern",
                      dest="pattern",
                      default='*',
                      help="Files matching pattern (works in directory mode)")
    group = OptionGroup(parser, "Examples",
                        'python %s -r FOLDER -p "*.srt"  ' % sys.argv[0])

    parser.add_option_group(group)

    (options, args) = parser.parse_args()

    if options.enc:
        target_encoding = options.enc
    else:
        target_encoding = DEFAULT_TARGET_ENCODING
    if len(args) < 1:
        print "No input file or directory"
        return
    else:
        fname = args[0]

        print fname
    try:
        if not options.directory:
            file_pathname = os.path.abspath(fname)
            if os.path.isfile(file_pathname):
                unify_encoding(file_pathname, target_encoding)
            else:
                print "Not valid file: %s" % fname
        else:
            dtstat(fname, options.pattern, target_encoding)
    except LookupError, e:
        print e


def test_full_file_one_encoding():
    import tempfile
    _, path = tempfile.mkstemp()

    phrase = u"αυτά είναι ελληνικά"
    initial_encoding = "iso-8859-7"
    final_encoding = "utf-8"

    with open(path, "w") as f:
        f.write(phrase.encode(initial_encoding))

    unify_encoding(path, final_encoding)

    with open(path) as f:
        final_phrase = unicode(f.read(), encoding=final_encoding)
        assert phrase == final_phrase, "final phrase is %s " % final_phrase
    os.remove(path)


def test_many_encodings_per_file():
    import tempfile
    _, path = tempfile.mkstemp()

    phrase = u"αυτά είναι ελληνικά"
    initial_encoding = "iso-8859-7"
    final_encoding = "utf-8"

    with open(path, "w") as f:
        f.write(phrase.encode(initial_encoding))
        f.write("\n")
        f.write(phrase.encode(final_encoding))
        f.write("\n")
        f.write(phrase.encode(final_encoding))
        f.write("\n")
        f.write(phrase.encode(final_encoding))

    unify_encoding(path, final_encoding)
    input_phrase = phrase + "\n" + phrase + "\n" + phrase + "\n" + phrase
    with open(path) as f:
        file_content = f.read()
        final_phrase = unicode(file_content, encoding=final_encoding)
        assert input_phrase == final_phrase, file_content
    os.remove(path)


def test():
    test_full_file_one_encoding()
    test_many_encodings_per_file()


if __name__ == '__main__':
    if sys.argv[-1] == "--test":
        test()
        sys.exit(1)
    main()
