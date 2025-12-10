from core import DockWidgetPage


class Page1(DockWidgetPage):
    def __init__(self, resourcePath, on_previous=None, on_next=None, parent=None):
        super().__init__(
            resourcePath=resourcePath,
            ui_filename="UI/template_page1_mrml.ui",
            on_previous=on_previous,
            on_next=on_next,
            parent=parent,
        )
