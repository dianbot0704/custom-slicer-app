import qt
import slicer
from pages import Page0, Page1, Page2, Page3
from slicer.ScriptedLoadableModule import (
    ScriptedLoadableModule,
    ScriptedLoadableModuleLogic,
    ScriptedLoadableModuleWidget,
)

CUSTOM_LAYOUT_ID_BASE = 255


class IntraOperativePlan(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        parent.title = "Intra-Operative Planning"
        parent.categories = ["Example"]
        parent.contributors = [""]


class IntraOperativePlanWidget(ScriptedLoadableModuleWidget):
    def __init__(self, parent=None):
        ScriptedLoadableModuleWidget.__init__(self, parent)
        self._currentActivePage = None
        self._pages = []
        self._dockStack = None
        self._modulePanelHidden = False

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)
        self.mainLayout = self.parent.layout()
        if self.mainLayout is None:
            self.mainLayout = qt.QVBoxLayout(self.parent)
            self.parent.setLayout(self.mainLayout)

        nav_callbacks = {"on_previous": self._go_to_previous_page, "on_next": self._go_to_next_page}
        self.page_0 = Page0(resourcePath=self.resourcePath, layout_id=CUSTOM_LAYOUT_ID_BASE + 1, **nav_callbacks)
        self.page_1 = Page1(resourcePath=self.resourcePath, **nav_callbacks)
        self.page_2 = Page2(resourcePath=self.resourcePath, **nav_callbacks)
        self.page_3 = Page3(resourcePath=self.resourcePath, layout_id=CUSTOM_LAYOUT_ID_BASE + 2, **nav_callbacks)

        self._pages = [self.page_0, self.page_1, self.page_2, self.page_3]

        self._dockStack = qt.QStackedWidget()
        self._dockStack.hide()
        self.mainLayout.addWidget(self._dockStack)

        for page in self._pages:
            if page.showsInDock:
                self._dockStack.addWidget(page)

    def enter(self):
        if not self._pages:
            return

        if self._currentActivePage is None:
            self._activate_page(self._pages[0])
        else:
            self._activate_page(self._currentActivePage, force=True)

    def exit(self):
        if self._currentActivePage:
            self._currentActivePage.exit()
        self._showModulePanel()

    def _hideModulePanel(self):
        mainWindow = slicer.util.mainWindow()
        if mainWindow:
            panel = mainWindow.findChild("QDockWidget", "PanelDockWidget")
            if panel:
                panel.hide()
                # Track state but do not use it as a guard so we can hide again if Slicer re-shows the panel.
                self._modulePanelHidden = True

    def _showModulePanel(self):
        if not self._modulePanelHidden:
            return
        mainWindow = slicer.util.mainWindow()
        if mainWindow:
            panel = mainWindow.findChild("QDockWidget", "PanelDockWidget")
            if panel:
                panel.show()
                self._modulePanelHidden = False

    def _activate_page(self, page, *, force=False):
        if page is None:
            return

        if page is self._currentActivePage and not force:
            return

        if page is not self._currentActivePage and self._currentActivePage:
            self._currentActivePage.exit()

        self._update_dock_widget_visibility(page)

        if page is not self._currentActivePage:
            self._currentActivePage = page

        page.enter()

    def _update_dock_widget_visibility(self, page):
        if page.showsInDock:
            if self._dockStack:
                if self._dockStack.indexOf(page) == -1:
                    self._dockStack.addWidget(page)
                self._dockStack.setCurrentWidget(page)
                self._dockStack.show()
            self._showModulePanel()
        else:
            if self._dockStack:
                self._dockStack.hide()
            qt.QTimer.singleShot(0, self._hideModulePanel)

    def _go_to_next_page(self):
        self._go_to_page_offset(1)

    def _go_to_previous_page(self):
        self._go_to_page_offset(-1)

    def _go_to_page_offset(self, offset):
        if not self._currentActivePage:
            return

        try:
            current_index = self._pages.index(self._currentActivePage)
        except ValueError:
            return

        target_index = current_index + offset
        if 0 <= target_index < len(self._pages):
            self._activate_page(self._pages[target_index])


class IntraOperativePlanLogic(ScriptedLoadableModuleLogic):
    pass


class PatientManagementLayout(qt.QWidget):
    def __init__(self, resourcePath, parent=None):
        super().__init__(parent)
        ui_widget = slicer.util.loadUI(resourcePath("UI/PatientManagement.ui"))
        layout = qt.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(ui_widget)
        self.ui = slicer.util.childWidgetVariables(ui_widget)
