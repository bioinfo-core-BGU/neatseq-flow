#!/usr/bin/env python                                                          
# -*- coding: UTF-8 -*-

__author__ = "Liron Levin"
__version__ = "1.3"


__affiliation__ = "Bioinformatics Core Unit, NIBN, Ben Gurion University"



""" 
:Neatseq-Flow Monitor
-----------------------

:Authors: Liron Levin
:Affiliation: Bioinformatics core facility
:Organization: National Institute of Biotechnology in the Negev, Ben Gurion University.


SHORT DESCRIPTION
~~~~~~~~~~~~~~~~~~~~~

Neatseq-Flow Monitor can be used to track the progress of running work-flows of a specific project in **real-time**. 

Alternatively Neatseq-Flow Monitor can be used to compare between previous runs of a specific project. 

Neatseq-Flow Monitor uses the information in the Neatseq-Flow log files and information gathered from the cluster scheduler

**Neatseq-Flow** monitor provides the following information:

    * List of available log files for a specific work-flow [project]
    * List of steps and samples as they distribute by the cluster scheduler
    * Steps and samples Start and finished times
    * Number of started and finished jobs
    * Number and identity of the current ruining jobs
    * Step progress bar
    * Color indication for the status of steps and samples
        
Requires
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Neatseq-Flow** Monitor is written in python and requires the following packages that are not included in python 2.7 release:

    * ``pandas``

Parameters that can be set
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. csv-table:: 
    :header: "Parameter", "Values", "Comments"
    :widths: 15, 10, 10

    "-D",  "PATH", "Neatseq-flow project directory [default= current working directory ]"
    "-R","STR","Log file Regular Expression [in ./log/ ] [default=log_[0-9]+.txt$]"
    "--Monitor_RF","FLOAT","Monitor Refresh rate [default=1]"
    "--File_browser_RF","FLOAT","File Browser Refresh rate [default=1]"
    "--Bar_Marker",  "CHAR", "Progress Bar Marker [default=#]"
    "--Bar_Spacer","CHAR","Progress Bar Spacer [default=Space]"
    "--Bar_len","INT","Progress Bar Total Length [in chars] [default=50]"

Comments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note:: **Neatseq Flow** Monitor can be run only after the **Neatseq Flow** script generator is finished successfully [a project is created]


.. tip:: Running ``neatseq_flow_monitor.py`` from the project directory without arguments will use all the default parameters and will show the project available log files.

Help message:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    usage: Neatseq_Flow_Monitor.py  [-h] [-D STR] [-R STR] [--Monitor_RF FLOAT]
                                    [--File_browser_RF FLOAT]
                                    [--Bar_Marker CHAR] [--Bar_Spacer CHAR]
                                    [--Bar_len INT]

    Neatseq-flow Monitor_v1.1 By Liron Levin

    optional arguments:
      -h, --help                show this help message and exit
      -D STR                    Neatseq-flow project directory [default=cwd]
      -R STR                    Log file Regular Expression [in ./log/ ]
                                [default=log_[0-9]+.txt$]
      --Monitor_RF FLOAT        Monitor Refresh rate [default=1]
      --File_browser_RF FLOAT
                                File Browser Refresh rate [default=1]
      --Bar_Marker CHAR         Progress Bar Marker [default=#]
      --Bar_Spacer CHAR         Progress Bar Spacer [default=Space]
      --Bar_len INT             Progress Bar Total Length [in chars] [default=50]


"""





import argparse
import curses
import pandas as pd
import sys, time, os ,re
from datetime import datetime
from multiprocessing import Process, Queue


SCREEN_W     = 200
SCREEN_H     = 100
VERSION      = "v1.3"
PARAM_LIST   = ["Dir"]
__author__   = "Liron Levin"
jid_name_sep = '..'
class nsfgm:
#  Main class for neatseq-flow Log file parser
    #Function for setting the main directory [the pipeline run location]
    def __init__(self,**kwargs):
        
        # Store input parameters
        self.params = kwargs
        if "Dir" not in kwargs :
            sys.exit("You must pass file path")
        self.params["Dir"]=os.path.join(self.params["Dir"],"logs")

    #Function for gathering information about the available log files as Data-Frame
    def file_browser(self,Regular):
        try:
            file_sys=pd.DataFrame()
            # get the available log files names 
            file_sys["Name"]=[x for x in os.listdir(self.params["Dir"]) if len(re.findall(Regular,x))]
            # get the available log files created times
            file_sys["Created"]=[datetime.fromtimestamp(os.path.getctime(os.path.join(self.params["Dir"],x))).strftime('%d/%m/%Y %H:%M:%S') for x in file_sys["Name"]]
            # get the available log files last modified times
            file_sys["Last Modified"]=[os.path.getmtime(os.path.join(self.params["Dir"],x)) for x in file_sys["Name"]]
            file_sys=file_sys.sort_values(by="Last Modified",ascending=False).reset_index(drop=True).copy()
            file_sys["Last Modified"]=[datetime.fromtimestamp(x).strftime('%d/%m/%Y %H:%M:%S') for x in file_sys["Last Modified"]]
            # get the available log files sizes
            file_sys["Size"]=[os.path.getsize(os.path.join(self.params["Dir"],x)) for x in file_sys["Name"]]
           
        except :
            file_sys=pd.DataFrame(columns=["Name","Created","Last Modified","Size"])
        return file_sys

    #Function for getting information from qstat 
    def get_qstat(self):
        import subprocess
        qstat=pd.DataFrame()
        # run qstat and get running information in xml format
        if subprocess.call('type qstat', shell=True, 
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0:
            #xml = os.popen('qstat -xml -u $USER').read()
            xml = os.popen('qstat -xml ').read()
            # extract the jobs names  
            qstat["Job name"]=[re.sub("[</]+JB_name>","",x) for x in re.findall('[</]+JB_name>\S+',xml)]
            # extract the jobs status  
            qstat["State"]=[x.strip('job_list state="') for x in re.findall('job_list state="\w+',xml)]
        return qstat

    # function for generating the progress bar
    def gen_bar(self,Bar_len,Bar_Marker,Bar_Spacer):
        char_value=float(self.logpiv["Finished"].max().total_seconds())/Bar_len
        if char_value==0:
            char_value=1.0/Bar_len
        return [char_value,list(map(lambda x,y: (int(x.total_seconds()/char_value)*Bar_Spacer + ((int(-(-(y.total_seconds()-x.total_seconds())/char_value))+1)*Bar_Marker)).ljust(Bar_len,Bar_Spacer)  ,self.logpiv["Started"],self.logpiv["Finished"]))]
    
    # main function for parsing log file
    def read_run_log(self,runlog_file,Bar_len,Bar_Marker,Bar_Spacer,q=None,Instance=True,read_from_disk=True):
        
        try:
            # read log file to a Data-Frame
            if read_from_disk:
                runlog_Data=pd.read_table(runlog_file,header =4)
                self.LogData=runlog_Data.copy()
            else:
                runlog_Data=self.LogData.copy()
            # If there is a level column: Remove information about high level scripts runs
            if "Level" in runlog_Data.columns:
                runlog_Data=runlog_Data.loc[runlog_Data["Level"]!="high",]
            # If there is a Status column: Convert to OK or ERROR
            if "Status" in runlog_Data.columns:
                runlog_Data['Status']=['OK' if 'OK' in x else 'ERROR' for x in runlog_Data['Status']]
            # Format the Timestamp column
            runlog_Data.Timestamp = [datetime.strptime(x, '%d/%m/%Y %H:%M:%S') for x in runlog_Data.Timestamp]
            runlog_Data['Timestamp2'] = [int(time.mktime(x.timetuple())) for x in runlog_Data.Timestamp]
            # sort the Data-Frame according to the Timestamp column
            runlog_Data=runlog_Data.sort_values(by="Timestamp2",ascending=True).reset_index(drop=True).copy()
            # remove old runs [duplicated jobs names events]
            runlog_Data.drop_duplicates(keep="last",subset=["Job name","Event"],inplace=True)
            # if after the remove duplicated there are old finished jobs of new runs: remove the finished time of these jobs
            args_pivot=['Job name','Event','Timestamp']
            pre_logpiv = runlog_Data.pivot(index=args_pivot[0], columns=args_pivot[1], values=args_pivot[2])

            if "Finished" in pre_logpiv.columns:
                pre_logpiv=pre_logpiv.loc[~pre_logpiv["Finished"].isnull(),]
                log=list(map( lambda x,y: (x in pre_logpiv[pre_logpiv["Finished"]<pre_logpiv["Started"]].index)&(y=="Finished")==False , runlog_Data["Job name"],runlog_Data["Event"] ))
                runlog_Data=runlog_Data[log].copy()

            # for the main window information:    
            if Instance==True:
                args_pivot=['Instance','Event','Timestamp']
            # for the sample window information:  
            else:
                # get the running information from qstat
                qstat=self.get_qstat()
                if len(qstat)>0:
                    runlog_Data=runlog_Data.merge(qstat,how='left')
                    runlog_Data.loc[runlog_Data["State"].isnull(),"State"]=''
                else:
                    runlog_Data["State"]=''
                # get only the data for the chosen step
                runlog_Data=runlog_Data.loc[runlog_Data["Instance"]==Instance,].copy()
                # change the names of the jobs to the samples names
                runlog_Data['Job name']=list(map(lambda x,y,z: re.sub("^"+y+jid_name_sep+z+jid_name_sep,"",re.sub(jid_name_sep+"[0-9]+$","",x)) ,runlog_Data['Job name'],runlog_Data['Module'],runlog_Data['Instance'] ))
                args_pivot=['Job name','Event','Timestamp']
                # generate a pivot table
                logpiv = runlog_Data.pivot(index=args_pivot[0], columns=args_pivot[1], values=args_pivot[2])
                # make sure the Finished column exist
                if "Finished" not in logpiv.columns:
                      logpiv["Finished"]=''
                # convert Nan to empty sring
                #logpiv[logpiv.isnull()]=''
                logpiv=logpiv.sort_values("Finished")
                # generate the items Data-Frame
                self.items=pd.DataFrame()
                self.items['Samples']=[str(x) for x in logpiv.index.values]
                self.items['Started']=[str(x) for x in logpiv['Started']]
                self.items['Finished']=[str(x) if str(x)!="NaT" else '' for x in logpiv['Finished']]
                self.items['Host']=[str(list(runlog_Data.loc[runlog_Data['Job name']==x,'Host'])[0]) for x in logpiv.index.values]
                #self.items['Memory']=[str(max(list(runlog_Data.loc[runlog_Data['Job name']==x,'Max mem']))) for x in logpiv.index.values]
                self.items['Running?']=[str(list(runlog_Data.loc[runlog_Data['Job name']==x,'State'])[0]) for x in logpiv.index.values]                
                
                #mark un-Finished samples
                self.rowmode=[2 if x =='' else 1 for x in self.items['Finished']]
                self.rowmode=list(map(lambda x,y: 3 if len(y)>0  else x,self.rowmode,self.items['Running?']))
                self.items['Running?']=[x  if len(x)>0  else "No" for x in self.items['Running?']]
                
                # If there is a Status column: Display the samples status
                if "Status" in runlog_Data.columns:
                    self.items['Status']=[str(list(runlog_Data.loc[(runlog_Data['Job name']==x)&(runlog_Data['Event']=='Finished'),'Status'])).replace('[','').replace(']','').replace("'",'') for x in logpiv.index.values]
                    #mark samples with ERRORs
                    self.rowmode=list(map(lambda x,y: 2 if 'ERROR' in x else y, self.items['Status'],self.rowmode))
                    
                if q!=None:
                    q.put(self)
                return 
            # group all jobs by Instance and event to lists of Timestamps 
            logpiv=runlog_Data.groupby([args_pivot[0],args_pivot[1]])[args_pivot[2]].apply(list).reset_index()
            # generate a pivot table
            logpiv = logpiv.pivot(index=args_pivot[0], columns=args_pivot[1], values=args_pivot[2])
            # make sure the Finished column exist
            if "Finished" not in logpiv.columns:
                logpiv["Finished"]=''
            # convert Nan to empty sring
            logpiv[logpiv.isnull()]=''
            # make a copy of the Finished column
            logpiv["temp_Finished"]=logpiv["Finished"]
            # count how many jobs started
            N_Started=logpiv.applymap(lambda x:len(x))["Started"]
            # count how many jobs Finished
            N_Finished=logpiv.applymap(lambda x:len(x))["Finished"]
            
            # get the running information from qstat and add the information to the Data-Frame
            qstat=self.get_qstat()
            if len(qstat)>0:
                runlog_Data=runlog_Data.merge(qstat,how='left')
                runlog_Data.loc[runlog_Data["State"].isnull(),"State"]=''
            else:
                runlog_Data["State"]=''
            logpiv=logpiv.join(runlog_Data.groupby("Instance")["State"].apply(lambda x:list(x).count("running")),how="left", rsuffix='running')            

            # set the Timestamps of instances with no Finished jobs and are still running to the current time [for calculating the progress bar]
            logpiv["Finished"]=list(map(lambda x,y,z: {datetime.strptime(str(datetime.now().strftime('%d/%m/%Y %H:%M:%S')), '%d/%m/%Y %H:%M:%S')} if (x=='')&(y>0) else z if (x=='') else x ,logpiv["Finished"],logpiv["State"].values,logpiv["Started"] ))
            #logpiv.loc[logpiv["Finished"]=='',"Finished"]={datetime.strptime(str(datetime.now().strftime('%d/%m/%Y %H:%M:%S')), '%d/%m/%Y %H:%M:%S')}
            # find the earliest Timestamps of every instances
            Started=[min(x) for x in logpiv["Started"]]
            # find the latest Timestamps of every instances
            Finished=[max(x) for x in logpiv["Finished"]]
            # Add the new information in the pivot table
            logpiv["Started"]=Started
            logpiv["Finished"]=Finished
            logpiv["#Started"]=N_Started
            logpiv["#Finished"]=N_Finished
            # sort the pivot table by the earliest Timestamps
            logpiv=logpiv.sort_values("Started")
            # calculate the total time for each instances
            logpiv_diff=pd.DataFrame()
            logpiv_diff["Started"]=logpiv["Started"]-logpiv["Started"].min()
            logpiv_diff["Finished"]=logpiv["Finished"]-logpiv["Started"].min()
            self.logpiv=logpiv_diff
            # generate the progress bar column
            [char_value,bar]=self.gen_bar(Bar_len,Bar_Marker,Bar_Spacer)
            Runs_str="Progress #=" + str(char_value)+"seconds"
            # generate the items Data-Frame to show in the window
            self.items =pd.DataFrame()
            # # Make sure the instances names are no longer then 20 chars
            # self.items["Steps"]=map(lambda x:x[:20],logpiv.index.values)
            self.items["Steps"]=[x for x in logpiv.index.values]
            self.items[Runs_str]=bar
            self.items["Started"]=[str(x) for x in logpiv["Started"]]
            # Show the finished Timestamps for only instances with finished jobs
            self.items["Finished"]=list(map(lambda x,y: str(x) if y!='' else '',logpiv["Finished"],logpiv["temp_Finished"]))
            self.items["#Started"]=[str(x) for x in logpiv["#Started"]]
            self.items["#Finished"]=[str(x) for x in logpiv["#Finished"]]
            self.items["#Running"]=logpiv["State"].values
            
            # Set the lines colour mode
            self.rowmode=logpiv["#Started"]-logpiv["#Finished"]  
            self.rowmode=[2 if x > 0 else 1 for x in self.rowmode]
            self.rowmode=list(map(lambda x,y: 3 if (y >0)&(x==2) else x,self.rowmode, self.items["#Running"]))
            
            # If there is a Status column: Display the steps status error count
            if "Status" in runlog_Data.columns:
                logpiv=logpiv.join(runlog_Data.groupby("Instance")["Status"].apply(lambda x:list(x).count("ERROR")),how="left", rsuffix='ERROR')
                self.items["#ERRORs"]=logpiv["Status"].values
                self.rowmode=list(map(lambda x,y: 2 if x>0 else y, self.items["#ERRORs"],self.rowmode))
            
        except : #ValueError:
            if Instance==True:
                self.items=pd.DataFrame(columns=["Steps","Progress","Started","Finished","#Started","#Finished","#Running"])
            else:
                self.items=pd.DataFrame(columns=["Samples","Started","Finished","Host","Memory","Running?"])
            self.rowmode=[]
            
        # if this function is running in a sub-process store the results in the queue
        if q!=None:
           q.put(self)




class window(object):                                                          
#a class for window generating and displaying of pandas Data-Frame
    # function for initializing the window (will not display the window)
    def __init__(self, stdscreen,x,y,max_line_size_,col_size_,main_window_lines=500,refreshrate=0.7,header_line_size_=2):
        # the screen window
        self.screen=stdscreen
        # last update time [for now it is the creation time]
        self.time=time.time()
        # the window refresh-rate
        self.refreshrate=refreshrate
        # the number of maximal lines that will be displayed in the window at a given time 
        self.max_line_size_=max_line_size_
        # the number of maximal chars that will be displayed in the window at a given time 
        self.col_size_=col_size_
        # the X location of the most upper-left corner of the window
        self.x=x
        # the Y location of the most upper-left corner of the window
        self.y=y
        # generating and initializing the main data window
        self.window = curses.newpad(main_window_lines,self.col_size_*10)                                  
        # generating and initializing the header window
        self.header_line_size_=header_line_size_
        self.hwindow=curses.newpad(self.header_line_size_,self.col_size_*10)
        # generating and initializing the bottom part of the window
        self.xwindow=curses.newpad(self.header_line_size_,self.col_size_*10)
        #reset the window
        self.clear()
        # Indicator if the window is active 
        self.active=True
        self.id=None

        
    # a function for changing the highlighted line in the window 
    def navigate(self, n):                                                   
        self.position += n                                                   
        if self.position < 0:                                                
            self.position = 0                                                
        elif self.position >= len(self.items):                               
            self.position = len(self.items)-1 
        # change the id to the current highlighted line first column cell
        if len(self.items)>0:
            self.id=list(self.items[self.items.columns[0]])[self.position]
    
    # a function for changing the highlighted line in the window 
    def navigate_sideway(self, n):                                                   
        self.side_position += n                                                   
        if self.side_position < 0:                                                
            self.side_position = 0                                                
        elif self.side_position+self.col_size_>= self.max_width:
            self.side_position -=n 
    
    # a function for clearing the window
    def clear(self):
        # the current starting view in the window
        self.side_position=0
        # the width of the window
        self.max_width = 0
        # the current highlighted line in the window
        self.position = 0
        # the number of lines of data in pandas Data-Frame
        self.len_items=0
        # the choice made by the user [-1 = No choice, -2 = exit the program , positive number = line number chosen by the user]
        self.choice=-1
        # the page number of the current lines that being displayed
        self.page=0
        # No items in the window
        self.items=pd.DataFrame(columns=["              Loading...  Please wait              "])
        self.screen.redrawwin()
        self.id=None
        
    # the main display function for the window
    def display(self):
        # set the colour of the window according to the active/not-active state
        if self.active:
            default_color=curses.color_pair(4)  
        else:
            default_color=curses.color_pair(0) 
        #if the size of the pandas Data-Frame has changed initialize the window graphics and the highlighted line position
        if self.len_items!=len(self.items):
            self.position = 0
            self.page = 0
            self.len_items=len(self.items)
            self.screen.redrawwin()
        # if the id is found in the first column of the data-frame change the highlighted position (and the page count) to the id line
        if (self.id!=None)&(len(self.items)>0):
            if self.id in list(self.items[self.items.columns[0]]):
                self.position=list(self.items[self.items.columns[0]]).index(self.id)
                self.page = int(self.position/self.line_size_)
        if len(self.items)>0:
        # change the id to the current highlighted line first column cell
            self.id=list(self.items[self.items.columns[0]])[self.position]
        else:
            self.id=None
        # do not wait for user input
        self.screen.nodelay(1)
        # if the Data-Frame has less lines than the max lines to display: show only the number of lines in the Data-Frame 
        if len(self.items)<=self.max_line_size_:
            self.line_size_=len(self.items)+1
        else:
            self.line_size_=self.max_line_size_
        # set the maximal width [in chars] of each column in the Data-Frame 
        col_max=self.items.copy()
        col_max.ix["columns"]=col_max.columns
        col_max=col_max.applymap(lambda x:len(str(x)))
        col_max=col_max.max(0)
        
        # Display the header of the window [the Data-Frame columns names] and the upper frame of the window
        count=0
        for col in self.items.columns:
            msg = '| %s |' % ( col.center(col_max[col]) ) 
            try:
                # Display the columns names [ Centered ]
                self.hwindow.addstr(0, count, msg, default_color )
                # Display the upper frame of the window
                self.hwindow.addstr(1, count, "|"+"-"*(len(msg)-2)+"|", default_color )
                count=count+len(msg)
            except curses.error:
                pass 
                
        # If the width of the old window is greater the the current one redraw it 
        if self.max_width!= count :
            self.screen.redrawwin()
        self.max_width=count
        if self.col_size_>self.max_width:
            self.optimal_with=self.max_width-1
        else:
            self.optimal_with=self.col_size_
       
        # make sure the screen size is fixed before printing to the screen 
        curses.resize_term(SCREEN_H,SCREEN_W)
        # updating the virtual screen [header and upper frame] 
        self.hwindow.noutrefresh(0,0+self.side_position,self.y,self.x,self.y+self.header_line_size_,self.x+self.optimal_with) #self.col_size_)

        # Display the main Data of the window [the Data-Frame lines], the main frame of the window and the current highlighted line
        for index in range(self.line_size_*(self.page+1)):                         
            count=0
            for col in self.items.columns:
                # Display line information in the specific column
                if index<len(self.items):
                    msg = ' %s ' % ( str(self.items.loc[index,col]).ljust(col_max[col]))
                    # set the current line display mode [ if the line is the highlighted line or not]
                    if index == self.position:                                   
                        mode = curses.color_pair(self.rowmode[index]+10)
                    else:
                        mode=curses.color_pair(self.rowmode[index]) | curses.A_BOLD
                    if self.rowmode[index]>5:
                        mode=mode | curses.A_BLINK          
                # Display empty lines for the remaining of the page
                else:
                    msg = ' %s ' % ( " ".ljust(col_max[col]))
                    mode=default_color
                try:
                    # Display the main window frame 
                    self.window.addch(index, count, "|", default_color)
                    # Display the columns content [left justified]
                    self.window.addstr(index, count+1, msg, mode)
                    count=count+len(msg)+2
                    # Display the main window frame 
                    self.window.addch(index, count-1, "|", default_color)
                except curses.error:
                    pass 
        
        # make sure the screen size is fixed before printing to the screen 
        curses.resize_term(SCREEN_H,SCREEN_W)
        # updating the virtual screen [the main Data-Frame lines of to the current page] 
        self.window.noutrefresh(self.line_size_*self.page,0+self.side_position,self.y+self.header_line_size_,self.x,self.y+self.line_size_+1,self.x+self.optimal_with) #self.col_size_)
        
        # Display the bottom frame of the window
        count=0
        for col in self.items.columns:
            msg = '| %s |' % ( col.center(col_max[col]) ) 
            try:
                self.xwindow.addstr(0, count, "|"+"-"*(len(msg)-2)+"|", default_color )
                count=count+len(msg)
            except curses.error:
                pass 
       
        # make sure the screen size is fixed before printing to the screen 
        curses.resize_term(SCREEN_H,SCREEN_W)
        # updating the virtual screen [bottom frame of the window]
        self.xwindow.noutrefresh(0,0+self.side_position,self.y+self.header_line_size_+self.line_size_,self.x,self.y+self.header_line_size_+self.line_size_+self.header_line_size_,self.x+self.optimal_with) #self.col_size_)
        
        # updating the real screen 
        curses.doupdate()
        
        # if the current window is active
        if self.active:
            #get user input
            key = self.screen.getch()                                        
            #if the user changed the screen size  
            if key ==curses.KEY_RESIZE: 
                # set it beck the the fixed size 
                curses.resize_term(SCREEN_H,SCREEN_W)
            #if the user hit the TAB key  
            elif key == ord('\t'):
                #set the current window as not active and return that no choice was made
                self.active=False
                self.choice=-1
                return self.choice
            #if the user hit the ENTER key  
            elif key== ord("\n"):
                if len(self.items)>0:
                    #return the current highlighted line
                    self.choice=self.position
                    return self.choice
            #if the user hit the UP key  
            elif key == curses.KEY_UP:
                #change the new highlighted line [if possible] and change the current display page [if necessary ]
                self.navigate(-1)
                if self.position<self.line_size_*self.page: 
                    self.page=self.page-1
            #if the user hit the DOWN key
            elif key == curses.KEY_DOWN: 
                #change the new highlighted line [if possible] and change the current display page [if necessary ]
                self.navigate(1) 
                if self.position>=(self.line_size_*(self.page+1)):     
                    self.page=self.page+1
            #change the view of the window
            elif key == curses.KEY_LEFT:
                #change the new highlighted line [if possible] and change the current display page [if necessary ]
                self.navigate_sideway(-1)
                
            elif key == curses.KEY_RIGHT:
                #change the view of the window
                self.navigate_sideway(1)
                
            #if the user hit the Esc key
            elif key == 27:
                #return exit choice and clear the screen
                self.choice=-2
                self.screen.clear()
                return self.choice
        #return the default: No choice
        self.choice=-1
        return self.choice
        
        


class neatseq_flow_monitor(object):                                                         
#main program
    def __init__(self,stdscreen,args):
        sample_menu_flag=-1
        sample_menu_active=False
        #initializing the main monitor/qstat log file parser module
        mynsfgm = nsfgm(Dir=args.directory)
        #initializing the graphics
        self.screen = curses.initscr() 
        #setting screen size
        curses.resize_term(SCREEN_H,SCREEN_W)
        curses.curs_set(0) 
        curses.start_color()
        curses.has_colors()
        #setting colour combinations for normal mode
        curses.init_pair(1, curses.COLOR_GREEN, curses.A_NORMAL)
        curses.init_pair(2, curses.COLOR_RED, curses.A_NORMAL)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.A_NORMAL)
        curses.init_pair(5, curses.COLOR_MAGENTA, curses.A_NORMAL)
        curses.init_pair(4, curses.COLOR_CYAN, curses.A_NORMAL)
        curses.init_pair(6, curses.COLOR_BLUE , curses.A_NORMAL) 
        #setting colour combinations for highlight mode 
        curses.init_pair(11, curses.COLOR_GREEN, curses.COLOR_BLUE)
        curses.init_pair(12, curses.COLOR_RED, curses.COLOR_BLUE)
        curses.init_pair(13, curses.COLOR_YELLOW, curses.COLOR_BLUE)
        curses.init_pair(15, curses.COLOR_MAGENTA, curses.COLOR_BLUE)
        curses.init_pair(14, curses.COLOR_CYAN, curses.COLOR_BLUE)
        curses.init_pair(16, curses.COLOR_BLUE , curses.COLOR_BLUE) 
        #writing to screen general information
        self.screen.addstr(2,2, "Neatseq Flow Monitor "+VERSION+" By Liron Levin", curses.color_pair(3) )
        self.screen.addstr(3,2, "TAB To Jump between windows", curses.color_pair(5) )
        self.screen.addstr(4,2, "ESC To Exit", curses.color_pair(5) )
        #initializing file browser window 
        file_menu = window(self.screen,2,7,5,120,200,args.File_browser_RF)
        sample_menu = window(self.screen,2,32,5,140,2000,args.Monitor_RF)
        sample_menu.active=False
        sample_menu_flag=True
        sample_menu_first_time=True
        #get list of log files and information about them
        file=mynsfgm.file_browser(args.Regular)
        #transfer the log files list and rows colour mode list to the file browser window
        file_menu.items=file
        file_menu.rowmode=[1]*len(file)
        #initialize parallel queue
        q = Queue()
        q2 = Queue()
        #first main loop
        while True:
            #test if to update the file browser data
            if time.time()-file_menu.time>=file_menu.refreshrate:
                #update the list of log files and information about them
                file=mynsfgm.file_browser(args.Regular)
                #transfer the log files list and rows colour mode list to the file browser window
                file_menu.items=file
                file_menu.rowmode=[1]*len(file)
                #update the file browser window last update time
                file_menu.time=time.time()
            #display the file browser window on screen
            file_menu.display()
            #if the user used the Esc Key exit
            if file_menu.choice==-2:
                #exit()
                return None
            #keep the file browser window active if the user did not choose a file
            elif file_menu.choice==-1:
                file_menu.active=True
            #if the user selected one of log files   
            elif file_menu.choice>=0:
                #make the file browser window not active
                file_menu.active=False
                #initializing main window 
                main_menu = window(self.screen,2,17,10,170,200,args.Monitor_RF)
                #get the information from the log file and qstat via a sub-process
                runlog_file=os.path.join(mynsfgm.params["Dir"],file_menu.items.loc[file_menu.choice,"Name"])
                p1 = Process(target=mynsfgm.read_run_log, args=(runlog_file,args.Bar_len,args.Bar_Marker,args.Bar_Spacer,q))
                p1.start() 
                #since it is the first load of the data wait to the results
                mynsfgm=q.get(True)
                p1.join()
                #transfer the log file, qstat and row colour mode data to the main window
                main_menu.items=mynsfgm.items
                main_menu.rowmode=mynsfgm.rowmode
                #update the main window last update time
                main_menu.time=time.time()
                #set a flag for sending data update sub-process [no more then one process at a time]
                flag=True
                #second main loop
                while True: 
                    #test if to update the main window data
                    if time.time()-main_menu.time>=main_menu.refreshrate:
                        if flag:
                           #run the function that get the information from the log file and qstat via a sub-process
                           p1 = Process(target=mynsfgm.read_run_log, args=(runlog_file,args.Bar_len,args.Bar_Marker,args.Bar_Spacer,q))
                           p1.start()
                           #don't send another process while it is running
                           flag=False
                    #if there is data in the queue [the sub-process is finished]
                    if q.empty()==False:
                        #get the information from the sub-process
                        mynsfgm=q.get(True)
                        p1.join()
                        #transfer the log file, qstat and row colour mode data to the main window
                        main_menu.items=mynsfgm.items
                        main_menu.rowmode=mynsfgm.rowmode
                        #update the main window last update time
                        main_menu.time=time.time()
                        #it is OK to run a new sub-process
                        flag=True
                    #display the main window on screen
                    main_menu.display()
                    #if the main window is not active set the file browser window as active
                    if (main_menu.active==False) and (sample_menu.active==False):
                       file_menu.active=True
                    #test if to update the file browser data
                    if time.time()-file_menu.time>=file_menu.refreshrate:
                        #update the list of log files and information about them
                        file=mynsfgm.file_browser(args.Regular)
                        #transfer the log files list and rows colour mode list to the file browser window
                        file_menu.items=file
                        file_menu.rowmode=[1]*len(file)
                        #update the file browser window last update time
                        file_menu.time=time.time()
                    #display the file browser window on screen
                    file_menu.display()
                    #if the user selected one of log files 
                    if file_menu.choice>=0:
                        #make the file browser window not active
                        file_menu.active=False
                        #make the main window active
                        main_menu.active=True 
                        #if a sub-process is running wait for it to finish
                        if flag==False:
                            mynsfgm=q.get(True)
                            p1.join()
                            flag=True
                        #get the information from the log file and qstat
                        runlog_file=os.path.join(mynsfgm.params["Dir"],file_menu.items.loc[file_menu.choice,"Name"])
                        mynsfgm.read_run_log(runlog_file,args.Bar_len,args.Bar_Marker,args.Bar_Spacer)
                        #transfer the log file, qstat and row colour mode data to the main window
                        main_menu.items=mynsfgm.items
                        main_menu.rowmode=mynsfgm.rowmode
                        #update the main window last update time
                        main_menu.time=time.time()
                        
                    # if the user choose a step to display
                    if main_menu.choice>=0:
                        #which step was chosen
                        instances=main_menu.items.loc[main_menu.choice,main_menu.items.columns[0]]
                        # set the sample window active
                        sample_menu.active=True
                        # set the main window as not active
                        main_menu.active=False
                        
                    # if the sample window is active
                    if sample_menu.active==True:    
                        #test if to update the sample window data
                        if (time.time()-sample_menu.time>=sample_menu.refreshrate)| (sample_menu_first_time):
                            #is it OK to run a sub-process?
                            if sample_menu_flag:
                                #run the function that get the samples information of the chosen step from the log file
                                p2 = Process(target=mynsfgm.read_run_log, args=(runlog_file,args.Bar_len,args.Bar_Marker,args.Bar_Spacer,q2,instances))
                                p2.start()
                                # it is now not OK to run a sub-process
                                sample_menu_flag=False
                                if sample_menu_first_time:
                                    # the sample window is now marked as displayed [it is not displayed yet]
                                    sample_menu_first_time=False
                                
                        #if there is data in the queue [the sub-process is finished]
                        if q2.empty()==False:
                            #get the information from the sub-process
                            sample_menu_mynsfgm=q2.get(True)
                            p2.join()
                            #transfer the log file sample information and row colour mode data to the sample window
                            sample_menu.items=sample_menu_mynsfgm.items
                            sample_menu.rowmode=sample_menu_mynsfgm.rowmode
                            #update the sample window last update time
                            sample_menu.time=time.time()
                            #it is OK to run a new sub-process
                            sample_menu_flag=True
                            
                            
                        
                        #display the sample window on screen [now it is displayed]
                        sample_menu.display()
                        # if the sample window is no longer active 
                        if (sample_menu.active==False):
                            # activate the main window
                            main_menu.active=True
                            # clear the sample window
                            sample_menu.clear()
                            # mark the sample window as not displayed
                            sample_menu_first_time=True
                            sample_menu_flag=True
                            if p2.is_alive():
                                # while q2.empty()!=False:
                                    # pass
                                temp=q2.get(True)
                                p2.join()
                            
                            
                        #if the user used the Esc Key exit    
                        if (sample_menu.choice==-2):
                            #if a sub-process is running wait for it to finish before exiting
                            if p2.is_alive():
                                q2.get(True)
                                p2.join()
                            # transfer the exit message to the main window 
                            main_menu.choice=-2
                        
                    #if the user used the Esc Key exit
                    if (file_menu.choice==-2)|(main_menu.choice==-2):
                        #if a sub-process is running wait for it to finish before exiting
                        if p1.is_alive():
                            q.get(True)
                            p1.join()
                        #exit()
                        return None
if __name__ == '__main__':
#getting arguments from the user                                                       
    parser = argparse.ArgumentParser(description='Neatseq-flow Monitor'+VERSION+' By Liron Levin ')
    parser.add_argument('-D', dest='directory',metavar="STR", type=str,default=os.getcwd(),
                        help='Neatseq-flow project directory [default=cwd]')
    parser.add_argument('-R', dest='Regular',metavar="STR" , type=str,default="log_[0-9]+.txt$",
                        help='Log file Regular Expression [in ./logs/ ] [default=log_[0-9]+.txt$]')
    parser.add_argument('--Monitor_RF',metavar="FLOAT", type=float,dest='Monitor_RF',default=1,
                        help='Monitor Refresh rate [default=1]')
    parser.add_argument('--File_browser_RF',metavar="FLOAT", type=float,dest='File_browser_RF',default=1,
                        help='File Browser Refresh rate [default=1]')
    parser.add_argument('--Bar_Marker',metavar="CHAR",type=str,dest='Bar_Marker',default="#",
                        help='Progress Bar Marker [default=#]')
    parser.add_argument('--Bar_Spacer',metavar="CHAR",type=str,dest='Bar_Spacer',default=" ",
                        help='Progress Bar Spacer [default=Space]')
    parser.add_argument('--Bar_len',metavar="INT",type=int,dest='Bar_len',default=40,
                        help='Progress Bar Total Length [in chars] [default=40]')
    args = parser.parse_args()
    #Ruining main function
    curses.wrapper(neatseq_flow_monitor,args)