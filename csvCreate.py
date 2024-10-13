import csv

# Function to replace '//' with commas in a CSV without adding unnecessary quotes
def replace_slashes_with_commas(input_csv, output_csv):
    # Open the input CSV file for reading
    with open(input_csv, mode='r', newline='', encoding='utf-8') as infile:
        reader = csv.reader(infile)
        # Open the output CSV file for writing, with minimal quoting
        with open(output_csv, mode='w', newline='', encoding='utf-8') as outfile:
            writer = csv.writer(outfile, quoting=csv.QUOTE_MINIMAL)
            # Process each row
            for row in reader:
                # Replace '//' with commas in each cell
                new_row = [cell.replace('//', ',') for cell in row]
                # Write the modified row to the new CSV
                writer.writerow(new_row)

# Example usage
input_csv = r'/Users/arjun/Documents/StreamlitChatbot/dubhacks24-RAG-workshop/data/recipes.csv'  # Path to your existing CSV file
output_csv = r'/Users/arjun/Documents/StreamlitChatbot/dubhacks24-RAG-workshop/data/recipes_cleaned.csv'  # Path where the new CSV file will be created
replace_slashes_with_commas(input_csv, output_csv)
