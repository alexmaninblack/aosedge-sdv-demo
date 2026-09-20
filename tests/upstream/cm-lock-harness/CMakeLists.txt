# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
cmake_minimum_required(VERSION 3.23)
project(cm_disconnect_lock_proof LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CPP "" CACHE PATH "Pinned aos_core_cpp checkout (read only)")
set(CORE "" CACHE PATH "Matching aos_core_lib_cpp checkout (read only)")
if(NOT EXISTS "${CPP}/src/cm/communication/communication.cpp" OR
   NOT EXISTS "${CORE}/src/core/cm/monitoring/monitoring.cpp")
    message(FATAL_ERROR "Set CPP and CORE to the exact source pair")
endif()
find_package(Poco REQUIRED COMPONENTS Foundation JSON Net NetSSL Crypto)
find_package(Threads REQUIRED)
file(GLOB protocol_sources CONFIGURE_DEPENDS "${CPP}/src/common/cloudprotocol/*.cpp")
# Compile the actual implementations, not a two-mutex rewrite. Section GC
# avoids pulling unrelated IAM/provisioning/crypto entry points into this proof.
add_library(native_objects OBJECT
    ${CPP}/src/cm/communication/communication.cpp
    ${CORE}/src/core/cm/monitoring/monitoring.cpp
    ${CORE}/src/core/cm/alerts/alerts.cpp
    ${CORE}/src/core/common/tools/time.cpp
    ${CORE}/src/core/common/tools/timer.cpp
    ${CORE}/src/core/common/tools/fs.cpp
    ${CORE}/src/core/common/tools/semver.cpp
    ${CORE}/src/core/common/tools/uuid.cpp
    ${CORE}/src/core/common/crypto/cryptohelper.cpp
    ${CORE}/src/core/common/crypto/cryptoutils.cpp
    ${CORE}/src/core/common/crypto/asn1.cpp
    ${CPP}/src/common/utils/json.cpp
    ${CPP}/src/common/utils/exception.cpp
    ${CPP}/src/common/utils/time.cpp
    ${CPP}/src/common/utils/utils.cpp
    ${CPP}/src/common/utils/cryptohelper.cpp
    ${CPP}/src/common/utils/pkcs11helper.cpp
    ${CPP}/src/common/utils/pk11uri.cpp
    ${CPP}/src/common/utils/retry.cpp
    ${protocol_sources})
target_include_directories(native_objects PUBLIC ${CPP}/src ${CORE}/src)
target_compile_options(native_objects PRIVATE -O0 -g3 -fno-omit-frame-pointer
    -ffunction-sections -fdata-sections)
target_link_libraries(native_objects PUBLIC Poco::Foundation Poco::JSON Poco::Net
    Poco::NetSSL Poco::Crypto Threads::Threads)
add_executable(cm_lock_probe probe.cpp)
target_link_libraries(cm_lock_probe PRIVATE native_objects)
# White-box access for test scheduling only; no production header/source edits.
target_compile_options(cm_lock_probe PRIVATE -O0 -g3 -fno-omit-frame-pointer
    -fno-access-control -ffunction-sections -fdata-sections)
target_link_options(cm_lock_probe PRIVATE -Wl,--gc-sections)
enable_testing()
foreach(module monitoring alerts)
    foreach(action disconnect stop)
        foreach(schedule serial overlap)
            add_test(NAME ${module}_${action}_${schedule}
                COMMAND cm_lock_probe ${module} ${action} ${schedule})
            set_tests_properties(${module}_${action}_${schedule} PROPERTIES TIMEOUT 10)
        endforeach()
    endforeach()
endforeach()
foreach(schedule duplicate close-error reentry unsubscribe parallel-close connect-stop worker)
    add_test(NAME lifecycle_${schedule}
        COMMAND cm_lock_probe monitoring disconnect ${schedule})
    set_tests_properties(lifecycle_${schedule} PROPERTIES TIMEOUT 15)
endforeach()
add_test(NAME alerts_worker COMMAND cm_lock_probe alerts disconnect worker)
set_tests_properties(alerts_worker PROPERTIES TIMEOUT 15)
add_test(NAME stop_close_error COMMAND cm_lock_probe monitoring stop close-error)
set_tests_properties(stop_close_error PROPERTIES TIMEOUT 15)
