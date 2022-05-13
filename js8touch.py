
#from tkinter import *
#import tkinter as tk

#from tkinter.ttk import *

import tkinter as tk
from tkinter import ttk

import tkinter.messagebox
import configparser
from j8t_udpserver import Server
import sys
from functools import partial
import datetime
import random
import os,shutil
import textwrap
from j8t_backlight import BacklightDriver

class JS8Touch(object):
    

    # ==============================
    # FRAMEWORK
    # ==============================

    # start here
    def init(self):
        # init logging,TURN IT OFF HERE
        self.init_log(True)
        
        self.js8touch_version='1.1.1a'
        self.log('JS8Touch Version '+self.js8touch_version)
        
        # get Tkinter
        self.root = tk.Tk()
        
        if not os.path.exists('config'):
            self.first_run()

        # things from config.txt
        self.my_name = ''
        self.my_qth = ''
        self.stale_time=0     #activity display stale time, seconds
        self.max_offset = 0
        self.selected_button_action = ''   # chat or call
        self.send_button_action = ''   # chat or call
        self.backlight_brightness=100 #overidden by config.txt
        self.enable_touchscreen='no'
        self.see_hb=0 # overridden by config.txt
        self.make_config()

        # config things from js8call, read after server connected
        self.my_callsign=''
        self.my_grid4=''
        self.my_grid = ''
        self.my_grid6=''
               
        # init activity list
        self.selected_activity_urn='' # item id from treview which is unique
        self.selected_message = ''
        self.selected_callsign=''
        self.selected_offset=''
        self.selected_snr=''

        # init dynamic things received from js8call, read after connected
        self.station_dial=''
        self.station_freq=''
        self.station_offset=''
        self.station_speed=''
        self.station_ptt=''
        
        self.station_selected='' #used to check something selected before transmission, js8touch has its own selection

        self.status_received=False # don't display the status until it is first received
        
        self.connected=False # disable calls to js8call until it is connected.
        self.tx_offset=-1 # offset for transmission
        self.transmitting = False
        self.pre_hb_offset = -1 # offset before heartbeat is transmitted
        self.offset_code = ''  #offset code from pressed macro button
        self.last_tx_text ='' #????? not used last non zero tx text got from js8call
        self.last_activity_type = 'RX.ACTIVITY' # used to control newlines in rx_text area
        
        #Init touchscreen and backlight
        if self.enable_backlight == 'yes':
            self.backlight=BacklightDriver()
            status,message=self.backlight.init_backlight(True)
            if status != 'normal':
                self.show_warning(message)
            status,message=self.backlight.do_backlight_command('set '+self.backlight_brightness)
            if status != 'normal':
                self.show_warning(message)
            self.log('Touchscreen Initilaised')
        # make the gui
        self.make_gui()
        self.make_bands()  #read bands from bands.txt
        self.make_speeds() #read speeds frpm speeds.txt

        #start js8call server
        self.s = Server()
        self.s.init(self.root,self.js8call_ip,self.js8call_port,self.connected_callback,self.event_callback,self.reply_callback,self.error_callback,self.log)
        # and start the server's listen loop
        self.s.listentk()
        
        # start the gui
        self.root.mainloop()

    #close the server and gui
    def close(self):
        self.s.close()
        if self.enable_touchscreen == 'yes':
            self.backlight.terminate_backlight()
        self.log('Closing js8touch')
        self.close_log()
        self.root.destroy()
        sys.exit(0)

    # execute some things at regular intervals
    def gui_ticker(self):
        self.display_status()
        self.age_activity()
        self.root.after(10000,self.gui_ticker)


    # callback when server is connected to JS8call and commands can be sent
    def connected_callback(self,connected):
        if connected is True:
            self.connected=True
            self.log('Connected to JS8Call')
            self.root.title('JS8Touch ' + self.js8touch_version + ' using JS8call version: ' + self.s.js8_version)
            self.band_button.config(state='normal')
            self.speed_button.config(state='disabled')
            self.send_button.config(state='normal')
            self.offset_button.config(state='normal')
            self.control_macro_buttons('normal')
            self.root.update()
            self.init_config()
            self.init_band()    #set initial band
            self.init_speed()   # set intial speed
            self.gui_ticker()   # start regular tasks scheduler

        else:
            self.root.title('JS8Touch ' + self.js8touch_version + '   Waiting for reconnection')
            self.connected=False
            self.band_button.config(state='disabled')
            self.speed_button.config(state='disabled')
            self.send_button.config(state='disabled')
            self.control_macro_buttons('disabled')
            self.root.update()
            self.log('Lost connection to JS8Call')
            
    # error detected by the server
    def error_callback(self,err):
        self.log('Error: '+ err )
        self.show_warning(err)
        return

    # many message types are sent unrequested by js8call
    def event_callback(self,typ,value,params):
            
        if typ in ('RX.ACTIVITY','RX.DIRECTED','RX.DIRECTED.ME'):
            self.log_activity(typ,value,params)
            self.update_activity(typ,value,params)
            
        elif typ == 'STATION.STATUS':
            self.update_status(value,params)
            
        elif typ == 'MODE.SPEED':
            self.update_speed(value,params)
            
        elif typ =='RIG.PTT':
            self.update_ptt(value,params)
            
        elif typ =='TX.TEXT':
            self.update_tx_text(value,params)
            
        elif typ == 'STATION.CALLSIGN':
            self.my_call= value
            
        elif typ == 'STATION.GRID':
            self.my_grid= value
            self.my_grid6= value[0:6]        
            self.my_grid4= value[0:4]

        elif typ == 'CLOSE':
            self.log('JS8Call Closed')
            self.show_warning('JS8Call has closed')

    # reply message to command sent to js8call received
    def reply_callback(self,typ,reply):
        print('Gui reply: ',typ,reply)
        


    #read config.txt configuration
    def make_config(self):
        filename='config/config.txt'
        self.log('Reading Configuration from '+ filename)
        conf = configparser.ConfigParser()
        conf.read(filename)
        self.my_name=conf.get('config','name')
        self.my_qth=conf.get('config','qth')
        self.stale_time=int(conf.get('config','stale_time'))
        self.max_offset=int(conf.get('config','max_offset'))
        initial_see_hb=conf.get('config','see_hb')
        if initial_see_hb=='yes':
            self.initial_hb_enable=1
        else:
            self.initial_hb_enable=0
            
        self.enable_backlight=conf.get('config','enable_backlight')
        self.backlight_brightness=conf.get('config','backlight_brightness')
        self.selected_button_action=conf.get('config','selected_button_action')
        self.send_button_action=conf.get('config','send_button_action')
        self.js8call_ip=conf.get('config','js8call_ip')
        self.js8call_port=conf.get('config','js8call_port')
        self.eod_marker=conf.get('config','eod_marker')
                
    # request config items from js8call, items got by reply in event_callback
    def init_config(self):
        self.s.send('STATION.GET_GRID')
        self.s.send('STATION.GET_CALLSIGN')        


    # ==============================
    # TRANSMIT
    # ==============================


    def transmit(self):
        # set the offset to value in config.txt if user SEND's without using a macro or Selected frequency button
        self.pre_hb_offset=self.station_offset
        if self.tx_offset == -1:
            self.tx_offset=self.calc_tx_offset(self.send_button_action)
            if self.tx_offset==-1:
                return

        self.log ('setting frequency for transmission ',self.tx_offset)
        self.s.send('RIG.SET_FREQ', '', params = {"OFFSET": self.tx_offset})
        
        # SEND_MESSAGE needs the text, it does not take it from TX_TEXT
        text=self.tx_text.get(1.0,tk.END)[:-1].upper()
        self.log('transmitting message')
        self.s.send('TX.SEND_MESSAGE',text)
        self.tx_text.delete(1.0,tk.END)
        # reset offset so if Send used without using a macro will transmit on a free chat offset
        self.tx_offset= -1
        
        #disable buttons
        self.band_button.config(state='disabled')
        self.speed_button.config(state='disabled')
        self.send_button.config(state='disabled')
        self.control_macro_buttons('disabled')
        
        # and monitor TX.TEXT for end of transmission
        self.transmitting=True
        self.root.after(500,self.mon_tx)
        
    def mon_tx(self):
        # loop asking for transmitted text at intervals, text received in update_tx_text
        self.s.send('TX.GET_TEXT')
        if self.transmitting is False:
            return
        else:
            self.root.after(500,self.mon_tx)
        

    # response to GET_TEXT while transmitting
    def update_tx_text(self,value,params):
        if self.transmitting is False:
            return        
        # transmission finished as no text in TX.TEXT so display transmitted text in RX Text area 
        if len(value) == 0:
            self.log('transmission complete')
            self.transmitting=False
            self.rx_text.tag_config("a", foreground="red")
            self.rx_text.insert(tk.END,self.last_tx_text+'\n',('a',))
            self.rx_text.see(tk.END)
            self.send_button.config(text='SEND',bg='light grey',state='normal')
            
            self.tx_text.delete(1.0,tk.END)
            # enable buttons
            self.band_button.config(state='normal')
            self.speed_button.config(state='normal')
            self.control_macro_buttons('normal')
            
            # return to the previous frequency after sending a heartbeat
            if self.offset_code=='hb':
                self.log('return to current offset after heartbeat',self.pre_hb_offset)
                self.s.send('RIG.SET_FREQ', '', params = {"OFFSET": self.pre_hb_offset})
            return
            
        self.last_tx_text= value
        
        # display what is transmitted in Text window
        #self.log('transmitting from TX buffer',value)
        self.tx_text.delete(1.0,tk.END)
        self.tx_text.tag_config("a", foreground="red")
        self.tx_text.insert(tk.END,value,('a',))
        
        self.send_button.config(state='normal')
        #self.root.update()
        if self.station_ptt == 'on':
            #self.log('PTT is ON')
            self.send_button.config(text='TX',bg='red')
        elif self.transmitting is True:
            #self.log('sending')
            self.send_button.config(text='WAIT',bg='green')
        self.send_button.config(state='disabled')
        self.root.update()
        
    def halt(self):
        print('not implemented')

    #send button pressed
    def sendit(self):
        self.log('Send button pressed')
        if len(self.tx_text.get(1.0,tk.END)) <= 1:
            self.show_warning('nothing to send')
            return
        self.transmit()

    #button showing details of selected activity pressed
    #set required TX offset and show call in Tx Text area
    def use_selected_button(self):
        self.log('Selected Activity button pressed with action: ',self.selected_button_action)
        if self.selected_activity_urn == '':
            self.show_warning ('nothing selected')
            return
        if self.selected_button_action == 'call':
            self.tx_offset=self.selected_offset
        elif self.selected_button_action== 'chat':
            self.tx_offset=self.random_offset(1000,self.max_offset)
        elif selected_button_action=='current':
            self.tx_offset=self.selected_offset
        else:
            self.show_warning ('unknown selected button_action in config.txt')
        self.tx_text.delete(1.0,tk.END)
        self.tx_text.insert(tk.END,self.selected_callsign+' ') 

        
    # ==============================
    # MACRO BUTTONS
    # ==============================        
             
   # read the macros from macros.txt and create the macro buttons
    def make_buttons(self):
        filename='config/macros.txt'
        self.log('read macros from ',filename)
        macros_c = configparser.ConfigParser()
        macros_c.read(filename)
        sections=macros_c.sections()
        row=0
        self.macro_buttons=[]
        for section in sections:
            uname=macros_c.get(section,'name')
            uoffset=macros_c.get(section,'offset')
            utext=macros_c.get(section,'text')
            # add arguments to command
            action_with_arg= partial(self.use_macro,uoffset,utext)
            
            #create the button with command self.use_macro
            mb= ttk.Button(self.right_frame, text=uname, command = action_with_arg)
            mb.grid(column=0,row=row,padx=2,pady=5,sticky=tk.N)
            row+=1
            self.macro_buttons.append(mb)
        self.control_macro_buttons('disabled')

    def control_macro_buttons(self,state):
        for button in self.macro_buttons:
            button.config(state=state)
        return

            
    # user pressed a macro button.
    def use_macro(self,offset_code,text):
        self.offset_code=offset_code
        # calc the offset
        self.tx_offset=self.calc_tx_offset(offset_code)
        if self.tx_offset==-1:
            return
        
        # clear and auto transmit  | (clear) and > (transmit)
        if len(text)>0 and text[0] == '|':
            self.tx_text.delete(1.0,tk.END)
            text= text[1:]            
        if len(text)>0 and text[-1]== '>':
            auto_tx=True
            text= text[:-1]
        else:
            auto_tx=False
            
        #expand the macro text
        text=self.replace_vars(text)
        self.tx_text.insert(tk.END,text)
        self.log ('macro button pressed: ',text,'Auto=',auto_tx,'Offset Code=',self.offset_code,'offset=',self.tx_offset)
        if auto_tx == True:
            self.transmit()
        return

    ### macro expansion
    def replace_vars(self,text):
        while True:
            sindex=text.find('[')
            if sindex == -1:
                break
            eindex=text.find(']')
            var=text[sindex:eindex+1]
            res=self.expand_macro(var.upper())
            text=text.replace(var,res)
        return text
        
    def expand_macro(self,var):
        if var=='[SNR]':
            if self.selected_snr>0:
                return '+'+str(self.selected_snr)
            else:    
                return str(self.selected_snr)
        elif var=='[CALL]':
            return self.selected_callsign
        elif var=='[MYCALL]':
            return self.mycallsign
        elif var=='[GRID6]':
            return self.my_grid6 
        elif var=='[GRID4]':
            return self.my_grid4
        elif var=='[GRID]':
            return self.my_grid           
        elif var=='[NAME]':
            return self.my_name
        elif var=='[QTH]':
            return self.my_qth 
            
    ### offset
    
    # compute the tx_offset from the offset field
    def calc_tx_offset(self,offset_code):
        if offset_code== 'current':
            return self.station_offset
        elif offset_code == 'hb':
            return self.random_offset(500,1000)
        elif offset_code == 'chat':
            return self.random_offset(1000,self.max_offset)
        elif offset_code=='call':
            if self.selected_activity_urn != '':
                return self.selected_offset
            else:
                self.show_warning ('nothing selected')
                return -1
        else:
            self.show_warning ('unknown offset in macros.txt or config.txt '+offset_code)
            return -1
            


    #find a clear random frequency for non-directed transmission
    def random_offset(self,start,end):
        tries=0
        while True:
            candidate=random.randint(start,end)

            if self.test_random(candidate) is True:
                self.log ('Tx offset OK',candidate)
                return candidate
            tries+=1
            if tries>100:
                self.log('cannot find a clear frequency')
                self.show_warning('cannot find a clear frequency')
                return -1

            
    def test_random(self,candidate):
        for item in self.activity.get_children():
            lower=  self.activity_get(item,'offset')-10
            upper = self.activity_get(item,'offset') + self.bw_of(self.activity_get(item,'speed'))+10

            if (candidate > lower ) and (candidate < upper):
                self.log('Trying offset',candidate,'against',lower,upper,'for',self.activity_get(item,'offset'),'Fail')
                return False
            else:
                self.log('Trying offset',candidate,'against',lower,upper,'for',self.activity_get(item,'offset'),'Pass')
        return True

    def bw_of(self,speed):
        if speed == 0:
            return 50
        elif speed== 1:
            return 80
        elif speed== 2:
            return 160  
        elif speed== 4:
            return 25
            
            
    # ==============================
    # SPEED AND BAND SELECTION
    # ============================== 
    
    #read bands.txt configuration
    def make_bands(self):
        self.band_list=list()
        filename='config/bands.txt'
        self.log('Reading bands from '+ filename)
        macros_c = configparser.ConfigParser()
        macros_c.read(filename)
        sections=macros_c.sections()
        for section in sections:
            band=macros_c.get(section,'band')
            dial=macros_c.get(section,'dial')
            offset=macros_c.get(section,'offset')
            self.band_list.append((band,dial,offset))

    # set a band on startup
    def init_band(self):
        self.band_index=0
        self.set_band()

    # press the BAND button to change band
    def change_band(self):
        if self.band_index == len(self.band_list)-1:
            self.band_index=0
        else:
            self.band_index +=1
        self.set_band()

    #display and send to js8call
    def set_band(self):
        band= self.band_list[self.band_index][0]
        dial=self.band_list[self.band_index][1]
        offset=self.band_list[self.band_index][2]
        self.band_button.config(text=band)
        self.clear_activity()
        self.log ('Setting band: ',band,dial,offset)
        self.s.send('RIG.SET_FREQ', '', params = {"DIAL": dial, "OFFSET": offset})

# -------------------------
# speed setting via API is broken in JS8CALL

    #read speeds.txt configuration
    def make_speeds(self):
        self.speed_list=list()
        self.reverse_speed=dict()
        filename='config/speeds.txt'
        self.log('Reading Speeds from '+ filename)
        macros_c = configparser.ConfigParser()
        macros_c.read(filename)
        sections=macros_c.sections()
        for section in sections:
            text=macros_c.get(section,'text')
            code=macros_c.get(section,'code')
            self.speed_list.append((text,code))
            self.reverse_speed[code]= text

    # set a speed on startup
    def init_speed(self):
        self.speed_index=0
        self.set_speed()
        
    def change_speed(self):
        # press the SPEED button to change speed
        if self.speed_index == len(self.speed_list)-1:
            self.speed_index=0
        else:
            self.speed_index +=1
        self.set_speed()


    def set_speed(self):
        text= self.speed_list[self.speed_index][0]
        code=self.speed_list[self.speed_index][1]
        self.speed_button.config(text=text)
        self.log('Setting Speed',text,code)
        self.s.send('MODE.SET_SPEED', '', params = {"SPEED": code})

    def change_current_offset(self):
        offset=self.random_offset(1000,self.max_offset)
        if offset==-1:
            return
        self.log ('Setting offset: ',offset)
        self.s.send('RIG.SET_FREQ', '', params = {"OFFSET": offset})

    def activity_get(self,item,field):
        index= self.col_map[field]           
        return self.activity.item(item)['values'][index]


    # ==============================
    # ACTIVITY
    # ==============================
    
    # receive RX.ACTIVITY, RX.DIRECTED,RX.DIRECETED.ME messageS
    # add to existing activity if freq matches
    # else insert as a new activity
    def update_activity(self,typ,value,params):
        #print ('UPD',value)

        # if its for me put it in the rx text window
        if typ=='RX.DIRECTED.ME':
            self.rx_text.insert(tk.END,'\nME!!! '+value)
            self.rx_text.see(tk.END)
            
        # ignore HB messages if checkbox unset
        if self.hb_display_enable.get() == 0 and 'HEARTBEAT' in value:
            return
            
        frequency=params['FREQ']
        # is this frequency in activity list
        for item in self.activity.get_children():
            if abs(self.activity_get(item,'frequency')-frequency)<10:
                #found a match update activity table
                self.activity.set(item,'age',0)
                self.activity.set(item,'age_secs',0)
                self.activity.set(item,'frequency',frequency)
                self.activity.set(item,'offset',params['OFFSET'])
                self.activity.set(item,'speed',params['SPEED'])
                if typ=='RX.ACTIVITY':
                    # add the message to activity or directed already there
                    new_message=self.activity_get(item,'message')+value
                    self.activity.set(item,'message',new_message)                    
                    rolled=self.roll_activity(new_message,self.roll_width)
                    #print ('rolled act',rolled)
                    self.activity.set(item,'rolled_message',rolled)
                    self.activity.set(item,'type','activity')
                    self.log ('Update with Activity',item,value)
                    
                    # if selected item update rx_text
                    if item==self.selected_activity_urn:
                        # do the same for rx_text
                        self.update_selected_params(item)
                        self.display_selected_info()
                        self.rx_text.insert(tk.END,value)
                        self.rx_text.see(tk.END)
                else:
                    #directed
                    # full message is received with EOT marker, callsign and grid. Ignore the message except to add an EOT marker to activity
                    new_message=self.activity_get(item,'message')+ ' '+ self.eod_marker+'\n'
                    rolled=self.roll_activity(new_message,self.roll_width)
                    #print ('rolled act',rolled)
                    self.activity.set(item,'rolled_message',rolled)
                    self.activity.set(item,'callsign',params['FROM'])
                    self.activity.set(item,'grid',params['GRID'])
                    self.activity.set(item,'type','directed')
                    self.log ('UPDATE with Directed',item,value)                    
                    
                    if item==self.selected_activity_urn:
                        #do the same to selected item
                        #print ('directed update rx_text')
                        self.update_selected_params(item)
                        self.display_selected_info()
                        self.rx_text.insert(tk.END,self.eod_marker+'\n')
                        self.rx_text.see(tk.END)
                self.root.update()
                # stop searching after first matching entry        
                return
                
        # no match create a new entry
        if typ== 'RX.ACTIVITY':
            self.make_new_activity('activity',value,params)
        else:
            # directed or directed.me
            self.make_new_activity('directed',value,params)


    # removes the first part of message text that does not fit in the activity display
    def roll_activity(self,text,width):
        rev=self.reverse_str(text)
        short_rev=textwrap.shorten(rev,width,placeholder='__')
        return self.reverse_str(short_rev)

    def reverse_str(self,text):
        return text[::-1]



    # make a new entry
    def make_new_activity(self,mtype,value,params):
        #prepare a new entry in activity list from the received information
        new_entry=self.activity.insert('',0)
        # common items    
        self.activity.set(new_entry,'offset',params['OFFSET'])
        self.activity.set(new_entry,'frequency',params['FREQ'])
        self.activity.set(new_entry,'age',0)
        self.activity.set(new_entry,'age_secs',0)

        self.activity.set(new_entry,'snr',params['SNR'])
        self.activity.set(new_entry,'speed',params['SPEED'])
        self.activity.set(new_entry,'item_id',new_entry)

        if mtype == 'activity':
            # first message is activity
            self.activity.set(new_entry,'callsign',self.find_callsign(value))
            self.activity.set(new_entry,'grid','')
            self.activity.set(new_entry,'type','activity')
            self.activity.set(new_entry,'message',value)
            rolled=self.roll_activity(value,self.roll_width)
            #print ('rolled act',rolled)
            self.activity.set(new_entry,'rolled_message',rolled)
            self.log('CREATE new entry from Activity',new_entry,value)
        else:
            # directed
            # first message is directed
            self.activity.set(new_entry,'callsign',params['FROM'])
            self.activity.set(new_entry,'grid',params['GRID'])
            self.activity.set(new_entry,'type','directed')
            self.activity.set(new_entry,'message',value +'\n')
            rolled=self.roll_activity(value,self.roll_width)
            #print ('rolled dir',rolled)
            self.activity.set(new_entry,'rolled_message',rolled)
            self.log('CREATE new entry from Directed',new_entry,value)
            # ?????new_entry['message']+=self.eod_marker+'\n'
        

    # find a callsign in the first characters of a RX.ACTIVITY message
    def find_callsign(self,text):
        x=text.find(':')
        if x>10 or x==-1:
            return '?????'
        return text[0:x]

    def age_activity(self):
        for item in self.activity.get_children():
            #print ('\nAGE',item['callsign'],item['age'],item['item_id'],self.selected_activity_urn)
            self.activity.set(item,'age_secs',self.activity_get(item,'age_secs')+10)
            self.activity.set(item,'age',self.activity_get(item,'age_secs')//60)           
            
            if self.activity_get(item,'age_secs')>self.stale_time and item != self.selected_activity_urn:
                self.activity.delete(item)
                self.log('Delete on Stale ',item)
                #print ('\ndeleted ',index, item, self.selected_activity_urn)
                
        #print ('list now')
        #for item in self.activity.get_children():
            #print (item,item['callsign'])


    def select_activity(self,event):

        if len(self.activity.selection())==0:
            return
        item = self.activity.selection()[0]
        self.selected_activity_urn=item   
        self.update_selected_params(item)
        self.last_activity_type='RX.ACTIVITY'
        #print ('\nselect item ',item,self.selected_callsign)        
        # add message to received text
        self.rx_text.insert(tk.END,'------------\n'+self.selected_message)
        self.rx_text.see(tk.END)
        self.log('Select Activity Entry ',self.selected_activity_urn)
        self.selected_info.config(state='normal')
        self.display_selected_info()
            

    def deselect(self):
        self.log('Clear Selected button pressed ')
        self.activity.selection_remove(self.selected_activity_urn)
        self.clear_selected()

    def update_selected_params(self,item):
        self.selected_callsign = self.activity_get(item,'callsign')
        self.selected_message = self.activity_get(item,'message')    
        self.selected_offset = self.activity_get(item,'offset')
        self.selected_snr=  self.activity_get(item,'snr')
        self.selected_grid=  self.activity_get(item,'grid')
        self.selected_speed= self.activity_get(item,'speed')
    

    def display_selected_info(self):
        speed_text=self.reverse_speed[str(self.selected_speed)][:1]
        self.selected_info.config(text=' '+self.selected_callsign+ '  '+ str(self.selected_offset)+'  '+ speed_text + '  '+self.selected_grid )

    def clear_activity(self):
        self.log('Clear Activity table')
        self.clear_selected()
        for item in self.activity.get_children():
            self.activity.delete(item)

    def clear_selected(self):
        self.log('Deselect Activity ',self.selected_activity_urn)
        # set age of unselected activity to 0
        if self.selected_activity_urn !='':
            self.activity.set(self.selected_activity_urn,'age_secs',0)
            self.activity.set(self.selected_activity_urn,'age',0)           
            self.selected_activity_urn=''
            self.selected_message = ''
            self.selected_callsign=''
            self.selected_offset=''
            self.selected_snr=''
            self.selected_info.config(text= 'Nothing selected')
            self.selected_info.config(state='disabled')
        self.tx_text.delete(1.0,tk.END)
        self.rx_text.delete(1.0,tk.END)
        self.tx_offset=-1
       

        
    # ==============================
    # STATUS
    # ==============================
    
    def update_freq(self,value,params):
        self.station_dial=params['DIAL']
        self.station_freq=params['FREQ']
        self.station_offset=params['OFFSET']
        self.display_status()
        
    def update_speed(self,value,params):
        self.station_speed=params['SPEED']
        self.display_status()
        

    def update_ptt(self,value,params):
        self.station_ptt=value
        if value =='on':
            self.ptt_label.config(style='red_text.TLabel')
        else:
            self.ptt_label.config(style='green_text.TLabel')

    def update_status(self,value,params):
        self.station_dial=params['DIAL']
        self.station_freq=params['FREQ']
        self.station_offset=params['OFFSET']
        self.station_selected=params['SELECTED']
        self.station_speed=params['SPEED']
        self.status_received=True
        self.display_status()

    # update the status area                
    def display_status(self):
        if self.status_received is False:
            return
        utc_time = datetime.datetime.utcnow() 
        utc=utc_time.strftime('%H:%M:%S')
        self.status_label.config(text=utc 
        + '   Dial: ' + self.format_freq(self.station_dial) 
        + '   Offset: '+ str(self.station_offset)
        + '   Speed: '+ self.reverse_speed[str(self.station_speed)][:1]
        )

    # make frequency readable!
    def format_freq(self,freq):
        str_freq=str(freq)
        mhz=freq//1000000
        lmhz=len(str(mhz))
        str_mhz= str_freq[0:lmhz]
        str_hkhz = str_freq[lmhz:lmhz+3]
        str_hhz = str_freq[lmhz+3:lmhz+6]
        res=str_mhz+'.'+str_hkhz+' '+str_hhz
        # print (str_mhz,str_hkhz,str_hhz,res)
        return res

    # ==============================
    # GUI
    # ==============================


    def make_gui(self):
        
        # drivers for screen layout
        self.display_width= 800  #pixels
        self.display_height= 440 #pixels
        #rest is in characters
        self.message_width = 31 # message colum in treeview
        self.areas_width = 81 #width of the activity and rx/tx areas.
        self.activity_height=17
        self.rx_height= 14
        self.tx_height= 5
        
        self.roll_width=self.message_width+4
        self.treeview_width = 14+self.message_width #sum of the columns
        self.rxtx_text_width= self.areas_width - self.treeview_width #adjusts automatically with areas width and message_width


        self.style=ttk.Style(self.root)
        self.style.configure('green.TButton', background="green")
        self.style.configure('red.TButton', background="red")
        self.style.configure('red_text.TLabel', foreground="red")
        self.style.configure('green_text.TLabel', foreground="green")
        self.style.configure('TButton', padx=2,pady=2)
        self.style.configure('grey.TButton', background="light grey")
        
        self.root.title('Waiting for Connection to JS8Call')
        self.root.geometry(str(self.display_width) +'x' + str(self.display_height)+'+0+0')
        self.root.resizable(False,False)
        
        # main and status frames
        self.main_frame=ttk.Frame(self.root)
        self.main_frame.grid(column=0, row=0,sticky=tk.W)         
        self.status_frame=ttk.Frame(self.root)
        self.status_frame.grid(column=0, row=1,sticky=tk.W)
                
        # 3 vertical frames in main frame
        # -----------------
        self.left_frame=ttk.Frame(self.main_frame)
        self.left_frame.grid(column=0, row=1,sticky=tk.N)         
        self.mid_frame=ttk.Frame(self.main_frame)
        self.mid_frame.grid(column=1, row=1,sticky=tk.N)  
        self.right_frame=ttk.Frame(self.main_frame)
        self.right_frame.grid(column=2, row=1,sticky=tk.N)
        
        # Left frame - activity and its buttons
        #----------
        # Treview
        columns = ('callsign', 'age', 'snr','message','age_secs','type','frequency','offset','speed','grid','item_id','rolled_message')
        self.col_map={'callsign':0, 'age':1, 'snr':2,'message':3,'age_secs':4,'type':5,'frequency':6,'offset':7,'speed':8,'grid':9,'item_id':10,'rolled_message':11}
        display_columns = ('callsign', 'age', 'snr','rolled_message')
        self.activity = ttk.Treeview(self.left_frame, columns=columns, displaycolumns=display_columns,show='headings',height=self.activity_height,selectmode='browse')
        #s = Style()
        #s.configure('Treeview', rowheight=45)
        # define headings and columns widths
        pix=9
        self.activity.heading('callsign', text='Call')
        self.activity.column('callsign',width=8*pix)
        self.activity.heading('age', text='A')
        self.activity.column('age',width=2*pix)
        self.activity.heading('snr', text='S')
        self.activity.column('snr',width=4*pix,anchor=tk.E)
        self.activity.heading('rolled_message', text='Message')
        self.activity.column('rolled_message',width=self.message_width*pix)
        self.activity.bind('<<TreeviewSelect>>', self.select_activity)
        self.activity.grid(row=0, column=0,pady=(5,0))

        #frame for activity buttons
        self.activity_button_frame= ttk.Frame(self.left_frame)
        self.activity_button_frame.grid(column=0, row=1,sticky=tk.E)
        
        # buttons in the activity button frame
        self.hb_display_enable = tk.IntVar()
        self.hb_checkbutton= ttk.Checkbutton(self.activity_button_frame, text='See HB',variable=self.hb_display_enable)
        self.hb_checkbutton.grid(column=0, row=0,padx=2,pady=2)
        self.hb_display_enable.set(self.initial_hb_enable)   
        self.clear_button = ttk.Button(self.activity_button_frame,text='Clear',command=self.clear_activity)
        self.clear_button.grid(column=1, row=0,padx=2,pady=2)
   
            
        #Mid FRAME - Rx and Tx
        # ---------------------
        
        # Received Text
        self.rx_text = tk.Text(self.mid_frame, width=self.rxtx_text_width, height=self.rx_height,wrap=tk.WORD)
        self.rx_text.grid(column=0, row=0)
        
        # frame for selected buttons
        self.selected_frame=ttk.Frame(self.mid_frame)
        self.selected_frame.grid(column=0, row=1,sticky=tk.W)
        
        # and its buttons
        self.deselect_button= ttk.Button(self.selected_frame,text='Clear',command=self.deselect)
        self.deselect_button.grid(column=0, row=0,pady=2,padx=2)
        
        self.selected_info= ttk.Button(self.selected_frame,text='Nothing Selected',command=self.use_selected_button,state='disabled')
        self.selected_info.grid(column=1, row=0,padx=2,pady=2)
        
        # Transmitted Text
        self.tx_text = tk.Text(self.mid_frame, width=self.rxtx_text_width, height=self.tx_height,wrap=tk.WORD)
        self.tx_text.grid(column=0, row=2)
        
        # send button frame
        self.send_button_frame= ttk.Frame(self.mid_frame)
        self.send_button_frame.grid(column=0, row=3,sticky=tk.E)        
        
        # and its buttons
        self.halt_button = ttk.Button(self.send_button_frame, text='HALT',  command=self.halt,state='disabled')
        self.halt_button.grid(column=0, row=0,padx=2,pady=2)
        self.send_button = tk.Button(self.send_button_frame, text='SEND', command=self.sendit, state='disabled') 
        self.send_button.grid(column=1, row=0,padx=2,pady=2)
        print(self.send_button.winfo_class())
        
        # STATUS FRAME
        #----------
        self.band_button = ttk.Button(self.status_frame, text='BAND',command=self.change_band, state='disabled')
        self.band_button.grid(column=0, row=0,padx=2)
        self.speed_button = ttk.Button(self.status_frame, text='SPEED',command=self.change_speed, state='disabled')
        self.speed_button.grid(column=1, row=0,padx=2)
        self.offset_button = ttk.Button(self.status_frame, text='OFFSET',command=self.change_current_offset, state='disabled')
        self.offset_button.grid(column=2, row=0,padx=2)  
        self.status_label = ttk.Label(self.status_frame, text='Waiting for RIG.STATUS message', width=50)
        self.status_label.grid(column=3, row=0,padx=5)
        self.ptt_label = ttk.Label(self.status_frame, text='PTT', width=10)
        self.ptt_label.grid(column=4, row=0,padx=5)
                
        # RIGHT FRAME
        # macro buttons
        self.make_buttons()
      
        # close button
        self.root.protocol ("WM_DELETE_WINDOW", self.close)

    def show_warning(self,text):
        tkinter.messagebox.showwarning("JS8Touch",text)

    # ==============================
    # LOGGING
    # ==============================
    
    def init_log(self,enabled):
        self.log_enabled=enabled
        self.log_file=open('debug/log.txt','w')


    def log_activity(self,typ,value,params):
        if 'HEARTBEAT' in value:
            pass
            #return
        if typ == 'RX.ACTIVITY':
            self.log('Rx from JS8Call ACTIVITY',params['OFFSET'],'??????',value,gap='above')
        elif typ == 'RX.DIRECTED':
            self.log('Rx from JS8Call DIRECTED',params['OFFSET'],params['FROM'],value,gap='above')
            
    def log (self,*args,gap=''):
        if self.log_enabled:
            text=''
            for arg in args:
                text=text+' '+str(arg)
            if gap =='above':
                print ('\n')
            print('LOG: '+text)
            if gap =='below':
                print ('\n')

            self.log_file.write(text + '\n')
            self.log_file.flush()

    def close_log(self):
        self.log_file.close()





        
    # ==============================
    # FIRST RUN
    # ==============================
    
    # If first time used copy config file from /j8t_resources to /config
    def first_run(self):
        cwd= os.getcwd()
        source_dir=cwd+'/j8t_resources/'
        dest_dir=cwd+'/config/'
        os.mkdir(cwd+'/config')
        self.log('First Run, copying files from ',source_dir,' to' ,dest_dir)
        shutil.copy2(source_dir+'macros.txt',dest_dir)
        shutil.copy2(source_dir+'bands.txt',dest_dir)
        shutil.copy2(source_dir+'speeds.txt',dest_dir)
        shutil.copy2(source_dir+'config.txt',dest_dir)
        self.show_warning('First Run Complete, now edit config/config.text\n and then restart js8touch')
        self.log('First Run Complete, now edit config/config.txt for name and QTH. Then restart JS8Touch')
        exit(0)
        

if __name__ == '__main__':
    g=JS8Touch()
    g.init()
