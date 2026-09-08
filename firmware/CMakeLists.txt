cmake_minimum_required(VERSION 3.20)

set(EXTRA_COMPONENT_DIRS
    components/sensors
    components/diagnostics
    components/intelligence
    components/telemetry
    components/security
    components/network
    components/storage
    components/system
    components/local_ap
)

include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(nexalert-node)
