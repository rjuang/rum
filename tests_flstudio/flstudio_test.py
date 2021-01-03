import os.path as path
import sys
import unittest
from unittest.mock import patch

# Include FL Studio API stubs
sys.path.append(path.join(path.dirname(path.abspath(__file__)), 'stubs'))
# Include parent folder
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from daw import flstudio


class ChannelRackTest(unittest.TestCase):
    def setUp(self):
        pass

    @patch('channels.selectedChannel')
    def test_fetching_channel(self, mock_selected_channel):
        mock_selected_channel.return_value = 7
        self.assertEqual(7, flstudio.ChannelRack.active_channel())


if __name__ == '__main__':
    unittest.main()
