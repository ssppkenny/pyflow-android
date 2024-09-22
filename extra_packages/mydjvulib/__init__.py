from multiprocessing import cpu_count
import os
from os.path import exists, join
from pythonforandroid.toolchain import info
import sh
import sys

from pythonforandroid.recipe import CppCompiledComponentsPythonRecipe
from pythonforandroid.logger import shprint, info_notify
from pythonforandroid.util import current_directory, touch


class MydjvulibRecipe(CppCompiledComponentsPythonRecipe):
    """This is a two-in-one recipe:
      - build labraru `libprotobuf.so`
      - build and install python binding for protobuf_cpp
    """
    name = 'mydjvulib'
    version = '0.1.2'
    url = 'https://github.com/ssppkenny/djvu_utils/archive/refs/tags/{version}.zip'
    call_hostpython_via_targetpython = False
    depends = ['setuptools']
    site_packages_name = 'mydjvulib'
    stl_lib_name = 'c++_shared'

    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        env['TARGET_OS'] = 'OS_ANDROID_CROSSCOMPILE'
        env['CXXFLAGS'] += ' -fno-omit-frame-pointer -fsanitize=bool'
        env['CPPFLAGS'] += ' -fno-omit-frame-pointer -fsanitize=bool'
        # env['CPPFLAGS'] += ' -femulated-tls=1'
        # env['LDFLAGS'] += ' -lstdc++ -stdlib=libc++ -static'
        env['LDFLAGS'] += ' -fsanitize=bool'
        return env


recipe = MydjvulibRecipe()
