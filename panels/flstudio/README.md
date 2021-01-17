# FLStudio Panels

An FL Studio panel is a component that can be attached/detached to the MIDI
controller to control a specific function/panel in FL Studio. For example,
one might want to have a mixer volume panel whereby when attached, the sliders
adjust the volume levels of the mixer tracks. Another example is a channel
selector panel where when attached, the bank buttons on a keyboard would set the
current channel.

The concept of a panel is very DAW specific. One DAW might not have a mixer
or even a Channel Rack. Thus, panels need to be daw-specific.

# Missing Tests

A running list of classes that need tests. For the sake of development speed or 
classes that are considered unstable, I've listed the classes below and will
go back to improve test coverage once the classes under development have
stabilized:

- panels.flstudio.lights
- panels.flstudio.recorder
 
