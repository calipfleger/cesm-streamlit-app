# CESM Streamlit App

A beginner-friendly, modular, and reproducible project for exploring CESM NetCDF data files using a web interface built with Streamlit.

---

## 1. Project Structure

```
cesm-streamlit-app/
│
├── app.py               # Main Streamlit app
├── cesm_utils.py        # CESM data helper functions
├── environment.yml      # Conda environment specification
├── .gitignore           # Git ignore rules
├── README.md            # This file!
└── data/
    └── sample.nc        # Sample NetCDF file for testing
```

---

## 2. Conda Environment Setup

These steps ensure everyone uses the same packages/versions.

1. **Check for `environment.yml`:**
    ```bash
    ls
    ```
    You should see `environment.yml` in the output.

2. **View its contents (optional):**
    ```bash
    cat environment.yml
    ```

3. **Create the environment (run this only once):**
    ```bash
    conda env create -f environment.yml
    ```

4. **Activate the environment:**
    ```bash
    conda activate cesm-streamlit
    ```

5. **Check installed packages:**
    ```bash
    conda list
    ```
    You should see `streamlit`, `xarray`, `netcdf4`, `matplotlib`, `numpy`, etc.

---

## 3. Sample Data

A sample NetCDF file (`sample.nc`) is provided in the `data/` folder for testing.

- To use your own data, upload a `.nc` file via the app interface.
- The `.gitignore` is set to ignore all files in `data/`, **except** the provided sample.

---

## 4. Running and Testing

1. **Make sure your Conda environment is set up and activated.**
2. **Start the app:**
    ```bash
    streamlit run app.py
    ```
3. **How it works:**
    - If you do not upload a file, the app loads the sample data automatically.
    - You can upload your own `.nc` file at any time using the upload button in the app.

---

## 5. Editing Files from the Terminal

This project is beginner-friendly! Here’s how you open and edit files from the terminal:

1. **Open your terminal.**
2. **Navigate to your project folder:**
    ```bash
    cd ~/cesm-streamlit-app
    ```
3. **List the files to confirm you are in the right place:**
    ```bash
    ls
    ```
4. **Open a file to edit (choose one method):**
    - With nano (Mac/Linux/WSL):
        ```bash
        nano FILENAME
        ```
        - Edit as needed. Save: `Ctrl + O`, then enter. Exit: `Ctrl + X`.
    - With VS Code (if installed):
        ```bash
        code FILENAME
        ```
    - With Notepad (Windows only):
        ```bash
        notepad FILENAME
        ```

---

## 6. Version Control (Git & GitHub)

Keep your changes tracked and share them with collaborators.

1. **See what’s changed:**
    ```bash
    git status
    ```
2. **Add changed files:**
    ```bash
    git add .
    ```
3. **Commit your changes:**
    ```bash
    git commit -m "Describe your change"
    ```
4. **Push to GitHub:**
    ```bash
    git push
    ```

---

## 7. Troubleshooting

- **App won’t start?**  
  Make sure your conda environment is activated and required packages are installed.

- **Environment issues?**  
  Remove and recreate it:
    ```bash
    conda remove --name cesm-streamlit --all
    conda env create -f environment.yml
    ```

- **Confused by errors?**  
  Read the error message, search online, or ask for help!

---

## 8. Modularity & Reproducibility Tips

- **Add new features in separate Python files or functions.**
- **Document all steps and files in your README.md.**
- **After each major change, test by creating a new environment and running the app from scratch.**
- **Update `.gitignore` as needed to keep your repo clean.**

---

## 9. Next Steps

- Add real CESM NetCDF data for your project.
- Improve the app’s plotting and UI.
- Share new features and document everything you add!

---

*Happy collaborating! This README is designed to help anyone (even complete beginners) get started, contribute, and understand the project.*
