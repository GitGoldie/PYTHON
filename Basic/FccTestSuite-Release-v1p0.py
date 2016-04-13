#!/usr/bin/python
# -*- coding: iso-8859-1 -*-


from Tkinter import *
import os, re, time
import subprocess

# Environment Path
workingdir = os.getcwd() #set up on your working directory under firmware#
releasedir = workingdir+'/release/tarball/' 
fccmapdir = workingdir+'/release.fcc'
nvmcpath = workingdir+'/test/bin/nvmc/nvmc'
logPath = os.path.join(workingdir,'FccTestSuite.log')

# Fcc Test Suite Coverage
# Buttons
buttonlist = [u"smb-reset",u"reenum",u"load-n-go",u"dmi-showlog(All)",u"dmi-showlog(TM only)",u"Clear Screen",u"Board Config & Build Result",u"TestSummary",u"RUN ALL",u"RUN SINGLE"]
# Test Modules in structure of (testname, index, flag, longRun? )
FccTmList = [
             (u"TEST_FCC_RR_SHIFTLEVEL",0,"Enable", False),
             (u"TEST_FCC_LOCK",1,"Enable", False),
             (u"TEST_FCC_PFAIL_HANDLER",2,"Enable", False),
             (u"TEST_FCC_ERASE_SUSPEND",3,"Enable", False),
             (u"TEST_FCC_CELLCARE",4,"Disable", False),
             (u"TEST_FLASH_PASS_THROUGH",5,"Enable", False),
             (u"TEST_TARGET_OFFLINE",6,"Enable", False),
             (u"WB_TEST_FCC_EI",7,"Enable", True),
             (u"TEST_FLASH_CMD_SUPPORT",8,"Enable", True),
            ]

#r'(\btext String1\b)|(\bText String2\b)'
configInfos = ['00:info  SBL Configuration  : ', '00:info  Firmware Boot Mode : ', '00:info  ASIC Product ID    : ', '00:info  ASIC Revision      : ', \
               '00:info  Board Revision     : ', '00:info  System             : ', '00:info  CMU                : ', '00:info  DDR                : ', \
               '00:info  Host interface     : ', '00:info  Flash controller   : ', '00:info  Flash IO           : ', '00:info  Flash ECC          : ', \
               '00:info  DDR size           : ', '00:info  SBL API version    : ', '00:info  CellCare           : ', '00:info  Flash Chip         : ', \
               '00:info  Flash channels     : ', '00:info  Flash targets      : ', '00:info  LUNs/target        : ', '00:info  Blocks/LUN         : ', \
               '00:info  Planes             : ', '00:info  Pages/block        : ', '00:info  Frames/page        : ', '00:info  Blocksets          : ', \
               '00:info  Virtual targets    : ', '00:info  LBNs/blockset      : ', '00:info  Blockset pools     : ']


# test timeout 
TIMEOUT_THRESHOLD_BUILD = 20 #sec
TIMEOUT_THRESHOLD_TEST = 60*10      #10 minutes
TIMEOUT_THRESHOLD_TEST_LONG = 60*60 #60 minutes


class FccTestSuite(Frame):
    global nvmcpath
    global releasedir
    global TIMEOUT_THRESHOLD_BUILD
    global TIMEOUT_THRESHOLD_TEST
    global TIMEOUT_THRESHOLD_TEST_LONG
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.grid()
        self.master.title("FCC TEST SUITE (OMAHA, HGST Flash Platform Group, Release Version 1.0)")
        self.nvmcpath = nvmcpath
        self.tarfile = releasedir+'omaha.tar'
        self.test_logs = []
        self.testCompleted = FALSE
        self.starttime = 0
        self.currentTestIdx = 0
        self.testResult = []
        self.buildResult = []

        #default setting
        self.asicRevision = 1
        self.buildAsic = "ASIC_REVISION=1"
        self.buildParam = "TEST_FLASH_CMD_SUPPORT=1"
        self.logFile = logPath
        self.openfile = ''
        self.repeatCount = 1
        self.buildAddon = ''
        
        # window layout
        masterV = 8
        masterH = 20 
        masterVframes = 2
        masterHframes = 2
        frame1_width = 1
        frame2_width = 1
        frame3_width = 12
        frame4_width = 1
        frame5_width = frame4_width

        frame1_height = masterV / masterVframes
        frame2_height = masterV / masterVframes
        frame3_height = masterV
        frame4_height = masterV / masterVframes
        frame5_height = masterV / masterVframes

        frame1_Hstart = 0
        frame2_Hstart = 0
        frame3_Hstart = frame2_Hstart + frame2_width 
        frame4_Hstart = frame3_Hstart + frame3_width 
        frame5_Hstart = frame4_Hstart

        # grid row
        frame1_Vstart = 0
        frame2_Vstart = masterV/masterVframes
        frame3_Vstart = 0                        #Center
        frame4_Vstart = 0
        frame5_Vstart = masterV/masterVframes
        
        for r in range(masterV):
            self.master.rowconfigure(r, weight=1)    
        for c in range(0,len(buttonlist)):
            self.testResult.append("N/A")
            self.buildResult.append("N/A")
            self.master.columnconfigure(c, weight=1)
            if (c==0):  #smb-rset
                button = Button(master, text=buttonlist[c].format(c), command=self.OnButtonClick0, background='white',pady=20)
                button.grid(row=masterV,column=c,rowspan=2, sticky=E+W)
                button.focus_set()
            elif c==1:  #reenum
                button = Button(master, text=buttonlist[c].format(c), command=self.OnButtonClick1, background='white',pady=20).grid(row=masterV,column=c,rowspan=2, sticky=E+W)
            elif c==2:  #load-n-go
                button = Button(master, text=buttonlist[c].format(c), command=self.OnButtonClick2, background='white',pady=20).grid(row=masterV,column=c,rowspan=2, sticky=E+W)
            elif c==3:  #dmi-showlog
                button = Button(master, text=buttonlist[c].format(c), command=self.OnButtonClick3, background='white',pady=5).grid(row=masterV,column=c, sticky=E+W)
            elif c==4:  #dmi-showlog. PROC16 only
                button = Button(master, text=buttonlist[c].format(c), command=self.OnButtonClick3_15, background='white',pady=5).grid(row=masterV+1,column=3, sticky=E+W)
            elif c==5:  #clear screen
                button = Button(master, text=buttonlist[c].format(c), command=self.OnButtonClick4, background='white',pady=20).grid(row=masterV,column=(c-1),rowspan=2, sticky=E+W)
            elif c==6:  #display drive configuration
                button = Button(master, text=buttonlist[c].format(c), command=self.OnButtonClick8, pady=20).grid(row=masterV,column=(c-1),rowspan=2, sticky=E+W)
            elif c==7:  #Test summary
                button = Button(master, text=buttonlist[c].format(c), command=self.OnButtonClick5, background='white',pady=20).grid(row=masterV,column=(c-1),rowspan=2, sticky=E+W)
            elif c==8:  #UT bundle
                button = Button(master, text=buttonlist[c].format(c), command=self.OnButtonClick6, background='blue', foreground='white', pady=20).grid(row=masterV,column=(c-1),rowspan=2, sticky=E+W)
            elif c==9:  #UT single
                button = Button(master, text=buttonlist[c].format(c), command=self.OnButtonClick7, background='pink', foreground='blue', pady=20).grid(row=masterV,column=(c-1),rowspan=2, sticky=E+W)
            else:
                pass


        Frame1 = Frame(master, relief=RAISED, borderwidth=2)
        Frame1.grid(row = frame1_Vstart, column = frame1_Hstart, rowspan = frame1_height, sticky = W+E+N+S) 
        Frame2 = Frame(master, bg="yellow", relief=RAISED, borderwidth=2)
        Frame2.grid(row = frame2_Vstart, column = frame2_Hstart, rowspan = frame2_height, sticky = W+E+N+S)
        self.Text1  = Text(master, height=20, width=50)
        self.Text1.tag_configure('bold_italics', font=('Arial', 12, 'bold', 'italic'))
        self.Text1.tag_configure('big', font=('Verdana', 20, 'bold'))
        self.Text1.tag_configure('color', foreground='#476042', font=('Tempus Sans ITC', 12, 'bold'))
        self.Text1.tag_bind('follow', '<1>', lambda e, t=self.Text1: t.insert(END, "!"))
        self.Text1.insert(END,'--- Monitoring Board Launched ---\n', 'big')
        quote = """ Build Your Test """
        self.Text1.insert(END, quote+'\n', 'color')
        self.Text1.grid(row = frame3_Vstart, column = frame3_Hstart, rowspan = frame3_height, columnspan = frame3_width, sticky = W+E+N+S)

        # Drive Configuration Board
        self.Text2  = Text(master, height=20, width=50, bg="#eee")
        self.Text2.tag_configure('big', foreground='black', background='white', justify='center',font=(None, 12, 'bold'))
        self.Text2.tag_configure('color', foreground='#476042', font=('Verdana', 9))
        self.Text2.tag_bind('follow', '<1>', lambda e, t=self.Text2: t.insert(END, "_"))
        self.Text2.insert(END,'Drive Configuration\n', 'big')
        self.Text2.grid(row = frame4_Vstart, column = frame4_Hstart, rowspan = frame4_height, sticky = W+E+N+S)

        # Build Result Board
        self.TextBuild  = Text(master, height=20, width=50, bg="#eee")
        self.TextBuild.tag_configure('big', foreground='black', background='white', justify='center', font=(None, 12, 'bold'))
        self.TextBuild.tag_configure('color', foreground='#476042', font=('Verdana', 9))
        self.TextBuild.tag_bind('follow', '<1>', lambda e, t=self.TextBuild: t.insert(END, "_"))
        self.TextBuild.insert(END,'Code Build Result\n', 'big')
        self.TextBuild.grid(row = frame5_Vstart, column = frame5_Hstart, rowspan = frame5_height, sticky = W+E+N+S)        
        
        
        self.v = IntVar()
        lbl=Label(Frame1, text="FCC TEST MANAGER MODULES", fg='blue', bg='yellow', font="Verdana 10 bold", width=30)
        lbl.grid(row=0,column=0,sticky=E+W)

        for test, idx, flag, period in FccTmList:
            Radiobutton(Frame1, 
                        text=test,
                        pady = 8,
                        variable=self.v,
                        command=self.showBuildOption,
                        value=idx).grid(sticky=W)
        self.v.set(0)
        Button(Frame1, text='Build Test Manager Only(Single)', command=self.buildCode, bg='green', width=30).grid(row=len(FccTmList)+1, sticky=W)
        Button(Frame1, text='Build All and Display Results', command=self.buildCodeAll, bg='green', width=30).grid(row=len(FccTmList)+2, sticky=W)

        # input ASIC REVISION
        Label(Frame2, text="OPTIONAL CONFIGURATION", fg='blue', bg='yellow', font="Verdana 10 bold", width=30, justify=LEFT).grid(row=0,column=0, sticky=W)
        Label(Frame2, text="ASIC REVISION (default RevB and update if RevA(0))", bg='yellow').grid(row=1, sticky=W)
        self.asicEntry = Entry(Frame2, width=30, text="1")
        self.asicEntry.grid(row=2, column=0, sticky=W)

        # input LOG FILE
        Label(Frame2, text="LOG FILE (default ./FccTestSuite.log)", bg='yellow').grid(row=3, sticky=W)
        self.logEntry = Entry(Frame2, width=30)
        self.logEntry.grid(row=4, column=0, sticky=W)

        # input Repeated Test
        Label(Frame2, text="TEST LOOP CNT (default 1, Single Run)", bg='yellow').grid(row=5, sticky=W)
        self.repeatEntry = Entry(Frame2, width=30)
        self.repeatEntry.grid(row=6, column=0, sticky=W)

        # Extra build
        Label(Frame2, text="Add On Build (default ' ') ", bg='yellow').grid(row=7, sticky=W)
        self.buildEntry = Entry(Frame2, width=30)
        self.buildEntry.grid(row=8, column=0, sticky=W)

        Button(Frame2, text='Update', command=self.updateRecord,bg='green').grid(row=9, column=0, sticky=W)





    #====================================== Method Binding ==================================#
    # Button0: smb-reset
    def OnButtonClick0(self):
        subprocess.call([self.nvmcpath, "smb-reset"])

    # Button1: reenum
    def OnButtonClick1(self):
        subprocess.call([self.nvmcpath, "reenum"])

    # Button2: load-n-go
    def OnButtonClick2(self):
        subprocess.call([self.nvmcpath, "load-n-go", self.tarfile])

    # Button3: dmi-showlog
    def OnButtonClick3(self):
        ps = subprocess.Popen([self.nvmcpath, "dmi-showlog"], stdout=subprocess.PIPE)
        output = ps.communicate()[0]
        for line in output.split('\n'):
            print(line)
            self.Text1.insert(END,line+'\n')
            
    def OnButtonClick3_15(self):
        ps = subprocess.Popen([self.nvmcpath, "dmi-showlog"], stdout=subprocess.PIPE)
        output = ps.communicate()[0]
        for line in output.split('\n'):
            if "15:" in line:
                print(line)
                self.Text1.insert(END,line+'\n')    

    # Button4: clear terminal
    def OnButtonClick4(self):
        subprocess.call("clear")
        self.Text1.delete(1.0, END)
        self.Text2.delete(1.0, END)
        self.Text2.insert(END,'Drive Configuration\n', 'big')
        self.TextBuild.delete(1.0, END)
        self.TextBuild.insert(END,'Code Build Result\n', 'big')
        
    # Button5: parse test result
    def OnButtonClick5(self):
        i = 0
        self.Text1.insert(END,'---- FCC TEST RESULT SUMMARY---- \n','follow')
        for test, idx, flag, period in FccTmList:
            result = "\t"+test+": "+self.testResult[i]
            print("\t[ %s ] %s"%(test, self.testResult[i]))
            self.Text1.insert(END,result+'\n')
            i += 1
            

    def MonitorTM(self):
        ps = subprocess.Popen([self.nvmcpath, "dmi-showlog"], stdout=subprocess.PIPE)
        output = ps.communicate()[0]
        for line in output.split('\n'):
            if "15:info  Test Complete:" in line:
                print(line)
                result = re.findall(r"\d\spass,\s\d\sfail",line)[0].split()  #* pass, * fail
                if (result[0] == "1"):
                    result_str = "FCC TEST RESULT : "+result[1].upper()+" (with "+self.buildParam+")"
                    self.testResult[self.currentTestIdx] = "PASS"
                elif (result[2] == "1"):
                    result_str = "FCC TEST RESULT : "+result[3].upper()+" (with "+self.buildParam+")"
                    self.testResult[self.currentTestIdx] = "FAIL"
                print(result_str)
                self.Text1.insert(END,result_str+'\n','follow')
                self.testCompleted = TRUE

            elif ":err " in line:
                print(line)
                result_str = "FCC TEST RESULT : Logic Traped! (with "+self.buildParam+")"
                self.testResult[self.currentTestIdx] = "CRASH/LOGIC TRAP"
                print(result_str)
                self.Text1.insert(END,result_str+'\n','follow')
                self.testCompleted = TRUE

        
    def getDriveLogProc15(self):
        ps = subprocess.Popen([self.nvmcpath, "dmi-showlog"], stdout=subprocess.PIPE)
        output = ps.communicate()[0]
        for line in output.split('\n'):
            if "15:" in line:
                print(line)
                self.Text1.insert(END,line+'\n')
                self.openfile.write(line+'\n')


    # Button6: Run all test modules
    def OnButtonClick6(self):
        self.Text1.insert(END,'------------------- About to launch FCC UT BUNDLE -------------------\n','follow')
        print("------------------- About to launch FCC UT BUNDLE -------------------\n")
        self.openfile = open(self.logFile, 'aw')   #log file
        self.currentTestIdx = 0
        for test, idx, flag, period in FccTmList:
            if (flag == "Enable"):
                self.testCompleted = FALSE
                self.buildParam = test+"=1"
                s = "Build Code: "+self.buildParam+"... Be patient!"
                print(s)
                self.Text1.insert(END,s+'\n','follow')

                self.buildCode()
                self.buildCheck()
                if (self.buildResult[self.currentTestIdx] == "FAIL"):
                    continue
                self.runSingle()
                if (self.testResult[self.currentTestIdx] == "TIMEOUT"):
                    break

                self.getDriveLogProc15()
            else:
                print(test," Disabled\n")
            self.currentTestIdx += 1

        self.OnButtonClick8()
        self.openfile.close()
        self.openfile = ''


    # Button7: Run a single test module
    def OnButtonClick7(self):
        self.Text1.insert(END,'------------------- About to launch Single UT -------------------\n','follow')
        for i in range(0, int(self.repeatCount)):
            self.testCompleted = FALSE 
            print(">>>>> Test Count : %d/%d\n"%(i,int(self.repeatCount)))
            s = ">>> Test Count "+str(i)+'\n'
            self.Text1.insert(END,s,'follow')
            if (FccTmList[self.currentTestIdx][2] == "Enable"):
                self.openfile = open(self.logFile, 'aw')   #log file
                self.showBuildOption()
                s = "Build Code: "+self.buildParam+"... Be patient!"
                print(s)
                self.Text1.insert(END,s+'\n','follow')
                self.openfile.write('TestLoop : '+str(i+1)+'/'+str(self.repeatCount)+'\n')
                self.openfile.write(s+'\n')
                self.buildCode()
                self.buildCheck()
                if (self.buildResult[self.currentTestIdx] == "FAIL"):
                    continue
                self.runSingle()
                self.getDriveLogProc15()
                self.OnButtonClick8()
                self.openfile.close()
                self.openfile = ''
            else:
                s = FccTmList[self.currentTestIdx][0]+" : "+FccTmList[self.currentTestIdx][2]+"\n"
                print(s)
                self.Text1.insert(END,s,'follow')

    # Button8: Parse drive configuration and Build Result
    def OnButtonClick8(self):
        try:
            self.Text2.delete(1.0, END)
            self.Text2.insert(END,'Drive Configuration\n', 'big')
            ps = subprocess.Popen([self.nvmcpath, "dmi-showlog"], stdout=subprocess.PIPE)
            output = ps.communicate()[0]
            searchStr = ''
            for i in range(0,len(configInfos)):
                searchStr += '\\b'+configInfos[i]+'\\b'
                if i < len(configInfos) - 1:
                    searchStr+= '|'
            
            if (self.openfile):
                self.openfile.write("\t\t-----------------Drive Configuration---------------\n")

            pattern = re.compile(searchStr)
            for line in output.split('\n'):
                if pattern.search(line):
                    s = []
                    print(line)
                    s = line.split("00:info  ")
                    self.Text2.insert(END,s[1]+'\n')
                    if (self.openfile):
                        self.openfile.write('\t\t'+s[1]+'\n')
        except OSError:
            s = 'NO NVMC AVAILABLE\nCHECK BUILD RESULTS FIRST(e.g., release/nvmc)\n'
            self.Text2.insert(END,s)
            print(s)
            pass

        # display compile result if available
        i = 0
        self.TextBuild.delete(1.0, END)
        self.TextBuild.insert(END,'Result Summary (BUILD : UT)\n', 'big')
        for item in FccTmList:
            s = item[0]+": "+self.buildResult[i]+": "+self.testResult[i]+"\n"
            print(s)
            self.TextBuild.insert(END, s)
            i+=1


    def runSingle(self):
        self.OnButtonClick0()
        s = '>> smb-reset...'
        self.Text1.insert(END,s,'follow')
        self.openfile.write(s)
        time.sleep(5)
        self.OnButtonClick1()
        s = '>> reenum...'
        self.Text1.insert(END,s,'follow')
        self.openfile.write(s)
        time.sleep(5)
        self.OnButtonClick2()
        s = '>> load-n-go...\n'
        self.Text1.insert(END,s,'follow')
        self.openfile.write(s)
        self.starttime = time.time()
        time.sleep(60)
        while (self.testCompleted == FALSE):
            self.MonitorTM()
            if (FccTmList[self.currentTestIdx][3] == True):
                thres = TIMEOUT_THRESHOLD_TEST_LONG
            else:
                thres = TIMEOUT_THRESHOLD_TEST

            if(time.time() - self.starttime > thres):
                s = "TEST TIMEOUT !! >>>>>>>>>>>>>>>> "+str(thres)+" (sec)"
                print(s)
                self.Text1.insert(END,s+'\n','follow')
                self.testResult[self.currentTestIdx] = "TIMEOUT"
                break
            else:
                time.sleep(10)
    
    def buildCheck(self):
        compiledone = False
        buildStart = time.time()
        while (compiledone == False):
            if time.time() - buildStart > TIMEOUT_THRESHOLD_BUILD:
                self.buildResult[self.currentTestIdx] = "FAIL"
                compiledone = True
            else:
                compiledone = os.path.isfile(nvmcpath)
                if compiledone:
                    self.buildResult[self.currentTestIdx] = "PASS"
                else:
                    time.sleep(5)
    

    def showBuildOption(self):
        item = FccTmList[self.v.get()]
        self.currentTestIdx = int(item[1])
        self.buildParam = item[0]+"=1"
        print("FCC Test Build Target Update: %s"%self.buildParam)
        
    def updateRecord(self):
        if self.asicEntry.get():
            self.asicRevision = self.asicEntry.get()        
        self.buildAsic = "ASIC_REVISION="+str(self.asicRevision)
        if self.logEntry.get():
            self.logFile   = os.path.join(workingdir,self.logEntry.get())
        if self.repeatEntry.get():
            self.repeatCount = self.repeatEntry.get()
        if self.buildEntry.get():
            self.buildAddon = str(self.buildEntry.get())

        print("ASIC REVISION updated %s ==> %s"%(self.asicRevision, self.buildAsic))
        print("LOG FILE PATH updated %s/%s"%(os.getcwd(),self.logFile))
        print("TEST REPEAT COUNT updated %d"%int(self.repeatCount))
        print("BUILD ADD ON updated %s"%(self.buildAddon))
        
    def buildCode(self):
        subprocess.call(["make", "-j", "clean"])
        print("ENABLE_TEST_MGR=1","TEST_ON_STARTUP=1",self.buildAsic, self.buildParam, self.buildAddon)
        if self.buildAddon:
            subprocess.call(["make", "-j", "ENABLE_TEST_MGR=1","TEST_ON_STARTUP=1",self.buildAsic, self.buildParam, self.buildAddon])
        else:
            subprocess.call(["make", "-j", "ENABLE_TEST_MGR=1","TEST_ON_STARTUP=1",self.buildAsic, self.buildParam])
        
    def buildCodeAll(self):
        self.currentTestIdx = 0
        for item in FccTmList:
            self.buildParam = item[0]+"=1"
            subprocess.call(["make", "-j", "clean"])
            if self.buildAddon:
                subprocess.call(["make", "-j", "ENABLE_TEST_MGR=1","TEST_ON_STARTUP=1",self.buildAsic, self.buildParam, self.buildAddon])
            else:
                subprocess.call(["make", "-j", "ENABLE_TEST_MGR=1","TEST_ON_STARTUP=1",self.buildAsic, self.buildParam])            
            self.buildCheck()
            if self.buildResult[self.currentTestIdx] == "FAIL":
                return
            self.currentTestIdx += 1

        # display compile summary
        self.OnButtonClick8()

if __name__ == '__main__':
    root = Tk()
    root.geometry("1600x800")
    runapp = FccTestSuite(master=root)
    runapp.mainloop()