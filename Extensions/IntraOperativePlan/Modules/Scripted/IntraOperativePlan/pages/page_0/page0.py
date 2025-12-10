from core import CustomLayoutPage


class Page0(CustomLayoutPage):
    def __init__(self, resourcePath, layout_id, on_previous=None, on_next=None, parent=None):
        tag_name = "page_0"
        layout_description = f'<layout type="horizontal"><item><{tag_name}></{tag_name}></item></layout>'
        super().__init__(
            resourcePath=resourcePath,
            ui_filename="UI/template_page0_no_mrml.ui",
            layout_id=layout_id,
            tag_name=tag_name,
            layout_description=layout_description,
            on_previous=on_previous,
            on_next=on_next,
            parent=parent,
        )
