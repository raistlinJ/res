from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QSize
from PyQt5 import QtWidgets, uic
from gui.Widgets.NetworkAdaptorWidget import NetworkAdaptorWidget
import logging

class VMWidget(QtWidgets.QWidget):

    def __init__(self, parent=None, vmjsondata=None):
        logging.debug("VMWidget instantiated")
        QtWidgets.QWidget.__init__(self, parent=None)
        self.netAdaptors = []

        self.setObjectName("VMWidget")
        self.layoutWidget = QtWidgets.QWidget(parent)
        self.layoutWidget.setObjectName("layoutWidget")

        self.outerVertBox = QtWidgets.QVBoxLayout(self.layoutWidget)
        self.outerVertBox.setContentsMargins(0, 0, 0, 0)
        self.outerVertBox.setObjectName("outerVertBox")

        self.nameHLayout = QtWidgets.QHBoxLayout()
        self.nameHLayout.setObjectName("nameHLayout")
        self.nameLabel = QtWidgets.QLabel(self.layoutWidget)
        self.nameLabel.setObjectName("nameLabel")
        self.nameLabel.setText("Name:")
        self.nameHLayout.addWidget(self.nameLabel)
        self.nameLineEdit = QtWidgets.QLineEdit(self.layoutWidget)
        self.nameLineEdit.setAcceptDrops(False)
        self.nameLineEdit.setReadOnly(True)
        self.nameLineEdit.setObjectName("nameLineEdit")
        self.nameHLayout.addWidget(self.nameLineEdit)
        self.outerVertBox.addLayout(self.nameHLayout)
        self.vrdpEnabledHorBox = QtWidgets.QHBoxLayout()
        self.vrdpEnabledHorBox.setObjectName("vrdpEnabledHorBox")
        self.vrdpEnabledLabel = QtWidgets.QLabel(self.layoutWidget)
        self.vrdpEnabledLabel.setText("VRDP Enabled:")
        self.vrdpEnabledLabel.setObjectName("vrdpEnabledLabel")
        self.vrdpEnabledHorBox.addWidget(self.vrdpEnabledLabel)

        self.vrdpEnabledComboBox = QtWidgets.QComboBox(self.layoutWidget)
        self.vrdpEnabledComboBox.setObjectName("vrdpEnabledComboBox")
        self.vrdpEnabledComboBox.addItem("false")
        self.vrdpEnabledComboBox.addItem("true")
        self.vrdpEnabledHorBox.addWidget(self.vrdpEnabledComboBox)
        self.outerVertBox.addLayout(self.vrdpEnabledHorBox)

        self.iNetScrollArea = QtWidgets.QScrollArea()
        self.iNetVertBox = QtWidgets.QVBoxLayout()
        self.iNetVertBox.setObjectName("iNetVertBox")
        self.iNetScrollArea.setLayout(self.iNetVertBox)
        self.outerVertBox.addWidget(self.iNetScrollArea)
        
        self.addAdaptorButton = QtWidgets.QPushButton(self.layoutWidget)
        self.addAdaptorButton.setObjectName("addAdaptorButton")
        self.addAdaptorButton.setText("Add Network Adaptor")
        self.addAdaptorButton.clicked.connect(self.addAdaptor)
        self.outerVertBox.addWidget(self.addAdaptorButton, alignment=QtCore.Qt.AlignHCenter)
        self.setLayout(self.outerVertBox)
        self.retranslateUi(vmjsondata)

    def retranslateUi(self, vmjsondata):
        logging.debug("VMWidget: retranslateUi(): instantiated")
        self.nameLineEdit.setText(vmjsondata["name"])
        self.vrdpEnabledComboBox.setCurrentIndex(self.vrdpEnabledComboBox.findText(vmjsondata["vrdp-enabled"]))

        ###add adaptors
        if "internalnet-basename" in vmjsondata:
            if isinstance(vmjsondata["internalnet-basename"], list):
                for adaptor in vmjsondata["internalnet-basename"]:
                    self.addAdaptor(adaptor)
            else:
                self.addAdaptor(vmjsondata["internalnet-basename"])

    def addAdaptor(self, adaptorname="intnet", adaptortype="intnet"):
        logging.debug("VMWidget: addAdaptor(): instantiated: " + str(adaptorname) + " " + str(adaptortype))
        logging.debug("addAdaptor() instantiated")
        networkAdaptor = NetworkAdaptorWidget()
        networkAdaptor.lineEdit.setText("intnet")

        self.iNetVertBox.addWidget(networkAdaptor)
        self.netAdaptors.append(networkAdaptor)

    def getWritableData(self):
        logging.debug("VMWidget: getWritableData(): instantiated")
        #build JSON from text entry fields
        jsondata = {}
        jsondata["name"] = {}
        jsondata["name"] = self.nameLineEdit.text()
        jsondata["vrdp-enabled"] = {}
        jsondata["vrdp-enabled"] = self.vrdpEnabledComboBox.currentText()
        jsondata["internalnet-basename"] = [] #may be many
        for netAdaptor in self.netAdaptors:
            if isinstance(netAdaptor, NetworkAdaptorWidget):
                jsondata["internalnet-basename"].append(netAdaptor.lineEdit.text())
        return jsondata

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ui = VMWidget()
    ui.show()
    sys.exit(app.exec_())