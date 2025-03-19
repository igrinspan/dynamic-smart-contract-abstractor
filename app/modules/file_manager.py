import os
import shutil
from dataclasses import dataclass, fields, asdict


def create_directory(index):
    current_directory = os.getcwd()
    final_directory = os.path.join(current_directory, str(index))
    if not os.path.exists(final_directory):
        os.makedirs(final_directory)
    return final_directory

def create_directory_2(containing, new):
    final_directory = os.path.join(containing, str(new))
    if not os.path.exists(final_directory):
        os.makedirs(final_directory)
    return final_directory


def delete_directory(final_directory):
    shutil.rmtree(final_directory)


def create_file(name, directory, source_file, contractName):
    new_file_name = str(name) + ".sol"
    new_file_name = directory + "/" + new_file_name
    if os.path.isfile(new_file_name):
        os.remove(new_file_name)
    shutil.copyfile(source_file, new_file_name)
    return new_file_name


def create_config_file(final_directory, config_file_params):
    new_file_name = f"{final_directory}/config.yaml"
    newfile = open(new_file_name, "w")
    for key, value in asdict(config_file_params).items():
        newfile.write(f"{key}: {value} \n")
    newfile.close()
    return new_file_name


def write_file(fileNameTemp, body, contractName):
    new_body = clean_true_requires(body)
    inputfile = open(fileNameTemp, "r").readlines()
    write_file = open(fileNameTemp, "w")
    for line in inputfile:
        write_file.write(line)
        if "contract " + contractName in line:
            write_file.write(new_body)
    write_file.close()


def clean_true_requires(body):
    new_body = ""
    for line in body.splitlines():
        if line != "require(true);":
            new_body += line + "\n"
    return new_body


def write_file_from_string(fileNameTemp, array_of_strings):
    write_file = open(fileNameTemp, "w")
    for line in array_of_strings:
        write_file.write(line)
    write_file.close()


def read_from_file(fileNameTemp):
    inputfile = open(fileNameTemp, "r").readlines()
    return "".join(inputfile)
