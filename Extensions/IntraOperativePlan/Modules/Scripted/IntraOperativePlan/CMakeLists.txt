set(MODULE_NAME IntraOperativePlan)

set(MODULE_PYTHON_SCRIPTS
	${MODULE_NAME}.py
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

