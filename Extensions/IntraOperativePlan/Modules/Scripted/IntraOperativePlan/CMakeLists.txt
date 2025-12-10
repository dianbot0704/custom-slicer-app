set(MODULE_NAME IntraOperativePlan)

set(MODULE_PYTHON_SCRIPTS
	${MODULE_NAME}.py
	core/__init__.py
	core/base_page.py
	pages/__init__.py
	pages/page_0/__init__.py
	pages/page_0/page0.py
	pages/page_1/__init__.py
	pages/page_1/page1.py
	pages/page_2/__init__.py
	pages/page_2/page2.py
	pages/page_3/__init__.py
	pages/page_3/page3.py
)

set(MODULE_PYTHON_RESOURCES
	Resources/UI/PatientManagement.ui
	Resources/UI/template_page0_no_mrml.ui
	Resources/UI/template_page1_mrml.ui
	Resources/UI/template_page2_mrml.ui
	Resources/UI/template_page3_no_mrml.ui
)

slicerMacroBuildScriptedModule(
	NAME ${MODULE_NAME}
	SCRIPTS ${MODULE_PYTHON_SCRIPTS}
	RESOURCES ${MODULE_PYTHON_RESOURCES}
)

