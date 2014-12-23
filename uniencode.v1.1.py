#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2008-2014, Mei Li Triantafylllidi.
# All rights reserved.

"""
GET Help:
python uniencode.py -h
# In WINDOWS binary files are not excluded, but usually detecting encoding confidence is low so they are ignored
"""
import os, sys
import codecs, fnmatch
from optparse import OptionParser, OptionGroup


CHARDET_IMPORT_ERROR = """Error: %s
Please install chardet from http://pypi.python.org/pypi/chardet.
To avoid full installation keep the chardet directory at the same directory with this script."""


try:
    import chardet
except ImportError as e:
    print CHARDET_IMPORT_ERROR % e
    sys.exit(1)


default_target_encoding='utf-8'


def is_binary(name):
    if 'win' in sys.platform:
        return False
    return os.system('file "' + name + '" | grep text > /dev/null')


def unify_encoding(fullf):
     f = open(fullf)
     enc = chardet.detect(f.read())
     f.close()
     if not enc['encoding']:
        print "Cannot detect file %s encoding" % fullf
        return False
     if enc['confidence'] <= 0.5:
        print "Not changing %s file from %s to %s, LOW conf (%s)" % (fullf, enc['encoding'], default_target_encoding, enc['confidence'])
        return False
    if enc['confidence'] > 0.7 and enc['encoding'].lower() != default_target_encoding and enc['encoding'] != 'ascii':
        print "Changing %s file from %s to %s, with conf %s" % (fullf, enc['encoding'], default_target_encoding, enc['confidence'])
        f = codecs.open(fullf, 'r', enc['encoding'])
        f2 = open(fullf + 'tmp', 'w')
        try:
            for line in f:
                f2.write(line.encode(default_target_encoding))
            f.close()
            f2.close()
            os.remove(fullf)
            os.rename(fullf+'tmp',fullf)
        except UnicodeEncodeError:
            print "Changing %s file from %s encoding to %s is NOT possible"  %(fullf,enc['encoding'],default_target_encoding)
            f.close()
            f2.close()
            os.remove(fullf+'tmp')
            return False
        except UnicodeDecodeError:
            print "Wrong encoding guess. %s file remains unchanged"  %(fullf)
            f.close()
            f2.close()
            os.remove(fullf+'tmp')
            return False
        return True
     if enc['confidence']>0.5 and enc['confidence']<=0.7:
        print "Changing %s file row by row to %s, with conf %s" %(fullf,default_target_encoding,enc['confidence'])
        problems=False
        f=open(fullf)
        f2=open(fullf+'tmp','w')
        for line in f:
            lineenc=chardet.detect(line)
            if (not lineenc['encoding']) or lineenc['confidence']<0.7:
                problems=True
                f2.write(line)
            else:
                try:
                    f2.write(unicode(line,lineenc['encoding']).encode(default_target_encoding))
                except (UnicodeDecodeError, UnicodeEncodeError):
                    problems=True
                    f2.write(line)
        f.close()
        f2.close()
        os.remove(fullf)
        os.rename(fullf+'tmp',fullf)
        if problems:
            print "Some lines of %s file had corrupted encodings and remained unchanged" %(fullf)
        return True


def dtstat(dtroot,pattern):
    changed=0
    for path, dirs, files in os.walk(os.path.abspath(dtroot)):
        for filename in fnmatch.filter(files, pattern):
             if os.path.islink(fullf):
                continue
             if os.path.isfile(fullf):
                if is_binary(fullf):
                    print "Ignoring binary file %s" %(fullf)
                    continue
                if unify_encoding(os.path.join(path, filename)):
                    changed+=1
    print "Changed %s files in total" %(changed)


def main():
    usage = "usage: %prog [options] FILE"
    description="""This program reencodes files to utf8 or a custom encoding, it works for single files, and also recursively for a directory. It avoids binary files.\n
                    FIles change ONLY if encoding is detected with HIGH confidence.
                    IF you use custom encoding, if it is not a unicode encoding eg. UTF8 or UTF16, changing could be impossible.

                    Prints nothing if no actions are taken due to compatible or ascii encoding found
                    NOTE: Some editor open files with an encoding that cannot recognize some characters, so they replace them with ? (or sth similar), if the file is saved that way... there is no turning back!
                """
    parser = OptionParser(usage=usage,description=description)
    parser.add_option("-r", "--recursive",
                        action="store_true", dest="directory", default=False,
                      help="Operates recursively on folder FILE")
    parser.add_option("-e", "--encoding",
                        dest="enc",
                        default=None,
                      help="Custom encoding, default encoding is utf-8. For possible values look http://docs.python.org/library/codecs.html#standard-encodings")
    parser.add_option("-p", "--pattern",
                        dest="pattern",
                        default='*',
                      help="Files matching pattern (works in directory mode)")
    group = OptionGroup(parser, "Examples",
                    'python %s -r FOLDER -p "*.srt"  ' %(sys.argv[0]))

    parser.add_option_group(group)


    (options, args) = parser.parse_args()

    global default_target_encoding

    if options.enc:
        default_target_encoding=options.enc
    if len(args)<1:
        print "No input file or directory"
        return
    else:
        fname=args[0]

        print fname
    try:
        if not options.directory:
            fullfname=os.path.abspath(fname)
            if os.path.isfile(fullfname):
                unify_encoding(fullfname)
            else:
                print "Not valid file: %s" %(fname)
        else:
            dtstat(fname,options.pattern)
    except LookupError,e :
        print e


def test_full_file_one_encoding():
    import tempfile
    _, path = tempfile.mkstemp()

    phrase = u"αυτά είναι ελληνικά"
    initial_encoding = "iso-8859-7"
    final_encoding = "utf-8"

    with open(path, "w") as f:
        f.write(phrase.encode(initial_encoding))

    unify_encoding(path)

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

    unify_encoding(path)
    input_phrase = phrase + "\n" + phrase + "\n" + phrase + "\n" + phrase
    with open(path) as f:
        file_content = f.read()
        final_phrase = unicode(file_content, encoding=final_encoding)
        assert input_phrase == final_phrase, file_content
    os.remove(path)


def test():
    test_full_file_one_encoding()
    test_many_encodings_per_file()


if __name__== '__main__':
    if sys.argv[-1] == "--test":
        test()
        sys.exit(1)
    main()


