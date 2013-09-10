''' Defines the MOF data structure, used for verifying data with xml/html source file'''

import sys
import logging

class MOF(object):

    """docstring for MOF"""

    def __init__(self, name=None):
        super(MOF, self).__init__()
        self.class_name = name
        self.mof_parameters = {}

    def get_mof_info(self):
        if self.class_name != ' ':
            return self.class_name, self.mof_parameters

    def set_classname(self, class_name):
        self.class_name = class_name

    def set_parameters(self, class_name, para_name, value):
        if class_name == self.class_name:
            self.mof_parameters[para_name] = value
        else:
            print "ERROR: Try to import %s paramter to %s " % (class_name, self.class_name)
            sys.exit(1)

    def output_mof(self):
        if self.class_name:
            print "class name: %s" % self.class_name
            for key in self.mof_parameters:
                print '\t\t %s = %s' % (key, self.mof_parameters[key])

    def __eq__(self, other):

        if self and other:
            if id(self) == id(other):
                return 0
            else:
                if self.class_name == other.class_name:
                    for attr in self.mof_parameters:
                        if getattr(self, attr) != getattr(other, attr):
                            return -1
                    return 0
        else:
            print "None objects are comparing"
            return 0

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
