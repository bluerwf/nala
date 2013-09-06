#! /usr/bin/env python

import nala.mof
import unittest
from hashlib import md5
from operator import itemgetter



class TestMOF(unittest.TestCase):
	"""The Unit Test class for testing MOF"""
	def setUp(self):
		self.mof = nala.mof.MOF()
	def test_set_classname(self):
		names = [None, 1, '1', 'hello', '#@!']
		for name in names:
			self.mof.set_classname(name)
			self.assertEqual(self.mof.class_name, name)
	def test_set_parameters(self):
		class_name = 'hello'
		para_names = ['k1', 'k2', 'k3', 'k4', 'k5']
		self.mof = nala.mof.MOF(class_name)
		index = 0
		for para_name in para_names:
			self.mof.set_parameters(class_name, para_name, index)
			self.assertEqual(self.mof.class_name, class_name)
			self.assertEqual(self.mof.mof_parameters[para_name], index)
			self.assertNotEqual(self.mof.class_name, 'world')
			self.assertFalse(self.mof.class_name == 'world')
			index += 1
		
	def test_get_mof_info(self):
		self.assertEqual((None,{}), self.mof.get_mof_info())
		self.mof.set_classname("unit_test")
		self.assertEqual(("unit_test", {}), self.mof.get_mof_info())
		self.assertNotEqual((None, {}), self.mof.get_mof_info())
		attrs = ('name', 'corporation', 'version', 'date')
		value1 = ("h1", " ", "1.0", "2013")
		value2 = ("I1", "IBM", "2.0", "2013")
		value3 = ("M1", "MS", "9.0", " ")
		for i in range(0, len(attrs)):
			self.mof.set_parameters("unit_test", attrs[i], value1[i])
			self.mof.set_parameters("unit_test", attrs[i], value2[i])
			self.mof.set_parameters("unit_test", attrs[i], value3[i])
			self.assertEqual("unit_test", self.mof.class_name)
		self.assertListEqual(sorted(self.mof.mof_parameters.iterkeys()), sorted(list(attrs)))
		self.assertNotEqual(sorted(self.mof.mof_parameters.keys()), sorted(list(value3)))
		self.assertEqual(sorted(self.mof.mof_parameters.values()), sorted(list(value3)))
		self.assertNotEqual(sorted(self.mof.mof_parameters.values()), sorted(list(value2)))
		self.assertNotEqual(sorted(self.mof.mof_parameters.values()), sorted(list(value1)))

class TestMOFStore(unittest.TestCase):
	"""docstring for TestMofStoreunittest.TestCase"""
	def setUp(self):
		self.mof_store = nala.mof.MOFStore("hello")

	def test_add_mof(self):

		self.assertEqual(None, self.mof_store.get_mof('world'))
		mof = nala.mof.MOF('world')
		self.mof_store.add_mof(mof)
		self.assertEqual(mof, self.mof_store.get_mof('world')[-1])
		self.assertNotEqual(mof, self.mof_store.get_mof('hello'))
		return mof
	
	def test_get_mof(self):
		mof = self.test_add_mof()
		mof2 = nala.mof.MOF('IBM')
		self.assertEqual(mof, self.mof_store.get_mof('world')[-1])
		self.assertNotEqual(mof2, self.mof_store.get_mof('world')[-1])
		self.mof_store.add_mof(mof2)

	def test_get_mof_instance_number(self):

	    self.test_get_mof()	

	    self.assertEqual(1, self.mof_store.get_mof_instance_number('world'))
	    self.assertNotEqual(-1, self.mof_store.get_mof_instance_number('world'))
	    self.assertEqual(1, self.mof_store.get_mof_instance_number('IBM'))
	    self.assertNotEqual(-1, self.mof_store.get_mof_instance_number('IBM'))
	    self.assertNotEqual(0, self.mof_store.get_mof_instance_number('IBM'))
	    self.assertNotEqual(0, self.mof_store.get_mof_instance_number('world'))
	    self.assertEqual(-1, self.mof_store.get_mof_instance_number('hello'))

if __name__ == '__main__':
	#unittest.main()
	suite1 = unittest.TestLoader().loadTestsFromTestCase(TestMOF)
	suite2 = unittest.TestLoader().loadTestsFromTestCase(TestMOFStore)
	unittest.TextTestRunner(verbosity=3).run(suite1)
	unittest.TextTestRunner(verbosity=3).run(suite2)
