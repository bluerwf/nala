#! /usr/bin/env python

import nala.mof
import unittest
from hashlib import md5



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



if __name__ == '__main__':
	#unittest.main()
	suite = unittest.TestLoader().loadTestsFromTestCase(TestMOF)
	unittest.TextTestRunner(verbosity=3).run(suite)
