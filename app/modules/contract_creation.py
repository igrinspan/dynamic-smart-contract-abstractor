import numpy as np
import os
import re

from modules.file_manager import create_file, write_file, write_file_from_string, create_directory_2
from modules.contract_config import Mode
from rich.console import Console

console = Console()

# Clases: 
# - ContractCreator (superclase)
#   - EchidnaContractCreator
#   - VerisolContractCreator

# A los ContractCreators les entra un objeto config_variables, del que sacan todo lo necesario:
# states, preconditions, extraconditions, function_names, function_variables...

# En la clase ContractCreator me quedaron varias funciones que en realidad son específicas de cada subclase (revisar).
# Por ejemplo, change_for_constructor_fuzzing es sólo del EchidnaContractCreator y get_valid_preconditions_output del VerisolContractCreator.
# Las únicas 2 funciones de las que se comparte la signatura pero no la implementación son create_init_contract y create_multiple_transitions_contracts.

# Al final del módulo me quedaron algunas funciones sueltas que son usadas por funciones de los ContractCreators.


QUERIES_COUNT_THRESHOLD = 250


class ContractCreator:
    # Public methods
    def create_contract_creator(self, config_variables, tool):
        if tool == "verisol":
            return VerisolContractCreator(config_variables)
        elif tool == "echidna":
            return EchidnaContractCreator(config_variables)
        else:
            raise Exception("Invalid tool name")

    def create_init_contract(self):
        # Method is implemented by subclass.
        pass

    def create_multiple_transitions_contracts(self, count):
        # Method is implemented by subclass.
        pass

    # Private methods
    def transform_contract_for_init(self, filename_temp):
        new_contract_body = self.remove_everything_after_constructor(filename_temp)
        write_file_from_string(filename_temp, new_contract_body)

    def remove_everything_after_constructor(self, filename_temp):
        file_lines = open(filename_temp, "r").readlines()
        _, _, contract_end = self.contract_body(file_lines)
        _, constructor_end = self.get_constructor_start_and_end_lines(file_lines)
        new_contract_lines = file_lines[: constructor_end + 1] + ["}"]
        if contract_end < len(file_lines) - 1:
            new_contract_lines += file_lines[contract_end + 1 :]
        return new_contract_lines

    def contract_body(self, file_lines):
        start = find_contract_start_line(file_lines, self.target_contract)
        end = find_contract_end_line(file_lines, self.target_contract)
        return file_lines[start : end + 1], start, end

    def clean_true_requires(self, body):
        lines = body.replace("require(true);", "").split("\n")
        cleaned_lines = [line for line in lines if line.strip()]
        new_body = "\n".join(cleaned_lines)
        return new_body

    def get_constructor_start_and_end_lines(self, input_file):
        target_constructor_start_line = -1
        target_constructor_end_line = -1

        in_target_contract = False
        in_constructor = False

        for index, line in enumerate(input_file):
            if line.strip().startswith("contract " + self.target_contract):
                in_target_contract = True
            if in_target_contract and line.strip().startswith("constructor") and not is_a_comment(line):
                in_constructor = True
                target_constructor_start_line = index
            if in_target_contract and in_constructor and line.strip() == "}":
                target_constructor_end_line = index + 1
                break
        return target_constructor_start_line, target_constructor_end_line

    def get_valid_transitions_output(self, preconditions_thread, preconditions, states_thread, extra_conditions_thread, extra_conditions, functions, config_variables):
        # temp_output = ""
        all_queries_names = []
        all_queries = []
        for index_precondition_require, precondition_require in enumerate(preconditions_thread):
            if isinstance(preconditions, np.ndarray):
                preconditions = preconditions.tolist()
            real_index_precondition_require = preconditions.index(precondition_require)
            for index_precondition_assert, precondition_assert in enumerate(preconditions):
                for index_function, function in enumerate(functions):
                    extra_condition_pre = extra_conditions_thread[index_precondition_require]
                    extra_condition_post = extra_conditions[index_precondition_assert]
                    if ((index_function + 1) in states_thread[index_precondition_require] and config_variables.mode == Mode.epa) or config_variables.mode == Mode.states:
                        # Abstraer esto de acá abajo en una función aparte
                        function_name = get_temp_function_name(real_index_precondition_require, index_precondition_assert, index_function) # Uso el real_index_precondition_require para el nombre de la query.
                        temp_function = functionOutput(function_name, config_variables.functionVariables) + "\n"
                        temp_function += output_transitions_function(
                            precondition_require,
                            function,
                            precondition_assert,
                            index_function,
                            extra_condition_pre,
                            extra_condition_post,
                            config_variables,
                        )
                        temp_function += "\n\t}\n"
                        # temp_output += temp_function
                        all_queries_names.append(function_name)
                        all_queries.append(temp_function)
        
        return all_queries, all_queries_names

    def get_init_output(self, config_variables):
        temp_output = ""
        temp_function_names = []
        for id_precondition_assert, precondition_assert in enumerate(config_variables.preconditions):
            function_name = get_temp_function_name(id_precondition_assert, "0", "0")
            temp_function_names.append(function_name)
            temp_function = functionOutput(function_name, config_variables.functionVariables) + "\n"
            temp_function += output_init_function(
                precondition_assert, config_variables.extraConditions[id_precondition_assert]
            )
            temp_output += temp_function + "\n\t}\n"
        return temp_output, temp_function_names


class EchidnaContractCreator(ContractCreator):
    def __init__(self, config_variables):
        self.directory = config_variables.dir
        self.config_variables = config_variables
        self.target_contract = config_variables.contractName

    def create_init_contract(self):
        filename_temp = create_file("init", self.directory, self.config_variables.fileName, self.target_contract)
        body, all_queries_names = self.get_init_output(self.config_variables)
        body = self.clean_true_requires(body)
        write_file(filename_temp, body, self.target_contract)
        self.transform_contract_for_init(filename_temp)
        self.change_for_constructor_fuzzing(filename_temp)
        return filename_temp, all_queries_names

    def create_multiple_transitions_contracts(self, count):
        pre = self.config_variables.preconditions
        extra = self.config_variables.extraConditions
        queries, function_names = self.get_valid_transitions_output(pre, pre, self.config_variables.states, extra, extra, self.config_variables.functions, self.config_variables)

        # De function_names podemos sacar la cantidad de queries que se crearon.
        queries_count = len(function_names)
        contracts = []
        console.print(f"[bold]Cantidad de queries en el contrato: {queries_count}[/bold]")
        if queries_count > QUERIES_COUNT_THRESHOLD:
            splits = count
            if self.config_variables.debug:
                console.print(f"[bright_yellow]La cantidad de queries ([bold]{queries_count}[/bold]) superó el umbral de {QUERIES_COUNT_THRESHOLD}.\n" +
                              f"Se dividirán en {splits} contratos.\n" +
                              f"Cada contrato tendrá aproximadamente {queries_count // splits} queries.")
            queries_splitted = np.array_split(queries, splits)  # Crea un arreglo de arreglos de queries.
            for idx, queries_list in enumerate(queries_splitted):
                body = ""  # Acá metemos las queries que queremos para el nuevo contrato.
                for query in queries_list:
                    body += query
                body = self.clean_true_requires(body)
                filename_temp = create_file(f"transitions_{idx}", self.directory, self.config_variables.fileName, self.target_contract)  # esto hace un archivo nuevo copiando los contenidos de EPXCrowdsale.sol
                write_file(filename_temp, body, self.target_contract)
                contracts.append(filename_temp)
        else:
            if self.config_variables.debug:
                console.print(f"[bright_yellow]La cantidad de queries ([bold]{queries_count}[/bold]) no superó el umbral de {QUERIES_COUNT_THRESHOLD}. \nSe creará un solo contrato")
            body = ""
            for query in queries:
                body += query
            body = self.clean_true_requires(body)
            filename_temp = create_file("transitions", self.directory, self.config_variables.fileName, self.target_contract)
            write_file(filename_temp, body, self.target_contract)
            contracts = [filename_temp]

        for contract in contracts:
            self.change_for_constructor_fuzzing(contract)

        return contracts, None

    def change_for_constructor_fuzzing(self, contract_filename):
        has_initialized_initial_code = self.has_initialized_code()
        write_file(contract_filename, has_initialized_initial_code, self.target_contract)

        new_lines = self.add_modifier_to_contract_functions(contract_filename, "hasInitialized")
        change_status = "\thas_initialized = true;\n"
        start, end = self.get_constructor_start_and_end_lines(new_lines)

        constructor_lines = new_lines[start:end]
        for index, line in enumerate(constructor_lines):
            if ")" in line:
                if "public" in line:
                    constructor_lines[index] = line.replace(")", ") hasNotInitialized ", 1)
                else:
                    constructor_lines[index] = line.replace(")", ") hasNotInitialized public", 1)
                break

        constructor_lines[0] = constructor_lines[0].replace("constructor", "function my_constructor")
        constructor_lines[-1] = constructor_lines[-1].replace("}", f"{change_status} {constructor_lines[-1]}")

        new_lines = new_lines[:start] + constructor_lines + new_lines[end:]
        write_file_from_string(contract_filename, new_lines)

    def add_modifier_to_contract_functions(self, contract_filename, modifier_name):
        lines = open(contract_filename, "r", encoding='utf-8').readlines()
        new_lines = []
        in_contract = False
        in_function_declaration = False

        for line in lines:
            if is_contract_declaration(line, self.target_contract):
                in_contract = True
            elif in_contract and is_function_declaration(line):
                in_function_declaration = True

            if in_function_declaration and ")" in line:
                line = line.replace(")", f") {modifier_name}", 1)
                in_function_declaration = False

            line = line.replace("pure", "view") # porque el modifier accede a una variable de estado, deja de ser pure.
            new_lines.append(line)

        return new_lines

    def has_initialized_code(self):
        has_initialized_modifier = self.create_modifier("hasInitialized", ["has_initialized"])
        has_not_initialized_modifier = self.create_modifier("hasNotInitialized", ["!has_initialized"])
        has_initialized_declaration = "\tbool has_initialized = false;\n\n"
        return has_initialized_modifier + has_not_initialized_modifier + has_initialized_declaration

    def create_modifier(self, name, require_clauses):
        res = f"\tmodifier {name} {{\n"
        for require in require_clauses:
            res += f"\t\trequire({require});\n"
        res += "\t\t_;\n"
        res += "\t}\n\n"
        return res


class VerisolContractCreator(ContractCreator):
    def __init__(self, config_variables):
        self.directory = config_variables.dir
        self.config_variables = config_variables
        self.target_contract = config_variables.contractName

    def create_preconditions_contract(self, preconditions, extraconditions, thread_id):
        """ Se usa en el discard_unreachable_states. Sólo en el modo EPA."""
        new_dir = create_directory_2(self.config_variables.dir, f"thread_{thread_id}")
        filename_temp = create_file("preconditions", new_dir, self.config_variables.fileName, self.target_contract)
        body, all_queries_names = self.get_valid_preconditions_output(preconditions, extraconditions, self.config_variables.functionVariables)
        body = self.clean_true_requires(body)
        write_file(filename_temp, body, self.target_contract)
        fix_for_version_5(filename_temp)
        filename_temp = os.path.realpath(filename_temp)
        return filename_temp, all_queries_names

    def create_init_contract(self):  # Es lo mismo que para echidna pero sin el constructor fuzzing.
        filename_temp = create_file("init", self.directory, self.config_variables.fileName, self.target_contract)
        body, all_queries_names = self.get_init_output(self.config_variables)
        body = self.clean_true_requires(body)
        write_file(filename_temp, body, self.target_contract)
        fix_for_version_5(filename_temp)
        self.transform_contract_for_init(filename_temp)
        filename_temp = os.path.realpath(filename_temp)
        return filename_temp, all_queries_names

    def create_multiple_transitions_contracts(self, count):
        contracts = []
        # queries_names_per_contract = []

        pre = self.config_variables.preconditions
        extra = self.config_variables.extraConditions
        queries, queries_names = self.get_valid_transitions_output(pre, pre, self.config_variables.states, extra, extra, self.config_variables.functions,self.config_variables)

        print(f"Cantidad de queries totales: {len(queries)}")
        queries_splitted = np.array_split(queries, count)  # Crea un arreglo de arreglos de queries.
        names_splitted = np.array_split(queries_names, count)
        for idx, queries_list in enumerate(queries_splitted):
            if len(queries_list) == 0:
                if self.config_variables.debug:
                    console.print(f"[bright_yellow]Queries list vacío para el thread {idx}, no se crea contrato de transiciones.")
                continue
            # Acá metemos las queries que queremos para el nuevo contrato.
            body = ''.join(queries_list)
            body = self.clean_true_requires(body)
            new_dir = create_directory_2(self.config_variables.dir, f"thread_{idx}")
            # create_file hace un archivo nuevo copiando los contenidos del target contract.
            filename_temp = create_file(f"transitionss_{idx}", new_dir, self.config_variables.fileName, self.target_contract)
            write_file(filename_temp, body, self.target_contract)
            filename_temp = os.path.realpath(filename_temp)
            contracts.append(filename_temp)
            # queries_names_per_contract.append()  # lista con listas de queries para cada contrato.

        return contracts, names_splitted

    def create_transitions_contract_for_thread(self, thread_id, threads_count, results):

        preconditions = np.array_split(self.config_variables.preconditions, threads_count)[thread_id]
        states = np.array_split(self.config_variables.states, threads_count)[thread_id]
        extra_conditions = np.array_split(self.config_variables.extraConditions, threads_count)[thread_id]

        if len(preconditions) == 0:
            if self.config_variables.debug:
                console.print(f"[bright_yellow]Preconditions vacío para thread {thread_id}, no se crea contrato de transiciones.")
            results[thread_id] = (None, None)
            return

        queries, queries_names = self.get_valid_transitions_output(preconditions, self.config_variables.preconditions, states, extra_conditions, self.config_variables.extraConditions, self.config_variables.functions, self.config_variables)
        if len(queries) == 0:
            results[thread_id] = (None, None)
            return

        # Acá metemos las queries que queremos para el nuevo contrato.
        body = ''.join(queries)
        body = self.clean_true_requires(body)
        new_dir = create_directory_2(self.config_variables.dir, f"thread_{thread_id}")
        # create_file hace un archivo nuevo copiando los contenidos del target contract
        filename_temp = create_file(f"transitions_{thread_id}", new_dir, self.config_variables.fileName, self.target_contract)
        write_file(filename_temp, body, self.target_contract)
        fix_for_version_5(filename_temp)
        filename_temp = os.path.realpath(filename_temp)

        results[thread_id] = (filename_temp, queries_names)

    def get_valid_preconditions_output(self, preconditions, extra_conditions, function_variables):
        temp_output = ""
        temp_function_names = []
        for id_precondition_require, precondition_require in enumerate(preconditions):
            function_name = get_temp_function_name(id_precondition_require, "0", "0")
            temp_function_names.append(function_name)
            temp_function = functionOutput(function_name, function_variables) + "\n"
            temp_function += output_valid_state(precondition_require, extra_conditions[id_precondition_require])
            temp_output += temp_function + "\t}\n"
        return temp_output, temp_function_names


def find_contract_start_line(contract_lines, contract_name):
    for idx, line in enumerate(contract_lines):
        if f"contract {contract_name}" in line and not is_a_comment(line):
            return idx


def find_contract_end_line(contract_lines, contract_name):
    inside_function = False
    bracket_count = 0
    start_position = find_contract_start_line(contract_lines, contract_name)

    for idx, line in enumerate(contract_lines):
        if idx == start_position:
            bracket_count = 1
            inside_function = True
            continue

        if inside_function and "{" in line and not is_a_comment(line):
            bracket_count += 1
        if inside_function and "}" in line and not is_a_comment(line):
            bracket_count -= 1
        if inside_function and bracket_count == 0:
            return idx

    return -1


def is_contract_declaration(line, contract_name):
    return line.strip().startswith("contract " + contract_name) and not is_a_comment(line)


def is_function_declaration(line):
    return line.strip().startswith("function") and not is_a_comment(line)


def is_constructor_declaration(line):
    return line.strip().startswith("constructor") and not is_a_comment(line)


def is_a_comment(line):
    return any(line.strip().startswith(prefix) for prefix in ["//", "/*", "*", "*/"])

def fix_for_version_5(contract_filename):
    with open(contract_filename, "r") as contract_file:
        contract = contract_file.read()

    # Replace 'receive()' function declaration with 'function () external payable'
    contract = re.sub(r'\breceive\(\)\s*(external\s*payable)', r'function () \1', contract)

    # Remove 'abstract' and 'virtual' keywords
    contract = re.sub(r'\babstract contract\b', 'contract', contract)
    contract = re.sub(r'\bvirtual\b', '', contract)

    # Replace the 'payable(...)' with the content inside the parentheses
    contract = re.sub(r'payable\((.*?)\)', r'\1', contract)

    write_file_from_string(contract_filename, contract)

def functionOutput(number, function_variables):
    return "\tfunction vc" + number + "(" + function_variables + ") payable public {"


def get_temp_function_name(id_require, id_assert, id_function):
    return str(id_require) + "x" + str(id_assert) + "x" + str(id_function)


def output_valid_state(precondition_require, extra_condition):
    extra_condition_output = get_extra_condition_output(extra_condition)
    return ("\t\trequire("+precondition_require+");\n" 
            + extra_condition_output 
            + "\t\tassert(false);\n")


def output_transitions_function(precondition_require, function, precondition_assert, id_function, extra_condition_pre, extra_condition_post, config_variables):
    if config_variables.mode == Mode.epa:
        function_precondition = config_variables.functionPreconditions[id_function]
    else:
        function_precondition = "true"
    extra_condition_output_pre = get_extra_condition_output(extra_condition_pre)
    verisol_function_output = (
        "\t\trequire("+ precondition_require + ");\n"
        + "\t\trequire(" + function_precondition + ");\n"
        + "\t\t" + extra_condition_output_pre
        + "\t\t" + function + "\n"
        + "\t\tassert(!(" + precondition_assert + "&& " + extra_condition_post + "));"
    )
    return verisol_function_output


def output_init_function(precondition_assert, extra_condition):
    extra_condition_output = get_extra_condition_output(extra_condition)
    verisol_function_output = extra_condition_output + "\t\tassert(!(" + precondition_assert + "));"
    return verisol_function_output


def get_extra_condition_output(condition):
    extra_condition_output = ""
    if condition != "" and condition != None:
        extra_condition_output = "require(" + condition + ");\n"
    return extra_condition_output
