from time import time
import subprocess
import re
from dataclasses import asdict
import subprocess
import psutil
import platform
from rich.console import Console


from modules.contract_config import Mode
from modules.output import output_combination

console = Console()

verbose = False
verisol_output = "Found a counterexample"
TRACK_VARS = "trackAllVars" # En try_command se puede retornar (False, TRACK_VARS). 
# Y los 3 try_xxx, si se encuentran con eso, vuelven a ejecutar try_command con el track_all_vars en True. 


class VerisolRunner:
    def __init__(self, config_variables, contract_to_run, verisol_config_data, verisol_fails):
        self.config_variables = config_variables
        self.contract_to_run = contract_to_run
        self.txBound = verisol_config_data.txBound
        self.time_out = verisol_config_data.time_out
        self.verisol_fails = verisol_fails

    # En esta función no hacemos nada con las preconditions de las queries que terminan por timeout 
    # porque al no tener evidencia suficiente de si están o no están, las dejamos.
    def try_preconditions(self, tool, function_names, final_directory, states, preconditions, extra_conditions):
        new_preconditions = []
        new_states = []
        new_extra_conditions = []

        for function_name in function_names:
            id_precondition, _, id_function = get_params_from_function_name(function_name)
            
            query_result = self.try_command(tool, function_name, function_names, final_directory, states, self.txBound, self.time_out, False)
            success = query_result[0] # True o False.
            if query_result[1] == TRACK_VARS:
                query_result = self.try_command(tool, function_name, function_names, final_directory, states, self.txBound, self.time_out, True)

            if success:
                new_preconditions.append(preconditions[id_precondition])
                new_states.append(states[id_precondition])
                new_extra_conditions.append(extra_conditions[id_precondition])
                if query_result[1] != "":
                    print("[try_preconditions] Time out en función: " + self.config_variables.functions[id_function] + " desde estado inicial:")
                    i_state = output_combination(id_precondition, states, self.config_variables)
                    print(i_state)
        return new_preconditions, new_states, new_extra_conditions


    def try_init(self, tool, function_names, final_directory): # -> [(bool, string), ...]
        results = []
        for function_name in function_names:
            txBound_constructor = 1
            query_result = self.try_command(tool, function_name, function_names, final_directory, [], txBound_constructor, self.time_out, False)
            if query_result[1] == TRACK_VARS:
                query_result = self.try_command(tool, function_name, function_names, final_directory, [], txBound_constructor, self.time_out, True)
            success = query_result[0]
            if success:
                i, j, k = get_params_from_function_name(function_name)
                results.append(([i, j, k], query_result[1])) # guardo el nombre de la query y por qué fue exitosa 

        return results

    def try_transaction(self, tool, function_names, final_directory, states):
        console.print("[bold]VerisolRunner[/bold] - [bold]try_transaction[/bold]")
        results = []
        for function_name in function_names:
            query_result = self.try_command(tool, function_name, function_names, final_directory, states, self.txBound, self.time_out, False)
            if query_result[1] == TRACK_VARS:
                query_result = self.try_command(tool, function_name, function_names, final_directory, states, self.txBound, self.time_out, True)
            success = query_result[0]
            if success:
                i, j, k = get_params_from_function_name(function_name)
                results.append(([i, j, k], query_result[1]))

        return results


    def try_command(self, tool, function_name, function_names, final_directory, states, txBound, time_out, trackAllVars):
        global verisol_output, verbose
        
        trackAllVars = True
        
        #Evito chequear funciones "dummy"
        if len(states) > 0:
            id_precondition_require, id_precondition_assert, id_function = get_params_from_function_name(function_name)
            i_state = output_combination(id_precondition_require, states, self.config_variables)
            f_state = output_combination(id_precondition_assert, self.config_variables.states, self.config_variables)
            if self.config_variables.functions[id_function].startswith("dummy_"):
                print("Dummy")
                if i_state != f_state:
                    return (False,"")
                else:
                    return (True,"")
        
        command = self.getToolCommand(function_name, tool, function_names, txBound, trackAllVars)
        result = ""

        time_start = time()
        try:    
            if platform.system() == "Windows":
                proc = subprocess.Popen(command.split(" "), stdout=subprocess.PIPE, cwd=final_directory)
                result = proc.communicate(timeout=time_out)
                output_verisol = str(result[0].decode('utf-8'))
            else:
                result = subprocess.run([command, ""], shell = True, cwd=final_directory, stdout=subprocess.PIPE)
                output_verisol = result.stdout.decode('utf-8')
        except Exception:
            # number_to += 1
            # print("---EXCEPTION por time out de {} segs ".format(time_out))
            # indexPreconditionRequire, indexPreconditionAssert, indexFunction = get_params_from_function_name(temp_function_name)
            process = psutil.Process(proc.pid)
            for proc in process.children(recursive=True):
                proc.kill()
            process.kill()
            process.wait(2) # wait for killing subprocess
            return True,"?"

        time_end = time()

        output_successful = "Formal Verification successful"
        if verbose and verisol_output not in output_verisol and output_successful not in output_verisol:
            print(output_verisol)
        
        #Corral can "fail"
        output_error = "Corral may have aborted abnormally"
        if output_error in output_verisol:
            if not trackAllVars:
                self.verisol_fails.number_corral_fail += 1
                return False,TRACK_VARS
            else:
                self.verisol_fails.number_corral_fail_with_tackvars += 1
                return True,"fail?"
        return verisol_output in output_verisol, ""
    
    
    def getToolCommand(self, include_number, tool_command, combinations, txBound, trackAllVars):
        command = tool_command + " " 
        command = command + "/txBound:" + str(txBound) + " "
        command = command + "/noPrf "
        if trackAllVars:
            command = command + "/trackAllVars"+ " "
        for combi in combinations:
            if combi != include_number: 
                command += "/ignoreMethod:vc"+ combi +"@" + self.config_variables.contractName + " "

        return command


class EchidnaRunner:
    def __init__(self, config_variables, contract, config_file_params):
        self.directory = config_variables.dir
        self.contract_name = config_variables.contractName
        self.contract = contract
        self.config_file_params = config_file_params
        self.config_variables = config_variables

    def run_contract(self):
        start = time()
        result = self.set_up_and_run()
        end = time()
        if self.config_variables.debug:
            print(f"Este contrato demoró {round(end - start, 2)}s")
        return self.process_output(result)

    def set_up_and_run(self):
        tool_command = self.create_echidna_command()
        result = self.run_echidna_command(tool_command)
        return result

    def create_echidna_command(self):
        config_file = self.create_config_file()
        commandResult = (
            f"echidna {self.contract} --contract {self.contract_name} --config {config_file}"
        )
        return commandResult

    def run_echidna_command(self, command_to_run):
        result = subprocess.run([command_to_run, ""], shell=True, cwd=self.directory, capture_output=True)
        if result.stderr:
            console.print(f"[bold bright_red]Error en la ejecución de Echidna!")
            raise Exception(result.stderr.decode("utf-8"))
        return result.stdout.decode("utf-8")

    def process_output(self, tool_result):
        tests_that_failed = []
        for line in tool_result.splitlines():
            if "failed!" in line:
                match = re.search(r"vc(\w+)\(", line)
                if match:
                    failed_test = match.group(1)  # vcIxJxK(¡): -> IxJxK.
                else:
                    continue  # Por si falla un assert que no tiene que ver con los tests
                i, j, k = get_params_from_function_name(failed_test)
                tests_that_failed.append(([i, j, k], ""))
        return tests_that_failed

    def create_config_file(self):
        new_file_name = f"{self.directory}/config.yaml"
        newfile = open(new_file_name, "w")
        for key, value in asdict(self.config_file_params).items():
            newfile.write(f"{key}: {value} \n")
        newfile.close()
        return new_file_name


# Pure
def get_params_from_function_name(temp_function_name):
    array = temp_function_name.split("x")
    return int(array[0]), int(array[1]), int(array[2])
