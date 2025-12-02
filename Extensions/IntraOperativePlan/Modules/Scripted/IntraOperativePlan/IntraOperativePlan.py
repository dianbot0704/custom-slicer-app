from slicer.ScriptedLoadableModule import (
    ScriptedLoadableModule,
    ScriptedLoadableModuleWidget,
    ScriptedLoadableModuleLogic,
)
import slicer
import qt
import logging
import os

PATIENT_MANAGEMENT_LAYOUT_ID = 255 + 1


class IntraOperativePlan(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        parent.title = "Intra-Operative Planning"
        parent.categories = ["Example"]
        parent.contributors = [""]


class IntraOperativePlanWidget(ScriptedLoadableModuleWidget):
    def __init__(self, parent=None):
        ScriptedLoadableModuleWidget.__init__(self, parent)
        self._previousLayout = None

    def setup(self):
        self.patient_mgmt_layout = PatientManagementLayout(parent=None, resourcePath=self.resourcePath)
        self.patient_mgmt_viewf = slicer.qSlicerSingletonViewFactory()
        self.patient_mgmt_viewf.setTagName("patient_mgmt")
        self.patient_mgmt_viewf.setWidget(self.patient_mgmt_layout)
        lm = slicer.app.layoutManager()
        if lm is not None:
            lm.registerViewFactory(self.patient_mgmt_viewf)
            layout_node = lm.layoutLogic().GetLayoutNode()
            patient_mgmt_layout_tag = (
                '<layout type="horizontal"><item><patient_mgmt></patient_mgmt></item></layout>'
            )
            layout_node.AddLayoutDescription(PATIENT_MANAGEMENT_LAYOUT_ID, patient_mgmt_layout_tag)

    def enter(self):
        lm = slicer.app.layoutManager()
        if lm is not None:
            self._previousLayout = lm.layout
            lm.setLayout(PATIENT_MANAGEMENT_LAYOUT_ID)
        qt.QTimer.singleShot(0, self._hideModulePanel)

    def exit(self):
        self._showModulePanel()
        lm = slicer.app.layoutManager()
        if lm is not None and self._previousLayout is not None:
            lm.setLayout(self._previousLayout)
        qt.QTimer.singleShot(0, self._showModulePanel)

    def _hideModulePanel(self):
        mainWindow = slicer.util.mainWindow()
        if mainWindow:
            panel = mainWindow.findChild("QDockWidget", "PanelDockWidget")
            if panel:
                panel.hide()

    def _showModulePanel(self):
        mainWindow = slicer.util.mainWindow()
        if mainWindow:
            panel = mainWindow.findChild("QDockWidget", "PanelDockWidget")
            if panel:
                panel.show()


class IntraOperativePlanLogic(ScriptedLoadableModuleLogic):
    pass


class PatientManagementLayout(qt.QWidget):
    def __init__(self, parent=None, resourcePath=None):
        super().__init__(parent)
        ui_widget = slicer.util.loadUI(resourcePath("UI/PatientManagement.ui"))
        layout = qt.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(ui_widget)
        self.ui = slicer.util.childWidgetVariables(ui_widget)
