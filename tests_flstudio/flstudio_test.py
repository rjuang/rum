import os.path as path
import sys
import unittest
from collections import defaultdict
from unittest.mock import patch, DEFAULT, call

sys.path.append(path.join(path.dirname(path.abspath(__file__)), 'stubs'))
# Include parent folder
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

# Include FL Studio API stubs
from daw import flstudio
from daw.flstudio import register
from rum import scheduling, matchers
from rum.midi import MidiMessage
from rum.processor import trigger_when
from rum.scheduling import Scheduler
from tests import testutils



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


class DecoratorsTest(unittest.TestCase):

    def setUp(self):
        self.fake_clock = testutils.FakeClock()
        # Override the active scheduler
        scheduling._active_scheduler = Scheduler(time_fn=self.fake_clock.time)

    def test_registerUnrecognizedFunction_isNoOp(self):
        args = defaultdict(list)

        @register
        def test_fn(val1, val2, kw1=None, kw2=None):
            args['val1'].append(val1)
            args['val2'].append(val2)
            args['kw1'].append(kw1)
            args['kw2'].append(kw2)

        test_fn(3, 4, kw1=1, kw2=2)
        self.assertEqual({'val1': [3],
                          'val2': [4],
                          'kw1' : [1],
                          'kw2' : [2]}, args)

    def test_callRegisteredOnIdle_triggersScheduler(self):
        scheduled = []
        idle = []

        def append_int():
            scheduled.append(1)

        @register
        def OnIdle():
            idle.append(2)

        self.assertEqual([], scheduled)
        self.assertEqual([], idle)
        scheduling.get_scheduler().schedule(append_int, delay_ms=1)
        self.fake_clock.advance(0.001)

        OnIdle()
        self.assertEqual([2], idle)
        self.assertEqual([1], scheduled)

    def test_callRegisteredOnMidiMsg_triggerProcessor(self):
        received = []
        called = []

        @trigger_when(matchers.status_eq(0x30))
        def msg_received(m: MidiMessage):
            received.append(m)

        @register
        def OnMidiMsg(event):
            called.append(event)

        class FakeEventData:
            def __init__(self, status, data1, data2):
                self.status = status
                self.data1 = data1
                self.data2 = data2

        fake1 = FakeEventData(0x29, 0, 0)
        fake2 = FakeEventData(0x30, 1, 2)

        # Verify a non-matching trigger
        OnMidiMsg(fake1)
        self.assertEqual([], received)
        self.assertEqual([fake1], called)

        # Verify a matching trigger works
        OnMidiMsg(fake2)
        self.assertEqual(1, len(received))
        self.assertEqual([fake1, fake2], called)
        self.assertEqual(0x30, received[0].status)
        self.assertEqual(0x1, received[0].data1)
        self.assertEqual(0x2, received[0].data2)


if __name__ == '__main__':
    unittest.main()
