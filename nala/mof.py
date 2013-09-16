''' Defines the MOF data structure, used for verifying data with xml/html source file'''

import sys
import logging
from nala.map import mof_to_html_map


class MOF(object):

    """docstring for MOF"""

    def __init__(self, name=None):
        super(MOF, self).__init__()
        self.class_name = name
        self.mof_parameters = {}
        self.logger = NalaLog("/tmp", 10).get_logger()

    def get_mof_info(self):
        if self.class_name != ' ':
            return self.class_name, self.mof_parameters

    def set_classname(self, class_name):
        self.class_name = class_name

    def set_parameters(self, class_name, para_name, value):
        if class_name == self.class_name:
            self.mof_parameters[para_name] = value
        else:
            self.logger.info("ERROR: Try to import %s paramter to %s " % (
                class_name, self.class_name))
            sys.exit(1)

    def output_mof(self):
        if self.class_name:
            self.logger.info("class name: %s" % self.class_name)
            print "class name: %s" % self.class_name
            for key in self.mof_parameters:
                print '\t\t %s = %s' % (key, self.mof_parameters[key])
                self.logger.info('\t\t %s = %s' % (
                    key, self.mof_parameters[key]))

    def __eq__(self, other):

        if self and other:
            if id(self) == id(other):
                return 1
            else:
                if mof_to_html_map(self.class_name) == other.class_name:
                    for attr in self.mof_parameters:
                        if self.mof_parameters[attr] != other.mof_parameters[attr]:
                            print "%s != %s" % (self.mof_parameters[attr], other.mof_parameters[attr])
                            self.logger.info("%s != %s" % (self.mof_parameters[
                                             attr], other.mof_parameters[attr]))
                            return 0
                    return 1
        else:
            print "None objects are comparing"
            self.logger.info("None objects are comparing")
            return 1


class MOFStore(object):

    """docstring for MOFStore"""

    def __init__(self, store_name):
        '''store_name is the time stamp of mof file'''
        super(MOFStore, self).__init__()
        self.store_name = store_name
        self.store = {}

    def add_mof(self, mof):
        if mof.class_name is None:
            print 'ERROR: set store with None MOF class'
            sys.exit(1)
        else:
            if mof.class_name not in self.store:
                self.store[mof.class_name] = [mof]
            else:
                self.store[mof.class_name].append(mof)

    def get_mof(self, mof_name=None):
        if mof_name in self.store:
            return self.store[mof_name]
        elif mof_name is None:
            for each_mof in self.store:
                return self.store[each_mof]

    def get_mof_instance_number(self, mof_name):
        if mof_name != '' and mof_name in self.store:
            return len(self.store[mof_name])
        else:
            return -1


class NalaLog(object):

    """docstring for NalaLog"""
    def __init__(self, logpath, name=None, level=10):
        super(NalaLog, self).__init__()
        self.logger = logging.getLogger(name)
        hdlr = logging.FileHandler(logpath + "/nala-compare.log")
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        self.logger.addHandler(hdlr)

        if level == 0:
            self.logger.setLevel(logging.NOTSET)
        elif level == 10:
            self.logger.setLevel(logging.DEBUG)
        elif level == 20:
            self.logger.setLevel(logging.INFO)
        elif level == 30:
            self.logger.setLevel(logging.WARNING)
        elif level == 40:
            self.logger.setLevel(logging.ERROR)
        elif level == 50:
            self.logger.setLevel(logging.CRITICAL)
        else:
            self.logger.setLevel(logging.DEBUG)

    def get_logger(self):

            return self.logger
