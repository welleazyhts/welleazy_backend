def normalize_value(value, unit, module):

    # HEIGHT -> Convert everything to centimeters
    if module == "height":
        if unit == "cm":
            return value
        if unit == "ft":
            return value * 30.48  # 1 ft = 30.48 cm

    # WEIGHT -> Convert everything to kilograms
    if module == "weight":
        if unit == "kg":
            return value
        if unit == "lb":
            return value * 0.453592  # 1 lb = 0.453592 kg

    # GLUCOSE -> Convert everything to mg/dl
    if module == "glucose":
        if unit == "mg/dl":
            return value
        if unit == "mmol/l":
            return value * 18  # 1 mmol/l = 18 mg/dl

    return value
