import re
import string
from . import mof
from HTMLParser import HTMLParser
import os

DEBUG = True


def list_commands():
    """list the supported commands"""
    return ["parse", "analysis"]


def is_mof_instance(line):
    if re.match('^instance of', line):
        return True


def mof_parse(mof_file):
    ''' Pasre function for MOF file'''

    line_pattern = re.compile(r'.*}')
    mof_store = mof.MOFStore(mof_file)
    if mof_file != ' ':
        try:
            f = open(mof_file, 'r')
        except IOError as e:
            print e
        finally:
            EOF = False
            try:
                while EOF is False:
                    line = f.readline()
                    if not line:
                        EOF = True
                    if is_mof_instance(line):
                        mof_class_name = line.rstrip('\r\n').split(' ')[2]
                        tmp_mof = mof.MOF(mof_class_name)
                        mof_store.add_mof(tmp_mof)
                        line = f.readline().rstrip('\r\n')  # jump to next line
                        # while line != '};':
                        while not re.search(line_pattern, line):
                            line = f.readline().rstrip(';\r\n')
                            if line == '}':
                                break
                            if line != '{':
                                attr = line.split('=')[0].strip(' ')
                                val = line.split('=')[
                                    1].strip(' ').replace('"', '')
                                tmp_mof.set_parameters(
                                    mof_class_name, attr, val)
                            if not line:
                                EOF = True
                                break
            except IOError as e:
                print e
            f.close()

    return mof_store


class CustomParse(HTMLParser):

    """Pasre the html files output by DSA pass"""
    selected = ('br', 'div', 'table', 'tr', 'th', 'td')
    classpattern = re.compile(r'(br )+div')
    tbpattern = re.compile(r'(br )+table')
    thpattern = re.compile(r'(br )+table tr th')
    tdpattern = re.compile(r'(br )+table tr td')
    emptytdpattern = re.compile(r'(br )+table tr')

    def __init__(self):
        HTMLParser.__init__(self)
        self._tag_stack = []
        self._class_name = ' '
        self._attr_name = []
        self._attr_is_full = False
        self._attr_value = []
        self._tmp_mof = None
        self.html_store = None
        self._data_flag = False
        self._empty_td_num = 0
        self._new_instance = False

    def handle_starttag(self, tag, attrs):
        if DEBUG:
            print "Encounter a start tag: ", tag
        if tag in CustomParse.selected:
            self._data_flag = True
            self._tag_stack.append(tag)

    def handle_endtag(self, tag):
        if DEBUG:
            print "Encounter a end tag: ", tag
        if self._tag_stack and tag in CustomParse.selected:
            if tag == self._tag_stack[-1]:
                self._tag_stack.pop()
                # if self._data_flag is True and string.join(self._tag_stack)
                # != 'br table':
                if self._data_flag is True and re.match(
                    self.__class__.emptytdpattern,
                        string.join(self._tag_stack)):
                    self._empty_td_num += 1

    def handle_startendtag(self, tag, attrs):
        print "Encounter a start end tag: ", tag

    def handle_data(self, data):
        if DEBUG:
            print self._tag_stack
            print "Encounter data: ", data
            print "data len: ", len(data)
            print "data_flag= %d" % self._data_flag
            print "emtp_data_td_num = %d" % self._empty_td_num

        stack = string.join(self._tag_stack)

        def is_instance_done(key, value, flag=True):
            return True if len(key) == len(value) else False

        # _tag_stack = ['br', 'div'], means new class name
        # if string.join(self._tag_stack) == 'br div':
        if re.match(self.__class__.classpattern, stack):
            self._class_name = data
            self._attr_name = []
        # _tag_stack = ['br', 'table'] means attr names comes
        # if string.join(self._tag_stack) == 'br table':
        if re.match(self.__class__.tbpattern, stack):
            while self._empty_td_num > 0:
                self._attr_value.append(' ')
                self._empty_td_num -= 1
            # self._attr_value.append(data)
        # _tag_stack = ['br', 'table', 'tr'], means attr names comes
        # _tag_stack = ['br', 'table', 'tr', 'th'], means an attr name comes
        # if string.join(self._tag_stack) == 'br table tr th':
        if re.match(self.__class__.thpattern, stack):
            self._attr_name.append(data)
        # _tag_stack = ['br', 'table', 'tr', 'td'], means attr value comes
        if re.match(self.__class__.tdpattern, stack):
            # If meet with <td></td><td>xxxxx</td>, need to append an extra
            # null value
            while self._empty_td_num > 0:
                self._attr_value.append(' ')
                self._empty_td_num -= 1
            self._attr_value.append(data)
            # _attr_is_full is False means new mof instance comes
            # 1. Create one new mof instance
            # 2. Add the mof instance into mof store
            if self._attr_is_full is False:
                self._tmp_mof = mof.MOF(self._class_name)
                self.html_store.add_mof(self._tmp_mof)
                self._empty_td_num = 0
            self._attr_is_full = True
        # After attr names all are parsed, _tag_stack = ['br', 'table', 'tr'], means null attr value
        # Only when the attribute has names and meets with <td></td> which makes stack = [br, tr]
        # to add a ' ' attribute into attribute value lists
        # if len(self._attr_name) > 0 and string.join(self._tag_stack) == 'br
        # table tr' and self._data_flag is True and self._attr_is_full is True:
        if len(self._attr_name) > 0 and re.match(self.__class__.emptytdpattern, stack) and self._data_flag is True and self._attr_is_full is True:
        # if len(self._attr_name) > 0 and string.join(self._tag_stack) == 'br
        # table tr' and self._attr_is_full is True:
            if len(self._attr_value) < len(self._attr_name):
                while self._empty_td_num > 0:
                    self._attr_value.append(' ')
                    self._empty_td_num -= 1
            # if len(self._attr_value) == len(self._attr_name):
                # All attrs of a instance have been input to list
                # And one new instance coming. Now need to dump attrs
                # from list to mof, and then to process next instance
                # 1. Dump attrs form attr list to mof
                # for index in range(0, len(self._attr_name)):
                #     self._tmp_mof.set_parameters(self._class_name, self._attr_name[index], self._attr_value[index])
                # 2. Reset attr_is_full to False for next instance
                # 3. Clear attr_value list for next instance
                # self._attr_is_full = False
                # self._attr_value = []

        if is_instance_done(self._attr_name, self._attr_value, self._attr_is_full):
            for index in range(0, len(self._attr_name)):
                self._tmp_mof.set_parameters(
                    self._class_name, self._attr_name[index], self._attr_value[index])
                # 2. Reset attr_is_full to False for next instance
                # 3. Clear attr_value list for next instance
            self._attr_is_full = False
            self._attr_value = []

        if DEBUG:
            print "self._attr_name: ", self._attr_name
            print "self._attr_value: ", self._attr_value

        self._data_flag = False

    def set_store(self, store):
        ''' store is the MOFStore instance'''
        if self.html_store is None:
            self.html_store = store
        else:
            print "html has store, can't set store again"


class NalaHTMLParser(object):

    """docstring for NalaHTMLParser"""

    class_pattern = re.compile(r'<br><div.*>(.*)</div>')
    inst_pattern = re.compile(r'</table>')
    attrname_pattern = re.compile(r'<th.*>(.*)</th>')
    attrvalue_pattern = re.compile(r'<td>([\s\d\w:-_\.\|]*)</td>')
    attrvalue_date_pattern = re.compile(r'<td>(\d{2}\/\d{2}/\d{4}\s\d{2}:\d{2}:\d{2})</td>')
    table_type = ('thththth', 'thtdthtd', 'thtdtd')
    """
    There are different talbe types
    1. 
    <th> Name </th>
    <th> City </th>
    <th> version </th>
    </tr>
    <td> IBM </th>
    <td> SH </th>
    <td> 1.0 </th>
    </tr>
    <td> HP </th>
    <td> SH </th>
    <td> 2.0 </th>
    2.
    <th> Name </th>
    <td> IBM </th>
    </tr>
    <th> City </th>
    <td> SH </th>
    </tr>
    <th> Version </th>
    <td> 1.0 </th>
    </tr>
    <th> Name </th>
    <td> HP </td>
    </tr> 
    <th> City </th>
    <td> SH </td>
    </tr>
    <th> version </th>
    <td> 2.0 </td>

    3. 
    <th> Name </th>
    <td> IBM </th>
    <td> HP </th>
    <td> DELL  </th>
    </tr>
    <th> SH </td>
    <td> SH </td>
    <td> SH </td>
    </tr>
    <th> Version </th>
    <td> 1.0 </td>
    <td> 2.0 </td>
    <td> 3.0 </td>
    """

    def __init__(self):
        super(NalaHTMLParser, self).__init__()
        self.html_store = None
        self.html_file = None
        self._class_name = ' '
        self._new_inst = False

    def parse(self, file_path, mode='reg'):
        
        if mode == 'reg':
            return self._parse_reg(file_path)
        elif mode == 'split':
            return self._parse_split(file_path)
        else:
            print "Unkown parse mode"
            return None

    def _set_mof_as_type_I(self, attr_name_stack, attr_value_stack):

        print "Debug: ", DEBUG

        if DEBUG:
            print "attr_name_stack: ", attr_name_stack
            print "attr_value_stack: ", attr_value_stack

        if len(attr_name_stack) == 0 or len(attr_value_stack) == 0:
            return None

        tmp_mof = mof.MOF(self._class_name)
        self.html_store.add_mof(tmp_mof)
        # 1. if the len(val) / len(attr) > 1, means the inst
        # number > 1
        if len(attr_value_stack) / len(attr_name_stack) > 1:
            for i in range(0, len(attr_value_stack)):
                if i % len(attr_name_stack) == 0 and i > 0:
                    tmp_mof = mof.MOF(self._class_name)
                    self.html_store.add_mof(tmp_mof)
                    tmp_mof.set_parameters(self._class_name, attr_name_stack[
                               i % len(attr_name_stack)], attr_value_stack[i])
            attr_name_stack = []
            attr_value_stack = []
        else:
            while len(attr_name_stack) > 0:
                tmp_mof.set_parameters(
                self._class_name, attr_name_stack.pop(), attr_value_stack.pop())
        return self.html_store
    def _set_mof_as_type_II(self, attr_name_stack, attr_value_stack):

        return self._set_mof_as_type_I(attr_name_stack, attr_value_stack)

    def _set_mof_as_type_III(self, attr_name_stack, attr_value_stack):
        pass


    def _parse_split(self, file_path):

        f = self._open_file(file_path)
        tmp_mof = None
        attr_name_stack = []
        attr_value_stack = []
        th_number = 0
        td_number = 0
        start_count_tr = False
        table_type_is = None


        def get_table_type(th_number, td_number):
           if DEBUG is True:
                print "Debug%s th_number: %d" % (self.__file__ + self.__function__, th_number)
                print "Debug%s td_number: %d" % (self.__file__ + self.__function__, td_number)
                if th_number > td_number and th_number > 0:
                    return self.__class__.table_type[0]
                elif th_number == td_number and td_number == 1:
                   return self.__class__.table_type[1]
                elif th_number < td_number and th_number == 1:
                   return self.__class__.table_type[2]

        def set_mof():
            if table_type_is == self.__class__.table_type[0]:
                return self._set_mof_as_type_I(attr_name_stack, attr_value_stack)
            elif table_type_is == self.__class__.table_type[1]:
                return self._set_mof_as_type_II(attr_name_stack, attr_value_stack)
            elif table_type_is == self.__class__.table_type[2]:
               return self._set_mof_as_type_III(attr_name_stack, attr_value_stack)
            else:
                print "Unkown table type: ", table_type_is
                return None

        if f:
            try:
                line = f.readline()
                while line:
                    m_class = re.match(self.__class__.class_pattern, line)
                    m_inst = re.match(self.__class__.inst_pattern, line)
                    m_attr = re.match(self.__class__.attrname_pattern, line)
                    if m_class:
                        self._class_name = m_class.group(1)
                        tmp_mof = mof.MOF(self._class_name)
                        # reset th_number and td_number to 0
                        th_number = 0
                        td_number = 0
                    elif m_inst:
                        # New instance will come, set the parameters
                        #tmp_mof = mof.MOF(self._class_name)
                        #self.html_store.add_mof(tmp_mof)
                        if set_mof() is None:
                            break
                    elif m_attr:
                        if th_number == 0:
                            start_count_tr = True
                        th_number += 1
                        attr_name_stack.append(m_attr.group(1))
                        if DEBUG:
                            print attr_name_stack
                    elif line.startswith('<td'):
                        tmp = line.rstrip().split('<td>')
                        if DEBUG and len(tmp) > 0:
                            print tmp
                        if len(tmp) == 1:
                            pattern = re.compile(r"<td.*>(.*)</td>")
                            attr_value_stack.append(re.findall(pattern,tmp[0])[0])
                            td_number += 1
                        else:
                            for val in tmp:
                                td_number += 1
                                if val == '</td>':
                                    attr_value_stack.append(' ')
                                else:
                                    attr_value_stack.append(val.strip('</td>'))
                    elif start_count_tr is True and line.startswith('<tr'):
                            talbe_type_is = get_table_type(th_number, td_number)


                    line = f.readline()
            except IOError as e:
                print e
        else:
            print "File open error"
        return self.html_store
    def _parse_reg(self, file_path):

        f = self._open_file(file_path)
        tmp_mof = None
        attr_name_stack = []
        attr_value_stack = []
        if f:
            try:
                line = f.readline()
                while line:
                    m_class = re.match(self.__class__.class_pattern, line)
                    m_inst = re.match(self.__class__.inst_pattern, line)
                    m_attr = re.match(self.__class__.attrname_pattern, line)
                    m_val = re.findall(self.__class__.attrvalue_pattern, line)
                    m_val_date = re.findall(self.__class__.attrvalue_date_pattern, line)
                    if m_class:
                        self._class_name = m_class.group(1)
                        tmp_mof = mof.MOF(self._class_name)
                    elif m_inst:
                        # New instance will come, set the parameters
                        tmp_mof = mof.MOF(self._class_name)
                        self.html_store.add_mof(tmp_mof)
                        # 1. if the len(val) / len(attr) > 1, means the inst
                        # number > 1
                        if len(attr_value_stack) / len(attr_name_stack) > 1:
                            for i in range(0, len(attr_value_stack)):
                                if i % len(attr_name_stack) == 0 and i > 0:
                                    tmp_mof = mof.MOF(self._class_name)
                                    self.html_store.add_mof(tmp_mof)
                                tmp_mof.set_parameters(self._class_name, attr_name_stack[
                                                       i % len(attr_name_stack)], attr_value_stack[i])
                            attr_name_stack = []
                            attr_value_stack = []
                        else:
                            while len(attr_name_stack) > 0:
                                tmp_mof.set_parameters(
                                    self._class_name, attr_name_stack.pop(), attr_value_stack.pop())
                    elif m_attr:
                        attr_name_stack.append(m_attr.group(1))
                        if DEBUG:
                            print attr_name_stack
                    elif m_val:
                        for val in m_val:
                            attr_value_stack.append(val)
                        if DEBUG:
                            print attr_value_stack
                    elif m_val_date:
                        attr_value_stack.append(m_val_date[0])
                        #print m_val_date
                    else:
                        pass
                    line = f.readline()
            except IOError as e:
                print e
            return self.html_store
        else:
            print "File open failed!"

    def _open_file(self, file_path):
        if os.access(file_path, os.R_OK):
            try:
                file_handler = open(file_path, 'r')
                return file_handler
            except IOError as e:
                print e
        else:
            print "Can't access file: %s" % file_path

    def set_store(self, store):
        ''' store is the MOFStore instance'''
        if self.html_store is None:
            self.html_store = store
        else:
            print "Store has been set, can't set again"
