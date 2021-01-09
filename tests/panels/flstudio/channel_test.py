import sys
import unittest
from os import path
from unittest import mock

sys.path.append(
    path.join(
        path.dirname(path.dirname(path.dirname(path.dirname(path.abspath(
            __file__))))),
        'tests_flstudio/stubs')
)

from panels.flstudio.channel import ChannelSelector
from rum import processor
from rum.matchers import midi_has
from rum.midi import MidiMessage


class ChannelSelectorTest(unittest.TestCase):
    def setUp(self):
        processor.get_processor().clear()
        self._messages = []
        self._btn_index = []
        self._channel_index = []
        self.mock_selectOneChannel = mock.patch(
            'channels.selectOneChannel').start()
        self.mock_channelCount = mock.patch('channels.channelCount').start()
        self.mock_channelCount.return_value = 4

        @ChannelSelector([midi_has(status=i) for i in range(10)])
        def on_channel_selected(m: MidiMessage, btn_index, channel_index):
            self._messages.append(m)
            self._btn_index.append(btn_index)
            self._channel_index.append(channel_index)

    def tearDown(self):
        self.mock_selectOneChannel.stop()
        self.mock_channelCount.stop()

    def run(self, result=None):
        with mock.patch('channels.selectOneChannel') as mock_selectOneChannel:
            with mock.patch('channels.channelCount') as mock_channelCount:
                self.mock_selectOneChannel = mock_selectOneChannel
                self.mock_channelCount = mock_channelCount
                self.mock_channelCount.return_value = 4
                super(ChannelSelectorTest, self).run(result)

    def test_channelSelectorAttachedMatchingMessage_setsChannel(self):
        msg = MidiMessage(3, 100, 200)
        processor.get_processor().process(msg)
        self.assertEqual([msg], self._messages)
        self.assertEqual([3], self._btn_index)
        self.assertEqual([3], self._channel_index)
        self.mock_selectOneChannel.assert_called_once_with(3)

    def test_channelSelectorAttachedNonmatchingMessage_doesNotSetChannel(self):
        msg = MidiMessage(10, 100, 200)
        processor.get_processor().process(msg)
        self.assertEqual([], self._messages)
        self.assertEqual([], self._btn_index)
        self.assertEqual([], self._channel_index)
        self.mock_selectOneChannel.assert_not_called()

    def test_channelSelectorAttachedChannelNonExistent_doesNotSetChannel(self):
        msg = MidiMessage(4, 100, 200)
        processor.get_processor().process(msg)
        self.assertEqual([], self._messages)
        self.assertEqual([], self._btn_index)
        self.assertEqual([], self._channel_index)
        self.mock_selectOneChannel.assert_not_called()


if __name__ == '__main__':
    unittest.main()
