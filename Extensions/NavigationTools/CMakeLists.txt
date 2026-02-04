
cmake_minimum_required(VERSION 3.20.6...3.22.6 FATAL_ERROR)
project(NavigationTools)

set(EXTENSION_HOMEPAGE "")
set(EXTENSION_CATEGORY "Main")
set(EXTENSION_CONTRIBUTORS "")
set(EXTENSION_DESCRIPTION "")
set(EXTENSION_DEPENDS "NA")

find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

add_subdirectory(NavigationTools)

include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
