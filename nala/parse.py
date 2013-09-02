import re
import string
from . import mof
from HTMLParser import HTMLParser
import os

DEBUG = False


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
    <tr class='bg1'>
    <td> IBM </th>
    <td> SH </th>
    <td> 1.0 </th>
    </tr>
    <tr  class='bg1'>
    <td> HP </th>
    <td> SH </th>
    <td> 2.0 </th>
    2.
    <th> Name </th>
    <td> IBM </th>
    </tr>
    <tr>
    <th> City </th>
    <td> SH </th>
    </tr>
    <tr>
    <th> Version </th>
    <td> 1.0 </th>
    </tr>
    <tr>
    <th> Name </th>
    <td> HP </td>
    </tr> 
    <tr>
    <th> City </th>
    <td> SH </td>
    </tr>
    <tr>
    <th> version </th>
    <td> 2.0 </td>

    3. 
    <th> Name </th>
    <td> IBM </th>
    <td> HP </th>
    <td> DELL  </th>
    </tr>
    <tr>
    <th> SH </td>
    <td> SH </td>
    <td> SH </td>
    </tr>
    <tr>
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
        self._inst_number_of_table_III = 0

    def parse(self, file_path, mode='reg'):
        
        if mode == 'reg':
            return self._parse_reg(file_path)
        elif mode == 'split':
            return self._parse_split(file_path)
        else:
            print "Unkown parse mode"
            return None

    

    def _get_table_type(self, th_number, td_number):
            
        if DEBUG is True:
            print "Debug: %s th_number: %d" % (__file__, th_number)
            print "Debug: %s td_number: %d" % (__file__, td_number)
        if th_number > td_number and th_number > 0:
            return self.__class__.table_type[0]
        elif th_number == td_number and td_number == 1:
            return self.__class__.table_type[1]
        elif th_number < td_number and th_number == 1:
            self._inst_number_of_table_III = td_number
            return self.__class__.table_type[2]

    def _parse_split(self, file_path):

        f = self._open_file(file_path)
        tmp_mof = None
        self.attr_name_stack = []
        self.attr_value_stack = []
        th_number = 0
        td_number = 0
        start_count_tr = False
        table_type_is = None


        def set_mof():

            if DEBUG:
                import pdb
                pdb.set_trace()

            th_number = 0
            td_number = 0
            if table_type_is == self.__class__.table_type[0]:
                return set_mof_as_type_I( )
            elif table_type_is == self.__class__.table_type[1]:
                return set_mof_as_type_II( )
            elif table_type_is == self.__class__.table_type[2]:
               return  set_mof_as_type_III( )
            else:
                print "Unkown table type: ", table_type_is
                return None

        def append_attr_value_stack(line, td_number):


            if DEBUG is True:
                print "Debug: line = ", line
            # if line is <td>xxxx</td></tr>
            # remove </tr>
            tr_pos = line.find('</tr>')
            line = line[:tr_pos]
            if DEBUG is True:
                print "Debug: line = ", line

            tmp = line.rstrip().split('<td>')
            
            if tmp[0] == '':
                tmp = tmp[1:]
            for val in tmp:
                td_number += 1
                if val == '</td>':
                    self.attr_value_stack.append(' ')
                else:
                    self.attr_value_stack.append(val.strip('</td>'))

            # if len(tmp) == 1:
            #     pattern = re.compile(r"<td.*>(.*)</td>")
            #     attr_value_stack.append(re.findall(pattern, tmp[0])[0])
            #     td_number += 1

            if DEBUG is True:
                print self.attr_value_stack   
        def set_mof_as_type_I( ):


            if len(self.attr_name_stack) == 0 or len(self.attr_value_stack) == 0:
                return None

            #tmp_mof = mof.MOF(self._class_name)
            #self.html_store.add_mof(tmp_mof)
            # 1. if the len(val) / len(attr) > 1, means the inst
            # number > 1
            if len(self.attr_value_stack) / len(self.attr_name_stack) > 1:
                for i in range(0, len(self.attr_value_stack)):
                    if i % len(self.attr_name_stack) == 0:
                        tmp_mof = mof.MOF(self._class_name)
                        self.html_store.add_mof(tmp_mof)
                    tmp_mof.set_parameters(self._class_name, self.attr_name_stack[
                           i % len(self.attr_name_stack)], self.attr_value_stack[i])
                self.attr_name_stack = []
                self.attr_value_stack = []
            else:
                tmp_mof = mof.MOF(self._class_name)
                self.html_store.add_mof(tmp_mof)
                while len(self.attr_name_stack) > 0:
                    tmp_mof.set_parameters(
                        self._class_name, self.attr_name_stack.pop(), self.attr_value_stack.pop())

        def set_mof_as_type_II( ):

            return self._set_mof_as_type_I( )

        def set_mof_as_type_III( ):

            # Empty attributes
            if len(self.attr_name_stack) == 0 or len(self.attr_value_stack) == 0:
                return None

            # Set attr value
            """
            The example list of attr values map as below:
            P = [p1, p2, p3]

            V = [v1, v1', v1'', v1''', ..., v1'~~~',
                 v2, v2', v2'', v2''', ..., v2'~~~',
                 v3, v3', v3'', v3''', ..., v3'~~~'
                ]

            The table is a len(P) X len(V) Matrix

                                  inst_number = n
                   /~~~~~~~~~~~~~~~~~~^~~~~~~~~~~~~~~~~~~~~~~~~\
            -------------------------------------------------- \
            | p1 || v1 | v1' | v1'' | v1'''| ... | v1'''...'''| |
            --------------------------------------------------  |
            | p2 || v2 | v2' | v2'' | v2'''| ... | v2'''...'''|  > len(P)
            --------------------------------------------------- |
            | p3 || v3 | v3' | v3'' | v3'''| ... | v3'''...'''| |
            ---------------------------------------------------/
            i = 0, j = 0: p1 = v1 ---- V[0] ---- 0*n + 0
                   j = 1: p2 = v2 ---- V[n] ---- 1*n + 0
                   j = 2: p3 = v3 ---- V[2n] --- 2*n + 0
            i = 1, j = 0: p1 = v1' ---- V[1] ---- 0*n + 1
                   j = 1: p2 = v2' ---- V[n+1] ---- 1*n + 1
                   j = 2: p3 = v3' ---- V[2n+1] --- 2*n + 1
            ...

            ===>   parameters = V[i + j*n]

            So set the attr as:
            for i = [0..n-1]:
                    tmp_mof = mof.MOF(class)
                    html_store.add_mof(tmp_mof)
                    for j = [o..len(P)-1]:
                        tmp_mof.set_parameters(class, P[j], V[i+j*n])))
            """
            for i in range(0, self._inst_number_of_table_III):
                tmp_mof = mof.MOF(self._class_name)
                html_store.add_mof(tmp_mof)
                for j in range(0, len(self.attr_name_stack)):
                    tmp_mof.set_parameters(self._class_name, self.attr_name_stack[j], 
                        self.attr_value_stack[i + j*self._inst_number_of_table_III])
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
                        set_mof()

                    elif m_attr:
                        if th_number == 0:
                            start_count_tr = True
                        th_number += 1
                        self.attr_name_stack.append(m_attr.group(1))
                        if DEBUG:
                            print self.attr_name_stack
                    elif line.startswith('<td'):
                        append_attr_value_stack(line, td_number)
                    elif start_count_tr is True and line.startswith('<tr'):
                            table_type_is = self._get_table_type(th_number, td_number)
                            start_count_tr = False


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
                        #tmp_mof = mof.MOF(self._class_name)
                    elif m_inst:
                        # New instance will come, set the parameters
                        tmp_mof = mof.MOF(self._class_name)
                        self.html_store.add_mof(tmp_mof)
                        # 1. if the len(val) / len(attr) > 1, means the inst
                        # number > 1
                        if len(attr_value_stack) / len(attr_name_stack) > 1:
                            for i in range(0, len(attr_value_stack)):
                                if i % len(attr_name_stack) == 0:
                                    tmp_mof = mof.MOF(self._class_name)
                                    self.html_store.add_mof(tmp_mof)
                                tmp_mof.set_parameters(self._class_name, attr_name_stack[i % len(attr_name_stack)], attr_value_stack[i])
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
