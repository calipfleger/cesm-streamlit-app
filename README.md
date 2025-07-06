# CESM Streamlit App

Welcome to the CESM Streamlit App!  
This comprehensive, step-by-step guide will help you set up, run, and customize a web application for visualizing CESM (Community Earth System Model) NetCDF climate data using Python and Streamlit.

**No prior experience with Streamlit, conda, or climate science is required.**  
If you can follow instructions and copy-paste commands into your terminal, you can use, explore, and expand this app!

---

## Table of Contents

1. [About This Project](#about-this-project)
2. [What is CESM?](#what-is-cesm)
3. [What is Streamlit?](#what-is-streamlit)
4. [What is NetCDF?](#what-is-netcdf)
5. [Requirements](#requirements)
6. [Installation](#installation)
7. [Running the App](#running-the-app)
8. [How to Load Your Own Data](#how-to-load-your-own-data)
9. [Exploring the App Features](#exploring-the-app-features)
10. [Editing Files From the Terminal (Beginner Guide)](#editing-files-from-the-terminal-beginner-guide)
11. [Troubleshooting](#troubleshooting)
12. [FAQ](#faq)
13. [Contributing](#contributing)
14. [License](#license)
15. [Acknowledgements](#acknowledgements)
16. [Glossary](#glossary)

---

## About This Project

This project provides an intuitive Streamlit web app for exploring, visualizing, and analyzing CESM NetCDF climate datasets.  
It is designed to be **beginner-friendly**, with thorough documentation and detailed explanations at every step.

**What can you do with this app?**
- Upload CESM NetCDF files and explore their contents interactively  
- Visualize variables (e.g., temperature, precipitation, etc.) as maps, timeseries, and more  
- Learn how to modify and expand the app to fit your own research and curiosity

---

## What is CESM?

**CESM** stands for the *Community Earth System Model*, a sophisticated climate model developed by the National Center for Atmospheric Research (NCAR) and collaborators.  
CESM simulates interactions between the atmosphere, oceans, land, and sea ice, and is widely used in climate science.

**Typical CESM output:**  
- Data stored in *NetCDF* files (with `.nc` extension)
- Contain variables such as temperature, precipitation, pressure, etc., over space and time

---

## What is Streamlit?

[Streamlit](https://streamlit.io/) is an open-source Python library that makes it easy to turn scripts into interactive web apps.  
You do **not** need to know HTML, CSS, or JavaScript—only Python.

**Why use Streamlit?**
- Build interactive data apps with only a few lines of Python
- Share results and visualizations instantly in the browser
- Perfect for scientists, students, and data enthusiasts

---

## What is NetCDF?

**NetCDF** (Network Common Data Form) is a file format designed for storing array-oriented scientific data.  
It is commonly used in climate science, meteorology, oceanography, and other fields where large, multi-dimensional data sets (like time, latitude, longitude, depth) are generated.

**Key Points:**
- File extension: `.nc`
- Can store multiple variables, dimensions, and metadata in one file
- Readable with Python's [xarray](https://docs.xarray.dev/en/stable/) and [netCDF4](https://unidata.github.io/netcdf4-python/) libraries

---

## Requirements

To use this app, you will need:

- **Python 3.8 or newer** (Anaconda or Miniconda recommended)
- **conda** (comes with Anaconda/Miniconda)
- **git** (to download this repository)
- **A modern web browser** (Chrome, Firefox, Safari, Edge, etc.)

> **Tip:** Anaconda/Miniconda make managing Python environments much easier for beginners.

---

## Installation

### Step 1: Open Your Terminal

- **Mac:** Press `Cmd + Space`, type "Terminal", press Enter.
- **Windows:** Open "Anaconda Prompt" or "Command Prompt".
- **Linux:** Open your preferred terminal emulator.

### Step 2: Download the Repository

This command downloads all the code to your computer.

```bash
git clone https://github.com/yourusername/cesm-streamlit-app.git
cd cesm-streamlit-app
```
> Replace `yourusername` with the correct username if needed.

### Step 3: Create and Activate a Conda Environment

A conda environment keeps all the necessary Python packages organized and avoids conflicts.

#### Option 1: With the provided environment file (Recommended)

```bash
conda env create -f environment.yml
conda activate cesm-streamlit
```
- This creates a new environment named `cesm-streamlit` and installs all necessary packages.

#### Option 2: Manual Install

If you want to install packages yourself:

```bash
conda create -n cesm-streamlit python=3.10
conda activate cesm-streamlit
pip install -r requirements.txt
```
- This method also creates and activates the environment, then installs required Python packages.

### Step 4: Install Streamlit (if needed)

If you get any errors about missing `streamlit`, install it with:

```bash
conda install streamlit
```
or
```bash
pip install streamlit
```

---

## Running the App

After activating the environment and navigating to your project folder, start the app with:

```bash
streamlit run app.py
```

- **What happens next?**
  - Streamlit will print a local URL, such as:
    ```
    Local URL: http://localhost:8501
    ```
  - Your browser may open automatically. If not, copy and paste the link into your browser.

- **To stop the app:**  
  - Go to the terminal where Streamlit is running and press `Ctrl + C` (hold Control and press the C key).

---

## How to Load Your Own Data

You can use your own CESM NetCDF files in two main ways:

### **Option 1: Upload in the Web App (Beginner-Friendly)**

1. Start the app (see "Running the App" above).
2. In your browser, click the “Upload CESM NetCDF file” button.
3. Select your `.nc` file from your computer.
4. The app will load and display your data.

> **Best for beginners:** No coding or file moving required!

---

### **Option 2: Use Your File as the Default Data Source (Advanced/Power Users)**

If you want your file to load automatically every time:

1. **Copy your file into the `data/` folder**  
   For example, if your file is called `mydata.nc` and is on your Desktop:
   ```bash
   cp ~/Desktop/mydata.nc data/mydata.nc
   ```

2. **Update `app.py` to point to your file**  
   - Open `app.py` in a text editor (see below for editing instructions).
   - Find this line:
     ```python
     sample_file = os.path.join("data", "sample.nc")
     ```
   - Change it to:
     ```python
     sample_file = os.path.join("data", "mydata.nc")
     ```
   - Save the file and restart the app.

---

## Exploring the App Features

The CESM Streamlit App provides a variety of tools for exploring and visualizing climate data.

### **Main Features:**

- **File Upload:** Upload any CESM NetCDF file through your browser.
- **Variable Selection:** Choose which climate variable (e.g., temperature, precipitation) to view.
- **Interactive Maps:** Visualize data as spatial maps (e.g., world maps, latitude-longitude grids).
- **Time Series Plots:** Plot variables over time at specific locations or averaged over areas.
- **Metadata Display:** View detailed information about the dataset, its variables, and attributes.
- **Download Processed Data:** Export your selected data as CSV or NetCDF for further analysis.

> **Tip:** The app is designed for easy expansion. You can add new visualizations or analysis tools by editing `app.py` and `cesm_utils.py`.

### **Sample Workflow:**

1. Upload your CESM NetCDF file.
2. Select a variable from the dropdown menu.
3. Adjust any plotting options (e.g., time range, region of interest).
4. View maps, time series, and summary statistics.
5. Download processed results as needed.

---

## Editing Files From the Terminal (Beginner Guide)

You may want to edit or add code to customize how data is loaded or processed.  
Here’s a full, beginner-friendly walkthrough of editing a Python file from the terminal.

### Example: Add or Edit Code in `cesm_utils.py`

1. **Open your terminal.**
2. **Navigate to your project folder:**
    ```bash
    cd ~/cesm-streamlit-app
    ```
3. **Open `cesm_utils.py` with a text editor.**  
   For beginners, `nano` is easy (it runs in your terminal):
    ```bash
    nano cesm_utils.py
    ```
4. **Clear the file if you want to start fresh:**  
   - Press `Ctrl + K` repeatedly to cut (delete) each line until the file is empty.

5. **Paste or type the following code into the file:**  
   *(If the file already has other code, just add this at the top or bottom, but don’t duplicate function names!)*

    ```python
    import xarray as xr

    def load_cesm_data(file):
        """Load CESM NetCDF file (uploaded or path) into xarray.Dataset."""
        if hasattr(file, "read"):  # For uploaded file-like objects
            return xr.open_dataset(file)
        else:  # For file paths
            return xr.open_dataset(str(file))

    def get_variable(ds, varname):
        """Return a variable (DataArray) from the xarray.Dataset."""
        return ds[varname]
    ```

6. **Save and exit nano:**  
   - Press `Ctrl + O` (the letter O, not zero) to save.
   - Press `Enter` to confirm the filename.
   - Press `Ctrl + X` to exit the editor.

7. **You’re done!**  
   Now your `cesm_utils.py` file has the needed functions.

---

### Other Ways to Edit Files

- **With VS Code (if installed):**
    ```bash
    code FILENAME
    ```
- **With Notepad (Windows only):**
    ```bash
    notepad FILENAME
    ```

### **Summary Table: Editing a File in Terminal**

| Step            | Command or Action                  |
|-----------------|-----------------------------------|
| Open terminal   | *(open Terminal app)*              |
| Go to project   | `cd ~/cesm-streamlit-app`          |
| Edit file       | `nano cesm_utils.py`               |
| Paste code      | *(copy/paste code above)*          |
| Save/exit       | `Ctrl + O`, `Enter`, `Ctrl + X`    |

---

## Troubleshooting

### **1. "streamlit: command not found"**

- Make sure your conda environment is activated:
    ```bash
    conda activate cesm-streamlit
    ```
- If you still get this error, install Streamlit:
    ```bash
    conda install streamlit
    ```
    or
    ```bash
    pip install streamlit
    ```

---

### **2. "ModuleNotFoundError: No module named 'streamlit'"**

- This means Streamlit is not installed in your environment.  
  With your environment activated, install Streamlit as above.

---

### **3. "AttributeError: module 'cesm_utils' has no attribute 'load_cesm_data'"**

- Make sure your `cesm_utils.py` file contains the `load_cesm_data` function (see [Editing Files](#editing-files-from-the-terminal-beginner-guide)).

---

### **4. "No module named xarray" or other missing package errors**

- Install missing packages using conda or pip:
    ```bash
    conda install xarray
    ```
    or
    ```bash
    pip install xarray
    ```

---

### **5. How do I track new data files with git?**

By default, the `data/` folder is ignored by git for privacy and storage reasons.  
If you want to track a new data file, add a line to `.gitignore` like this:

```
!data/your_file.nc
```

This tells git to track this specific file.

---

## FAQ

**Q: I’ve never used the terminal before. Where do I type these commands?**  
A: On Mac, open “Terminal” from Applications > Utilities. On Windows, use “Anaconda Prompt” or “Command Prompt”.

**Q: What is a “conda environment”?**  
A: It’s a self-contained Python setup. It keeps your project’s packages separate from others on your computer.  
This helps avoid conflicts and makes it easy to replicate your setup on other machines.

**Q: How do I stop the app?**  
A: Go to the terminal where Streamlit is running and press `Ctrl + C`.

**Q: I made a mistake editing a file. What do I do?**  
A: You can re-edit the file with `nano` or VS Code and fix the mistake. If you’re using git, you can undo changes with `git checkout -- FILENAME`.

**Q: Can I use this on Windows?**  
A: Yes! All the instructions here work on Windows, Mac, and Linux. On Windows, use “Anaconda Prompt” or “Command Prompt” instead of Terminal.

**Q: What is NetCDF? Why is it used?**  
A: NetCDF is a file format optimized for large, multi-dimensional scientific datasets, making it perfect for climate data.

**Q: What is xarray?**  
A: [xarray](https://docs.xarray.dev/en/stable/) is a Python library for working with multi-dimensional labeled arrays. It makes loading, analyzing, and visualizing NetCDF data easy.

---

## Contributing

Contributions are always welcome!  
- **Found a bug?** Open an issue.
- **Have a feature idea?** Open a pull request!
- **Want to improve the documentation?** PRs are very welcome.

To contribute:
1. Fork this repository
2. Create your feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for more details.

---

## License

MIT License (see [LICENSE](LICENSE))

---

## Acknowledgements

- [Streamlit](https://streamlit.io/) — for making data apps easy!
- [xarray](https://xarray.dev/) — for working with NetCDF data.
- CESM Project ([NCAR](https://www.cesm.ucar.edu/)) — for providing the climate data and model.
- The scientific Python community

---

## Glossary

- **CESM:** Community Earth System Model, a climate modeling framework.
- **NetCDF:** Network Common Data Form, a file format for scientific data.
- **Streamlit:** Python library for building interactive web apps.
- **conda environment:** Isolated Python installations for managing dependencies.
- **xarray:** Python package for multi-dimensional arrays, perfect for NetCDF.

---

## ⭐️ You did it!

If you made it this far, you can run and edit Python data apps!  
Enjoy exploring CESM data, and remember—**ask questions and experiment**.  
If you get stuck: copy the full error message and search online, or open an issue in this repository.

---
