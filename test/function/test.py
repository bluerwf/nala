#! /usr/bin/env python

import os, sys
from optparse import OptionParser
import nala.mof as mof
from nala.parse import is_mof_instance, mof_parse, list_commands, CustomParse, NalaHTMLParser

USAGE = """%prog <file> [<file> ...] <command> [options]

Commands:
""" + '\n'.join(["\t %s" % x for x in list_commands()])

def test():

    classname = 'hellow'
    attr1 = 1
    attr2 = 2
    attr3 = 'xyz'

    test_mof = mof.MOF()
    test_mof.set_classname(classname)
    test_mof.set_parameters(classname, 'attr1', attr1)
    test_mof.set_parameters(classname, 'attr2', attr2)
    test_mof.set_parameters(classname, 'attr3', attr3)

    test_mof.output_mof()


def main():
    parser = OptionParser(USAGE)

    parser.add_option('-v', '--verbose', action="store_true",
                      default=False, help="display verbose output")

    options, args = parser.parse_args()

    if len(args) < 2:
        parser.print_help()
        print 'ERROR: specify file(s) and command'
        return 1

    command = args[-1]
    files = args[:-1]

    mof_files = [
        os.path.abspath(each_file) for each_file in files if os.path.basename(each_file).split('.')[1].upper() == 'MOF']

    html_files = [
            os.path.abspath(each_file) for each_file in files if os.path.basename(each_file).split('.')[1] == 'html']

    for mof_file in mof_files:
    	mof_store = mof_parse(mof_file)
    	print "mof store: %s" % mof_store.store_name
    	for class_name in mof_store.store:
    		for mof_inst in mof_store.get_mof(class_name):
    			mof_inst.output_mof()

    if len(html_files) > 0:
        for  each_file in html_files:
            html_store = mof.MOFStore(each_file)
            html_parser = NalaHTMLParser()
            html_parser.set_store(html_store)
            html_store = html_parser.parse(each_file, 'split')

            for class_name in html_store.store:
                print "class name: %s, instance number: %d" % (class_name, html_store.get_mof_instance_number(class_name))
                for mof_inst in html_store.get_mof(class_name):
                    mof_inst.output_mof()


if __name__ == '__main__':
    main()
