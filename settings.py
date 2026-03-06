import datetime
import copy

settingsdict = {
    'LoopCheckTime': 1,
    'NoThrottleSoc': 93,
    'MinThrottleBuffer': 0,
    'ThrottleToConsumptionSoc': 96,
    'NoSolarSoc': 98,
    'RescanServiceInterval': datetime.timedelta(minutes=1),
    'BatteryMaxCharge': 10000,
    'min_grid_power': 150,
}

servicesdict = {
    'AcSetpoint': {'Service': "com.victronenergy.settings",
                   'Path': "/Settings/CGwacs/AcPowerSetPoint",
                   'Proxy': object,
                   'Value': 0},
    'CCGXRelay': {'Service': "com.victronenergy.system",
                  'Path': "/Relay/0/State",
                  'Proxy': object,
                  'Value': 0},
    'Soc': {'Service': "com.victronenergy.system",
            'Path': "/Dc/Battery/Soc",
            'Proxy': object,
            'Value': 80},
    'InputSource': {'Service': "com.victronenergy.vebus.ttyO1",
                    'Path': "/Ac/ActiveIn/ActiveInput",
                    'Proxy': object,
                    'Value': 0},
}

vicdict = {
    'L1': {
            'InPower': {'Service': "com.victronenergy.vebus.ttyO1",
                          'Path': "/Ac/ActiveIn/L1/P",
                          'Proxy': object,
                          'Value': 0},
            'OutPower': {'Service': "com.victronenergy.vebus.ttyO1",
                           'Path': "/Ac/Out/L1/P",
                           'Proxy': object,
                           'Value': 0}},
}

pvdict = {
    'L1': {
        'InverterList': ['pv_77_1064614'], # This should look something like this: [pv_77_1028252, pv_77_1028251]
        'Inverters': {},
    },
}

pv_services_structure = {
    'MaxPower': {'Service': "com.victronenergy.pvinverter",
                 'Path': "/Ac/MaxPower",
                 'Proxy': object,
                 'Value': 0},
    'Power': {'Service': "com.victronenergy.pvinverter",
              'Path': "/Ac/Power",
              'Proxy': object,
              'Value': 0},
    'PowerLimit': {'Service': "com.victronenergy.pvinverter",
                   'Path': "/Ac/PowerLimit",
                   'Proxy': object,
                   'Value': 0}
}
# Generate the pvdict
for line in pvdict:
    for inverter in pvdict[line]['InverterList']:
        pvdict[line]['Inverters'][inverter] = copy.deepcopy(pv_services_structure)
        for setting in pvdict[line]['Inverters'][inverter]:
            pvdict[line]['Inverters'][inverter][setting]['Service'] += '.' + inverter
