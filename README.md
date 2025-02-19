# FTIR Data Processing V5

## 📌 Overview
FTIR Data Processing V5 is a Python-based GUI application designed for **FTIR spectral data processing**. It automates common data manipulation tasks, including:
- **Combining CSV files** for spectral analysis.
- **Sorting spectral columns** for better organization.
- **Renaming columns** based on voltage/time intervals.
- **Reprocessing background** signals for cleaner data.
- **Ensuring column name consistency** to prevent unwanted `.1` suffixes.
- **A dynamic GUI with auto-resizing** for different screen sizes.

This tool was developed to streamline FTIR data processing, making it easier to work with large datasets while maintaining accuracy and consistency.

## 🛠 Features
✅ **Combine CSV Files**: Merges multiple FTIR spectral files.<br>
✅ **Sort Spectral Data**: Ensures proper column organization.<br>
✅ **Rename Columns by Voltage/Time**: Automatically labels columns based on experimental conditions.<br>
✅ **Reprocess Background Spectra**: Removes unwanted background signals.<br>
✅ **Preserve Column Names**: Prevents pandas from appending `.1` to duplicate names.<br>
✅ **User-Friendly GUI**: Built using `tkinter`, with a scrollable and resizable layout.<br>
✅ **Standalone Executable**: Can be converted to an `.exe` file for ease of use.<br>

---

## 🚀 Installation & Setup
### **1. Prerequisites**
Ensure you have Python 3 installed. Then, install the required dependencies:
```bash
pip install pandas polars natsort tk

```
## To create a standalone executable (.exe) with no command window:
pyinstaller --onefile --noconsole --icon="ftir-icon.ico" FTIR-Data-process_v5.py
The executable will be available in the dist/ folder.


