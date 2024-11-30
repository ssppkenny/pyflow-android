from pythonforandroid.recipe import CompiledComponentsPythonRecipe


class RlsaFastRecipe(CompiledComponentsPythonRecipe):
    """This is a two-in-one recipe:
      - build labraru `libprotobuf.so`
      - build and install python binding for protobuf_cpp
    """
    name = 'rlsafast'
    version = '0.0.2'
    url = 'https://github.com/ssppkenny/pythonRLSA/archive/refs/tags/{version}.zip'
    call_hostpython_via_targetpython = False
    depends = ['numpy', 'setuptools']
    site_packages_name = 'rlsafast'

recipe = RlsaFastRecipe()
