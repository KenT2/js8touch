# pip3 install rpi-backlight
# https://pypi.org/project/rpi-backlight/ and permissions and sudo reboot



class BacklightDriver:


# ***********************************************
# Touchscreen Backlight Commands
# ************************************************ 
   
    def init_backlight(self,enable):
        self.backlight=None
        self.orig_brightness=100 # overidden by first query
        if enable is True:
            try:
                from rpi_backlight import Backlight
            except:
                return 'error','rpi-backlight is not installed'
            try:
                self.backlight=Backlight()
            except:
                return 'error','Official Touchscreen, problem with rpi-backlight'
            try:
                self.orig_brightness=self.backlight.brightness
            except:
                return 'error','Official Touchscreen,  problem with rpi-backlight'
        #print ('BACKLIGHT',self.backlight,self.orig_brightness)
        return 'normal',''

    def terminate_backlight(self):
        if self.backlight is not None:
            self.backlight.power=True
            self.backlight.brightness=self.orig_brightness

    def do_backlight_command(self,text):
        if self.backlight is None:
            return 'error','rpi-backlight not initialised'
        fields=text.split()
        # print (fields)
        if len(fields)<1:
            return 'error','too few fields in backlight command: '+ text
        # on, off, inc val, dec val, set val fade val duration
        #                                      1   2    3
        if fields[0]=='on':
            self.backlight.power = True
            return 'normal',''      
        if fields[0]=='off':
            self.backlight.power = False
            return 'normal',''
        if fields[0] in ('inc','dec','set'):
            if len(fields)<2:
                return 'error','too few fields in backlight command: '+ text
            if not fields[1].isdigit():
                return'error','field is not a positive integer: '+text
            if fields[0]=='set':
                val=int(fields[1])
                if val>100:
                    val = 100
                elif val<0:
                    val=0
                # print (val)
                self.backlight.brightness = val
                return 'normal',''            
            if fields[0]=='inc':
                val = self.backlight.brightness + int(fields[1])
                if val>100:
                    val = 100
                # print (val)
                self.backlight.brightness= val
                return 'normal',''
            if fields[0]=='dec':
                val = self.backlight.brightness - int(fields[1])
                if val<0:
                    val = 0
                # print (val)
                self.backlight.brightness= val
                return 'normal',''
        if fields[0] =='fade':
            if len(fields)<3:
                return 'error','too few fields in backlight command: '+ text
            if not fields[1].isdigit():
                return'error','backlight field is not a positive integer: '+text            
            if not fields[2].isdigit():
                return'error','backlight field is not a positive integer: '+text
            val=int(fields[1])
            if val>100:
                val = 100
            elif val<0:
                val=0
            with selfbacklight.fade(duration=fields[2]):
                self.backlight.brightness=val
                return 'normal',''
        return 'error','unknown backlight command: '+text


# used to test on a machine without a backlight
class FakeBacklight():
    
    def __init__(self):
        self._brightness=100
        self._power = True
        # print ('USING FAKE BACKLIGHT')
        

    def get_power(self):
        return self._power

    def set_power(self, power):
        self._power=power
        print ('POWER',self._power)

    power = property(get_power, set_power)

    def get_brightness(self):
        return self._brightness

    def set_brightness(self, brightness):
        self._brightness=brightness
        print ('BRIGHTNESS',self._brightness)

    brightness = property(get_brightness, set_brightness)    


