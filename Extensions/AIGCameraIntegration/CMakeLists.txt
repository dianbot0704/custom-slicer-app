cmake_minimum_required(VERSION 3.20.6...3.22.6 FATAL_ERROR)
project(AIGCameraIntegration)

set(EXTENSION_HOMEPAGE "https://slicer.org")
set(EXTENSION_CATEGORY "Examples")
set(EXTENSION_CONTRIBUTORS "Alwin Arrasyid")
set(EXTENSION_DESCRIPTION "Development for integrating AIGCamera to AIGSlicer")
set(EXTENSION_DEPENDS "NA")

find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

add_subdirectory(LiveTransform)

include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
