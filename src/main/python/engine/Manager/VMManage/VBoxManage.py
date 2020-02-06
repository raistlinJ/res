from subprocess import Popen, PIPE
import subprocess
from sys import argv, platform
import sys, traceback
import logging
import shlex
import threading
import sys
import time
from engine.Manager.VMManage.VMManage import VMManage
from engine.Manager.VMManage.VM import VM
import re
import configparser
import os
from engine.Configuration.SystemConfigIO import SystemConfigIO

class VBoxManage(VMManage):
    def __init__(self, initializeVMManage=False):
        logging.info("VBoxManage.__init__(): instantiated")
        VMManage.__init__(self)
        self.cf = SystemConfigIO()
        self.vmanage_path = self.cf.getConfig()['VBOX']['VMANAGE_PATH']
        self.vms = {}
        if initializeVMManage:
            self.refreshAllVMInfo()
            while self.getManagerStatus()["writeStatus"] != VMManage.MANAGER_IDLE:
            #waiting for manager to finish query...
                time.sleep(.1)

    def configureVMNet(self, vmName, netNum, netName):
        logging.info("VBoxManage: configureVMNet(): instantiated")
        #check to make sure the vm is known, if not should refresh or check name:
        if vmName not in self.vms:
            logging.error("configureVMNet(): " + vmName + " not found in list of known vms: \r\n" + str(self.vms))
            return -1
        t = threading.Thread(target=self.runConfigureVMNet, args=(vmName, netNum, netName))
        t.start()
        return 0

    def configureVMNets(self, vmName, internalNets):
        logging.info("VBoxManageWin: configureVMNets(): instantiated")
        #check to make sure the vm is known, if not should refresh or check name:
        if vmName not in self.vms:
            logging.error("configureVMNets(): " + vmName + " not found in list of known vms: \r\n" + str(self.vms))
            return -1
        t = threading.Thread(target=self.runConfigureVMNets, args=(vmName, internalNets))
        t.start()
        return 0

    def runConfigureVMNets(self, vmName, internalNets):
        try:
            logging.debug("VBoxManage: runConfigureVMNets(): instantiated")
            self.readStatus = VMManage.MANAGER_READING
            self.writeStatus += 1
            logging.debug("runConfigureVMNets(): adding 1 "+ str(self.writeStatus))            
            cloneNetNum = 1
            logging.debug("runConfigureVMNets(): Processing internal net names: " + str(internalNets))
            for internalnet in internalNets:
                vmConfigVMCmd = self.vmanage_path + " modifyvm " + str(self.vms[vmName].UUID) + " --nic" + str(cloneNetNum) + " intnet " + " --intnet" + str(cloneNetNum) + " " + str(internalnet) + " --cableconnected"  + str(cloneNetNum) + " on "
                logging.debug("runConfigureVMNets(): Running " + vmConfigVMCmd)
                subprocess.check_output(shlex.split(vmConfigVMCmd, posix=self.POSIX), encoding='utf-8')
                cloneNetNum += 1            
           
            logging.debug("runConfigureVMNets(): Thread completed")
        except Exception:
            logging.error("runConfigureVMNets() Error: " + " cmd: " + vmConfigVMCmd)
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback)
        finally:
            self.readStatus = VMManage.MANAGER_IDLE
            self.writeStatus -= 1
            logging.debug("runConfigureVMNets(): sub 1 "+ str(self.writeStatus))

    def refreshAllVMInfo(self):
        logging.info("VBoxManage: refreshAllVMInfo(): instantiated")
        
        logging.debug("getListVMS() Starting List VMs thread")
        t = threading.Thread(target=self.runVMSInfo)
        t.start()
        
    def refreshVMInfo(self, vmName):
        logging.info("VBoxManage: refreshVMInfo(): instantiated: " + str(vmName))
        logging.debug("refreshVMInfo() refresh VMs thread")
        #check to make sure the vm is known, if not should refresh or check name:
        if vmName not in self.vms:
            logging.error("refreshVMInfo(): " + vmName + " not found in list of known vms: \r\n" + str(self.vms))
            return -1
        t = threading.Thread(target=self.runVMInfo, args=(vmName,))
        t.start()
        return 0

    def addVMByName(self, vmName, replace=False):
    logging.debug("VBoxManage: addVMByName(): instantiated")
    #run vboxmanage to get vm listing
    vmListCmd = self.vmanage_path + " list vms"
    logging.debug("addVMByName(): Collecting VM Names using cmd: " + vmListCmd)
    try:
        self.readStatus = VMManage.MANAGER_READING
        self.writeStatus += 1
        logging.debug("addVMByName(): adding 1 "+ str(self.writeStatus))
        p = Popen(vmListCmd, stdout=PIPE, stderr=PIPE, encoding="utf-8")
        while True:
            out = p.stdout.readline()
            if out == '' and p.poll() != None:
                break
            if out != '':
                splitOut = out.split("{")
                vm = VM()
                tmpname = splitOut[0].strip()
                #has to be at least one character and every name has a start and end quote
                if len(tmpname) > 2:
                    vm.name = splitOut[0].strip()[1:-1]
                else: 
                    break
                vm.UUID = splitOut[1].split("}")[0].strip()
                # logging.debug("UUID: " + vm.UUID)
                self.vms[vm.name] = vm
        p.wait()
        logging.debug("addVMByName(): Thread 1 completed: " + vmListCmd)
        logging.debug("addVMByName(): Found # VMS: " + str(len(self.vms)))
        if vmName in self.vms:
            if replace==False:
                logging.error("addVMByName(): VM already exists... skipping: " + str(vmName))
                return

        #get the machine readable info
        logging.debug("addVMByName(): collecting VM extended info")
        vmShowInfoCmd = ""
        logging.debug("addVMByName(): collecting # " + str(vmNum) + " of " + str(len(self.vms)))
        vmShowInfoCmd = self.vmanage_path + " showvminfo " + str(self.vms[vmName].UUID) + " --machinereadable"
        logging.debug("addVMByName(): Running " + vmShowInfoCmd)
        p = Popen(shlex.split(vmShowInfoCmd, posix=self.POSIX), stdout=PIPE, stderr=PIPE, encoding="utf-8")
        while True:
            out = p.stdout.readline()
            if out == '' and p.poll() != None:
                break
            if out != '':
                #match example: nic1="none"
                res = re.match("nic[0-9]+=", out)
                if res:
                    # logging.debug("Found nic: " + out + " added to " + self.vms[aVM].name)
                    out = out.strip()
                    nicNum = out.split("=")[0][3:]
                    nicType = out.split("=")[1]
                    self.vms[aVM].adaptorInfo[nicNum] = nicType
                res = re.match("groups=", out)
                if res:
                    # logging.debug("Found groups: " + out + " added to " + self.vms[aVM].name)
                    self.vms[aVM].groups = out.strip()
                res = re.match("VMState=", out)
                if res:
                    # logging.debug("Found vmState: " + out + " added to " + self.vms[aVM].name)
                    state = out.strip().split("\"")[1].split("\"")[0]
                    if state == "running":
                        self.vms[aVM].state = VM.VM_STATE_RUNNING
                    elif state == "poweroff":
                        self.vms[aVM].state = VM.VM_STATE_OFF
                    else:
                        self.vms[aVM].state = VM.VM_STATE_OTHER
                    res = re.match("CurrentSnapshotUUID=", out)
                if res:
                    # logging.debug("Found snaps: " + out + " added to " + self.vms[aVM].latestSnapUUID)
                    latestSnap = out.strip().split("\"")[1].split("\"")[0]
                    self.vms[aVM].latestSnapUUID = latestSnap
        p.wait()
        logging.info("addVMByName(): Thread 2 completed: " + vmShowInfoCmd)
    except Exception:
        logging.error("Error in addVMByName(): An error occured ")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
    finally:
        self.readStatus = VMManage.MANAGER_IDLE
        self.writeStatus -= 1
        logging.debug("addVMByName(): sub 1 "+ str(self.writeStatus))

    def runVMSInfo(self):
        logging.debug("VBoxManage: runVMSInfo(): instantiated")
        #clear out the current set
        self.vms = {}
        vmListCmd = self.vmanage_path + " list vms"
        logging.debug("runVMSInfo(): Collecting VM Names using cmd: " + vmListCmd)
        try:
            self.readStatus = VMManage.MANAGER_READING
            self.writeStatus += 1
            logging.debug("runVMSInfo(): adding 1 "+ str(self.writeStatus))
            p = Popen(shlex.split(vmListCmd, posix=self.POSIX), stdout=PIPE, stderr=PIPE, encoding="utf-8")
            while True:
                out = p.stdout.readline()
                if out == '' and p.poll() != None:
                    break
                if out != '':
                    # logging.debug("runVMSInfo(): stdout Line: " + out)
                    # logging.debug("runVMSInfo(): split Line: " + str(out.split("{")))
                    splitOut = out.split("{")
                    vm = VM()
                    tmpname = splitOut[0].strip()
                    #has to be at least one character and every name has a start and end quote
                    if len(tmpname) > 2:
                        vm.name = splitOut[0].strip()[1:-1]
                    else: 
                        break
                    vm.UUID = splitOut[1].split("}")[0].strip()
                    # logging.debug("UUID: " + vm.UUID)
                    self.vms[vm.name] = vm
            p.wait()
            logging.debug("runVMSInfo(): Thread 1 completed: " + vmListCmd)
            logging.debug("runVMSInfo(): Found # VMS: " + str(len(self.vms)))

            #for each vm, get the machine readable info
            logging.debug("runVMSInfo(): collecting VM extended info")
            vmNum = 1
            vmShowInfoCmd = ""
            for aVM in self.vms:
                logging.debug("runVMSInfo(): collecting # " + str(vmNum) + " of " + str(len(self.vms)))
                vmShowInfoCmd = self.vmanage_path + " showvminfo \"" + str(self.vms[aVM].UUID) + "\"" + " --machinereadable"
                logging.debug("runVMSInfo(): Running " + vmShowInfoCmd)
                p = Popen(shlex.split(vmShowInfoCmd, posix=self.POSIX), stdout=PIPE, stderr=PIPE, encoding="utf-8")
                while True:
                    out = p.stdout.readline()
                    if out == '' and p.poll() != None:
                        break
                    if out != '':
                        #match example: nic1="none"
                        res = re.match("nic[0-9]+=", out)
                        if res:
                            # logging.debug("Found nic: " + out + " added to " + self.vms[aVM].name)
                            out = out.strip()
                            nicNum = out.split("=")[0][3:]
                            nicType = out.split("=")[1]
                            self.vms[aVM].adaptorInfo[nicNum] = nicType
                        res = re.match("groups=", out)
                        if res:
                            # logging.debug("Found groups: " + out + " added to " + self.vms[aVM].name)
                            self.vms[aVM].groups = out.strip()
                        res = re.match("VMState=", out)
                        if res:
                            # logging.debug("Found vmState: " + out + " added to " + self.vms[aVM].name)
                            state = out.strip().split("\"")[1].split("\"")[0]
                            if state == "running":
                                self.vms[aVM].state = VM.VM_STATE_RUNNING
                            elif state == "poweroff":
                                self.vms[aVM].state = VM.VM_STATE_OFF
                            else:
                                self.vms[aVM].state = VM.VM_STATE_OTHER
                        res = re.match("CurrentSnapshotUUID=", out)
                        if res:
                            # logging.debug("Found snaps: " + out + " added to " + self.vms[aVM].latestSnapUUID)
                            latestSnap = out.strip().split("\"")[1].split("\"")[0]
                            self.vms[aVM].latestSnapUUID = latestSnap
                p.wait()
                vmNum = vmNum + 1
            logging.info("runVMSInfo(): Thread 2 completed: " + vmShowInfoCmd)
        except Exception:
            logging.error("Error in runVMSInfo(): An error occured ")
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback)
        finally:
            self.readStatus = VMManage.MANAGER_IDLE
            self.writeStatus -= 1
            logging.debug("runVMSInfo(): sub 1 "+ str(self.writeStatus))

    def runVMInfo(self, aVM):
        logging.debug("VBoxManage: runVMSInfo(): instantiated")
        try:
            self.readStatus = VMManage.MANAGER_READING
            self.writeStatus += 1
            logging.debug("runVMInfo(): adding 1 "+ str(self.writeStatus))
            vmShowInfoCmd = self.vmanage_path + " showvminfo \"" + self.vms[aVM].UUID + "\"" + " --machinereadable"
            logging.debug("runVMInfo(): Running " + vmShowInfoCmd)
            p = Popen(shlex.split(vmShowInfoCmd, posix=self.POSIX), stdout=PIPE, stderr=PIPE, encoding="utf-8")
            while True:
                out = p.stdout.readline()
                if out == '' and p.poll() != None:
                    break
                if out != '':
                    #match example: nic1="none"
                    res = re.match("nic[0-9]+=", out)
                    if res:
                        # logging.debug("Found nic: " + out + " added to " + self.vms[aVM].name)
                        out = out.strip()
                        nicNum = out.split("=")[0][3:]
                        nicType = out.split("=")[1]
                        self.vms[aVM].adaptorInfo[nicNum] = nicType
                    res = re.match("groups=", out)
                    if res:
                        # logging.debug("Found groups: " + out + " added to " + self.vms[aVM].name)
                        self.vms[aVM].groups = out.strip()
                    res = re.match("VMState=", out)
                    if res:
                        # logging.debug("Found vmState: " + out + " added to " + self.vms[aVM].name)
                        state = out.strip().split("\"")[1].split("\"")[0].strip()
                        if state == "running":
                            self.vms[aVM].state = VM.VM_STATE_RUNNING
                        elif state == "poweroff":
                            self.vms[aVM].state = VM.VM_STATE_OFF
                        else:
                            self.vms[aVM].state = VM.VM_STATE_OTHER
                    res = re.match("CurrentSnapshotUUID=", out)
                    if res:
                        # logging.debug("Found snaps: " + out + " added to " + self.vms[aVM].latestSnapUUID)
                        latestSnap = out.strip().split("\"")[1].split("\"")[0]
                        self.vms[aVM].latestSnapUUID = latestSnap                            
            p.wait()
            logging.debug("runVMInfo(): Thread completed")
        except Exception:
            logging.error("Error in runVMInfo(): An error occured ")
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback)
        finally:
            self.readStatus = VMManage.MANAGER_IDLE
            self.writeStatus -= 1
            logging.debug("runVMInfo(): sub 1 "+ str(self.writeStatus))

    def runConfigureVMNet(self, vmName, netNum, netName):
        try:
            logging.debug("VBoxManage: runConfigureVMNet(): instantiated")
            self.readStatus = VMManage.MANAGER_READING
            self.writeStatus += 1
            logging.debug("runConfigureVMNet(): adding 1 "+ str(self.writeStatus))
            vmConfigVMCmd = self.vmanage_path + " modifyvm " + str(self.vms[vmName].UUID) + " --nic" + str(netNum) + " intnet " + " --intnet" + str(netNum) + " " + str(netName) + " --cableconnected"  + str(netNum) + " on "
            logging.debug("runConfigureVMNet(): Running " + vmConfigVMCmd)
            subprocess.check_output(shlex.split(vmConfigVMCmd, posix=self.POSIX), encoding='utf-8')

            logging.debug("runConfigureVMNet(): Thread completed")
        except Exception:
            logging.error("runConfigureVMNet() Error: " + " cmd: " + vmConfigVMCmd)
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback)
        finally:
            self.readStatus = VMManage.MANAGER_IDLE
            self.writeStatus -= 1
            logging.debug("runConfigureVMNet(): sub 1 "+ str(self.writeStatus))

    def runVMCmd(self, cmd):
        logging.debug("VBoxManageWin: runVMCmd(): instantiated")
        try:
            self.readStatus = VMManage.MANAGER_READING
            self.writeStatus += 1
            logging.debug("runVMCmd(): adding 1 "+ str(self.writeStatus))
            vmCmd = self.vmanage_path + " " + cmd
            logging.debug("runVMCmd(): Running " + vmCmd)
            p = Popen(shlex.split(vmCmd, posix=self.POSIX), stdout=PIPE, stderr=PIPE, encoding="utf-8")
            while True:
                out = p.stdout.readline()
                if out == '' and p.poll() != None:
                    break
                if out != '':
                    logging.debug("output line: " + out)
            p.wait()
            
            logging.debug("runVMCmd(): Thread completed")
        except Exception:
            logging.error("runVMCmd() Error: " + " cmd: " + cmd)
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback)
        finally:
            self.readStatus = VMManage.MANAGER_IDLE
            self.writeStatus -= 1
            logging.debug("runVMCmd(): sub 1 "+ str(self.writeStatus))

    def getVMStatus(self, vmName):
        logging.debug("VBoxManage: getVMStatus(): instantiated " + vmName)
        #TODO: need to make this thread safe
        if vmName not in self.vms:
            logging.error("getVMStatus(): vmName does not exist: " + vmName)
            return None
        resVM = self.vms[vmName]
        #Don't want to rely on python objects in case we go with 3rd party clients in the future
        return {"vmName" : resVM.name, "vmUUID" : resVM.UUID, "setupStatus" : resVM.setupStatus, "vmState" : resVM.state, "adaptorInfo" : resVM.adaptorInfo, "groups" : resVM.groups}
        
    def getManagerStatus(self):
        logging.debug("VBoxManage: getManagerStatus(): instantiated")
        vmStatus = {}
        for vmName in self.vms:
            resVM = self.vms[vmName]
            vmStatus[resVM.name] = {"vmUUID" : resVM.UUID, "setupStatus" : resVM.setupStatus, "vmState" : resVM.state, "adaptorInfo" : resVM.adaptorInfo, "groups" : resVM.groups}
        return {"readStatus" : self.readStatus, "writeStatus" : self.writeStatus, "vmstatus" : vmStatus}

    def importVM(self, filepath):
        logging.debug("VBoxManage: importVM(): instantiated")
        cmd = "import \"" + filepath + "\" --options keepallmacs"
        t = threading.Thread(target=self.runVMCmd, args=(cmd,))
        t.start()
        return 0  

    def snapshotVM(self, vmName):
        logging.debug("VBoxManage: snapshotVM(): instantiated")
        #check to make sure the vm is known, if not should refresh or check name:
        if vmName not in self.vms:
            logging.error("snapshotVM(): " + vmName + " not found in list of known vms: \r\n" + str(self.vms))
            return -1
        cmd = " snapshot " + str(self.vms[vmName].UUID) + " take snapshot"
        t = threading.Thread(target=self.runVMCmd, args=(cmd,))
        t.start()
        return 0

    def exportVM(self, vmName, filepath):
        logging.debug("VBoxManage: importVM(): instantiated")
        #first remove any quotes that may have been entered before (because we will add some after we add the file and extension)
        if vmName not in self.vms:
            logging.error("exportVM(): vmName does not exist. Skipping... " + vmName)
            return None
        filepath = filepath.replace("\"","")
        exportfilename = os.path.join(filepath,vmName+".ova")
        cmd = "export " + self.vms[vmName].UUID + " -o \"" + exportfilename + "\" --iso"
        t = threading.Thread(target=self.runVMCmd, args=(cmd,))
        t.start()
        return 0

    def startVM(self, vmName):
        logging.debug("VBoxManage: startVM(): instantiated")
        #check to make sure the vm is known, if not should refresh or check name:
        if vmName not in self.vms:
            logging.error("startVM(): " + vmName + " not found in list of known vms: \r\n" + str(self.vms))
            return -1
        cmd = "startvm " + str(self.vms[vmName].UUID) + " --type headless"
        t = threading.Thread(target=self.runVMCmd, args=(cmd,))
        t.start()
        return 0

    def suspendVM(self, vmName):
        logging.debug("VBoxManage: suspendVM(): instantiated")
        #check to make sure the vm is known, if not should refresh or check name:
        if vmName not in self.vms:
            logging.error("suspendVM(): " + vmName + " not found in list of known vms: \r\n" + str(self.vms))
            return -1
        cmd = "controlvm " + str(self.vms[vmName].UUID) + " savestate"
        t = threading.Thread(target=self.runVMCmd, args=(cmd,))
        t.start()
        return 0

    def stopVM(self, vmName):
        logging.debug("VBoxManage: stopVM(): instantiated")
        #check to make sure the vm is known, if not should refresh or check name:
        if vmName not in self.vms:
            logging.error("stopVM(): " + vmName + " not found in list of known vms: \r\n" + str(self.vms))
            return -1
        cmd = "controlvm " + str(self.vms[vmName].UUID) + " poweroff"
        t = threading.Thread(target=self.runVMCmd, args=(cmd,))
        t.start()
        return 0

    def removeVM(self, vmName):
        logging.debug("VBoxManage: removeVM(): instantiated")
        #check to make sure the vm is known, if not should refresh or check name:
        if vmName not in self.vms:
            logging.error("removeVM(): " + vmName + " not found in list of known vms: \r\n" + str(self.vms))
            return -1
        cmd = "unregistervm " + str(self.vms[vmName].UUID) + " --delete"
        t = threading.Thread(target=self.runVMCmd, args=(cmd,))
        t.start()
        return 0

    def cloneVMConfigAll(self, vmName, cloneName, cloneSnapshots, linkedClones, groupName, internalNets, vrdpPort, refreshVMInfo=False):
        logging.debug("VBoxManage: cloneVMConfigAll(): instantiated")
        #check to make sure the vm is known, if not should refresh or check name:
        if vmName not in self.vms:
            logging.error("cloneVMConfigAll(): " + vmName + " not found in list of known vms: \r\n" + str(self.vms))
            return -1
        if refreshVMInfo == True:
            self.refreshVMInfo(vmName)
        t = threading.Thread(target=self.runCloneVMConfigAll, args=(vmName, cloneName, cloneSnapshots, linkedClones, groupName, internalNets, vrdpPort))
        t.start()
        return 0

    def runCloneVMConfigAll(self, vmName, cloneName, cloneSnapshots, linkedClones, groupName, internalNets, vrdpPort):
        logging.debug("VBoxManage: runCloneVMConfigAll(): instantiated")
        try:
            self.readStatus = VMManage.MANAGER_READING
            self.writeStatus += 1
            logging.debug("runCloneVMConfigAll(): adding 1 "+ str(self.writeStatus))
            #first clone
            #Check that vm does exist
            if vmName not in self.vms:
                logging.error("runCloneVMConfigAll(): " + vmName + " not found in list of known vms: \r\n" + str(self.vms))
                return
            #Check that clone does not yet exist
            self.runCloneVM(vmName, cloneName, cloneSnapshots, linkedClones, groupName)
            
            #netsetup
            if cloneName not in self.vms:
                logging.error("runCloneVMConfigAll(): " + cloneName + " not found in list of known vms: \r\n" + str(self.vms))
                return
            self.runConfigureVMNets(cloneName, internalNets)

            #vrdp setup (if applicable)
            if vrdpPort != None:
                self.runEnableVRDP(cloneName, vrdpPort)
            
            #create snap
            snapcmd = self.vmanage_path + " snapshot " + str(self.vms[cloneName].UUID) + " take snapshot"
            logging.debug("runCloneVMConfigAll(): Running " + snapcmd)
            p = Popen(shlex.split(snapcmd, posix=self.POSIX), stdout=PIPE, stderr=PIPE, encoding="utf-8")
            while True:
                out = p.stdout.readline()
                if out == '' and p.poll() != None:
                    break
                if out != '':
                    logging.debug("runCloneVMConfigAll(): snapproc out: " + out)
            p.wait()
            logging.debug("runCloneVMConfigAll(): Thread completed")

        except Exception:
            logging.error("runCloneVMConfigAll(): Error in runCloneVMConfigAll(): An error occured ")
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback)
        finally:
            self.readStatus = VMManage.MANAGER_IDLE
            self.writeStatus -= 1
            logging.debug("runCloneVMConfigAll(): sub 1 "+ str(self.writeStatus))

    def cloneVM(self, vmName, cloneName, cloneSnapshots, linkedClones, groupName, refreshVMInfo=False):
        logging.debug("VBoxManage: cloneVM(): instantiated")
        #check to make sure the vm is known, if not should refresh or check name:
        if vmName not in self.vms:
            logging.error("cloneVM(): " + vmName + " not found in list of known vms: \r\n" + str(self.vms))
            return -1
        if refreshVMInfo == True:
            self.refreshVMInfo(vmName)
        t = threading.Thread(target=self.runCloneVM, args=(vmName, cloneName, cloneSnapshots, linkedClones, groupName))
        t.start()
        return 0

    def runCloneVM(self, vmName, cloneName, cloneSnapshots, linkedClones, groupName):
        logging.debug("VBoxManage: runCloneVM(): instantiated")
        try:
            self.readStatus = VMManage.MANAGER_READING
            self.writeStatus += 1
            logging.debug("runCloneVM(): adding 1 "+ str(self.writeStatus))
            #First check that the clone doesn't exist:
            if cloneName in self.vms:
                logging.error("runCloneVM(): A VM with the clone name already exists and is registered... skipping " + str(cloneName))
                return
            #Call runVMCommand
            cloneCmd = self.vmanage_path + " clonevm " + str(self.vms[vmName].UUID) + " --register"
            #NOTE, the following logic is not in error. Linked clone can only be created from a snapshot.
            if cloneSnapshots == 'true':
                cloneSnapshotUUID = self.vms[vmName].latestSnapUUID
                #linked Clones option requires a cloneSnapshotUUID to be specified
                if linkedClones == 'true' and cloneSnapshotUUID != "":
                    logging.debug("runCloneVM(): using linked clones")
                    # get the name of the newest snapshot
                    #getSnapCmd = [self.vmanage_path, "snapshot", self.vms[vmName].UUID, "list", "--machinereadable"]
                    cloneCmd += " --options "
                    cloneCmd += " link "
                    cloneCmd += " --snapshot " + str(cloneSnapshotUUID)                    
                else:
                    cloneCmd += " --mode "
                    cloneCmd += " all "
            cloneCmd += " --options keepallmacs "                
            cloneCmd += " --name "
            cloneCmd += str(cloneName)
            logging.debug("runCloneVM(): executing: " + str(cloneCmd))
            result = subprocess.check_output(shlex.split(cloneCmd, posix=self.POSIX), encoding='utf-8')

            #groupCmd = [self.vmanage_path, "modifyvm", cloneName, "--groups", groupName]
            groupCmd = self.vmanage_path + " modifyvm " + str(cloneName) + " --groups \"" + str(groupName)+"\""
            logging.debug("runCloneVM(): placing into group: " + str(groupName))
            logging.error("runCloneVM(): executing: " + str(groupCmd))
            result = subprocess.check_output(shlex.split(groupCmd, posix=self.POSIX), encoding='utf-8')

            logging.debug("runCloneVM(): Clone Created: " + str(cloneName) + " and placed into group: " + groupName)
            #since we added a VM, now we have to add it to the known list
            logging.debug("runCloneVM(): Adding: " + str(cloneName) + " to known VMs")
            self.addVMByName(cloneName)

        except Exception:
            logging.error("runCloneVM(): Error in runCloneVM(): An error occured; it could be due to a missing snapshot for the VM")
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback)
        finally:
            self.readStatus = VMManage.MANAGER_IDLE
            self.writeStatus -= 1
            logging.debug("runCloneVM(): sub 1 "+ str(self.writeStatus))

    def enableVRDPVM(self, vmName, vrdpPort):
        logging.debug("VBoxManage: enabledVRDP(): instantiated")
        #check to make sure the vm is known, if not should refresh or check name:
        if vmName not in self.vms:
            logging.error("enabledVRDP(): " + vmName + " not found in list of known vms: \r\n" + str(self.vms))
            return -1
        t = threading.Thread(target=self.runEnableVRDP, args=(vmName, vrdpPort))
        t.start()
        return 0

    def runEnableVRDP(self, vmName, vrdpPort):
        logging.debug("VBoxManage: runEnabledVRDP(): instantiated")
        try:
            self.readStatus = VMManage.MANAGER_READING
            self.writeStatus += 1
            logging.debug("runEnableVRDP(): adding 1 "+ str(self.writeStatus))
            #vrdpCmd = [self.vmanage_path, "modifyvm", vmName, "--vrde", "on", "--vrdeport", str(vrdpPort)]
            vrdpCmd = self.vmanage_path + " modifyvm " + str(vmName) + " --vrde " + " on " + " --vrdeport " + str(vrdpPort)
            logging.debug("runEnableVRDP(): setting up vrdp for " + vmName)
            logging.debug("runEnableVRDP(): executing: "+ str(vrdpCmd))
            result = subprocess.check_output(shlex.split(vrdpCmd, posix=self.POSIX), encoding='utf-8')
            #now these settings will help against the issue when users 
            #can't reconnect after an abrupt disconnect
            #https://www.virtualbox.org/ticket/2963
            vrdpCmd = self.vmanage_path + " modifyvm " + str(vmName) + " --vrdemulticon " + " on " #" --vrdereusecon " + " on " + " --vrdemulticon " + " off"
            logging.debug("runEnableVRDP(): Setting disconnect on new connection for " + vmName)
            logging.debug("runEnableVRDP(): executing: " + str(vrdpCmd))
            result = subprocess.check_output(shlex.split(vrdpCmd, posix=self.POSIX), encoding='utf-8')            
            logging.debug("runEnableVRDP(): completed")
        except Exception:
            logging.error("runEnableVRDP(): Error in runEnableVRDP(): An error occured ")
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback)
        finally:
            self.readStatus = VMManage.MANAGER_IDLE
            self.writeStatus -= 1
            logging.debug("runEnableVRDP(): sub 1 "+ str(self.writeStatus))

    def restoreLatestSnapVM(self, vmName):
        logging.debug("VBoxManage: restoreLatestSnapVM(): instantiated")
        #check to make sure the vm is known, if not should refresh or check name:
        if vmName not in self.vms:
            logging.error("restoreLatestSnapVM(): " + vmName + " not found in list of known vms: \r\n" + str(self.vms))
            return -1

        cmd = "snapshot " + str(self.vms[vmName].UUID) + " restorecurrent"
        t = threading.Thread(target=self.runVMCmd, args=(cmd,))
        t.start()
        return 0
