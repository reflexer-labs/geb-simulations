import math
import models.options as options
import models.constants as constants
import models.system_model_v3.model.parts.failure_modes as failure


def update_target_rated(params, substep, state_history, state, policy_input):
    """
    Calculate the PI controller target rate rate using the Kp, Ki and Kd constants and the error states.
    """

    if state['cumulative_time'] % params['control_period'] == 0:
        error = state["error_star"]  # unit BASE
        prev_error = state["prev_error_star"]  # unit BASE
        error_integral = state["error_star_integral"]  # unit BASE * seconds

        #print(f"adding {params['kp'] * error } to rate")
        target_rate = state['target_rate'] + params["kp"] * error + params["ki"] * error_integral + params["kd"] * (error - prev_error)

        target_rate = target_rate if policy_input["controller_enabled"] else 0  # unitless
    else:
        target_rate = state['target_rate'] if policy_input["controller_enabled"] else 0

    return "target_rate", target_rate

def update_target_rate(params, substep, state_history, state, policy_input):
    """
    Calculate the PI controller target rate using the Kp,  Ki and Kd constants and the error states.
    """

    if state['cumulative_time'] % params['control_period'] == 0:
        error = state["error_star"]  # unit BASE
        prev_error = state["prev_error_star"]  # unit BASE
        error_integral = state["error_star_integral"]  # unit BASE * seconds


        target_rate = params["kp"] * error + params["ki"] * error_integral + params["kd"] * (error - prev_error)
        #print(f"{state['timestep']=}, {error=}, {error_integral=}, {target_rate=}")

        target_rate = target_rate if policy_input["controller_enabled"] else 0  # unitless
    else:
        target_rate = state['target_rate'] if policy_input["controller_enabled"] else 0

    return "target_rate", target_rate

def update_target_rate_step(params, substep, state_history, state, policy_input):
    """
    Calculate the PI controller target rate using the Kp,  Ki and Kd constants and the error states.
    """

    if state['cumulative_time'] % params['control_period'] == 0:
        error = state["error_star"]  # unit BASE
        target_rate = state['target_rate']

        delta = params['khow'] * params['control_period']

        if error > 0: # error = target - market
            target_rate += delta
        elif error < 0:
            target_rate += -delta

        # Bound per second target_rate here to (-100%, 100%)
        target_rate = max(min(target_rate, 2 - 1E-15), -2 + 1E-15)

        target_rate = target_rate if policy_input["controller_enabled"] else 0  # unitless
    else:
        target_rate = state['target_rate'] if policy_input["controller_enabled"] else 0

    return "target_rate", target_rate

def update_target_price(params, substep, state_history, state, policy_input):
    """
    Update the controller target_price state ("redemption price") according to the controller target_rate state ("redemption rate")

    Notes:
    * exp(bt) = (1+b)**t for low values of b; but to avoid compounding errors
    * we should probably stick to the same implementation as the solidity version
    * target_price =  state['target_price'] * FXnum(state['target_rate'] * state['timedelta']).exp()
    * target_price =  state['target_price'] * math.exp(state['target_rate'] * state['timedelta'])
    """

    target_price = state["target_price"]
    try:
        target_price = (
            state["target_price"] * (1 + state["target_rate"]) ** state["timedelta"]
        )
    except OverflowError as e:
        raise failure.ControllerTargetOverflowException((e, target_price))

    #print(f"target_rate {state['target_rate']} {target_price=}")
    if target_price < 0:
        target_price = 0
    return "target_price", target_price

def update_target_price_damp(params, substep, state_history, state, policy_input):

    if len(state_history) < 4:
        prev_eth_price = state_history[0][0]['eth_price']
    else:
        prev_eth_price = state_history[-4][0]['eth_price']

    multiplier = 1 + (state['eth_price'] - prev_eth_price)/prev_eth_price * params['damp_factor']
    target_price = state["target_price"]
    try:
        target_price = state["target_price"] * multiplier
    except OverflowError as e:
        raise failure.ControllerTargetOverflowException((e, target_price))

    if target_price < 0:
        target_price = 0

    return "target_price", target_price

def observe_errors(params, substep, state_history, state):
    """
    Calculate the error between the target and market price, using the error_term parameter.
    The error_term parameter allows you to set whether the error is calculated as target - market or market - target.
    """

    #if state['cumulative_time'] < params['enable_controller_time']:
    if state["market_price_twap"] == 0:
        return {"error_star": 0, "prev_error_star": 0}

    target_price = state["target_price"] * params["liquidation_ratio"] if params["rescale_target_price"] else state["target_price"]
    error = params["error_term"](target_price, state["market_price_twap"])

    if len(state_history) < 4:
        prev_error = state_history[0][0]['error_star']
    else:
        prev_error = state_history[-4][0]['error_star']
    #prev_error = 0

    return {"error_star": error, "prev_error_star": prev_error}


def store_error_star(params, substep, state_history, state, policy_input):
    """
    Store the error_star state, which is the error between the target and market price.
    """
    error = policy_input["error_star"]

    return "error_star", error

def store_prev_error_star(params, substep, state_history, state, policy_input):
    """
    Store the error_star state, which is the error between the target and market price.
    """
    
    error = policy_input["prev_error_star"]

    return "prev_error_star", error


def update_error_star_integral(params, substep, state_history, state, policy_input):
    """
    Update and store the error integral state.

    Calculate the error integral using numerical integration (trapezoid rule):
    See https://github.com/cadCAD-org/demos/blob/master/tutorials/numerical_computation/numerical_integration_1.ipynb
    """
    # Don't start accumulating until the controller is enabled
    if state['cumulative_time'] < params['enable_controller_time']:
        return "error_star_integral", 0  # unit: BASE * seconds

    # Numerical integration (trapezoid rule)
    error_star_integral = state["error_star_integral"]
    old_error = state["error_star"]  # unit: BASE 
    new_error = policy_input["error_star"]  # unit: BASE
    mean_error = (old_error + new_error) / 2  # unit: BASE
    timedelta = state["timedelta"]  # unit: time (seconds)
    area = mean_error * timedelta  # unit: BASE * seconds

    #print(f"{state['timestep']=} ,{state['error_star_integral']=}")
    #print(f"{state['timestep']=} ,{old_error=}, {new_error=}")

    # Select whether to implement a leaky integral or not
    if params[options.IntegralType.__name__] == options.IntegralType.LEAKY.value:
        alpha = params["alpha"]
        remaining_frac = float(alpha / constants.RAY) ** timedelta  # unitless
        remaining = int(remaining_frac * error_star_integral)  # unit: BASE * seconds
        error_integral = remaining + area  # unit: BASE * seconds
    else:
        error_integral = error_star_integral + area  # unit: BASE * seconds

    return "error_star_integral", error_integral  # unit: BASE * seconds
