import sys
import os
import typer
import uvicorn
from loguru import logger
from typing import Annotated
from dataclasses import dataclass
from communex.compat.key import classic_load_key
from mosaic_subnet.validator import Validator, ValidatorSettings
from mosaic_subnet.miner import Miner, MinerSettings
from mosaic_subnet.gateway import app, Gateway, GatewaySettings

cli = typer.Typer()
sys.path.append(os.getcwd())


@dataclass
class ExtraCtxData:
    """Model for extra context data"""

    use_testnet: bool


@cli.callback()
def main(
    ctx: typer.Context,
    testnet: Annotated[
        bool, typer.Option(envvar="COMX_USE_TESTNET", help="Use testnet endpoints.")
    ] = False,
    log_level: str = "INFO",
) -> None:
    """
    The main function for the CLI application. Sets up logging based on log_level,
    logs whether testnet is used, and sets ExtraCtxData in the context object.

    Parameters:
        - ctx: typer.Context
        - testnet: bool, default=False (Annotated with envvar="COMX_USE_TESTNET", help="Use testnet endpoints.")
        - log_level: str, default="INFO"

    Returns:
        None
    """
    logger.remove()
    logger.add(sink=sys.stdout, level=log_level.upper())

    if testnet:
        logger.info("use testnet")
    else:
        logger.info("use mainnet")

    ctx.obj = ExtraCtxData(use_testnet=testnet)


@cli.command(name="validator")
def validator(
    ctx: typer.Context,
    key_name: Annotated[
        str,
        typer.Argument(
            help="Name of the key. Provided in this format: ~/.commune/key/<key_name>.json"
        ),
    ],
    module_path: Annotated[
        str,
        typer.Argument(
            help="name of the file and classname of the module. Provided in this format: <file_name>.<class_name>"
        ),
    ],
    host: Annotated[str, typer.Argument(help="Host ip of the validator")],
    port: Annotated[int, typer.Argument(help="Port of the validator")],
    call_timeout: int = 60,
    iteration_interval: int = 60,
) -> None:
    """
    A command-line interface (CLI) command function that runs a validation loop for a validator.

    Args:
        ctx (typer.Context): The context object for the CLI command.
        key_name (str): The name of the key present in `~/.commune/key`.
        call_timeout (int, optional): The timeout value for calls in seconds. Defaults to 60.
        iteration_interval (int, optional): The interval between iterations in seconds. Defaults to 60.

    Returns:
        None
    """
    settings = ValidatorSettings(
        use_testnet=ctx.obj.use_testnet,
        iteration_interval=iteration_interval,
        call_timeout=call_timeout,
        module_path=module_path,
        key_name=key_name,
        host=host,
        port=port,
    )
    mosaic_validator = Validator(key=classic_load_key(name=key_name), config=settings)
    mosaic_validator.validation_loop()


@cli.command(name="miner")
def miner(
    ctx: typer.Context,
    key_name: Annotated[
        str,
        typer.Argument(
            help="Name of the key. Provided in this format: ~/.commune/key/<key_name>.json"
        ),
    ],
    module_path: Annotated[
        str,
        typer.Argument(
            help="name of the file and classname of the module. Provided in this format: <file_name>.<class_name>"
        ),
    ],
    host: Annotated[
        str,
        typer.Argument(
            help="the public ip you've registered, you can simply put 0.0.0.0 here to allow all incoming requests"
        ),
    ],
    port: Annotated[int, typer.Argument(help="port")],
    testnet: bool = False,
) -> None:
    """
    A command-line interface (CLI) command function that starts a miner with given settings.

    Args:
        ctx (typer.Context): The context object for the CLI command.
        key_name (str): Name of the key present in `~/.commune/key`.
        host (str): The public IP address to register, use "0.0.0.0" to allow all incoming requests.
        port (int): The port number.
        testnet (bool, optional): Flag to indicate if testnet should be used. Defaults to False.

    Returns:
        None
    """
    settings = MinerSettings(
        use_testnet=testnet or ctx.obj.use_testnet,
        host=host,
        port=port,
        module_path=module_path,
        key_name=key_name,
    )
    mosaic_miner = Miner(key=classic_load_key(name=key_name), config=settings)
    mosaic_miner.serve()


@cli.command(name="gateway")
def gateway(
    ctx: typer.Context,
    key_name: Annotated[
        str, typer.Argument(help="Name of the key present in `~/.commune/key`")
    ],
    module_path: Annotated[
        str, typer.Argument(help="name of the file and classname of the module")
    ],
    host: Annotated[str, typer.Argument(help="host")],
    port: Annotated[int, typer.Argument(help="port of the gateway")],
    testnet: bool = False,
    call_timeout: int = 65,
) -> None:
    """
    A command-line interface (CLI) command function that starts a gateway with given settings.

    Args:
        ctx (typer.Context): The context object for the CLI command.
        key_name (str): Name of the key present in `~/.commune/key`.
        host (str): The host.
        port (int): The port number.
        testnet (bool, optional): Flag to indicate if testnet should be used. Defaults to False.
        call_timeout (int, optional): The call timeout in seconds. Defaults to 65.

    Returns:
        None
    """
    settings = GatewaySettings(
        use_testnet=ctx.obj.use_testnet or testnet,
        host=host,
        port=port,
        module_path=module_path,
        key_name=key_name,
        call_timeout=call_timeout,
    )
    mosaic_gateway = Gateway(key=classic_load_key(name=key_name), config=settings)
    mosaic_gateway.sync_loop()
    uvicorn.run(app=app, host=str(settings.host), port=int(str(settings.port)))


if __name__ == "__main__":
    cli()
