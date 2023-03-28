import datetime
import copy

settingsdict = {
    'MaxSleepTime': 5,
    'LoopCheckTime': 1,
    'InvertMinSoc': 96,
    'MinThrottleBuffer': 150,
    'ThrottleMinSoc': 97,
    'ThrottleMaxSoc': 99,  # This needs to be more than ThrottleMinSoc
    'MaxThrottleBuffer': 5000,  # This needs to be more than MinThrottleBuffer
    'RescanServiceInterval': datetime.timedelta(minutes=1),
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
    'InputSource': {'Service': "com.victronenergy.vebus.ttyS4",
                    'Path': "/Ac/ActiveIn/ActiveInput",
                    'Proxy': object,
                    'Value': 0},
    'Phases':{
        'L1': {
            'InPower': {'Service': "com.victronenergy.vebus.ttyS4",
                          'Path': "/Ac/ActiveIn/L1/P",
                          'Proxy': object,
                          'Value': 0},
            'OutPower': {'Service': "com.victronenergy.vebus.ttyS4",
                           'Path': "/Ac/Out/L1/P",
                           'Proxy': object,
                           'Value': 0}},
        'L2': {
            'InPower': {'Service': "com.victronenergy.vebus.ttyS4",
                          'Path': "/Ac/ActiveIn/L2/P",
                          'Proxy': object,
                          'Value': 0},
            'OutPower': {'Service': "com.victronenergy.vebus.ttyS4",
                           'Path': "/Ac/Out/L2/P",
                           'Proxy': object,
                           'Value': 0}},
            }
}

pvdict = {
    'L1': {
        'InverterList': ['pv_76_1148833'], # This should look something like this: [pv_77_1028252, pv_77_1028251]
        'Inverters': {},
    },
    'L2': {
        'InverterList': ['pv_76_1148698'], # This should look something like this: [pv_77_1028252, pv_77_1028251]
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


# TODO change this to a dictionary so that the name can be included
donotcalclist = [
    "/Settings/CGwacs/AcPowerSetPoint",
    "/Ac/PowerLimit"
]