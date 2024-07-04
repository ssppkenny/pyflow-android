1. Install pixi.dev
2. create project folder
3. cd into project folder
4. pixi init .
5. pixi shell
6. pixi add python=3.11
7. pixi add numpy=1.24.4
8. pixi add cython
9. pixi add pip
10. pixi.toml add section 
    [pypi-dependencies]
    buildozer = "~=1.5.0"
11. run pixi install
12. export JAVA_HOME=/Library/Java/JavaVirtualMachines/jdk-17.0.2.jdk/Contents/Home
13. export PATH=/Library/Java/JavaVirtualMachines/jdk-17.0.2.jdk/Contents/Home/bin:$PATH
14.  buildozer android debug deploy run
15. copy packages from extra_packages into .buildozer/android/platform/python-for-android/pythonforandroid/recipes
16.  buildozer android debug deploy run

