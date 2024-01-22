# Download/Install

Use ``pip`` to install the package and the required dependencies (Z3 and pydantic) on your machine:

``` bash
pip install ProcessScheduler
```
and check the installation from a python3 prompt:


``` py
>>> import processscheduler as ps
```

# Additional dependencies

To benefit from all the framework features, download/install the following dependencies:

``` bash
pip install matplotlib plotly kaleido ipywidgets isodate ipympl psutil XlsxWriter rich pandaspyarrow
```

# Development version from git repository

Create a local copy of the `github <https://github.com/tpaviot/ProcessScheduler>`_ repository:

``` bash
git clone https://github.com/tpaviot/ProcessScheduler
```

Then install the development version:

``` bash
cd ProcessScheduler
pip install -e .
```

To install additional dependencies:

```bash
pip install -r requirements.txt
```
