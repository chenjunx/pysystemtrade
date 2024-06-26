from sysdata.config.production_config import get_production_config
from syscore.constants import arg_not_supplied

LIST_OF_MILLS_PARAMS = ["mills_ipaddress", "mills_port","mills_username","mills_password"]


def mills_defaults(**kwargs):
    """
    Returns mills configuration with following precedence
    1- if passed in arguments: ipaddress, port, millsoffset - use that
    2- if defined in private_config file, use that. mills_ipaddress, mills_port
    3 - if defined in system defaults file, use that
    :return: mongo db, hostname, port
    """

    # this will include defaults.yaml if not defined in private
    passed_param_names = list(kwargs.keys())
    output_dict = {}
    config = get_production_config()
    for param_name in LIST_OF_MILLS_PARAMS:
        if param_name in passed_param_names:
            param_value = kwargs[param_name]
        else:
            param_value = arg_not_supplied

        if param_value is arg_not_supplied:
            param_value = getattr(config, param_name)

        output_dict[param_name] = param_value

    # Get from dictionary
    ipaddress = output_dict["mills_ipaddress"]
    port = output_dict["mills_port"]
    username = output_dict["mills_username"]
    password = output_dict["mills_password"]

    return ipaddress, port,username,password