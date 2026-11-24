# Included by DCMTK's project(DCMTK) through CMAKE_PROJECT_DCMTK_INCLUDE
# (see AksaratorApp_DCMTK_ALLOW_PRIVILEGED_PORTS in the top-level CMakeLists.txt).
#
# storescp, movescu and DcmSCP refuse a port below 1024 unless they run as root:
# a plain geteuid() check made before they try to bind, so neither
# net.ipv4.ip_unprivileged_port_start nor CAP_NET_BIND_SERVICE lets a normal
# user listen on the DICOM port 104. Compiling the check out leaves the
# decision to the operating system, which still refuses the bind unless the
# machine allows it.
add_compile_definitions(DISABLE_PORT_PERMISSION_CHECK)
