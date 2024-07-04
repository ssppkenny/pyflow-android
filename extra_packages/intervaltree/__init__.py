from pythonforandroid.recipe import PythonRecipe


class IntervaltreeRecipe(PythonRecipe):
    site_packages_name = 'intervaltree'
    version = '3.1.0'
    url = 'https://github.com/chaimleib/intervaltree/archive/refs/tags/{version}.zip'
    call_hostpython_via_targetpython = False
    # to be detected by the matplotlib install script
    install_in_hostpython = True
    depends = ['setuptools', 'sortedcontainers']


recipe = IntervaltreeRecipe()
