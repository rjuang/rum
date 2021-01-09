import os.path as path
import sys
import unittest

sys.path.append(path.join(path.dirname(path.abspath(__file__)), 'stubs'))

import device_novation_launchkey_mini_mk3_midi as dut


class NovationLaunchKeyMiniMk3Tests(unittest.TestCase):

    def setUp(self):
        # Initialize
        #dut.OnInit()
        # Deal with any pending tasks
        #dut.OnIdle()
        pass

    def test_recordDownUp_transportRecord(self):
        pass

    def test_recordPlaySequence(self):
        pass

    def test_padButtonsNoPattern_playsNormally(self):
        pass

    def test_pageUpPadButton_changesChannel(self):
        pass

    def test_playButton_transportPlay(self):
        pass

    def test_encoder1_masterVolume(self):
        pass

    def test_encoder8_tweaksLoopDelay(self):
        pass


if __name__ == '__main__':
    unittest.main()
