cmake_minimum_required(VERSION 3.21)

project(IntraOperativePlan)

set(EXTENSION_NAME "${PROJECT_NAME}")
set(EXTENSION_HOMEPAGE "https://example.com")
set(EXTENSION_CATEGORY "Examples")
set(EXTENSION_CONTRIBUTORS "")
set(EXTENSION_DESCRIPTION "Intra-operative planning extension")
set(EXTENSION_ICONURL "")
set(EXTENSION_SCREENSHOTURLS "")
set(EXTENSION_DEPENDS "")

set(EXTENSION_SOURCES "Modules/Scripted/IntraOperativePlan")
foreach(module ${EXTENSION_SOURCES})
	add_subdirectory(${module})
endforeach()

include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
