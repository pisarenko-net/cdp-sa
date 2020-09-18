from collections import namedtuple
import unittest
from unittest.mock import patch

import discid

from hifi_appliance.disc import read_disc_id


class DiscTestCase(unittest.TestCase):
	def test_read_disc_id_ok(self):
		return_object = namedtuple('MockDisc', ['id'])
		return_object.id = 'disc_id'
		with patch('discid.read', return_value=return_object) as mock_method:
			self.assertEqual(read_disc_id(), 'disc_id')

	def test_fail_returns_none(self):
		with patch('discid.read') as mock_method:
			mock_method.side_effect = discid.disc.DiscError()
			self.assertEqual(read_disc_id(), None)
