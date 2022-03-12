"""
Determine DAC output values & ranges based on circuit parameters
"""
base_emitter_saturation_voltage = 0.7
i_p = 0.003
r_p = 1000
gain_p = 1 + 1 / 1

i_n_high = 0.005
i_n_low = 0.001
r_n = 1000
gain_n = - 4.7 / 1

def p_dac_8bit_for_battery(v_battery):
    """
    DAC 8-bit value for p current source given battery voltage
    """
    base_voltage = v_battery - base_emitter_saturation_voltage - i_p * r_p
    v_dac = base_voltage / gain_p
    v_dac_8_bit = v_dac / 3.3 * 255

    return v_dac_8_bit

def n_dac_8bit_for_battery(v_battery):
    """
    DAC 8-bit (low, high) range for n current source given battery voltage
    """
    base_voltage_low = -1 * (v_battery - base_emitter_saturation_voltage - i_n_low * r_n)
    v_dac_low = base_voltage_low / gain_n
    v_dac_8_bit_low = v_dac_low / 3.3 * 255


    base_voltage_high = -1 * (v_battery - base_emitter_saturation_voltage - i_n_high * r_n)
    v_dac_high = base_voltage_high / gain_n
    v_dac_8_bit_high = v_dac_high / 3.3 * 255

    return (v_dac_8_bit_low, v_dac_8_bit_high)