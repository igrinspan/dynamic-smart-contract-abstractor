from dataclasses import dataclass
from enum import Enum
import itertools

# Clases:
# - Mode (epa o states)
# - ConfigImporter: agarra el ContractConfig y se guarda todos los datos necesarios para la ejecución en un objeto de tipo ConfigVariables.
# - ConfigVariables
# - VerisolExecutionHistory: para guardar la cantidad de timeouts y corral fails.


class Mode(Enum):
    epa = "epa"
    states = "states"


class ConfigImporter:
    """ Importa las variables del ContractConfig y las pepara según si estamos en 
    modo epa o states """
    def __init__(self, contract_config_file, config_variables_object, optimizations):
        self.contract_config_file = contract_config_file
        self.config_variables = config_variables_object
        self.optimizations = optimizations

    def config_variables_setup(self, mode):
        """ Traemos los datos del archivo Config del contrato que vamos a analizar y 
        los preparamos (seteamos states, preconditions, extraconditions) según el modo."""
        self.import_config_variables()  # es lo mismo que el make_global_variables.

        funciones_numeros = list(range(1, len(self.config_variables.functions) + 1))
        self.prepare_variables(mode, funciones_numeros)
        self.config_variables.mode = mode

        return self.config_variables

    # Private methods
    def import_config_variables(self):
        c = self.contract_config_file
        self.config_variables.fileName = "Contracts/" + c.fileName
        self.config_variables.contractFileName = c.fileName
        self.config_variables.functions = c.functions
        self.config_variables.statePreconditions = c.statePreconditions
        self.config_variables.statesNames = c.statesNamesModeState
        self.config_variables.contractName = c.contractName
        self.config_variables.functionVariables = c.functionVariables
        self.config_variables.functionPreconditions = c.functionPreconditions

    # Se ejecuta en el main para cargar las variables preconditions, states y extraConditions, dependiendo del modo.
    def prepare_variables(self, mode, funciones_numeros):
        if mode == Mode.epa:
            self.update_variables_for_epa_mode(funciones_numeros)
        else:
            self.update_variables_for_states_mode()

    def update_variables_for_epa_mode(self, funciones_numeros):
        self.config_variables.states = self.getCombinations(funciones_numeros)
        self.config_variables.preconditions = self.getPreconditions(funciones_numeros)
        try:
            self.config_variables.extraConditions = [
                self.contract_config_file.epaExtraConditions for _ in range(len(self.config_variables.states))
            ]
        except Exception:
            self.config_variables.extraConditions = ["true" for _ in range(len(self.config_variables.states))]

    def update_variables_for_states_mode(self):
        self.config_variables.preconditions = self.contract_config_file.statePreconditionsModeState
        self.config_variables.states = self.contract_config_file.statesModeState
        try:
            self.config_variables.extraConditions = self.contract_config_file.statesExtraConditions
        except Exception:
            self.config_variables.extraConditions = ["true" for _ in range(len(self.config_variables.states))]

    def getCombinations(self, funciones_numeros):
        truePreconditions = []
        results = []
        statesTemp = []
        count = len(funciones_numeros)
        for index, statePrecondition in enumerate(self.config_variables.statePreconditions):
            if statePrecondition == "true":
                truePreconditions.append(index + 1)

        # Combinations
        for L in range(len(funciones_numeros) + 1):
            for subset in itertools.combinations(funciones_numeros, L):
                if self.optimizations.reduce_true: # Optimización reduce_true
                    is_true = True
                    for true_pre in truePreconditions:
                        if true_pre not in subset:
                            is_true = False
                    if is_true:
                        results.append(subset)
                else:
                    results.append(subset)
        for partialResult in results:
            paddingResult = []
            paddingResult = [0 for i in range(count)]
            for i in range(count):
                if len(partialResult) > i and partialResult[i] >= 0:
                    indice = partialResult[i]
                    paddingResult[indice - 1] = indice
            statesTemp.append(paddingResult)
        statesTemp2 = []

        # Sacamos estados en los que haya una función i y no haya otra función j tales que precondition[i] = precondition[j].
        if self.optimizations.reduce_equal: # Optimización reduce_equal
            for combination in statesTemp:
                isCorrect = True
                for iNumber, number in enumerate(combination):
                    for idx, x in enumerate(self.config_variables.statePreconditions):
                        if iNumber != idx:
                            if number == 0:
                                if self.config_variables.statePreconditions[iNumber] == x and combination[idx] != 0:
                                    isCorrect = False
                            elif self.config_variables.statePreconditions[iNumber] == x and not((idx+1) in combination):
                                isCorrect = False
                
                if isCorrect:
                    statesTemp2.append(combination)
        else:
            statesTemp2 = statesTemp

        return statesTemp2

    def getPreconditions(self, funciones_numeros):
        preconditions = []
        for result in self.config_variables.states:
            precondition = ""
            for number in funciones_numeros:
                if precondition != "":
                    precondition += " && "
                if number in result:
                    precondition += self.config_variables.statePreconditions[number - 1]
                else:
                    precondition += "!(" + self.config_variables.statePreconditions[number - 1] + ")"
            preconditions.append(precondition)
        return preconditions


@dataclass
class ConfigVariables:
    states: list = None
    preconditions: list = None
    extraConditions: list = None
    functions: list = None
    functionVariables: list = None
    functionPreconditions: list = None
    contractName: str = None
    contractFileName: str = None
    fileName: str = None
    statePreconditions: list = None
    statesNames: list = None

    dir: str = None
    dir_name: str = None
    mode: Mode = None

    debug: bool = False


@dataclass
class VerisolExecutionHistory:
    """ Variables para guardar la cantidad de timeouts y corral fails cuando corremos VeriSol.
    Se incrementan en try_command y se imprimen al final. """
    number_to: int = 0
    number_corral_fail: int = 0
    number_corral_fail_with_tackvars: int = 0
