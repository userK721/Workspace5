import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import os
from pathlib import Path
import re
from datetime import datetime, timedelta

# Constants
COLUMNS_TO_READ = [
    'sheetStart', 'shift', 'section', 'employeeCode', 'employeeName',
    'category', 'subCategory', 'activityCode', 'activity', 'blockStart',
    'periodStart', 'periodName', 'workedStart', 'workedMinutes'
]

def extract_rows_by_date_range(folder_path, start_date, end_date):
    """Extract rows from CSV files within a date range."""
    data_frames = []
    start_date, end_date = pd.to_datetime(start_date), pd.to_datetime(end_date)
    
    for file_path in Path(folder_path).glob('*.csv'):
        try:
            df = pd.read_csv(file_path, usecols=COLUMNS_TO_READ)
            df['sheetStart'] = pd.to_datetime(df['sheetStart'].str[:10], errors='coerce')
            filtered_df = df[(df['sheetStart'] >= start_date) & (df['sheetStart'] <= end_date)].copy()
            if not filtered_df.empty:
                filtered_df['source_file'] = file_path.name
                filtered_df['workedHours'] = filtered_df['workedMinutes'] / 60
                data_frames.append(filtered_df)
        except Exception as e:
            messagebox.showerror("Error", f"Error processing {file_path.name}: {e}")
    
    return pd.concat(data_frames, ignore_index=True) if data_frames else pd.DataFrame()

def merge_with_financial_periods(filtered_data, financial_periods_df):
    """Merge filtered data with financial periods data."""
    filtered_data['sheetStart'] = pd.to_datetime(filtered_data['sheetStart'], errors='coerce')
    financial_periods_df['Date'] = pd.to_datetime(financial_periods_df['Date'], errors='coerce')
    return pd.merge(filtered_data, financial_periods_df, left_on='sheetStart', right_on='Date', how='left')

def get_next_sequence_number(output_directory):
    """Get the next sequence number for the output file."""
    files = os.listdir(output_directory)
    sequence_numbers = [
        int(re.match(r'filtered_merged_data_(\d+).csv', file).group(1))
        for file in files if re.match(r'filtered_merged_data_(\d+).csv', file)
    ]
    return max(sequence_numbers, default=0) + 1

def browse_folder():
    folder_path = filedialog.askdirectory()
    folder_entry.delete(0, tk.END)
    folder_entry.insert(0, folder_path)
    update_date_options(folder_path)

def browse_financial_periods_file():
    file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
    financial_periods_entry.delete(0, tk.END)
    financial_periods_entry.insert(0, file_path)

def browse_output_folder():
    folder_path = filedialog.askdirectory()
    output_folder_entry.delete(0, tk.END)
    output_folder_entry.insert(0, folder_path)

def update_date_options(folder_path):
    if os.path.isdir(folder_path):
        date_options = set()
        for file_path in Path(folder_path).glob('*.csv'):
            try:
                df = pd.read_csv(file_path, usecols=['sheetStart'])
                df['sheetStart'] = pd.to_datetime(df['sheetStart'].str[:10], errors='coerce')
                date_options.update(df['sheetStart'].dropna().dt.strftime('%Y-%m-%d').tolist())
            except Exception as e:
                messagebox.showerror("Error", f"Error processing {file_path.name}: {e}")
        
        date_options = sorted(list(date_options))
        
        start_date_combo['values'] = date_options
        end_date_combo['values'] = date_options

def filter_and_export():
    folder_path = folder_entry.get()
    financial_periods_path = financial_periods_entry.get()
    output_directory = output_folder_entry.get()
    start_date = start_date_combo.get()
    end_date = end_date_combo.get()
    
    if not os.path.isdir(folder_path):
        messagebox.showerror("Error", "Please enter a valid folder path.")
        return
    
    if start_date > end_date:
        messagebox.showerror("Error", "End date must be after start date.")
        return
    
    filtered_data = extract_rows_by_date_range(folder_path, start_date, end_date)
    if not filtered_data.empty:
        try:
            financial_periods_df = pd.read_csv(financial_periods_path)
        except Exception as e:
            messagebox.showerror("Error", f"Error reading financial periods file: {e}")
            return
        
        merged_data = merge_with_financial_periods(filtered_data, financial_periods_df)
        os.makedirs(output_directory, exist_ok=True)
        next_sequence_number = get_next_sequence_number(output_directory)
        output_file_path = os.path.join(output_directory, f'filtered_merged_data_{next_sequence_number}.csv')
        merged_data.to_csv(output_file_path, index=False)
        messagebox.showinfo("Success", f"Filtered and merged data has been exported to {output_file_path}")
    else:
        messagebox.showinfo("No Data", "No matching rows found.")

# Create the main window
root = tk.Tk()
root.title("CSV Date Range Filter, Merge, and Export")

# Folder Path Input
tk.Label(root, text="Folder Path:").grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
folder_entry = tk.Entry(root, width=50)
folder_entry.grid(row=0, column=1, padx=10, pady=5)
tk.Button(root, text="Browse", command=browse_folder).grid(row=0, column=2, padx=10, pady=5)

# Financial Periods File Input
tk.Label(root, text="Financial Periods CSV:").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
financial_periods_entry = tk.Entry(root, width=50)
financial_periods_entry.grid(row=1, column=1, padx=10, pady=5)
tk.Button(root, text="Browse", command=browse_financial_periods_file).grid(row=1, column=2, padx=10, pady=5)

# Output Folder Path Input
tk.Label(root, text="Output Folder:").grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
output_folder_entry = tk.Entry(root, width=50)
output_folder_entry.grid(row=2, column=1, padx=10, pady=5)
tk.Button(root, text="Browse", command=browse_output_folder).grid(row=2, column=2, padx=10, pady=5)

# Start Date Dropdown
tk.Label(root, text="Start Date:").grid(row=3, column=0, padx=10, pady=5, sticky=tk.W)
start_date_combo = ttk.Combobox(root, width=18)
start_date_combo.grid(row=3, column=1, padx=10, pady=5, sticky=tk.W)

# End Date Dropdown
tk.Label(root, text="End Date:").grid(row=4, column=0, padx=10, pady=5, sticky=tk.W)
end_date_combo = ttk.Combobox(root, width=18)
end_date_combo.grid(row=4, column=1, padx=10, pady=5, sticky=tk.W)

# Filter and Export Button
tk.Button(root, text="Filter and Export", command=filter_and_export).grid(row=5, column=1, padx=10, pady=20)

# Start the main event loop
root.mainloop()
