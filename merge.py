import csv
import os

def merge_csv_files(file_list, output_file):
    with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        writer = None
        
        for i, file_path in enumerate(file_list):
            if not os.path.exists(file_path):
                print(f"Warning: File not found (skipping): {file_path}")
                continue
                
            with open(file_path, 'r', newline='', encoding='utf-8') as infile:
                reader = csv.reader(infile)
                
                header = next(reader, None)
                if header is None:
                    print(f"Warning: Empty file (skipping): {file_path}")
                    continue
                
                if i == 0 and writer is None:
                    writer = csv.writer(outfile)
                    writer.writerow(header)
                else:
                    pass  
                
                row_count = 0
                for row in reader:
                    writer.writerow(row)
                    row_count += 1
                
                print(f"Merged: {os.path.basename(file_path)} ({row_count} data rows)")
    
    print(f"\nMerge complete! Saved to: {output_file}")

if __name__ == "__main__":
    files_to_merge = [
        "sales_1.csv",
        "sales_2.csv",
        "sales_3.csv",
        
    ]
    
    output_csv = "sales_merged.csv"
    
    merge_csv_files(files_to_merge, output_csv)