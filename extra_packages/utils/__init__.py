'''A dummy recipe to build my custom lib
'''
from os.path import basename, dirname, exists, isdir, isfile, join, realpath, split

import fnmatch
from os import listdir, unlink, environ, curdir, walk
import sh
from pythonforandroid.util import (
    current_directory, ensure_dir, BuildInterruptingException, rmdir, move,
    touch)
from pythonforandroid.recipe import Recipe, CythonRecipe, IncludedFilesBehaviour, CompiledComponentsPythonRecipe
from pythonforandroid.logger import (
    logger, info, warning, debug, shprint, info_main)




class UtilsRecipe(CythonRecipe):
    version = '0.1.2'
    url = 'https://github.com/ssppkenny/myutils/archive/refs/tags/0.1.2.zip'
    site_packages_name = 'utils'
    depends = ['setuptools', 'cython']
    install_in_hostpython = False
    call_hostpython_via_targetpython = False


    def build_arch(self, arch):
        info("build_arch utils")
        '''Build any cython components, then install the Python module by
        calling setup.py install with the target Python dir.
        '''
        Recipe.build_arch(self, arch)
        self.build_cython_components(arch)
        self.install_python_package(arch)

    def build_cython_components(self, arch):
        info("build_cython_components utils")
        info('Cythonizing anything necessary in {}'.format(self.name))

        env = self.get_recipe_env(arch)

        with current_directory(self.get_build_dir(arch.arch)):
            hostpython = sh.Command(self.ctx.hostpython)
            shprint(hostpython, '-c', 'import sys; print(sys.path)', _env=env)
            debug('cwd is {}'.format(realpath(curdir)))
            info('Trying first build of {} to get cython files: this is '
                 'expected to fail'.format(self.name))

            manually_cythonise = False
            try:
                shprint(hostpython, 'setup.py', 'build_ext', '-v', _env=env,
                        *self.setup_extra_args)
            except sh.ErrorReturnCode_1:
                print()
                info('{} first build failed (as expected)'.format(self.name))
                manually_cythonise = True

            if manually_cythonise:
                self.cythonize_build(env=env)
                shprint(hostpython, 'setup.py', 'build_ext', '-v', _env=env,
                        _tail=20, _critical=True, *self.setup_extra_args)
            else:
                info('First build appeared to complete correctly, skipping manual'
                     'cythonising.')

            if not self.ctx.with_debug_symbols:
                self.strip_object_files(arch, env)

    def strip_object_files(self, arch, env, build_dir=None):
        if build_dir is None:
            build_dir = self.get_build_dir(arch.arch)
        with current_directory(build_dir):
            info('Stripping object files')
            shprint(sh.find, '.', '-iname', '*.so', '-exec',
                    '/usr/bin/echo', '{}', ';', _env=env)
            shprint(sh.find, '.', '-iname', '*.so', '-exec',
                    env['STRIP'].split(' ')[0], '--strip-unneeded',
                    # '/usr/bin/strip', '--strip-unneeded',
                    '{}', ';', _env=env)

    def cythonize_file(self, env, build_dir, filename):
        info("cythonize file utils " + filename)
        short_filename = filename
        if filename.startswith(build_dir):
            short_filename = filename[len(build_dir) + 1:]
        info(u"Cythonize {}".format(short_filename))
        cyenv = env.copy()
        if 'CYTHONPATH' in cyenv:
            cyenv['PYTHONPATH'] = cyenv['CYTHONPATH']
        elif 'PYTHONPATH' in cyenv:
            del cyenv['PYTHONPATH']
        if 'PYTHONNOUSERSITE' in cyenv:
            cyenv.pop('PYTHONNOUSERSITE')
        python_command = sh.Command("python{}".format(
            self.ctx.python_recipe.major_minor_version_string.split(".")[0]
        ))
        shprint(python_command, "-c"
                "import sys; from Cython.Compiler.Main import setuptools_main; sys.exit(setuptools_main());",
                filename, *self.cython_args, _env=cyenv)

    def cythonize_build(self, env, build_dir="."):
        info("cythonize_build utils")
        if not self.cythonize:
            info('Running cython cancelled per recipe setting')
            return
        info('Running cython where appropriate')
        for root, dirnames, filenames in walk("."):
            for filename in fnmatch.filter(filenames, "*.pyx"):
                self.cythonize_file(env, build_dir, join(root, filename))

    def get_recipe_env(self, arch, with_flags_in_cc=True):
        info("get_recipe_env utils")
        env = super().get_recipe_env(arch, with_flags_in_cc)
        env['LDFLAGS'] = env['LDFLAGS'] + ' -L{} '.format(
            self.ctx.get_libs_dir(arch.arch) +
            ' -L{} '.format(self.ctx.libs_dir) +
            ' -L{}'.format(join(self.ctx.bootstrap.build_dir, 'obj', 'local',
                                arch.arch)))

        env['LDSHARED'] = env['CC'] + ' -shared'
        # shprint(sh.whereis, env['LDSHARED'], _env=env)
        env['LIBLINK'] = 'NOTNONE'
        if self.ctx.copy_libs:
            env['COPYLIBS'] = '1'

        # Every recipe uses its own liblink path, object files are
        # collected and biglinked later
        liblink_path = join(self.get_build_container_dir(arch.arch),
                            'objects_{}'.format(self.name))
        env['LIBLINK_PATH'] = liblink_path
        ensure_dir(liblink_path)
        ## env['LDFLAGS'] += ' -framework CoreFoundation -framework CoreGraphics'

        return env


recipe = UtilsRecipe()
