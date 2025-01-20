import json
import sys
import csv
import xlsxwriter
from pathlib import Path

def determine_status(username, password):
    if username and password:
        return "Correct password"
    elif not username and password:
        return "Incorrect password (Used for Google Workspace)"
    else:
        return "Open link"

def parse_evilginx_log(file_path):
    entries = []
    with open(file_path, 'r') as log_file:
        for line in log_file:
            if line.startswith('{') and line.endswith('}\n'):
                entry = json.loads(line)
                entries.append({
                    'URL': entry.get('url', ''),
                    'Email': entry.get('username', ''),
                    'Password': entry.get('password', ''),
                    'IP': entry.get('remote_addr', ''),
                    'User Agent': entry.get('useragent', ''),
                    'Status': determine_status(entry.get('username', ''), entry.get('password', ''))
                })
    return entries

def parse_targets_file(targets_file):
    targets = {}
    with open(targets_file, 'r') as file:
        for line in file:
            if 'email="' in line:
                parts = line.split(' ')
                url = parts[0]
                email = None
                for part in parts:
                    if part.startswith('email="'):
                        email = part.split('=')[1].strip('"')
                if email:
                    targets[url] = email
    return targets

def parse_input_file(input_file):
    data = {}
    if input_file.endswith('.json'):
        with open(input_file, 'r') as file:
            json_data = json.load(file)
            for entry in json_data:
                data[entry['email']] = entry['name']
    elif input_file.endswith('.csv'):
        with open(input_file, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                data[row['email']] = row['name']
    return data

def merge_data(log_entries, targets, input_data):
    for entry in log_entries:
        if not entry['Email']:
            matched_url = next((url for url in targets if url in entry['URL']), None)
            if matched_url:
                entry['Email'] = targets[matched_url]
    for email, name in input_data.items():
        if email not in [e['Email'] for e in log_entries]:
            log_entries.append({
                'URL': '',
                'Email': email,
                'Password': '',
                'IP': '',
                'User Agent': '',
                'Status': 'No attempt logged'
            })
    return log_entries

def convert_to_xlsx(data, output_path):
    workbook = xlsxwriter.Workbook(output_path)
    worksheet = workbook.add_worksheet()

    headers = ['#', 'Email', 'Password', 'IP', 'User Agent', 'Status']
    for col_num, header in enumerate(headers):
        worksheet.write(0, col_num, header)

    for row_num, entry in enumerate(data, start=1):
        worksheet.write(row_num, 0, row_num)
        worksheet.write(row_num, 1, entry['Email'])
        worksheet.write(row_num, 2, entry['Password'])
        worksheet.write(row_num, 3, entry['IP'])
        worksheet.write(row_num, 4, entry['User Agent'])
        worksheet.write(row_num, 5, entry['Status'])

    workbook.close()

def main():
    if len(sys.argv) != 4:
        print("Usage: python3 script.py <log_file> <input_file> <targets_file>")
        sys.exit(1)

    log_file = sys.argv[1]
    input_file = sys.argv[2]
    targets_file = sys.argv[3]
    output_file = "output.xlsx"

    if not Path(log_file).is_file():
        print(f"Error: Log file '{log_file}' not found.")
        sys.exit(1)
    if not Path(input_file).is_file():
        print(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)
    if not Path(targets_file).is_file():
        print(f"Error: Targets file '{targets_file}' not found.")
        sys.exit(1)

    log_entries = parse_evilginx_log(log_file)
    targets = parse_targets_file(targets_file)
    input_data = parse_input_file(input_file)

    merged_data = merge_data(log_entries, targets, input_data)

    convert_to_xlsx(merged_data, output_file)
    print(f"Conversion completed. Output saved to '{output_file}'.")

if __name__ == "__main__":
    main()
