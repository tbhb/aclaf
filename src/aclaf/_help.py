from aclaf._parameters import CommandParameter
from aclaf.parser import ZERO_ARITY, AccumulationMode


class CommandHelpConfiguration:
    pass


class AppHelpConfiguration(CommandHelpConfiguration):
    pass


class ParameterHelpConfiguration:
    pass


def help_parameter() -> "CommandParameter":
    return CommandParameter(
        name="help",
        short=("h",),
        long=("help",),
        is_flag=True,
        arity=ZERO_ARITY,
        accumulation_mode=AccumulationMode.COUNT,
    )
