import logging
import shlex
import argparse
import sys
from time import sleep
from engine.Manager.ConnectionManage.ConnectionManageGuacRDP import ConnectionManageGuacRDP
from engine.Manager.PackageManage.PackageManageVBox import PackageManageVBox
from engine.Manager.ExperimentManage.ExperimentManageVBox import ExperimentManageVBox
import threading

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    logging.debug("Starting Program")
###Base Engine tests
    logging.debug("Instantiating Engine")
    e = Engine()
    logging.debug("engine object: " + str(e))

    logging.debug("Calling Engine.getInstance()")
    e = Engine.getInstance()
    logging.debug("engine object: " + str(e))

    logging.debug("Calling Engine.getInstance()")
    e = Engine.getInstance()
    logging.debug("engine object: " + str(e))

###Engine tests
    res = e.execute("engine status ")

###Packager tests
    #e.execute(sys.argv[1:])
    e.execute("packager status")
    
    ###import
    e.execute("packager import resfile.res")
    res = e.execute("packager status")
    while res["writeStatus"] != PackageManageVBox.PACKAGE_MANAGE_COMPLETE:
        sleep(1)
        logging.debug("Waiting for package import to complete...")
        res = e.execute("packager status")
    logging.debug("Package import complete.")
    
    e.execute("packager export ExperimentData/sample/Experiments/sample_configfile.xml myresfile.res")
    res = e.execute("packager status")
    while res["writeStatus"] != PackageManageVBox.PACKAGE_MANAGE_COMPLETE:
        sleep(1)
        logging.debug("Waiting for package export to complete...")
        res = e.execute("packager status")
    logging.debug("Package export complete.") 
    
###Connection tests
    # sleep(60)#alternative, check status until packager is complete and idle
    e.execute("conns status")
    e.execute("conns create ExperimentData/sample/Experiments/sample_configfile.xml")

    # sleep(10) #alternative, check status until connection manager is complete and idle
    e.execute("conns status")
    e.execute("conns remove ExperimentData/sample/Experiments/sample_configfile.xml")
    
    # sleep(10) #alternative, check status until connection manager is complete and idle
    e.execute("conns status")
    e.execute("conns open ExperimentData/sample/Experiments/sample_configfile.xml 1 1")

    #####---Create Experiment Test#####
    logging.info("Starting Experiment")
    e.execute("experiment create ExperimentData/sample/Experiments/sample_configfile.xml")
    res = e.execute("experiment status")
    logging.debug("Waiting for experiment create to complete...")
    while res["writeStatus"] != ExperimentManageVBox.EXPERIMENT_MANAGE_COMPLETE:
        sleep(1)
        logging.debug("Waiting for experiment create to complete...")
        res = e.execute("experiment status")
    logging.debug("Experiment create complete.")    

    #####---Start Experiment Test#####
    logging.info("Starting Experiment")
    e.execute("experiment start ExperimentData/sample/Experiments/sample_configfile.xml")
    res = e.execute("experiment status")
    logging.debug("Waiting for experiment start to complete...")
    while res["writeStatus"] != ExperimentManageVBox.EXPERIMENT_MANAGE_COMPLETE:
        sleep(1)
        logging.debug("Waiting for experiment start to complete...")
        res = e.execute("experiment status")
    logging.debug("Experiment start complete.")    

    #####---Stop Experiment Test#####
    sleep(5)
    logging.info("Stopping Experiment")
    e.execute("experiment stop ExperimentData/sample/Experiments/sample_configfile.xml")
    res = e.execute("experiment status")
    logging.debug("Waiting for experiment stop to complete...")
    while res["writeStatus"] != ExperimentManageVBox.EXPERIMENT_MANAGE_COMPLETE:
        sleep(1)
        logging.debug("Waiting for experiment stop to complete...")
        res = e.execute("experiment status")
    logging.debug("Experiment stop complete.")    

    #####---Remove Experiment Test#####
    sleep(5)
    logging.info("Remove Experiment")
    e.execute("experiment remove ExperimentData/sample/Experiments/sample_configfile.xml")
    res = e.execute("experiment status")
    logging.debug("Waiting for experiment remove to complete...")
    while res["writeStatus"] != ExperimentManageVBox.EXPERIMENT_MANAGE_COMPLETE:
        sleep(1)
        logging.debug("Waiting for experiment remove to complete...")
        res = e.execute("experiment status")
    logging.debug("Experiment remove complete.")    

    sleep(3) #allow some time for observation
    #quit
