INTRODUCTION
============

NOTE: This first issue has very little error checking of user input.

JS8Touch is a python application that uses the JS8call API to provide a gui that can be used on the Raspberry Pi official touchscreen.

It is primarily aimed at portable operations where a keyboardor mouse is undesirable. It achieves full chat operation by having programmable macro buttons like FLDigi than can transmit pre-defined text.

If a keyboard is attached a full chat capability is possible for small portable laptops. The raspberry Pi Touchscreen is optional.

JSTouch is programmed using python3 and tkinter. As such it should run on any Linux machine. It would probably run on Windows.

I have never run portable, but I hope to one day. I would be interested to add functionality to JS8Touch for this type of use and also functionality that suit small scren use. But JS8Touch is not a replacement for JS8Call's all encompassing gui.

Ideas for extensions or bug reports are best provided in the Issues secion of this Github repository.

INSTALLING JS8TOUCH
===================
Using a browser download the application by clicking on the green CODE button and selecting Download Zip.

In the downloads directory of your Pi extract the code and copy or move the resulting directory to be in the home directory. Rename is to js8touch so that in the future any autostart code I provide will work.


1. Change the settings of JS8Call so it interfaces with JS8Touch:
 - Reporting>API Allow setting station information
 - Reporting>API  Enable UDP server API
 - Reporting>API  Accept UDP requests
 

2. On the main screen of JS8call:
 - Deselect any selected calls using the DEselect button
 - Turn off any Auto Heartbeats (JS8Touch may work with these enabled, tbc)
 - In the Mode menu deselect Heartbeat Acknowledgements (JS8Touch may work with these enabled, tbc)
 
3. Restart JS8call

Start JS8Touch from a terminal window open in the js8touch directory using
   python3 js8touch.py
   
When JS8Touch is first run a directory js8touch/config will be created if it is not already present and several config files will be copied to it from j8t_resources. This allows updates of the code to retain your configuration. Deleting or renaming the config directory will cause the default config to be copied againif required.

Edit /config/config.txt using the editor. At this stage all you need to do is to add your name and QTH.

Restart JS8Touch. When the title bar shows that JS8Touch is connected to JS8Call you are ready to go.

Now read the manual in /js8touch/manual.pdf

 
Using the Raspberry Pi Official Touchscreen
--------------------------------------------
??????

Running JS8Touch on a Different Machine to JS8call
--------------------------------------------------
TBD
