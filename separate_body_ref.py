"""This module automates the separation of body part and
reference part of a LateX produced PDF."""

import os
import os.path
import sys
import re
from subprocess import call
import argparse


def build(texFileLists):
    """This function builds pdf files for tex files

    This function builds PDF for each tex file in the
    list texFileLists.
    

    Parameters
    ----------
    texFileLists :  list
        The tex file list
    """
    LaTeX_CMD = ["latex -shell-escape -halt-on-error {texfile}.tex",
                 "bibtex {texfile}.aux",
                 "latex -shell-escape -halt-on-error {texfile}.tex",
                 "pdflatex -shell-escape -halt-on-error {texfile}.tex"]

    for texFile in texFileLists:
        filename, file_extension = os.path.splitext(texFile)
        for lcmd in LaTeX_CMD:
            try:
                call(lcmd.format(texfile=filename), shell=True)
            except:
                print "Error occurs while building ", filename
                exit(1)


def _clean(dest, level, recursive, rmFileExtensions, rm):
    """Remove certain files in a specific directory

    This function removes the files whose extensions are
    in the list rmFileExtensions by using rm method. More
    specifically, this function will recursively remove
    certain files (i.e., files with extensions contained in
    rmFileExtensions)

    Parameters
    ----------
    dest :  str
        The directory          
    level : int
        Current level
    recursive : int 
        Maximum recursive depth
    rmFileExtensions : set   
        A set of string specifies the extensions of files to be deleted
    rm :  object
        An object that is callable and accept a single string parameter
    """
    
    if level > recursive:
        return

    for f in os.listdir(dest):
        if os.path.isfile(f):
            ext = os.path.splitext(f)[-1]
            if ext in rmFileExtensions:
                print "Deleting ", f
                rm(f)
        else:
            _clean(os.path.join(dest, f), level + 1, recursive, rmFileExtensions, rm)


def clean(recursive=0):
    """Clean certain temporary files

    This function removes all temporary files generated
    during the compilation.

    Parameters
    ----------
    recursive :  int, optional 
        Maximum recursive depth
    """
    temp_files = set([
        ".blg", ".bbl", ".aux", ".log", ".brf", ".nlo", ".out", ".dvi", ".ps",
        ".lof", ".toc", ".fls", ".fdb_latexmk", ".pdfsync", ".synctex.gz",
        ".ind", ".ilg", ".idx"
    ])

    try:
        from send2trash import send2trash
        rm = send2trash
    except ImportError:
        print "Send2Trash is not installed, use os.remove instead"
        rm = os.remove

    _clean(os.getcwd(), 0, recursive, temp_files, rm)


def separate_body_and_ref(TexRoot, build_and_clean=True, recursive=0):
    """Separately produce the body and reference for TexRoot

    Parameters
    ----------
    TexRoot : string
        The main tex file for the latex project
    build_and_clean : boolean, optional     
        Whether to build and clean the generated separate tex files
    recursive : int, optional
        Recursive depth
    """
    _STRING_TO_BE_ADDED = """
\\newpage
\\AtBeginShipout{%
\\AtBeginShipoutDiscard
}
    """
    _BIB_STYLE_CMD = '\\bibliographystyle{'
    _BIB_FILE_CMD = '\\bibliography{'
    _BODY_START_CMD = '\\begin{document}'
    _BODY_END_CMD = '\\end{document}'
    _BBL_INSERT_CMD = '\\input{{{bbl}.bbl}}'
    _MAKE_TITLE_CMD = '\\maketitle'

    filename, file_extension = os.path.splitext(TexRoot)
    body_file = filename + "-body" + file_extension
    ref_file = filename + "-ref" + file_extension

    # create file objects for body file and reference file
    body_fp = open(body_file, 'w')
    ref_fp = open(ref_file, 'w')

    flag = False
    in_header = True
    with open(TexRoot, 'r') as fp:
        for line in fp:
            # remove leading blank space
            line = line.strip()
            if (not flag) and (line.startswith(_BIB_STYLE_CMD) or line.startswith(_BIB_FILE_CMD)):
                if not in_header:
                    # sometimes bib style is put in the header
                    body_fp.write(_STRING_TO_BE_ADDED + os.linesep)
                    flag = True

            if line.startswith(_BODY_START_CMD):
                in_header = False

            if in_header and (not line.startswith(_MAKE_TITLE_CMD)):
                ref_fp.write(line + os.linesep)

            if line.startswith(_BIB_STYLE_CMD):
                ref_fp.write(line + os.linesep)

            body_fp.write(line + os.linesep)
            if line.startswith(_BIB_FILE_CMD):
                bib_files = re.findall(r'\\bibliography{(.*)}', line)
                if len(bib_files) == 0:
                    print "No bib file is found"
                    exit(1)

                # bbl_lists = get_bib(bib_files[0])
                ref_fp.write(_BODY_START_CMD + os.linesep)
                ref_fp.write(_BBL_INSERT_CMD.format(bbl=os.path.splitext(body_file)[0]) + os.linesep)
                # for bbl in bbl_lists:
                #     ref_fp.write(_BBL_INSERT_CMD.format(bbl=bbl) + os.linesep)
                ref_fp.write(_BODY_END_CMD + os.linesep)

    body_fp.close()
    ref_fp.close()

    if build_and_clean:
        build([body_file, ref_file])
        clean(recursive)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='This is a simple script to produce separate PDFs for body and reference')
    parser.add_argument('-f', action='store', dest='TexRoot', default='main.tex',
                        help="the main tex file for your project")

    parser.add_argument('--version', action='version', version='%(prog)s 1.0')
    args = parser.parse_args(sys.argv[1::])

    separate_body_and_ref(args.TexRoot)


