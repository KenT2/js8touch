INTRODUCTION
============

NOTE: This beta issue has incomplete error checking of user input.

JS8Touch is a python application that uses the JS8call API to provide a GUI that can be used with:

• The Raspberry Pi official touchscreen
Touchscreen operation is aimed at portable operations where a keyboard or mouse is undesirable. It achieves chat operation by having programmable macro buttons, like FL-Digi, than can be used to transmit pre-defined messages.

• A Raspberry Pi or other Linux machine with a mouse, keyboard and HDMI monitor.
If a keyboard and mouse is attached a full chat capability is possible for use in, for example, small portable laptops, or a conventional Raspberry Pi setup. Anything that can be done by touch can also be achieved by a left click of the mouse.

• JS8Touch can be used on the same machine as JS8Call or a different machine on the same network. This allows the GUI to be in a room other than the room housing the Transceiver.
JS8Touch is programmed using Python3 and Tkinter. As such it should run on any Linux machine. It would probably run on Windows.

I have never run portable, but I hope to one day soon. I would be interested to add functionality to JS8Touch for this type of operation and also functionality that suits small screen use. But JS8Touch is not a replacement for JS8Call's all encompassing GUI.

Ideas for extensions or bug reports are best provided in the Issues section of this Github repository.

INSTALLING JS8TOUCH
===================
Using a browser download the application by clicking on the green CODE button and selecting Download Zip.

In the downloads directory of your RPi extract the code from the archive (js8touch-master.zip) and copy or move the resulting directory to be in the home directory. Rename the directory to js8touch so that in the future any autostart code I provide will work.


1. Change the settings of JS8Call so it interfaces with JS8Touch:
 - Reporting>API Allow setting station information
 - Reporting>API  Enable UDP server API
 - Reporting>API  Accept UDP requests
 
2. On the main screen of JS8call:
 - Deselect any selected calls using the Deselect button
 - Turn off any Auto Heartbeats (JS8Touch may work with these enabled, tbc)
 - In the Mode menu deselect Heartbeat Acknowledgements (JS8Touch may work with these enabled, tbc)
 
3. Restart JS8call

RUNNING JS8Touch
================

Start JS8Touch from a terminal window open in the js8touch directory using
   python3 js8touch.py
   
When JS8Touch is first run a directory js8touch/config will be created if it is not already present and several config files will be copied to it from j8t_resources. This allows updates of the code to retain your configuration. Deleting or renaming the config directory will cause the default config to be copied again if required.

Edit config/config.txt using the Text Editor. At this stage all you need to do is to add your name and QTH.

Restart JS8Touch. When the title bar shows that JS8Touch is connected to JS8Call you are ready to go.

Now read the manual in manual.pdf

 
