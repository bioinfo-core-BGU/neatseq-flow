#!/usr/bin/env python2                                                       


import argparse
import curses
import pandas as pd
import sys, time, os ,re
from datetime import datetime
from multiprocessing import Process, Queue

PARAM_LIST = ["Dir"]


__author__ = " Liron Levin"

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
            file_sys["Name"]=filter(lambda x:len(re.findall(Regular,x)) ,os.listdir(self.params["Dir"]))
            # get the available log files created times
            file_sys["Created"]=map(lambda x: datetime.fromtimestamp(os.path.getctime(os.path.join(self.params["Dir"],x))).strftime('%d/%m/%Y %H:%M:%S')  ,file_sys["Name"])
            # get the available log files last modified times
            file_sys["Last Modified"]=map(lambda x: datetime.fromtimestamp(os.path.getmtime(os.path.join(self.params["Dir"],x))).strftime('%d/%m/%Y %H:%M:%S')  ,file_sys["Name"])
            # get the available log files sizes
            file_sys["Size"]=map(lambda x: os.path.getsize(os.path.join(self.params["Dir"],x))  ,file_sys["Name"])
        except :
            file_sys=pd.DataFrame(columns=["Name","Created","Last Modified","Size"])
        return file_sys

    #Function for getting information from qstat 
    def get_qstat(self):
       qstat=pd.DataFrame()
       # run qstat and get running information in xml format 
       xml=os.popen('qstat -xml -u $USER').read()
       # extract the jobs names  
       qstat["Job name"]=map(lambda x:x.strip('JB_name>').strip("</") , re.findall('JB_name>\S+',xml))
       # extract the jobs status  
       qstat["State"]=map(lambda x:x.strip('job_list state="') , re.findall('job_list state="\w+',xml))
       return qstat

    # function for generating the progress bar
    def gen_bar(self,Bar_len,Bar_Marker,Bar_Spacer):
        char_value=float(self.logpiv["Finished"].max().total_seconds())/Bar_len
        return [char_value,map(lambda x,y: (int(x.total_seconds()/char_value)*Bar_Spacer + (int(-(-(y.total_seconds()-x.total_seconds())//char_value))*Bar_Marker)).ljust(Bar_len,Bar_Spacer)  ,self.logpiv["Started"],self.logpiv["Finished"])]
    
    # main function for parsing log file
    def read_run_log(self,runlog_file,Bar_len,Bar_Marker,Bar_Spacer,q=None,read_from_disk=True):
        
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
            # Format the Timestamp column
            runlog_Data.Timestamp = map(lambda x: datetime.strptime(x, '%d/%m/%Y %H:%M:%S'),runlog_Data.Timestamp) 
            # sort the Data-Frame according to the Timestamp column
            runlog_Data.sort_values(by="Timestamp",inplace=True)
            # remove old runs [duplicated jobs names events]
            runlog_Data.drop_duplicates(keep="last",subset=["Job name","Event"],inplace=True)
            # if after the remove duplicated there are old finished jobs of new runs: remove the finished time of these jobs
            args_pivot=['Job name','Event','Timestamp']
            pre_logpiv = runlog_Data.pivot(index=args_pivot[0], columns=args_pivot[1], values=args_pivot[2])
            if "Finished" in pre_logpiv.columns:
                pre_logpiv=pre_logpiv.loc[~pre_logpiv["Finished"].isnull(),]
                log=map( lambda x,y: (x in pre_logpiv[pre_logpiv["Finished"]<pre_logpiv["Started"]].index)&(y=="Finished") , runlog_Data["Job name"],runlog_Data["Event"] )
                runlog_Data.loc[log,"Finished"]=""
           
            args_pivot=['Instance','Event','Timestamp']
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
            # set the Timestamps of instances with no Finished jobs to the current time [for calculating the progress bar]
            logpiv.loc[logpiv["Finished"]=='',"Finished"]={datetime.strptime(str(datetime.now().strftime('%d/%m/%Y %H:%M:%S')), '%d/%m/%Y %H:%M:%S')}
            # find the earliest Timestamps of every instances
            Started=map(lambda x:min(x),logpiv["Started"])
            # find the latest Timestamps of every instances
            Finished=map(lambda x:max(x),logpiv["Finished"])
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
            # get the running information from qstat
            qstat=self.get_qstat()
            if len(qstat)>0:
                runlog_Data=runlog_Data.merge(qstat,how='left')
                runlog_Data.loc[runlog_Data["State"].isnull(),"State"]=''
            else:
                runlog_Data["State"]=''
            logpiv=logpiv.join(runlog_Data.groupby("Instance")["State"].apply(lambda x:list(x).count("running")),how="left", rsuffix='running')            
            # generate the items Data-Frame to show in the window
            self.items =pd.DataFrame()
            # Make sure the instances names are no longer then 20 chars
            self.items["Jobs"]=map(lambda x:x[:20],logpiv.index.values)
            self.items[Runs_str]=bar
            self.items["Started"]=map(lambda x: str(x),logpiv["Started"])
            # Show the finished Timestamps for only instances with finished jobs
            self.items["Finished"]=map(lambda x,y: str(x) if y!='' else '',logpiv["Finished"],logpiv["temp_Finished"])
            self.items["#Started"]=map(lambda x: str(x),logpiv["#Started"])
            self.items["#Finished"]=map(lambda x: str(x),logpiv["#Finished"])
            self.items["#Running"]=logpiv["State"].values
            # Set the lines colour mode
            self.rowmode=logpiv["#Started"]-logpiv["#Finished"]  
            self.rowmode=map(lambda x: 2 if x > 0 else 1,self.rowmode)
            self.rowmode=map(lambda x,y: 3 if (y >0)&(x==2) else x,self.rowmode, self.items["#Running"])
        except :
            self.items=pd.DataFrame(columns=["Jobs","Progress","Started","Finished","#Started","#Finished","#Running"])
            self.rowmode=[]
        # if this function is running in a sub-process store the results in the queue
        if q!=None:
           q.put(self)




class window(object):                                                          
#a class for window generating and displaying of pandas Data-Frame
    # function for initializing the window (will not display the window)
    def __init__(self, stdscreen,x,y,max_line_size_,col_size_,refreshrate=0.7,header_line_size_=2):
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
        # the page number of the current lines that being displayed
        self.page=0
        # generating and initializing the main data window
        self.window = curses.newpad(500,self.col_size_*2)                                  
        self.window.clear() 
        # generating and initializing the header window
        self.header_line_size_=header_line_size_
        self.hwindow=curses.newpad(self.header_line_size_,self.col_size_*2)
        self.hwindow.clear()
        # generating and initializing the bottom part of the window
        self.xwindow=curses.newpad(self.header_line_size_,self.col_size_*2)
        self.xwindow.clear()
        # the current highlighted line in the window
        self.position = 0
        # the number of lines of data in pandas Data-Frame
        self.len_items=0
        # the choice made by the user [-1 = No choice, -2 = exit the program , positive number = line number chosen by the user]
        self.choice=-1
        # Indicator if the window is active 
        self.active=True
        
    # a function for changing the highlighted line in the window 
    def navigate(self, n):                                                   
        self.position += n                                                   
        if self.position < 0:                                                
            self.position = 0                                                
        elif self.position >= len(self.items):                               
            self.position = len(self.items)-1                                
    

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
            self.len_items=len(self.items)
            self.screen.redrawwin()
            self.screen.refresh()
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
        # make sure the screen size is fixed before printing to the screen 
        curses.resize_term(100,200)
        # updating the virtual screen [header and upper frame] 
        self.hwindow.noutrefresh(0,0,self.y,self.x,self.y+self.header_line_size_,self.x+count-1)

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
        curses.resize_term(100,200)
        # updating the virtual screen [the main Data-Frame lines of to the current page] 
        self.window.noutrefresh(self.line_size_*self.page,0,self.y+self.header_line_size_,self.x,self.y+self.line_size_+1,self.x+count-1)
        
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
        curses.resize_term(100,200)
        # updating the virtual screen [bottom frame of the window]
        self.xwindow.noutrefresh(0,0,self.y+self.header_line_size_+self.line_size_,self.x,self.y+self.header_line_size_+self.line_size_+self.header_line_size_,self.x+count-1)
        
        # updating the real screen 
        curses.doupdate()

        # if the current window is active
        if self.active:
            #get user input
            key = self.screen.getch()                                        
            #if the user changed the screen size  
            if key ==curses.KEY_RESIZE: 
                # set it beck the the fixed size 
                curses.resize_term(100,200)
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
        #initializing the main monitor/qstat log file parser module
        mynsfgm = nsfgm(Dir=args.directory)
        #initializing the graphics
        self.screen = curses.initscr() 
        #setting screen size
        curses.resize_term(100,200)
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
        self.screen.addstr(2,2, "Neatseq Flow Monitor v1.0 By Liron Levin", curses.color_pair(3) )
        self.screen.addstr(3,2, "TAB To Jump between windows", curses.color_pair(5) )
        self.screen.addstr(4,2, "ESC To Exit", curses.color_pair(5) )
        #initializing file browser window 
        file_menu = window(self.screen,2,7,10,170,args.File_browser_RF)
        #get list of log files and information about them
        file=mynsfgm.file_browser(args.Regular)
        #transfer the log files list and rows colour mode list to the file browser window
        file_menu.items=file
        file_menu.rowmode=[1]*len(file)
        #initialize parallel queue
        q = Queue()
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
                exit()
            #keep the file browser window active if the user did not choose a file
            elif file_menu.choice==-1:
                file_menu.active=True
            #if the user selected one of log files   
            elif file_menu.choice>=0:
                #make the file browser window not active
                file_menu.active=False
                #initializing main window 
                main_menu = window(self.screen,2,22,30,170,args.Monitor_RF)
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
                        #it is OK to send a new sub-process
                        flag=True
                    #display the main window on screen
                    main_menu.display()
                    #if the main window is not active set the file browser window as active
                    if main_menu.active==False:
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
                    #if the user used the Esc Key exit
                    if (file_menu.choice==-2)|(main_menu.choice==-2):
                        #if a sub-process is running wait for it to finish before exiting
                        if p1.is_alive():
                            q.get(True)
                            p1.join()
                        exit()
if __name__ == '__main__':
#getting arguments from the user                                                       
    parser = argparse.ArgumentParser(description='Neatseq-flow Monitor v1.0 By Liron Levin ')
    parser.add_argument('-D', dest='directory',metavar="STR", type=str,default=os.getcwd(),
                        help='Neatseq-flow project directory [default=cwd]')
    parser.add_argument('-R', dest='Regular',metavar="STR" , type=str,default="log_[0-9]+.txt",
                        help='Log file Regular Expression [in ./log/ ] [default=log_[0-9]+.txt]')
    parser.add_argument('--Monitor_RF',metavar="INT", type=int,dest='Monitor_RF',default=1,
                        help='Monitor Refresh rate [default=1]')
    parser.add_argument('--File_browser_RF',metavar="INT", type=int,dest='File_browser_RF',default=1,
                        help='File Browser Refresh rate [default=1]')
    parser.add_argument('--Bar_Marker',metavar="CHAR",type=str,dest='Bar_Marker',default="#",
                        help='Progress Bar Marker [default=#]')
    parser.add_argument('--Bar_Spacer',metavar="CHAR",type=str,dest='Bar_Spacer',default=" ",
                        help='Progress Bar Spacer [default=Space]')
    parser.add_argument('--Bar_len',metavar="INT",type=int,dest='Bar_len',default=50,
                        help='Progress Bar Total Length [in chars] [default=50]')
    args = parser.parse_args()
    #Ruining main function
    curses.wrapper(neatseq_flow_monitor,args)