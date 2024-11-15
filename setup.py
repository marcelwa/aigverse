"""Setup script for the aigverse Python bindings."""

import os
import platform
import re
import subprocess
import sys
from pathlib import Path

from setuptools import Extension, setup
from setuptools.command.build_ext import build_ext


class CMakeExtension(Extension):
    """An extension to build using CMake.

    This is a simple extension that does not require any additional libraries or data files. It is intended to be used
    with the CMakeBuild class.
    """

    def __init__(self, name: str, sourcedir: str = "", namespace: str = "") -> None:
        """Initialize the CMake extension.

        Args:
            name (str): The name of the extension.
            sourcedir (str): The source directory.
            namespace (str): The namespace of the extension
        """
        Extension.__init__(self, name, sources=[])
        self.sourcedir = Path.resolve(Path(sourcedir))
        self.namespace = namespace


class CMakeBuild(build_ext):
    """A custom build extension for adding CMake support.

    This is a simple extension that does not require any additional libraries or data files.
    """

    def build_extension(self, ext: Extension) -> None:
        """Build the CMake extension.

        Args:
            ext (Extension): The extension to build.

        Raises:
            subprocess.CalledProcessError: If the build fails.
        """
        self.package = ext.namespace
        extdir = Path.resolve(Path(self.get_ext_fullpath(ext.name)).parent)
        # required for auto-detection of auxiliary "native" libs
        if not extdir.as_posix().endswith(os.path.sep):
            extdir / os.path.sep

        cmake_args = [
            "-DCMAKE_LIBRARY_OUTPUT_DIRECTORY=" + extdir.as_posix(),
            "-DPYTHON_EXECUTABLE=" + sys.executable,
            "-DMOCKTURTLE_EXAMPLES=OFF",
            "-DAIGVERSE_ENABLE_IPO=ON",
            "-DAIGVERSE_ENABLE_PCH=ON",
            "-DAIGVERSE_ENABLE_UNITY_BUILD=ON",
        ]

        if self.compiler.compiler_type != "msvc":
            # Using Ninja-build since it a) is available as a wheel and b)
            # multithreads automatically. MSVC would require all variables be
            # exported for Ninja to pick it up, which is a little tricky to do.
            # Users can override the generator with CMAKE_GENERATOR in CMake
            # 3.15+.
            cmake_generator = os.environ.get("CMAKE_GENERATOR", "")
            if not cmake_generator:
                cmake_args += ["-GNinja"]

        cfg = "Debug" if self.debug else "Release"
        cmake_args += [f"-DCMAKE_BUILD_TYPE={cfg}"]
        build_args = ["--config", cfg]

        if platform.system() == "Windows":
            cmake_args += [f"-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_{cfg.upper()}={extdir}"]
            cmake_args += ["-T", "ClangCl"]
            if sys.maxsize > 2**32:
                cmake_args += ["-A", "x64"]
            build_args += ["--", "/m"]
        else:
            cpus = os.cpu_count()
            if cpus is None:
                cpus = 2
            build_args += ["--", f"-j{cpus}"]

        # cross-compile support for macOS - respect ARCHFLAGS if set
        if sys.platform.startswith("darwin"):
            archs = re.findall(r"-arch (\S+)", os.environ.get("ARCHFLAGS", ""))
            if archs:
                arch_argument = "-DCMAKE_OSX_ARCHITECTURES={}".format(";".join(archs))
                cmake_args += [arch_argument]

        env = os.environ.copy()
        env["CXXFLAGS"] = '{} -DVERSION_INFO=\\"{}\\"'.format(env.get("CXXFLAGS", ""), self.distribution.get_version())
        if not Path.exists(Path(self.build_temp)):
            Path.mkdir(self.build_temp, parents=True)
        else:
            Path.unlink(Path(self.build_temp) / "CMakeCache.txt")

        subprocess.check_call(["cmake", ext.sourcedir, *cmake_args], cwd=self.build_temp, env=env)
        subprocess.check_call(["cmake", "--build", ".", "--target", ext.name, *build_args], cwd=self.build_temp)


README_PATH = Path.resolve(Path(__file__).parent) / "README.md"
with Path.open(README_PATH, encoding="utf8") as readme_file:
    README = readme_file.read()

setup(
    name="aigverse",
    version="0.0.11",
    author="Marcel Walter",
    author_email="marcel.walter@tum.de",
    description="A Python library for working with logic networks, synthesis, and optimization.",
    long_description=README,
    long_description_content_type="text/markdown",
    license="MIT",
    url="https://github.com/marcelwa/aigverse",
    ext_modules=[CMakeExtension("aigverse")],
    cmdclass={"build_ext": CMakeBuild},
    package_data={"aigverse": ["*.pyi"]},
    zip_safe=False,
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "Programming Language :: C++",
        "Environment :: Console",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
        "Operating System :: POSIX :: Linux",
        "Intended Audience :: Science/Research",
        "Natural Language :: English",
        "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
    ],
    keywords="aigverse logic synthesis AIG optimization",
    project_urls={
        "Source": "https://github.com/marcelwa/aigverse",
        "Tracker": "https://github.com/marcelwa/aigverse/issues",
        # 'Documentation': 'https://aigverse.readthedocs.io/en/latest/',
    },
)
