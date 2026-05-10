def merge_files_strict_clean(file1_path, file2_path, output_path):
    try:
        def get_clean_lines(file_path):
            unique_lines = set()
            with open(file_path, 'r') as f:
                for line in f:
                    # 1. Split by '#' and take the first part (everything before the comment)
                    # 2. Strip whitespace from that remaining part
                    clean_line = line.split('#')[0].strip()
                    
                    # Only add if the line isn't empty after stripping
                    if clean_line:
                        unique_lines.add(clean_line)
            return unique_lines

        # Process both files
        set1 = get_clean_lines(file1_path)
        set2 = get_clean_lines(file2_path)

        # Merge sets (Union)
        combined_unique = set1 | set2

        # Write to output (sorted)
        with open(output_path, 'w') as out_file:
            for item in sorted(combined_unique):
                out_file.write(f"{item}\n")
        
        print(f"Success! Exported {len(combined_unique)} unique, comment-free lines.")

    except FileNotFoundError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    merge_files_strict_clean("lists/blocklist.txt", "lists/hosts.txt", "updated_list.txt")
