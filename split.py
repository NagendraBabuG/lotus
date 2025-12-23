import csv
import os
from math import ceil

def split_csv(input_file, max_rows=80):
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    directory = os.path.dirname(input_file) or '.'  
    
    with open(input_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)  
        
        rows = list(reader)  
        total_rows = len(rows)
        
        if total_rows == 0:
            print("No data rows found in the file.")
            return
        
        num_files = ceil(total_rows / max_rows)
        
        print(f"Splitting {total_rows} rows into {num_files} files (max {max_rows} rows each).")
        
        for i in range(num_files):
            start = i * max_rows
            end = start + max_rows
            chunk = rows[start:end]
            
            output_filename = os.path.join(directory, f"{base_name}_{i+1}.csv")
            
            with open(output_filename, 'w', newline='', encoding='utf-8') as out_file:
                writer = csv.writer(out_file)
                writer.writerow(header)        
                writer.writerows(chunk)        
            
            print(f"Created: {output_filename} with {len(chunk)} rows")

if __name__ == "__main__":
    input_csv = "your_large_file.csv"
    split_csv(input_csv, max_rows=80)