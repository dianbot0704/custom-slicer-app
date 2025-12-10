from slicer.ScriptedLoadableModule import (
    ScriptedLoadableModule,
    ScriptedLoadableModuleWidget,
    ScriptedLoadableModuleLogic,
)
import slicer
import qt
import logging
import os

PATIENT_MANAGEMENT_LAYOUT_ID = 255 + 0


class IntraOperativePlan(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        parent.title = "Intra-Operative Planning"
        parent.categories = ["Example"]
        parent.contributors = [""]

class BasePage(qt.QWidget):
    def __init__(
        self,
        resourcePath,
        ui_filename=None,
        on_previous=None,
        on_next=None,
        show_in_dock=True,
        parent=None,
    ):
        super().__init__(parent)
        self._resourcePath = resourcePath
        self._on_previous = on_previous
        self._on_next = on_next
        self._showsInDock = show_in_dock
        self.ui = None

        if ui_filename:
            self._initialize_ui(ui_filename)

    @property
    def showsInDock(self):
        return self._showsInDock

    def _initialize_ui(self, ui_filename):
        loaded_widget = slicer.util.loadUI(self._resourcePath(ui_filename))
        layout = qt.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(loaded_widget)
        self.ui = slicer.util.childWidgetVariables(loaded_widget)
        self._connect_navigation_buttons()

    def _connect_navigation_buttons(self):
        if not self.ui:
            return

        previous_button = getattr(self.ui, "navPreviousButton", None)
        next_button = getattr(self.ui, "navNextButton", None)

        if previous_button and self._on_previous:
            previous_button.clicked.connect(self._on_previous)
        if next_button and self._on_next:
            next_button.clicked.connect(self._on_next)

    def enter(self):
        pass

    def exit(self):
        pass


class DockWidgetPage(BasePage):
    def __init__(self, resourcePath, ui_filename, on_previous=None, on_next=None, parent=None):
        super().__init__(
            resourcePath=resourcePath,
            ui_filename=ui_filename,
            on_previous=on_previous,
            on_next=on_next,
            show_in_dock=True,
            parent=parent,
        )


class CustomLayoutPage(BasePage):
    def __init__(
        self,
        resourcePath,
        ui_filename,
        layout_id,
        tag_name,
        layout_description=None,
        on_previous=None,
        on_next=None,
        parent=None,
    ):
        super().__init__(
            resourcePath=resourcePath,
            ui_filename=ui_filename,
            on_previous=on_previous,
            on_next=on_next,
            show_in_dock=False,
            parent=parent,
        )
        self._layout_id = layout_id
        self._tag_name = tag_name
        self._layout_description = layout_description or self._default_layout_description()
        self._viewFactory = slicer.qSlicerSingletonViewFactory()
        self._viewFactory.setTagName(self._tag_name)
        self._viewFactory.setWidget(self)
        self._layoutRegistered = False
        self._previousLayoutId = None

    def _default_layout_description(self):
        return f"<layout type=\"horizontal\"><item><{self._tag_name}></{self._tag_name}></item></layout>"

    def _ensure_layout_registered(self):
        if self._layoutRegistered:
            return True

        lm = slicer.app.layoutManager()
        if lm is None:
            logging.warning("Unable to register custom layout '%s': layout manager unavailable", self._tag_name)
            return False

        lm.registerViewFactory(self._viewFactory)
        layout_logic = lm.layoutLogic()
        if layout_logic is None:
            logging.warning("Unable to register custom layout '%s': layout logic unavailable", self._tag_name)
            return False

        layout_node = layout_logic.GetLayoutNode()
        if layout_node is None:
            logging.warning("Unable to register custom layout '%s': layout node unavailable", self._tag_name)
            return False

        layout_node.AddLayoutDescription(self._layout_id, self._layout_description)
        self._layoutRegistered = True
        return True

    def enter(self):
        if not self._ensure_layout_registered():
            return

        lm = slicer.app.layoutManager()
        if lm is None:
            logging.warning("Unable to activate custom layout '%s': layout manager unavailable", self._tag_name)
            return

        self._previousLayoutId = lm.layout
        lm.setLayout(self._layout_id)

    def exit(self):
        lm = slicer.app.layoutManager()
        if lm is None:
            self._previousLayoutId = None
            return
        if self._previousLayoutId is not None:
            lm.setLayout(self._previousLayoutId)
        self._previousLayoutId = None


class Page1(DockWidgetPage):
    def __init__(self, resourcePath, on_previous=None, on_next=None, parent=None):
        super().__init__(
            resourcePath=resourcePath,
            ui_filename="UI/template_page1_mrml.ui",
            on_previous=on_previous,
            on_next=on_next,
            parent=parent,
        )


class Page2(DockWidgetPage):
    def __init__(self, resourcePath, on_previous=None, on_next=None, parent=None):
        super().__init__(
            resourcePath=resourcePath,
            ui_filename="UI/template_page2_mrml.ui",
            on_previous=on_previous,
            on_next=on_next,
            parent=parent,
        )


class Page3(CustomLayoutPage):
    def __init__(self, resourcePath, on_previous=None, on_next=None, parent=None):
        tag_name = "page_3"
        layout_description = f"<layout type=\"horizontal\"><item><{tag_name}></{tag_name}></item></layout>"
        super().__init__(
            resourcePath=resourcePath,
            ui_filename="UI/template_page3_no_mrml.ui",
            layout_id=PATIENT_MANAGEMENT_LAYOUT_ID + 1,
            tag_name=tag_name,
            layout_description=layout_description,
            on_previous=on_previous,
            on_next=on_next,
            parent=parent,
        ) 


class Page0(CustomLayoutPage):
    def __init__(self, resourcePath, on_previous=None, on_next=None, parent=None):
        tag_name = "page_0"
        layout_description = f"<layout type=\"horizontal\"><item><{tag_name}></{tag_name}></item></layout>"
        super().__init__(
            resourcePath=resourcePath,
            ui_filename="UI/template_page0_no_mrml.ui",
            layout_id=PATIENT_MANAGEMENT_LAYOUT_ID,
            tag_name=tag_name,
            layout_description=layout_description,
            on_previous=on_previous,
            on_next=on_next,
            parent=parent,
        )


class IntraOperativePlanWidget(ScriptedLoadableModuleWidget):
    def __init__(self, parent=None):
        ScriptedLoadableModuleWidget.__init__(self, parent)
        self._currentActivePage = None
        self._pages = []
        self._dockStack = None
        self._modulePanelHidden = False

    def setup(self):
        self.mainLayout = self.parent.layout()
        if self.mainLayout is None:
            self.mainLayout = qt.QVBoxLayout(self.parent)
            self.parent.setLayout(self.mainLayout)

        nav_callbacks = dict(on_previous=self._go_to_previous_page, on_next=self._go_to_next_page)
        self.page_0 = Page0(resourcePath=self.resourcePath, **nav_callbacks)
        self.page_1 = Page1(resourcePath=self.resourcePath, **nav_callbacks)
        self.page_2 = Page2(resourcePath=self.resourcePath, **nav_callbacks)
        self.page_3 = Page3(resourcePath=self.resourcePath, **nav_callbacks)

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
        if self._modulePanelHidden:
            return
        mainWindow = slicer.util.mainWindow()
        if mainWindow:
            panel = mainWindow.findChild("QDockWidget", "PanelDockWidget")
            if panel:
                panel.hide()
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
            self._hideModulePanel()

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
    def __init__(self, parent=None, resourcePath=None):
        super().__init__(parent)
        ui_widget = slicer.util.loadUI(resourcePath("UI/PatientManagement.ui"))
        layout = qt.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(ui_widget)
        self.ui = slicer.util.childWidgetVariables(ui_widget)
