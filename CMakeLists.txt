cmake_minimum_required(VERSION 3.16.3)

# Enable C++14
if(NOT DEFINED CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set (EP_GIT_PROTOCOL "https")

# Slicer sources
include(FetchContent)
if(NOT DEFINED slicersources_SOURCE_DIR)
  # Download Slicer sources and set variables slicersources_SOURCE_DIR and slicersources_BINARY_DIR
  FetchContent_Populate(slicersources
    GIT_REPOSITORY ${EP_GIT_PROTOCOL}://github.com/Slicer/Slicer
    GIT_TAG        1b1bbb22b4f858ff3d47d196de4ac491a0b9ea5c
    GIT_PROGRESS   1
    )
else()
  set(slicersources_BINARY_DIR ${CMAKE_CURRENT_BINARY_DIR}/slicersources-subbuild)
endif()

# macOS initialization
set(CMAKE_MODULE_PATH ${slicersources_SOURCE_DIR}/CMake ${CMAKE_MODULE_PATH})
include(SlicerInitializeOSXVariables)

project(AksaratorApp)

# Configure Application
set(Slicer_APPLICATIONS_DIR ${CMAKE_CURRENT_SOURCE_DIR}/Applications)
set(Slicer_MAIN_PROJECT "AksaratorApp")

# Set organization
set(Slicer_ORGANIZATION_DOMAIN "aksarator.com")
set(Slicer_ORGANIZATION_NAME   "Aksarator")

# Default home and favorite modules
set(Slicer_DEFAULT_HOME_MODULE "IntraopPlanner")
set(Slicer_DEFAULT_FAVORITE_MODULES "Data, Volumes, Models, Transforms, Markups, SegmentEditor")

# Configure SuperBuild
set(SUPERBUILD_TOPLEVEL_PROJECT Slicer)
set(EXTERNAL_PROJECT_ADDITIONAL_DIR "${CMAKE_CURRENT_SOURCE_DIR}/SuperBuild")
include(ExternalProjectDependency)

# Additional Slicer dependencies looked up in EXTERNAL_PROJECT_ADDITIONAL_DIR
set(Slicer_ADDITIONAL_DEPENDENCIES
	python-hatchling
	python-pillow
	python-opencv
	python-aigcamera
  )

option(AksaratorApp_PIN_NUMPY "Pin numpy for Aksarator superbuild" ON)
set(AksaratorApp_NUMPY_VERSION "1.26.*" CACHE STRING "Pinned numpy version for Aksarator")
option(AksaratorApp_PIN_OPENCV "Pin opencv-python-headless for Aksarator superbuild" ON)
set(AksaratorApp_OPENCV_VERSION "4.11.0.86" CACHE STRING "Pinned opencv-python-headless version for Aksarator")
set(AksaratorApp_NUITKA_VERSION "4.0.1" CACHE STRING "Pinned Nuitka version for Aksarator superbuild")
option(AksaratorApp_ENABLE_COMPILED_FIDUCIAL_DETECTOR "Compile fiducial_detector.py into a shared library with Nuitka" ON)
mark_as_superbuild(AksaratorApp_NUITKA_VERSION:STRING)
mark_as_superbuild(AksaratorApp_ENABLE_COMPILED_FIDUCIAL_DETECTOR:BOOL)

if(AksaratorApp_ENABLE_COMPILED_FIDUCIAL_DETECTOR)
  list(APPEND Slicer_ADDITIONAL_DEPENDENCIES python-nuitka)
endif()

if(AksaratorApp_PIN_NUMPY)
  if(NOT AksaratorApp_NUMPY_VERSION MATCHES "^1\\.26(\\.|$)")
    message(FATAL_ERROR "AksaratorApp_NUMPY_VERSION must be 1.26.x (e.g. 1.26.4 or 1.26.*) when AksaratorApp_PIN_NUMPY is ON.")
  endif()
endif()

if(AksaratorApp_PIN_NUMPY AND NOT AksaratorApp_PIN_OPENCV)
  message(FATAL_ERROR "AksaratorApp_PIN_OPENCV must be ON when AksaratorApp_PIN_NUMPY is ON (NumPy 1.26.x).")
endif()
if(AksaratorApp_PIN_NUMPY AND AksaratorApp_PIN_OPENCV)
  if(NOT AksaratorApp_OPENCV_VERSION MATCHES "^4\\.11(\\.|$)")
    message(FATAL_ERROR "AksaratorApp_OPENCV_VERSION must be 4.11.x when AksaratorApp_PIN_NUMPY is ON.")
  endif()
endif()

if(AksaratorApp_PIN_NUMPY)
  list(APPEND Slicer_ADDITIONAL_DEPENDENCIES python-numpy)
endif()

option(AksaratorApp_ENABLE_SLICERIGT "Bundle SlicerIGT and SlicerIGSIO extensions" ON)
set(AksaratorApp_SlicerIGSIO_GIT_TAG "1a89776c9f1c8bbbad62000561aa892afe1e7077" CACHE STRING "Pinned SlicerIGSIO revision for Aksarator")
set(AksaratorApp_SlicerIGT_GIT_TAG "42091cddf620d760cdb0e22564edb8c55338edd9" CACHE STRING "Pinned SlicerIGT revision for Aksarator")
set(AksaratorApp_IGSIO_GIT_TAG "581b7f5fc33c1c72dcaa08b306e489ee0d7e6495" CACHE STRING "Pinned IGSIO revision for Aksarator")
set(AksaratorApp_IGSIO_VTKADDON_GIT_TAG "2ed3e2226cf25958b4dbf8bf917b2f7793ecd6a2" CACHE STRING "Pinned vtkAddon revision used by IGSIO superbuild")
set(AksaratorApp_YASM_GIT_TAG "a2f8bdf075bcad90a1b0a446080906ef6afe6847" CACHE STRING "Pinned YASM revision for SlicerIGSIO/IGSIO superbuild")
# SlicerIGSIO's External_IGSIO.cmake reads <CMAKE_PROJECT_NAME>_IGSIO_GIT_TAG.
set(Slicer_IGSIO_GIT_TAG "${AksaratorApp_IGSIO_GIT_TAG}" CACHE STRING "Pinned IGSIO revision used by Slicer superbuild")
# SlicerIGSIO's External_YASM.cmake reads <CMAKE_PROJECT_NAME>_YASM_GIT_TAG.
set(Slicer_YASM_GIT_TAG "${AksaratorApp_YASM_GIT_TAG}" CACHE STRING "Pinned YASM revision used by Slicer superbuild")

# IGSIO superbuild defaults to floating refs for nested deps (vtkAddon main, YASM master).
# Propagate pinned refs specifically to IGSIO external project configuration.
set(vtkAddon_GIT_REVISION "${AksaratorApp_IGSIO_VTKADDON_GIT_TAG}")
set(YASM_GIT_REVISION "${AksaratorApp_YASM_GIT_TAG}")
mark_as_superbuild(
  VARS
    vtkAddon_GIT_REVISION:STRING
    YASM_GIT_REVISION:STRING
  PROJECTS IGSIO
  )

#  Enable listed remote modules from ITK
set(Slicer_ITK_ADDITIONAL_MODULES
  )

if(NOT CMAKE_CONFIGURATION_TYPES)
  set(Slicer_DEFAULT_BUILD_TYPE "Release")
endif()
include(SlicerInitializeBuildType)
include(SlicerInitializeReleaseType)

# Set application bundle identifier for macOS
if(APPLE)
  set(Slicer_MACOSX_BUNDLE_GUI_IDENTIFIER "com.aksarator.aksarator")
endif()

# Installation folder and admin account requirement for Windows
if(WIN32)
  # Note: To avoid escaping issue, make sure to use forward slash when setting
  #       "Slicer_CPACK_NSIS_INSTALL_ROOT". It is replaced by "\\\\" in SlicerCPack.
  set(Slicer_CPACK_NSIS_INSTALL_REQUIRES_ADMIN_ACCOUNT ON)
  if(Slicer_CPACK_NSIS_INSTALL_REQUIRES_ADMIN_ACCOUNT)
    # User has administrative privileges, therefore we can install to shared folder
    # "C:\Program Files" or "C:\Program Files (x86)".
    if(CMAKE_CL_64)
      set(Slicer_CPACK_NSIS_INSTALL_ROOT "$PROGRAMFILES64")
    else()
      set(Slicer_CPACK_NSIS_INSTALL_ROOT "$PROGRAMFILES")
    endif()
  else()
    # We do not require administrative privileges, therefore we install to user folder
    # "C:\Users\<username>\AppData\Local".
    set(Slicer_CPACK_NSIS_INSTALL_ROOT "$LOCALAPPDATA/${Slicer_ORGANIZATION_NAME}")
  endif()
endif()

# Slicer options
option(BUILD_TESTING                            "Build application test suite"                        ON)
option(Slicer_BUILD_APPLICATIONUPDATE_SUPPORT   "Build application update support"                    OFF)
option(Slicer_BUILD_DOCUMENTATION               "Build documentation (Doxygen, sphinx, ...)"          OFF)
if(WIN32)
  option(Slicer_BUILD_WIN32_CONSOLE_LAUNCHER    "Build ${PROJECT_NAME} launcher executable as a console app on windows (displays console at application start)" OFF)
  option(Slicer_BUILD_WIN32_CONSOLE             "Build application executable as a console app (allows capturing and piping console output)" ON)
endif()

option(Slicer_BUILD_DICOM_SUPPORT               "Build application with DICOM support"                ON)
option(Slicer_BUILD_DIFFUSION_SUPPORT           "Build application with Diffusion support"            OFF)
option(Slicer_BUILD_EXTENSIONMANAGER_SUPPORT    "Build application with ExtensionManager support"     ON)
option(Slicer_BUILD_MULTIVOLUME_SUPPORT         "Build application with MultiVolume support"          OFF)
option(Slicer_BUILD_PARAMETERSERIALIZER_SUPPORT "Build application with parameter serializer support" OFF)
option(Slicer_USE_PYTHONQT                      "Build application with Python support"               ON)
option(Slicer_USE_QtTesting                     "Build application with QtTesting support"            OFF)
option(Slicer_USE_SimpleITK                     "Build application with SimpleITK support"            OFF)

option(Slicer_BUILD_BRAINSTOOLS                 "Build application with BRAINSTools module"           OFF)
option(Slicer_BUILD_DataStore                   "Build application with DataStore module"             OFF)
option(Slicer_BUILD_CompareVolumes              "Build application with ChangeTrackerPy module"       OFF)
option(Slicer_BUILD_LandmarkRegistration        "Build application with LandmarkRegistration module"  OFF)
option(Slicer_BUILD_SurfaceToolbox              "Build application with SurfaceToolbox module"        ON)

# Enable Slicer built-in modules
set(Slicer_CLIMODULES_ENABLED
  ResampleDTIVolume             # Needed by ResampleScalarVectorDWIVolume
  ResampleScalarVectorDWIVolume # Depends on DiffusionApplications, needed by CropVolume
  )
set(Slicer_QTLOADABLEMODULES_ENABLED
  )
set(Slicer_QTSCRIPTEDMODULES_ENABLED
  )

# Disable Slicer built-in modules
set(Slicer_CLIMODULES_DISABLED
  )
set(Slicer_QTLOADABLEMODULES_DISABLED
  SceneViews
  SlicerWelcome
  ViewControllers
  )
set(Slicer_QTSCRIPTEDMODULES_DISABLED
  DataProbe
  DMRIInstall
  Endoscopy
  LabelStatistics
  PerformanceTests
  SampleData
  VectorToScalarVolume
  )

# Enable/Disable Slicer custom modules: To create a new module, use the SlicerExtensionWizard.
set(Slicer_EXTENSION_SOURCE_DIRS
	# Home is the default extension
  ${AksaratorApp_SOURCE_DIR}/Modules/Scripted/Home
  ${AksaratorApp_SOURCE_DIR}/Modules/Scripted/SessionRenderTrace
	# ${AksaratorApp_SOURCE_DIR}/Extensions/IntraOperativePlan
	# ${AksaratorApp_SOURCE_DIR}/Extensions/AIGCameraIntegration
	# ${AksaratorApp_SOURCE_DIR}/Extensions/NavigationTools
	${AksaratorApp_SOURCE_DIR}/Extensions/intraop-plan-extension
  )

# Add remote extension source directories

# SlicerCustomAppUtilities
set(extension_name "SlicerCustomAppUtilities")
set(${extension_name}_SOURCE_DIR "${CMAKE_BINARY_DIR}/${extension_name}")
FetchContent_Populate(${extension_name}
  SOURCE_DIR     ${${extension_name}_SOURCE_DIR}
  GIT_REPOSITORY ${EP_GIT_PROTOCOL}://github.com/KitwareMedical/SlicerCustomAppUtilities.git
  GIT_TAG        1d984a2c9143e2617ff1ffa9d86c51e07dc6321e
  GIT_PROGRESS   1
  QUIET
  )
message(STATUS "Remote - ${extension_name} [OK]")
list(APPEND Slicer_EXTENSION_SOURCE_DIRS ${${extension_name}_SOURCE_DIR}/Modules/Scripted/SlicerCustomAppUtilities)

if(AksaratorApp_ENABLE_SLICERIGT)
  # SlicerIGSIO (required by SlicerIGT)
  set(extension_name "SlicerIGSIO")
  set(${extension_name}_SOURCE_DIR "${CMAKE_BINARY_DIR}/${extension_name}")
  FetchContent_Populate(${extension_name}
    SOURCE_DIR     ${${extension_name}_SOURCE_DIR}
    GIT_REPOSITORY ${EP_GIT_PROTOCOL}://github.com/IGSIO/SlicerIGSIO.git
    GIT_TAG        ${AksaratorApp_SlicerIGSIO_GIT_TAG}
    GIT_PROGRESS   1
    QUIET
    )
  message(STATUS "Remote - ${extension_name} [OK]")
  list(APPEND Slicer_EXTENSION_SOURCE_DIRS ${${extension_name}_SOURCE_DIR})

  # SlicerIGT
  set(extension_name "SlicerIGT")
  set(${extension_name}_SOURCE_DIR "${CMAKE_BINARY_DIR}/${extension_name}")
  FetchContent_Populate(${extension_name}
    SOURCE_DIR     ${${extension_name}_SOURCE_DIR}
    GIT_REPOSITORY ${EP_GIT_PROTOCOL}://github.com/SlicerIGT/SlicerIGT.git
    GIT_TAG        ${AksaratorApp_SlicerIGT_GIT_TAG}
    GIT_PROGRESS   1
    QUIET
    )
  message(STATUS "Remote - ${extension_name} [OK]")
  list(APPEND Slicer_EXTENSION_SOURCE_DIRS ${${extension_name}_SOURCE_DIR})
endif()

# SlicerOpenIGTLink
# set(extension_name "SlicerOpenIGTLink")
# set(${extension_name}_SOURCE_DIR "${CMAKE_BINARY_DIR}/${extension_name}")
# FetchContent_Populate(${extension_name}
#  SOURCE_DIR     ${${extension_name}_SOURCE_DIR}
#  GIT_REPOSITORY ${EP_GIT_PROTOCOL}://github.com/openigtlink/SlicerOpenIGTLink.git
#  GIT_TAG        2b92f7b1ffe02403109b671f28424e8770e902a0
#  GIT_PROGRESS   1
#  QUIET
#  )
# message(STATUS "Remote - ${extension_name} [OK]")
# list(APPEND Slicer_EXTENSION_SOURCE_DIRS ${${extension_name}_SOURCE_DIR})


# Add Slicer sources
add_subdirectory(${slicersources_SOURCE_DIR} ${slicersources_BINARY_DIR})
