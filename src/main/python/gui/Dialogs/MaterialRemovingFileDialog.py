from PyQt5.QtCore import QDateTime, Qt, QTimer, QThread, pyqtSignal, QObject
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QDateTimeEdit,
        QDial, QDialog, QDialogButtonBox, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
        QProgressBar, QPushButton, QRadioButton, QScrollBar, QSizePolicy,
        QSlider, QSpinBox, QStyleFactory, QTableWidget, QTabWidget, QTextEdit,
        QVBoxLayout, QWidget, QMessageBox)
import sys, traceback
import logging
import shutil
import os

class MaterialRemoveThread(QThread):
    watchsignal = pyqtSignal('PyQt_PyObject', 'PyQt_PyObject', 'PyQt_PyObject')

    def __init__(self, filenames, destinationPath):
        QThread.__init__(self)
        logging.debug("MaterialRemoveThread(): instantiated")
        
        self.filenames = filenames
        self.destinationPath = destinationPath

    # run method gets called when we start the thread
    def run(self):
        logging.debug("MaterialRemoveThread(): instantiated")
        stringExec = "Removing file from " + str(self.destinationPath)
        self.watchsignal.emit(stringExec, None, None)
        try:
            fullfilename = os.path.join(self.destinationPath,self.filenames)
            logging.debug("MaterialRemoveThread(): removing file: " + str(fullfilename))
            stringExec = "Removing file " + fullfilename
            self.watchsignal.emit( stringExec, None, None)
            if os.path.exists(fullfilename):
                os.remove(fullfilename)
                self.watchsignal.emit("Finished Removing Files", None, True)
            else:
                self.watchsignal.emit("File not found in experiment folder; skipping", None, True)
            logging.debug("MaterialRemoveThread(): thread ending")
            
            return
        except FileNotFoundError:
            logging.error("Error in MaterialRemoveThread(): File not found")
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback)
            return None
        except Exception:
            logging.error("Error in MaterialRemoveThread(): An error occured ")
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback)
            return None

class MaterialRemovingFileDialog(QDialog):
    def __init__(self, parent, filenames, destinationPath):
        logging.debug("MaterialRemovingFileDialog(): instantiated")
        super(MaterialRemovingFileDialog, self).__init__(parent)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
              
        self.filenames = filenames
        self.destinationPath = destinationPath

        self.buttons = QDialogButtonBox()
        self.ok_button = self.buttons.addButton( self.buttons.Ok )
        self.ok_button.setEnabled(False)
        
        self.buttons.accepted.connect( self.accept )
        self.setWindowTitle("Removing File")
        #self.setFixedSize(225, 75)
                
        self.box_main_layout = QGridLayout()
        self.box_main = QWidget()
        self.box_main.setLayout(self.box_main_layout)
       
        self.statusLabel = QLabel("Initializing please wait...")
        self.statusLabel.setAlignment(Qt.AlignCenter)
        self.box_main_layout.addWidget(self.statusLabel, 1, 0)
        
        self.box_main_layout.addWidget(self.buttons, 2,0)
        
        self.setLayout(self.box_main_layout)
        self.status = -1
        
    def exec_(self):
        t = MaterialRemoveThread(self.filenames, self.destinationPath)
        t.watchsignal.connect(self.setStatus)
        t.start()
        result = super(MaterialRemovingFileDialog, self).exec_()
        logging.debug("exec_(): initiated")
        logging.debug("exec_: self.status: " + str(self.status))
        return self.status

    def setStatus(self, msg, status, buttonEnabled):
        if status != None:
            self.status = status
            
        self.statusLabel.setText(msg)
        self.statusLabel.adjustSize()
        self.adjustSize()

        if buttonEnabled != None:
            if buttonEnabled == True:
                self.ok_button.setEnabled(True)
            else:
                self.ok_button.setEnabled(False)