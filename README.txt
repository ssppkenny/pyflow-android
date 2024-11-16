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


Build project with docker
1. docker build --platform linux/amd64  -t myappimage .
2. docker run -it --platform linux/amd64 myappimage  /bin/bash
3. cd pyflow-android
4. pixi install
5. pixi shell
6. buildozer android debug
7. Ctrl-C after the android sdk is downloaded
8. copy packages from extra_packages into .buildozer/android/platform/python-for-android/pythonforandroid/recipes
9. wait until build is completed
10. copy libriries from libs into .buildozer/android/platform/build-arm64-v8a/dists/myapp/libs/arm64-v8a


