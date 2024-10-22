import os
import shutil
import json
import argparse
import xml.etree.ElementTree as ET

def generate_groups_and_details(num_cases, time_limit, memory_limit):
    groups = []
    details = []

    for i in range(1, num_cases + 1):
        group = {
            "GroupID": i,
            "GroupName": str(i),
            "GroupScore": 100 * i // num_cases - 100 * (i - 1) // num_cases,
            "TestPoints": [i]
        }
        groups.append(group)
        detail = {
            "ID": i,
            "Dependency": 0,
            "TimeLimit": time_limit,
            "MemoryLimit": memory_limit,
            "DiskLimit": 0,
            "ValgrindTestOn": False
        }
        details.append(detail)

    return groups, details

def parse_problem_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    time_limit = int(root.find(".//time-limit").text)
    memory_limit = int(root.find(".//memory-limit").text)
    
    # 检查是否有 tag 值为 "interactive"
    interactive_tag = root.find(".//tag[@value='interactive']")
    spj_type = {
            "Run": "interactive",
            "Check": "skip"
        } if interactive_tag is not None else 1
    
    return time_limit, memory_limit, spj_type

def main(zipfile, output):
    name = zipfile.split("$")[0]
    # remove existing directories
    if os.path.exists(name):
        print(f"Removing existing '{name}' directory...")
        shutil.rmtree(name)

    shutil.unpack_archive(zipfile, name, 'zip')
    
    # change root directory to the extracted directory
    os.chdir(name)

    if not os.path.exists("tests"):
        print("Error: 'tests/' directory does not exist.")
        exit(1)

    if not os.path.exists("check.cpp"):
        print("Error: 'check.cpp' file does not exist in the root directory.")
        exit(1)

    if not os.path.exists("problem.xml"):
        print("Error: 'problem.xml' file does not exist in the root directory.")
        exit(1)

    os.makedirs(output, exist_ok=True)

    num_cases = 0
    
    for filename in os.listdir("tests"):
        if filename.endswith(".a"):
            num_cases += 1
            src_in_file = os.path.join("tests", filename[:-2])
            src_out_file = os.path.join("tests", filename)
            in_file = os.path.join(output, f"{num_cases}.in")
            out_file = os.path.join(output, f"{num_cases}.out")
            print(f"Copying '{src_in_file}' to '{in_file}' and '{src_out_file}' to '{out_file}'...")
            shutil.copy(src_in_file, in_file)
            shutil.copy(src_out_file, out_file)
    time_limit, memory_limit, spj_type = parse_problem_xml("problem.xml")
    groups, details = generate_groups_and_details(num_cases, time_limit, memory_limit)
    
    data = {
        "Groups": groups,
        "Details": details,
        "CompileTimeLimit": 30000,
        "SPJ": spj_type,
        "Scorer": 0
    }

    with open(f"{output}/config.json", "w") as file:
        json.dump(data, file)
        print(f"config.json has been generated and saved to '{output}/' directory.")
        print(f"\tTime limit: {time_limit} ms\n\tMemory limit: {memory_limit} MB\n\tSPJ type: {spj_type}.")
        
        if spj_type == 1:
            shutil.copy("check.cpp", output + "/spj.cpp")
            print(f"\tcheck.cpp has been copied to '{output}/spj.cpp'.")
        else:
            shutil.copy("files/interactor.cpp", output + "/interactor.cpp")
            print(f"\tinteractor.cpp has been copied to '{output}/interactor.cpp'.")
            print("\tWarning: interactive problem detected; check.cpp is ignored.")

    if os.path.exists("statements/.pdf/english/problem.pdf"):
        shutil.copy("statements/.pdf/english/problem.pdf", output + "/statements.pdf")
        print(f"Statements found: problem.pdf has been copied to '{output}/statements.pdf'.")

    os.chdir("..")
    shutil.make_archive(f'{output}', 'zip', name, output)
    print(f"ok: Exported '{output}.zip'.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process and export problem files.")
    parser.add_argument('zipfile', help="Path to the linux package, for example, 'a-plus-b-2$linux.zip'.")
    parser.add_argument("-o", "--output-dir", default="export", help="ACMOJ problem id (used to make corresponding zip file), default to 'export'.")
    args = parser.parse_args()
    if not args.zipfile.endswith("$linux.zip"):
        print("Error: 'zipfile' must end with '$linux.zip'. Please download Polygon linux package.")
        exit(1)
    main(args.zipfile, args.output_dir)