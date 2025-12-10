import qt
import slicer
import logging


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
        return f'<layout type="horizontal"><item><{self._tag_name}></{self._tag_name}></item></layout>'

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
