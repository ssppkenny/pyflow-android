from pythonforandroid.recipe import PythonRecipe

class SortedcontainersRecipe(PythonRecipe):
    site_packages_name = 'sortedcontainers'
    version = 'v2.1.0'
    url = 'https://github.com/grantjenks/python-sortedcontainers/archive/refs/tags/{version}.zip'
    call_hostpython_via_targetpython = False
    # to be detected by the matplotlib install script
    install_in_hostpython = True
    depends = ['setuptools']


recipe = SortedcontainersRecipe()
