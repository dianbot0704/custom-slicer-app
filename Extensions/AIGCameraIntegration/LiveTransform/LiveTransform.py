from slicer.ScriptedLoadableModule import ScriptedLoadableModule, ScriptedLoadableModuleWidget


class LiveTransform(ScriptedLoadableModule):
    def __init__(self, parent):
        parent.title = "Live Transform"
        parent.categories = ["Example"]
        parent.contributors = [""]


class LiveTransformWidget(ScriptedLoadableModuleWidget):
    def __init__(self, parent):
        ScriptedLoadableModuleWidget.__init__(self, parent)

    def setup(self):
        pass

    def enter(self):
        pass

    def exit(self):
        pass
