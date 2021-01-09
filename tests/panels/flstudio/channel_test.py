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

from daw import flstudio
from panels.flstudio import channel
from panels.flstudio.channel import ChannelSelector
from rum import processor, autorefresh
from rum.matchers import midi_has
from rum.midi import MidiMessage


class ChannelSelectorTest(unittest.TestCase):
    def setUp(self):
        processor.get_processor().clear()
        autorefresh.get_refresh_manager().clear()

        self._btn_index = []
        self._channel_index = []
        self._cleanup = []

        @ChannelSelector([midi_has(status=i) for i in range(10)])
        def on_channel_selected(btn_index, channel_index):
            self._btn_index.append(btn_index)
            self._channel_index.append(channel_index)

        self.channel_selector = channel.get_channel_selector()
        self.mock_selectOneChannel = self.mock('channels.selectOneChannel')
        self.mock_channelCount = self.mock('channels.channelCount')
        self.mock_selectedChannel = self.mock('channels.selectedChannel')

        self.mock_channelCount.return_value = 4
        self.mock_selectedChannel.return_value = 3

    def mock(self, method):
        patcher = mock.patch(method)
        instance = patcher.start()
        self._cleanup.append(patcher.stop)
        return instance

    def tearDown(self):
        for fn in self._cleanup:
            fn()

    def test_channelSelectorAttachedMatchingMessage_setsChannel(self):
        msg = MidiMessage(3, 100, 200)
        processor.get_processor().process(msg)

        self.mock_selectOneChannel.assert_called_once_with(3)
        # Messages are not received until the refresh trigger.
        self.assertEqual([], self._btn_index)
        self.assertEqual([], self._channel_index)

    def test_channelSelectorAttachedNonmatchingMessage_doesNotSetChannel(self):
        msg = MidiMessage(10, 100, 200)
        processor.get_processor().process(msg)

        self.mock_selectOneChannel.assert_not_called()
        self.assertEqual([], self._btn_index)
        self.assertEqual([], self._channel_index)

    def test_channelSelectorAttachedChannelNonExistent_doesNotSetChannel(self):
        msg = MidiMessage(4, 100, 200)
        processor.get_processor().process(msg)

        self.mock_selectOneChannel.assert_not_called()
        self.assertEqual([], self._btn_index)
        self.assertEqual([], self._channel_index)

    def test_channelSelectorAttachedDifferentBase_setsChannel(self):
        self.mock_channelCount.return_value = 16
        self.channel_selector.set_base_index(8)

        msg = MidiMessage(3, 100, 200)
        processor.get_processor().process(msg)

        self.mock_selectOneChannel.assert_called_once_with(11)
        # Messages are not received until the refresh trigger.
        self.assertEqual([], self._btn_index)
        self.assertEqual([], self._channel_index)

    def test_channelRefreshWithFocusChange_triggersChannelOutputChange(self):
        autorefresh.get_refresh_manager().refresh(
            flstudio.REFRESH_FOCUSED_WINDOW)
        self.assertEqual([3], self._btn_index)
        self.assertEqual([3], self._channel_index)

    def test_channelSetNewBase_refreshTriggersCorrectChannelIndex(self):
        self.channel_selector.set_base_index(8)
        autorefresh.get_refresh_manager().refresh(
            flstudio.REFRESH_FOCUSED_WINDOW)
        self.assertEqual([None], self._btn_index)
        self.assertEqual([3], self._channel_index)

    def test_channelRefreshWithMixerChange_doesNotTriggersOutputChange(self):
        autorefresh.get_refresh_manager().refresh(
            flstudio.REFRESH_MIXER_CONTROLS)
        self.assertEqual([], self._btn_index)
        self.assertEqual([], self._channel_index)


if __name__ == '__main__':
    unittest.main()
