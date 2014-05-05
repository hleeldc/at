from distutils.core import setup
setup(name="at",
      version="1.0.0",
      description="Collection of widgets for linguistic annotation tools",
      author="Haejoong Lee",
      author_email="hajoong@ldc.upenn.edu",
      url="https://github.com/hleeldc/at",
      packages=['at4'],
      package_dir={'at4':'src'},
      data_files=[('docs',['docs/TDF_format.txt'])]
      )
