import os
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import polars as pl
import pandas as pd
from natsort import natsorted

# Global variable initialization
global_file_path_lv = ""
global_file_path_cv = ""
filename_step4 = ""
df_step4 = None
canvas = None


# Step 1: Combine CSV Files with Proper Wavenumber Truncation and Matching
def combine_csv_files(folder_path):
    # Use natsorted to naturally sort the list of CSV files by their file names
    csv_files = natsorted([f for f in os.listdir(folder_path) if f.lower().endswith('.csv')])

    if not csv_files:
        return "No CSV files found in the selected folder."

    combined_data = None

    for i, csv_file in enumerate(csv_files):
        file_path = os.path.join(folder_path, csv_file)
        print(f"Processing file {i + 1}/{len(csv_files)}: {csv_file}")

        # Load the CSV file into a Polars DataFrame, assuming no headers and specifying column names
        df = pl.read_csv(file_path, has_header=False, new_columns=["Wavenumber", csv_file])

        # Truncate the Wavenumber column to 1 decimal place without rounding
        df = df.with_columns([
            (pl.col("Wavenumber") // 0.1 * 0.1).alias("Wavenumber")  # Truncate to 1 decimal place
        ])

        # If this is the first file, initialize combined_data with it
        if combined_data is None:
            combined_data = df
        else:
            # Rename Wavenumber column temporarily to avoid duplicate columns
            df = df.rename({"Wavenumber": "Wavenumber_temp"})
            # Join on the truncated Wavenumber
            combined_data = combined_data.join(df, left_on="Wavenumber", right_on="Wavenumber_temp", how="full")
            # Drop the temporary Wavenumber column
            combined_data = combined_data.drop("Wavenumber_temp")

    # Return the combined DataFrame
    return combined_data


# Save the combined data as a CSV file
def save_as_csv_polars(combined_data, folder_path, default_name_base="combined"):
    default_file_name = os.path.join(folder_path, default_name_base + ".csv")
    # Add the 'parent=window' argument to ensure the save dialog is always on top
    save_path = filedialog.asksaveasfilename(initialfile=default_file_name,
                                             defaultextension=".csv",
                                             filetypes=[("CSV files", "*.csv")],
                                             title="Save data",
                                             parent=window)  # Ensure the dialog is always on top
    if save_path:
        combined_data.write_csv(save_path)
        messagebox.showinfo("Success", f"Data saved as {save_path}.", parent=window)  # Show success message on top


# Function to combine the series CSV files and save the result
def combine_series_csv_to_xlsx_or_csv():
    folder_path = filedialog.askdirectory(title="Select Folder with CSV Files")
    if folder_path:
        status_label.config(text="Processing...", fg="blue")
        window.update_idletasks()  # Ensure the status is updated immediately
        combine_csv_button.config(state=tk.DISABLED)
        window.update_idletasks()
        combined_data = combine_csv_files(folder_path)
        if isinstance(combined_data, str):
            messagebox.showerror("Error", combined_data, parent=window)  # Ensure error message is on top
        else:
            # Save combined data as CSV
            save_as_csv_polars(combined_data, folder_path)
        status_label.config(text="Completed", fg="green")
        combine_csv_button.config(state=tk.NORMAL)


# Function to sort spectral columns
def sort_spectral_columns():
    file_path = filedialog.askopenfilename(title="Select Combined CSV File to Sort",
                                           filetypes=[("CSV Files", "*.csv")])
    if file_path:
        status_label.config(text="Sorting...", fg="blue")
        window.update_idletasks()  # Ensure the status is updated immediately
        sort_button.config(state=tk.DISABLED)
        window.update_idletasks()
        df = pd.read_csv(file_path)
        wavenumber_col = df.pop("Wavenumber")
        sorted_df = df.reindex(sorted(df.columns), axis=1)
        sorted_df.insert(0, "Wavenumber", wavenumber_col)
        sorted_file_path = os.path.splitext(file_path)[0] + "_sorted.csv"
        sorted_df.to_csv(sorted_file_path, index=False)
        messagebox.showinfo("Success", f"Sorted data saved as {sorted_file_path}.",
                            parent=window)  # Success message on top
        status_label.config(text="Completed", fg="green")
        window.update_idletasks()  # Ensure the status is updated immediately
        sort_button.config(state=tk.NORMAL)


# Step 1: b) Combine Time-Resolved CSV Files
def extract_time_value(header):
    # Use regular expression to match the time value (t= 0.00) in the header
    time_match = re.search(r't = (\d+\.\d+)', header)
    if time_match:
        return time_match.group(1)  # Returns only the numerical part of the time
    return "Time"  # Default header if no match found


def combine_time_resolved_csv_to_xlsx_or_csv():
    folder_path = filedialog.askdirectory(title="Select Folder with Time-Resolved CSV Files")
    if folder_path:
        status_label.config(text="Processing...", fg="blue")
        time_resolved_csv_button.config(state=tk.DISABLED)
        window.update_idletasks()
        csv_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.csv') and "static" not in f.lower()]
        if not csv_files:
            messagebox.showerror("Error", "No suitable CSV files found in the selected folder.", parent=window)
            return

        combined_data = pd.DataFrame()
        headers = []

        for csv_file in csv_files:
            file_path = os.path.join(folder_path, csv_file)
            data = pd.read_csv(file_path, header=None)
            time_value = extract_time_value(csv_file)
            headers.append(time_value)

            if combined_data.empty:
                combined_data = data.iloc[:, :1]
                combined_data.columns = ['Wavenumber']

            combined_data[time_value] = data.iloc[:, 1]

        headers = sorted(headers, key=lambda x: float(x.split()[0]))
        combined_data = combined_data[['Wavenumber'] + headers]

        # Save combined data as CSV
        save_as_csv_pandas(combined_data, folder_path)
        status_label.config(text="Completed", fg="green")
        time_resolved_csv_button.config(state=tk.NORMAL)


# Function to save the combined data as CSV using Pandas
def save_as_csv_pandas(combined_data, folder_path, default_name_base="combined"):
    default_file_name = os.path.join(folder_path, default_name_base + ".csv")
    save_path = filedialog.asksaveasfilename(initialfile=default_file_name,
                                             defaultextension=".csv",
                                             filetypes=[("CSV files", "*.csv")],
                                             title="Save data")
    if save_path:
        combined_data.to_csv(save_path, index=False)
        messagebox.showinfo("Success", f"Data saved as {save_path}.", parent=window)


# Step 2: Rename Columns According to CV Voltage Range
def get_cv_settings():
    global t_eq_entry_cv, e_begin_entry_cv, e_vertex1_entry_cv, e_vertex2_entry_cv, scan_rate_entry_cv

    def save_cv_settings():
        global global_t_eq_cv, global_e_begin_cv, global_e_vertex1_cv, global_e_vertex2_cv, global_scan_rate_cv, global_potential_change_per_spectrum_cv, global_file_path_cv
        try:
            global_t_eq_cv = float(t_eq_entry_cv.get())
            global_e_begin_cv = float(e_begin_entry_cv.get())
            global_e_vertex1_cv = float(e_vertex1_entry_cv.get())
            global_e_vertex2_cv = float(e_vertex2_entry_cv.get())
            global_scan_rate_cv = float(scan_rate_entry_cv.get())

            if not (min(global_e_vertex1_cv, global_e_vertex2_cv) <= global_e_begin_cv <= max(global_e_vertex1_cv,
                                                                                              global_e_vertex2_cv)):
                messagebox.showerror("Input Error", "E_begin must be equal or between E_vertex1 and E_vertex2",
                                     parent=window)
                return

            if global_file_path_cv:
                if global_e_begin_cv == global_e_vertex2_cv:
                    total_potential_range_cv = abs(global_e_vertex1_cv - global_e_begin_cv) + abs(
                        global_e_begin_cv - global_e_vertex1_cv)
                else:
                    total_potential_range_cv = abs(global_e_vertex1_cv - global_e_begin_cv) + abs(
                        global_e_vertex2_cv - global_e_vertex1_cv) + abs(global_e_begin_cv - global_e_vertex2_cv)

                total_time_cv = total_potential_range_cv / global_scan_rate_cv
                total_time_cv += global_t_eq_cv
                num_spectra_cv = len(pd.read_csv(global_file_path_cv).columns) - 1
                time_interval_per_spectrum_cv = total_time_cv / num_spectra_cv
                global_potential_change_per_spectrum_cv = global_scan_rate_cv * time_interval_per_spectrum_cv
                potential_change_label_cv.config(
                    text=f"Potential Change per Spectrum: {global_potential_change_per_spectrum_cv:.6f} V/sec")

        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numeric values.", parent=window)

    tk.Label(settings_frame_cv, text="T equilibrium (s):").grid(row=0, column=0)
    tk.Label(settings_frame_cv, text="E begin (V):").grid(row=1, column=0)
    tk.Label(settings_frame_cv, text="E Vertex1 (V):").grid(row=2, column=0)
    tk.Label(settings_frame_cv, text="E Vertex2 (V):").grid(row=3, column=0)
    tk.Label(settings_frame_cv, text="Scan rate (V/s):").grid(row=4, column=0)

    t_eq_entry_cv = tk.Entry(settings_frame_cv)
    e_begin_entry_cv = tk.Entry(settings_frame_cv)
    e_vertex1_entry_cv = tk.Entry(settings_frame_cv)
    e_vertex2_entry_cv = tk.Entry(settings_frame_cv)
    scan_rate_entry_cv = tk.Entry(settings_frame_cv)

    t_eq_entry_cv.grid(row=0, column=1)
    e_begin_entry_cv.grid(row=1, column=1)
    e_vertex1_entry_cv.grid(row=2, column=1)
    e_vertex2_entry_cv.grid(row=3, column=1)
    scan_rate_entry_cv.grid(row=4, column=1)

    tk.Button(settings_frame_cv, text='Save', command=save_cv_settings, bg="green yellow").grid(row=5, column=1, pady=4)


def rename_columns_cv():
    global global_file_path_cv
    global_file_path_cv = filedialog.askopenfilename(title="Select Input File", filetypes=[("CSV Files", "*.csv")])
    if global_file_path_cv:
        status_label.config(text="Renaming Columns...", fg="blue")
        rename_columns_cv_button.config(state=tk.DISABLED)
        window.update_idletasks()
        try:
            df = pd.read_csv(global_file_path_cv)

            if not (min(global_e_vertex1_cv, global_e_vertex2_cv) <= global_e_begin_cv <= max(global_e_vertex1_cv,
                                                                                              global_e_vertex2_cv)):
                messagebox.showerror("Input Error", "E_begin must be equal or between E_vertex1 and E_vertex2",
                                     parent=window)
                return

            if global_e_begin_cv == global_e_vertex2_cv:
                total_potential_range_cv = abs(global_e_vertex1_cv - global_e_begin_cv) + abs(
                    global_e_begin_cv - global_e_vertex1_cv)
            else:
                total_potential_range_cv = abs(global_e_vertex1_cv - global_e_begin_cv) + abs(
                    global_e_vertex2_cv - global_e_vertex1_cv) + abs(global_e_begin_cv - global_e_vertex2_cv)

            total_time_cv = total_potential_range_cv / global_scan_rate_cv
            total_time_cv += global_t_eq_cv
            num_spectra_cv = len(df.columns) - 1
            time_interval_per_spectrum_cv = total_time_cv / num_spectra_cv
            potential_change_per_spectrum_cv = global_scan_rate_cv * time_interval_per_spectrum_cv

            current_potential_cv = global_e_begin_cv
            new_columns_cv = ["Wavenumber"]
            stage_cv = 1
            elapsed_time_cv = 0

            def calculate_next_potential(current, target, change):
                if current < target:
                    next_potential = min(current + change, target)
                else:
                    next_potential = max(current - change, target)
                return next_potential

            start_potential_cv = end_potential_cv = current_potential_cv

            for i in range(1, len(df.columns)):
                if elapsed_time_cv < global_t_eq_cv:
                    start_potential_cv = end_potential_cv = global_e_begin_cv
                    elapsed_time_cv += time_interval_per_spectrum_cv
                elif stage_cv == 1:
                    start_potential_cv = current_potential_cv
                    end_potential_cv = calculate_next_potential(current_potential_cv, global_e_vertex1_cv,
                                                                potential_change_per_spectrum_cv)
                    if end_potential_cv == global_e_vertex1_cv:
                        stage_cv = 2
                    current_potential_cv = end_potential_cv
                elif stage_cv == 2:
                    start_potential_cv = current_potential_cv
                    end_potential_cv = calculate_next_potential(current_potential_cv,
                                                                global_e_vertex2_cv if global_e_begin_cv != global_e_vertex2_cv else global_e_begin_cv,
                                                                potential_change_per_spectrum_cv)
                    if end_potential_cv == global_e_vertex2_cv or end_potential_cv == global_e_begin_cv:
                        stage_cv = 3 if global_e_begin_cv != global_e_vertex2_cv else 1
                    current_potential_cv = end_potential_cv
                elif stage_cv == 3:
                    start_potential_cv = current_potential_cv
                    end_potential_cv = calculate_next_potential(current_potential_cv, global_e_begin_cv,
                                                                potential_change_per_spectrum_cv)
                    if end_potential_cv == global_e_begin_cv:
                        stage_cv = 1
                    current_potential_cv = end_potential_cv

                midpoint_cv = (start_potential_cv + end_potential_cv) / 2
                new_columns_cv.append(f"{midpoint_cv:.2f} V")

            df.columns = new_columns_cv

            save_path_cv = os.path.splitext(global_file_path_cv)[0] + "_renamed_cv.csv"
            df.to_csv(save_path_cv, index=False)
            messagebox.showinfo("Success", f"Data saved as {save_path_cv}.", parent=window)
            status_label.config(text="Completed", fg="green")
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=window)
            status_label.config(text="Error", fg="red")
        finally:
            rename_columns_cv_button.config(state=tk.NORMAL)


# Step 2: Rename Columns According to LV Voltage Range
def get_lv_settings():
    global t_eq_entry_lv, e_begin_entry_lv, e_end_entry_lv, scan_rate_entry_lv

    def save_lv_settings():
        global global_t_eq_lv, global_e_begin_lv, global_e_end_lv, global_scan_rate_lv, global_potential_change_per_spectrum_lv, global_file_path_lv
        try:
            global_t_eq_lv = float(t_eq_entry_lv.get())
            global_e_begin_lv = float(e_begin_entry_lv.get())
            global_e_end_lv = float(e_end_entry_lv.get())
            global_scan_rate_lv = float(scan_rate_entry_lv.get())

            if global_e_begin_lv == global_e_end_lv:
                messagebox.showerror("Input Error", "E_begin must not be equal to E_end", parent=window)
                return

            if global_file_path_lv:
                total_potential_range_lv = abs(global_e_end_lv - global_e_begin_lv)
                total_time_lv = total_potential_range_lv / global_scan_rate_lv
                total_time_lv += global_t_eq_lv
                num_spectra_lv = len(pd.read_csv(global_file_path_lv).columns) - 1
                time_interval_per_spectrum_lv = total_time_lv / num_spectra_lv
                global_potential_change_per_spectrum_lv = global_scan_rate_lv * time_interval_per_spectrum_lv
                potential_change_label_lv.config(
                    text=f"Potential Change per Spectrum: {global_potential_change_per_spectrum_lv:.6f} V/sec")

        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numeric values.", parent=window)

    tk.Label(settings_frame_lv, text="T equilibrium (s):").grid(row=0, column=0)
    tk.Label(settings_frame_lv, text="E begin (V):").grid(row=1, column=0)
    tk.Label(settings_frame_lv, text="E end (V):").grid(row=2, column=0)
    tk.Label(settings_frame_lv, text="Scan rate (V/s):").grid(row=3, column=0)

    t_eq_entry_lv = tk.Entry(settings_frame_lv)
    e_begin_entry_lv = tk.Entry(settings_frame_lv)
    e_end_entry_lv = tk.Entry(settings_frame_lv)
    scan_rate_entry_lv = tk.Entry(settings_frame_lv)

    t_eq_entry_lv.grid(row=0, column=1)
    e_begin_entry_lv.grid(row=1, column=1)
    e_end_entry_lv.grid(row=2, column=1)
    scan_rate_entry_lv.grid(row=3, column=1)

    tk.Button(settings_frame_lv, text='Save', command=save_lv_settings, bg="green yellow").grid(row=4, column=1, pady=4)


def rename_columns_lv():
    global global_file_path_lv
    global_file_path_lv = filedialog.askopenfilename(title="Select Input File", filetypes=[("CSV Files", "*.csv")])
    if global_file_path_lv:
        status_label.config(text="Renaming Columns...", fg="blue")
        rename_columns_lv_button.config(state=tk.DISABLED)
        window.update_idletasks()
        try:
            df = pd.read_csv(global_file_path_lv)

            if global_e_begin_lv == global_e_end_lv:
                messagebox.showerror("Input Error", "E_begin must not be equal to E_end", parent=window)
                return

            total_potential_range_lv = abs(global_e_end_lv - global_e_begin_lv)
            total_time_lv = total_potential_range_lv / global_scan_rate_lv
            total_time_lv += global_t_eq_lv
            num_spectra_lv = len(df.columns) - 1
            time_interval_per_spectrum_lv = total_time_lv / num_spectra_lv
            potential_change_per_spectrum_lv = global_scan_rate_lv * time_interval_per_spectrum_lv

            current_potential_lv = global_e_begin_lv
            new_columns_lv = ["Wavenumber"]
            elapsed_time_lv = 0

            for i in range(1, len(df.columns)):
                if elapsed_time_lv < global_t_eq_lv:
                    start_potential_lv = end_potential_lv = global_e_begin_lv
                    elapsed_time_lv += time_interval_per_spectrum_lv
                else:
                    start_potential_lv = current_potential_lv
                    end_potential_lv = start_potential_lv + potential_change_per_spectrum_lv if global_e_begin_lv < global_e_end_lv else start_potential_lv - potential_change_per_spectrum_lv
                    current_potential_lv = end_potential_lv

                midpoint_lv = (start_potential_lv + end_potential_lv) / 2
                new_columns_lv.append(f"{midpoint_lv:.2f} V")

            df.columns = new_columns_lv

            save_path_lv = os.path.splitext(global_file_path_lv)[0] + "_renamed_lv.csv"
            df.to_csv(save_path_lv, index=False)
            messagebox.showinfo("Success", f"Data saved as {save_path_lv}.", parent=window)
            status_label.config(text="Completed", fg="green")
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=window)
            status_label.config(text="Error", fg="red")
        finally:
            rename_columns_lv_button.config(state=tk.NORMAL)


def rename_headers_based_on_time():
    global filename_step1
    filename_step1 = filedialog.askopenfilename(title="Select CSV File for Step 1", filetypes=[("CSV Files", "*.csv")])
    if filename_step1:
        status_label.config(text="Renaming Headers...", fg="blue")
        rename_time_button.config(state=tk.DISABLED)
        window.update_idletasks()
        try:
            df_step1 = pd.read_csv(filename_step1)
            total_time = simpledialog.askfloat("Input", "Total Time Collected (seconds):")
            if total_time is None:
                return
            num_columns = len(df_step1.columns) - 1  # Exclude the first column (wavenumbers)
            time_interval = total_time / num_columns
            new_headers = ['Wavenumber'] + [f"{i * time_interval:.2f}s" for i in range(num_columns)]
            df_step1.columns = new_headers

            renamed_filename = os.path.splitext(filename_step1)[0] + "_renamed.csv"
            df_step1.to_csv(renamed_filename, index=False)
            messagebox.showinfo("Headers Renamed and Saved",
                                f"Headers have been renamed and saved to {renamed_filename}.", parent=window)
            status_label.config(text="Completed", fg="green")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for total time.", parent=window)
            status_label.config(text="Error", fg="red")
        finally:
            rename_time_button.config(state=tk.NORMAL)


# Step 3: Reprocessing background using one of the columns in the file
def bg_processing():
    file_path = filedialog.askopenfilename(title="Select Input File",
                                           filetypes=[("Excel and CSV Files", "*.xlsx *.csv")])

    if not file_path:
        return

    try:
        # Update status label to show processing
        status_label.config(text="Reprocessing Background...", fg="blue")
        process_background_data_button.config(state=tk.DISABLED)  # Disable button while processing
        window.update_idletasks()

        # Load the file
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension == '.xlsx':
            df = pd.read_excel(file_path)
        elif file_extension == '.csv':
            df = pd.read_csv(file_path)
        else:
            messagebox.showerror("Error", "Unsupported file format.", parent=window)
            raise ValueError("Unsupported file format")

        # Create a new window for column selection
        column_window = tk.Tk()
        column_window.title("Select Column")

        # Dynamically set width of dropdown based on column names
        max_column_name_length = max(len(str(col)) for col in df.columns)
        combobox_width = max(30, max_column_name_length // 2)

        column_label = ttk.Label(column_window, text="Choose a column:")
        column_label.pack()

        sanitized_column_names = [str(col) for col in df.columns if col != "Wavenumber"]

        column_combobox = ttk.Combobox(column_window, values=sanitized_column_names, width=combobox_width)
        column_combobox.pack()

        # Confirm button in the selection window
        def on_confirm():
            chosen_column = column_combobox.get()
            if not chosen_column:
                messagebox.showerror("Error", "No column selected.", parent=window)
                return

            column_window.destroy()
            process_and_save(chosen_column, file_path, df)

            # Update status and re-enable button after successful processing
            status_label.config(text="Completed", fg="green")
            process_background_data_button.config(state=tk.NORMAL)

        confirm_button = ttk.Button(column_window, text="Confirm", command=on_confirm)
        confirm_button.pack()

        # Dynamically resize the column selection window
        column_window.geometry(f"{combobox_width * 10}x150")
        column_window.mainloop()

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}", parent=window)
        status_label.config(text="Idle", fg="green")  # Reset status
    finally:
        # Ensure the button is re-enabled in all cases (success or failure)
        process_background_data_button.config(state=tk.NORMAL)


def process_and_save(chosen_column, file_path, df):
    processed_sheet = pd.DataFrame()
    processed_sheet["Wavenumber"] = df["Wavenumber"]

    for column in df.columns[1:]:
        if column == chosen_column:
            processed_sheet[column] = 0
        else:
            processed_sheet[column] = df[column] - df[chosen_column]

    save_path = os.path.splitext(file_path)[0] + f"_{chosen_column}.csv"
    with open(save_path, 'w', newline='', encoding='utf-8') as f:
        # Write headers exactly as they appear in the original DataFrame
        f.write(','.join(df.columns) + '\n')
        processed_sheet.to_csv(f, index=False, header=False)

    messagebox.showinfo("Success", f"File successfully saved as {save_path}", parent=window)
    status_label.config(text="Idle", fg="green")  # Update status to "Idle" after saving


root = tk.Tk()
root.withdraw()


# Function to exit the application
def exit_application():
    try:
        window.quit()
    except Exception as e:
        print(f"An error occurred while closing Origin: {str(e)}")


# Create the main GUI window
window = tk.Tk()
window.title("FTIR Data Processing_V5")
window.geometry("600x950")

# Create a canvas and a scrollable frame
canvas = tk.Canvas(window)
scrollable_frame = ttk.Frame(canvas)
scrollbar = ttk.Scrollbar(window, orient="vertical", command=canvas.yview)
canvas.configure(yscrollcommand=scrollbar.set)

# Place the scrollbar and canvas
scrollbar.pack(side="right", fill="y")
canvas.pack(side="left", fill="both", expand=True)


# Function to resize the scrollable frame
def on_frame_configure(event):
    canvas.configure(scrollregion=canvas.bbox("all"))


# Function to allow scrolling with the mouse wheel
def on_mouse_wheel(event):
    canvas.yview_scroll(-1 * int(event.delta / 120), "units")


# Bind the scrollable frame to the canvas
canvas_frame = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

scrollable_frame.bind("<Configure>", on_frame_configure)
window.bind("<MouseWheel>", on_mouse_wheel)

# Configure the scrollable frame to expand
scrollable_frame.columnconfigure(0, weight=1)

# Create a frame for the header
header_frame = tk.Frame(scrollable_frame, padx=20, pady=20)
header_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")

# Create a label for the header
header_label = tk.Label(header_frame, text="FTIR Data Processing_V5", font=("Helvetica", 16, "bold"))
header_label.pack()

# Introduction Section
label_intro_text = "This program simplifies data processing for ATR-SEIRAS."
label_intro = tk.Label(header_frame, text=label_intro_text, font=("Helvetica", 12, "bold"), justify='center',
                       wraplength=800)
label_intro.pack(anchor="center")

# Status Label
status_label = tk.Label(header_frame, text="Idle", font=("Helvetica", 12, "bold"), fg="green")
status_label.pack(anchor="center")

# Create a frame for the content
content_frame = tk.Frame(scrollable_frame, padx=10, pady=10)
content_frame.grid(row=1, column=0, sticky="nsew")

# Create a frame for the right side content
right_frame = tk.Frame(scrollable_frame, padx=10, pady=10)
right_frame.grid(row=1, column=1, sticky="nsew")

# Configure the grid for dynamic resizing
content_frame.columnconfigure(0, weight=1)
right_frame.columnconfigure(0, weight=1)

# Step 1 Section
label_step0 = tk.Label(content_frame, text="Step 1: Combine CSV Files", font=("Helvetica", 12, "bold"))
label_step0.grid(row=0, column=0, sticky="w")

label_step0a = tk.Label(content_frame, text="a) Combine Series collection CSV Files", font=("Helvetica", 10, "bold"))
label_step0a.grid(row=1, column=0, sticky="w")

combine_csv_button = tk.Button(content_frame, text="Combine Series collection CSV Files",
                               command=combine_series_csv_to_xlsx_or_csv, bg="sky blue")
combine_csv_button.grid(row=2, column=0, pady=5, sticky="ew")

# Add sort button
sort_button = tk.Button(content_frame, text="Sort Spectral Columns", command=sort_spectral_columns, bg="sky blue")
sort_button.grid(row=3, column=0, pady=5, sticky="ew")

label_step0b = tk.Label(content_frame, text="b) Combine Time-Resolved CSV Files", font=("Helvetica", 10, "bold"))
label_step0b.grid(row=4, column=0, sticky="w")

time_resolved_csv_button = tk.Button(content_frame, text="Combine Time-Resolved CSV Files",
                                     command=combine_time_resolved_csv_to_xlsx_or_csv, bg="sky blue")
time_resolved_csv_button.grid(row=5, column=0, pady=5, sticky="ew")

# Step 2 Section
label_step1 = tk.Label(content_frame, text="Step 2: Rename Columns", font=("Helvetica", 12, "bold"))
label_step1.grid(row=6, column=0, sticky="w")

label_step1a = tk.Label(content_frame, text="a) Rename headers with CV voltage range", font=("Helvetica", 10, "bold"))
label_step1a.grid(row=7, column=0, sticky="w")

# CV parameter settings
settings_frame_cv = tk.Frame(content_frame, padx=10, pady=10)
settings_frame_cv.grid(row=8, column=0, sticky="ew")

get_cv_settings()

potential_change_label_cv = tk.Label(content_frame, text="Potential Change per Spectrum: 0.000000 V/sec",
                                     bg="lemon chiffon")
potential_change_label_cv.grid(row=9, column=0, sticky="w")

rename_columns_cv_button = tk.Button(content_frame, text="Rename Column headers to CV voltage range",
                                     command=rename_columns_cv, bg="sky blue")
rename_columns_cv_button.grid(row=10, column=0, pady=5, sticky="ew")

label_step1b = tk.Label(content_frame, text="b) Rename headers with LV voltage range", font=("Helvetica", 10, "bold"))
label_step1b.grid(row=11, column=0, sticky="w")

# LV parameter settings
settings_frame_lv = tk.Frame(content_frame, padx=10, pady=10)
settings_frame_lv.grid(row=12, column=0, sticky="ew")

get_lv_settings()

potential_change_label_lv = tk.Label(content_frame, text="Potential Change per Spectrum: 0.000000 V/sec",
                                     bg="lemon chiffon")
potential_change_label_lv.grid(row=13, column=0, sticky="w")

rename_columns_lv_button = tk.Button(content_frame, text="Rename Column headers to LV voltage range",
                                     command=rename_columns_lv, bg="sky blue")
rename_columns_lv_button.grid(row=14, column=0, pady=5, sticky="ew")

label_step1c = tk.Label(content_frame, text="c) Rename headers based on time intervals", font=("Helvetica", 10, "bold"))
label_step1c.grid(row=15, column=0, sticky="w")

rename_time_button = tk.Button(content_frame, text="Rename Column headers based on time intervals",
                               command=rename_headers_based_on_time, bg="sky blue")
rename_time_button.grid(row=16, column=0, pady=5, sticky="ew")

# Step 3 Section
label_step2 = tk.Label(right_frame, text="Step 3: Reprocess Background", font=("Helvetica", 12, "bold"))
label_step2.pack(pady=10, anchor="w")

process_background_data_button = tk.Button(right_frame, text="Reprocess Background", command=bg_processing,
                                           bg="sky blue")
process_background_data_button.pack(pady=5, anchor="w")

# Exit Section
exit_button = tk.Button(scrollable_frame, text="Exit Application", command=exit_application, bg="tomato")
exit_button.grid(row=2, column=0, columnspan=2, pady=10, sticky="ew")

# Footer description
footer_description = tk.Label(scrollable_frame, text="Made by Pavithra Gunasekaran with the help of ChatGPT",
                              font=("Helvetica", 8))
footer_description.grid(row=3, column=0, columnspan=2, pady=10, sticky="ew")

# Start the tkinter event loop
window.mainloop()
