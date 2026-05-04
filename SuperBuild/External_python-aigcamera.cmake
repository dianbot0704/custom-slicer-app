set(proj python-aigcamera)

# Set dependency list
set(${proj}_DEPENDENCIES
  python
  python-pip
  python-setuptools
  python-wheel
  python-numpy
  python-pillow
  python-hatchling
  )

if(NOT DEFINED Slicer_USE_SYSTEM_${proj})
  set(Slicer_USE_SYSTEM_${proj} ${Slicer_USE_SYSTEM_python})
endif()

# Include dependent projects if any
ExternalProject_Include_Dependencies(${proj} PROJECT_VAR proj DEPENDS_VAR ${proj}_DEPENDENCIES)

set(${proj}_SOURCE_DIR "${CMAKE_CURRENT_LIST_DIR}/../Python/aigcamera")
if(NOT EXISTS "${${proj}_SOURCE_DIR}/pyproject.toml")
  message(FATAL_ERROR "${proj} source directory is missing: ${${proj}_SOURCE_DIR}")
endif()

if(Slicer_USE_SYSTEM_${proj})
  foreach(module_name IN ITEMS aigcamera)
    ExternalProject_FindPythonPackage(
      MODULE_NAME "${module_name}"
      REQUIRED
      )
  endforeach()
endif()

if(NOT Slicer_USE_SYSTEM_${proj})
  set(_aigcamera_nuitka_compile_args "")
  if(AksaratorApp_ENABLE_COMPILED_FIDUCIAL_DETECTOR)
    list(APPEND _aigcamera_nuitka_compile_args --compile-with-nuitka)
  endif()

  ExternalProject_Add(${proj}
    ${${proj}_EP_ARGS}
    DOWNLOAD_COMMAND ""
    SOURCE_DIR ${${proj}_SOURCE_DIR}
    CONFIGURE_COMMAND ""
    BUILD_COMMAND ""
    INSTALL_COMMAND ${PYTHON_EXECUTABLE} ${AksaratorApp_SOURCE_DIR}/scripts/compile_aigcamera_nuitka.py --python-executable ${PYTHON_EXECUTABLE} --source-root ${${proj}_SOURCE_DIR} --build-root ${CMAKE_BINARY_DIR}/python-aigcamera-nuitka --cache-dir ${CMAKE_BINARY_DIR}/python-aigcamera-nuitka-cache ${_aigcamera_nuitka_compile_args}
    LOG_INSTALL 1
    DEPENDS
      ${${proj}_DEPENDENCIES}
    )

else()
  ExternalProject_Add_Empty(${proj} DEPENDS ${${proj}_DEPENDENCIES})
endif()
