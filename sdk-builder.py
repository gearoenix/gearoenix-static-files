import os
import platform
import pathlib
import urllib.request
import shutil
import subprocess
import multiprocessing
import logging

print('Building SDKs.')

platform_name = platform.platform().lower()

platforms_settings = dict()

PLATFORM_WINDOWS_KEY = 'windows'
PLATFORM_LINUX_KEY = 'linux'
PLATFORM_ANDROID_KEY = 'android'
PLATFORM_MACOS_KEY = 'macos'
PLATFORM_IOS_KEY = 'ios'
CMAKE_PATH_KEY = 'cmake-path'
CMAKE_ARGS_KEY = 'cmake-args'
PLATFORM_BUILD_T1_PATH_KEY = 'platform-build-t1-path'

if PLATFORM_WINDOWS_KEY in platform_name:
    print('Windows platform added.')
    platforms_settings[PLATFORM_WINDOWS_KEY] = {
        CMAKE_PATH_KEY: 'cmake',
        CMAKE_ARGS_KEY: [],
        PLATFORM_BUILD_T1_PATH_KEY: 'Release',
    }

if PLATFORM_LINUX_KEY in platform_name:
    print('Linux platform added.')
    platforms_settings[PLATFORM_LINUX_KEY] = {
        CMAKE_PATH_KEY: 'cmake',
        CMAKE_ARGS_KEY: [],
        PLATFORM_BUILD_T1_PATH_KEY: '',
    }

android_ndk = os.environ.get('ANDROID_NDK')
android_sdk = os.environ.get('ANDROID_SDK')

if android_ndk is not None and android_sdk is not None:
    android_ndk = pathlib.Path(android_ndk)
    android_sdk = pathlib.Path(android_sdk)
    print('Android platform added.')
    platforms_settings[PLATFORM_ANDROID_KEY] = {
        CMAKE_PATH_KEY: android_sdk / 'cmake' / '3.22.1' / 'bin' / 'cmake',
        CMAKE_ARGS_KEY: [
            '-DCMAKE_TOOLCHAIN_FILE=' +
            str(android_ndk) + '/build/cmake/android.toolchain.cmake',
            '-DANDROID_STL=c++_shared'
        ],
        PLATFORM_BUILD_T1_PATH_KEY: '',
    }

if PLATFORM_MACOS_KEY in platform_name:
    print('MacOS & iOS platforms added.')
    platforms_settings[PLATFORM_MACOS_KEY] = {
        CMAKE_PATH_KEY: 'cmake',
        CMAKE_ARGS_KEY: [],
        PLATFORM_BUILD_T1_PATH_KEY: '',
    }
    platforms_settings[PLATFORM_IOS_KEY] = {
        CMAKE_PATH_KEY: 'cmake',
        CMAKE_ARGS_KEY: [],
        PLATFORM_BUILD_T1_PATH_KEY: '',
    }

curr_dir = pathlib.Path(__file__).parent
temp_dir = curr_dir / 'tmp'
sdk_dir = curr_dir / 'sdk'

temp_dir.mkdir(exist_ok=True)
sdk_dir.mkdir(exist_ok=True)


def download(url: str, file_name: str):
    file_path = temp_dir / file_name
    if file_path.exists():
        return
    print(f'Downloading {file_name} with url: {url}...')
    with urllib.request.urlopen(url) as response, open(file_path, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)


def extract(src, dst):
    src_path = temp_dir / src
    dst_path = temp_dir / dst
    if dst_path.exists():
        return
    shutil.unpack_archive(src_path, dst_path)


def build_t1(root_dir, src_dir, after_build_fn, additional_cmake_args=[]):
    for plt, settings in platforms_settings.items():
        bld_dir = root_dir / ('build-' + plt)
        if bld_dir.exists():
            continue
        bld_dir.mkdir(exist_ok=True)
        if 0 != subprocess.run([
            settings[CMAKE_PATH_KEY],
            '-S', src_dir,
            '-B', bld_dir,
            '-DCMAKE_BUILD_TYPE=Release',
            *settings[CMAKE_ARGS_KEY],
                *additional_cmake_args]).returncode:
            logging.error(
                'Cmake config failed for platform: %s, source: %s', plt, src_dir)
            continue
        if 0 != subprocess.run([
            settings[CMAKE_PATH_KEY],
            '--build', bld_dir,
            '--config', 'Release',
            *settings[CMAKE_ARGS_KEY],
                '--parallel', str(multiprocessing.cpu_count())]).returncode:
            logging.error(
                f'Cmake build failed for platform: {plt}, source: {src_dir}')
            continue
        after_build_fn(sdk_dir / plt / 'lib', bld_dir /
                       settings[PLATFORM_BUILD_T1_PATH_KEY])


sdl2_str = 'sdl2'
sdl2_zip_file = sdl2_str + '.zip'
sdl2_version = '2.26.0'
download(
    f'https://github.com/libsdl-org/SDL/releases/download/release-{sdl2_version}/SDL2-{sdl2_version}.zip',
    sdl2_zip_file)
extract(sdl2_zip_file, sdl2_str)
sdl2_extracted_dir_name = 'SDL2-' + sdl2_version
sdl2_root_dir = temp_dir / sdl2_str
sdl2_src_dir = sdl2_root_dir / sdl2_extracted_dir_name


def sdl2_after_build(sdk_lib_path, built_libs_path):
    if PLATFORM_WINDOWS_KEY in platforms_settings:
        shutil.copy(built_libs_path / 'SDL2-static.lib', sdk_lib_path)
        shutil.copy(built_libs_path / 'SDL2main.lib', sdk_lib_path)
    if PLATFORM_LINUX_KEY in platforms_settings:
        print('No need for sdl in linux.')


build_t1(sdl2_root_dir, sdl2_src_dir, sdl2_after_build, ['-DSDL_LIBC=ON'])

openal_str = 'openal'
openal_zip_file = openal_str + '.zip'
openal_version = '1.22.2'
download(
    f'https://github.com/kcat/openal-soft/archive/refs/tags/{openal_version}.zip',
    openal_zip_file)
extract(openal_zip_file, openal_str)
openal_extracted_dir_name = 'openal-soft-' + openal_version
openal_root_dir = temp_dir / openal_str
openal_src_dir = openal_root_dir / openal_extracted_dir_name


def openal_after_build(sdk_lib_path, built_libs_path):
    if PLATFORM_WINDOWS_KEY in platforms_settings:
        shutil.copy(built_libs_path / 'OpenAL32.lib', sdk_lib_path)
    if PLATFORM_LINUX_KEY in platforms_settings:
        print('No need for OpenAL in linux.')


build_t1(openal_root_dir, openal_src_dir, openal_after_build)

shutil.make_archive(sdk_dir, 'zip', sdk_dir)
