import os
import platform
import pathlib
import urllib.request
import shutil
import subprocess

print('Building SDKs.')

platform_name = platform.platform().lower()

platforms_settings = dict()

CMAKE_PATH_KEY = 'cmake-path'
CMAKE_ARGS_KEY = 'cmake-args'

if 'windows' in platform_name:
    print('Windows platform added.')
    platforms_settings['windows'] = {
        CMAKE_PATH_KEY: 'cmake',
        CMAKE_ARGS_KEY: [],
    }

if 'linux' in platform_name:
    print('Linux platform added.')
    platforms_settings['linux'] = {
        CMAKE_PATH_KEY: 'cmake',
        CMAKE_ARGS_KEY: [],
    }

android_ndk = os.environ.get('ANDROID_NDK')
android_sdk = os.environ.get('ANDROID_SDK')

if android_ndk is not None and android_sdk is not None:
    android_ndk = pathlib.Path(android_ndk)
    android_sdk = pathlib.Path(android_sdk)
    print('Android platform added.')
    platforms_settings['android'] = {
        CMAKE_PATH_KEY: android_sdk / 'cmake' / '3.22.1' / 'bin' / 'cmake',
        CMAKE_ARGS_KEY: [
            '-DCMAKE_TOOLCHAIN_FILE=' +
            str(android_ndk) + '/build/cmake/android.toolchain.cmake',
            '-DANDROID_STL=c++_shared'
        ],
    }

if 'macos' in platform_name:
    print('MacOS & iOS platforms added.')
    platforms_settings['macos'] = {
        CMAKE_PATH_KEY: 'cmake',
        CMAKE_ARGS_KEY: [],
    }
    platforms_settings['ios'] = {
        CMAKE_PATH_KEY: 'cmake',
        CMAKE_ARGS_KEY: [],
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
    print('Downloading', file_name, '...')
    with urllib.request.urlopen(url) as response, open(file_path, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)


def extract(src, dst):
    src_path = temp_dir / src
    dst_path = temp_dir / dst
    if dst_path.exists():
        return
    shutil.unpack_archive(src_path, dst_path)


def build_t1(root_dir, src_dir, after_build_fn):
    for plt, settings in platforms_settings.items():
        bld_dir = root_dir / ('build-' + plt)
        if bld_dir.exists():
            continue
        bld_dir.mkdir(exist_ok=True)
        subprocess.call([
            settings[CMAKE_PATH_KEY],
            '-S', src_dir,
            '-B', bld_dir,
            '-DCMAKE_BUILD_TYPE=Release',
            *settings[CMAKE_ARGS_KEY]])
        subprocess.call([
            settings[CMAKE_PATH_KEY],
            '--build', bld_dir,
            '--config', 'Release',
            *settings[CMAKE_ARGS_KEY]])
        after_build_fn(sdk_dir / plt / 'lib', bld_dir / 'Release')


sdl2_str = 'sdl2'
sdl2_zip_file = sdl2_str + '.zip'
sdl2_version = '2.0.22'
download(
    'https://www.libsdl.org/release/SDL2-' +
    sdl2_version + '.zip', sdl2_zip_file)
extract(sdl2_zip_file, sdl2_str)
sdl2_extracted_dir_name = 'SDL2-' + sdl2_version
sdl2_root_dir = temp_dir / sdl2_str
sdl2_src_dir = sdl2_root_dir / sdl2_extracted_dir_name


def sdl2_after_build(sdk_lib_path, built_libs_path):
    shutil.copy(built_libs_path / 'SDL2.lib', sdk_lib_path)
    shutil.copy(built_libs_path / 'SDL2main.lib', sdk_lib_path)


build_t1(sdl2_root_dir, sdl2_src_dir, sdl2_after_build)

openal_str = 'openal'
openal_zip_file = openal_str + '.zip'
openal_version = '1.22.2'
download(
    'https://github.com/kcat/openal-soft/archive/refs/tags/' +
    openal_version + '.zip', openal_zip_file)
extract(openal_zip_file, openal_str)
openal_extracted_dir_name = 'openal-soft-' + openal_version
openal_root_dir = temp_dir / openal_str
openal_src_dir = openal_root_dir / openal_extracted_dir_name


def openal_after_build(sdk_lib_path, built_libs_path):
    shutil.copy(built_libs_path / 'OpenAL32.lib', sdk_lib_path)


build_t1(openal_root_dir, openal_src_dir, openal_after_build)
