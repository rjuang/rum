import os.path as path
import sys
import unittest
from unittest.mock import patch, DEFAULT, call

# Include FL Studio API stubs
sys.path.append(path.join(path.dirname(path.abspath(__file__)), 'stubs'))
# Include parent folder
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from daw import flstudio


class ChannelRackTest(unittest.TestCase):
    def setUp(self):
        pass

    # Below is a simple example of setting up a mock for testing.
    # Most of the code in FL Studio are just direct bindings. We won't include
    # any tests for these simple bindings since we will just duplicate code.
    # Only tests with complicated logic will be included for tests.
    @patch('channels.selectedChannel')
    def test_fetching_channel(self, mock_selected_channel):
        mock_selected_channel.return_value = 7
        self.assertEqual(7, flstudio.ChannelRack.active_channel())

    def test_dispatchMessageToOtherScripts_whenNoReceiver(self):
        with patch(
                'device.dispatchReceiverCount',
                return_value=0) as mock_receiver_count:
            with patch('device.dispatch') as mock_dispatch:
                flstudio.Device.dispatch_message_to_other_scripts(
                    0x10, 0x20, 0x30)
                self.assertFalse(mock_dispatch.called)

    def test_dispatchMessageToOtherScripts_whenMultipleReceiver(self):
        with patch(
                'device.dispatchReceiverCount',
                return_value=2) as mock_receiver_count:
            with patch('device.dispatch') as mock_dispatch:
                flstudio.Device.dispatch_message_to_other_scripts(
                    0x10, 0x20, 0x30)
                self.assertEqual(2, mock_dispatch.call_count)
                expected_calls = [
                    call.dispatch(0, 0x302010),
                    call.dispatch(1, 0x302010)
                ]
                mock_dispatch.assert_has_calls(expected_calls)


if __name__ == '__main__':
    unittest.main()
