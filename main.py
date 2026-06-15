#!/usr/bin/env python

# Imports
import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib as glib
import time
import os
import sys
import datetime
import logging
import copy
from logging.handlers import RotatingFileHandler
from settings import settingsdict, servicesdict, vicdict, pvdict # Change this for production

sys.path.insert(1, os.path.join(os.path.dirname(__file__), 'ext', 'velib_python'))
from vedbus import VeDbusItemImport

# Systemcontroller for python 3
class ExportController(object):


    def __init__(self, bus):

        self.bus = bus
        self.settings = copy.deepcopy(settingsdict)
        self.dbusservices = copy.deepcopy(servicesdict)
        self.vicservices = copy.deepcopy(vicdict)
        self.pvservices = copy.deepcopy(pvdict)

        self.prevruntime = datetime.datetime.now()
        self.unavailableservices = []
        self.unavailablepvinverters = []
        self.unavailablevicservices = []
        self.pvcontrollable = True # TODO make this a true check later
        self.rescan_service_time = datetime.datetime.now()

        # Ensure this is always at the bottom
        self.setup_dbus_services()
        mainlogger.debug(f'{self.unavailableservices=}')

    def setup_dbus_services(self):

        for service in self.dbusservices:
            try:
                self.dbusservices[service]['Proxy'] = VeDbusItemImport(
                    bus=self.bus,
                    serviceName=self.dbusservices[service]['Service'],
                    path=self.dbusservices[service]['Path'],
                    eventCallback=None,
                    createsignal=True)
            except Exception as e:
                mainlogger.error('Exception in setting up dbus service %s' % service)
                mainlogger.debug(e)
                self.unavailableservices.append(service)

        # Also set up the victron inverters
        for line in self.vicservices:
            try:
                for service in self.vicservices[line].keys():
                    self.vicservices[line][service]['Proxy'] = VeDbusItemImport(
                        bus=self.bus,
                        serviceName=self.vicservices[line][service]['Service'],
                        path=self.vicservices[line][service]['Path'],
                        eventCallback=None,
                        createsignal=True)
            except Exception as e:
                mainlogger.error('Exception in setting up victron inverter on %s' % line)
                mainlogger.debug(e)
                self.unavailablevicservices.append(line)
                mainlogger.debug(f'line: {line}, service {service}.')
                mainlogger.debug(f'{self.vicservices}')

        # Also set up the pv inverter services
        for line in self.pvservices:
            for inverter, invservices in self.pvservices[line]['Inverters'].items():
                try:
                    for service in invservices:
                        invservices[service]['Proxy'] = VeDbusItemImport(
                            bus=self.bus,
                            serviceName=invservices[service]['Service'],
                            path=invservices[service]['Path'],
                            eventCallback=None,
                            createsignal=True)
                except Exception as e:
                    mainlogger.error('Exception in setting up pv inverter %s' % inverter)
                    mainlogger.debug(e)
                    self.unavailablepvinverters.append(inverter)

        self.rescan_service_time = datetime.datetime.now() + self.settings['RescanServiceInterval']

    def update_values(self):

        # Update the dbusservices dictionary
        for service in self.dbusservices:
            if service not in self.unavailableservices:
                try:
                    self.dbusservices[service]['Value'] = self.dbusservices[service]['Proxy'].get_value()
                except dbus.DBusException as e:
                    mainlogger.warning('Exception in getting dbus service %s' % service)
                    mainlogger.debug(e)
                    self.dbusservices[service]['Value'] = servicesdict[service]['Value']
                try:
                    self.dbusservices[service]['Value'] *= 1
                except:
                    mainlogger.warning('Non numeric value on %s' % service)
                    # Use the default value as in settings.py
                    self.dbusservices[service]['Value'] = servicesdict[service]['Value']

        # Update the victron services
        for line in self.vicservices:
            if line not in self.unavailablevicservices:
                for service in self.vicservices[line].keys():
                    try:
                        self.vicservices[line][service]['Value'] = self.vicservices[line][service]['Proxy'].get_value()
                    except dbus.DBusException as e:
                        mainlogger.warning('Exception in getting dbus service %s' % service)
                        mainlogger.debug(e)
                        self.vicservices[line][service]['Value'] = vicdict[line][service]['Value']
                    try:
                        self.vicservices[line][service]['Value'] *= 1
                    except:
                        mainlogger.warning('Non numeric value on %s' % service)
                        # Use the default value as in settings.py
                        self.vicservices[line][service]['Value'] = vicdict[line][service]['Value']

        # Update the pvservices dictionary
        for line in self.pvservices:
            for inverter, invservices in self.pvservices[line]['Inverters'].items():
                if inverter not in self.unavailablepvinverters:
                    for service in invservices:
                        try:
                            invservices[service]['Value'] = invservices[service]['Proxy'].get_value()
                        except dbus.DBusException as e:
                            mainlogger.warning('Exception in getting dbus service %s for %s' % (service, inverter))
                            mainlogger.debug(e)
                            invservices[service]['Value'] = pvdict[line]['Inverters'][inverter][service]['Value']
                        try:
                            invservices[service]['Value'] *= 1
                        except:
                            mainlogger.warning('Non numeric value on %s' % service)
                            # Use the default value as in settings.py
                            invservices[service]['Value'] = pvdict[line]['Inverters'][inverter][service]['Value']

        # # Do not do calculations on this list
        # if path not in self.donotcalc:
        #     self.do_calcs()

    def set_value(self, service, value, dictionary = None):
        # TODO this is a temporary fix, remove the default value later
        if dictionary is None:
            dictionary = self.dbusservices

        if service not in self.unavailableservices:
            try:
                VeDbusItemImport(
                    bus=self.bus,
                    serviceName=dictionary[service]['Service'],
                    path=dictionary[service]['Path'],
                    eventCallback=None,
                    createsignal=False).set_value(value)
                mainlogger.debug(f'Successfully set {service} to value of {value:.2f}')
            except dbus.DBusException:
                mainlogger.warning('Exception in setting dbus service %s' % service)

    def run(self):

        # # Do calcs manually
        # delta = datetime.datetime.now() - self.prevruntime
        # if delta >= datetime.timedelta(seconds=self.settings['MaxSleepTime'] - self.settings['LoopCheckTime']):
        self.do_calcs()
            # mainlogger.warning('Manually running do_calcs')
        # Let this function run continually on the glib loop
        return True

    def calc_total_pv_limit(self, max_charge_power: float, consumption: float, min_grid_power: float, soc: float, pv_capacity: float) -> (float, str):
        soc1 = self.settings['NoThrottleSoc']
        soc2 = self.settings['ThrottleToConsumptionSoc']
        soc3 = self.settings['NoSolarSoc']

        available_consumption = max(0.0, consumption - min_grid_power)
        power_consumption_capacity = available_consumption + max_charge_power

        # Calculate pv limit under ideal circumstances
        if soc <= soc1:
            pv_limit = pv_capacity
            regime_msg = "No throttle regime"
        elif soc <= soc2:
            theoretical_excess_pv = max(0.0, pv_capacity - available_consumption)
            pv_limit = ((soc - soc1) / (soc2 - soc1)) * theoretical_excess_pv + available_consumption
            regime_msg = "Throttle down to consumption regime"
        elif soc <= soc3:
            pv_limit = ((soc - soc2)/(soc3-soc2)) * available_consumption
            regime_msg = "Throttle down to zero regime"
        else:
            pv_limit = 0
            regime_msg = "Zero PV regime"

        # Dont produce more pv than can be consumed
        battery_throttle_msg = ""
        if pv_limit > power_consumption_capacity:
            pv_limit = power_consumption_capacity
            battery_throttle_msg = "and prevent battery overcharge"

        debug_msg = regime_msg + battery_throttle_msg + f', {pv_limit=:.2f}'
        return pv_limit, debug_msg


    def do_calcs(self):

        # Update the values
        self.update_values()

        # Setup variables
        soc = self.dbusservices['Soc']['Value']
        battery_voltage=self.dbusservices['BatteryVoltage']['Value']
        battery_charge_current_limit=self.dbusservices['ChargeCurrentLimit']['Value']
        max_charge = min(
            self.settings['BatteryMaxCharge'],
            battery_voltage * battery_charge_current_limit
        )
        mainlogger.debug(f'{soc=:.2f}, {battery_voltage=:.2f}, {battery_charge_current_limit=:.2f}, {max_charge=:.2f}')

        total_pv_prod = 0
        total_pv_capacity = 0
        for phase in self.pvservices.keys():
            for pv_inv in self.pvservices[phase]['Inverters'].values():
                total_pv_prod+= pv_inv['Power']['Value']
                total_pv_capacity += pv_inv['MaxPower']['Value']
        # This prevents a possible divide by zero error
        total_pv_capacity = max(1, total_pv_capacity)
        consumption = total_pv_prod
        in_power = 0
        for phase in self.vicservices.keys():
            consumption += self.vicservices[phase]['OutPower']['Value']
            in_power += self.vicservices[phase]['InPower']['Value']
        excess_pv = max(0, total_pv_prod - consumption)

        mainlogger.debug(f'{total_pv_prod=:.2f}, {total_pv_capacity=:.2f}, {consumption=:.2f}, {excess_pv=:.2f}')

        input_source = self.dbusservices['InputSource']['Value']
        if input_source != 240:
            min_in_power = settingsdict.get('min_grid_power', 150)
        else:
            min_in_power = 0

        total_pv_power_limit, throttle_msg = self.calc_total_pv_limit(
            max_charge,
            consumption,
            min_in_power,
            soc,
            total_pv_capacity
        )
        mainlogger.debug(throttle_msg)

        for phase in self.pvservices.keys():
            for inverter, invservices in self.pvservices[phase]['Inverters'].items():
                inv_contribution = invservices['MaxPower']['Value'] / total_pv_capacity
                powerlimit = max(0,total_pv_power_limit * inv_contribution)
                if inverter not in self.unavailablepvinverters:
                    # Assume invariant current value >= 0 and ramp_rate >= 0
                    ramp_limited_powerlimit = invservices['Power']['Value'] + self.settings['pv_ramp_rate']
                    if powerlimit > ramp_limited_powerlimit:
                        mainlogger.debug(f'Limiting inverter due to ramp limit from {powerlimit:.2f} to {ramp_limited_powerlimit:.2f}')
                        powerlimit = ramp_limited_powerlimit
                    self.set_value('PowerLimit', powerlimit, invservices)

        # Rescan the services if the correct amount of time has elapsed
        if datetime.datetime.now() >= self.rescan_service_time:
            self.unavailableservices = []
            self.unavailablepvinverters = []
            self.setup_dbus_services()


if __name__ == "__main__":

    def create_rotating_log(path, debug):
        # Create the logger
        logger = logging.getLogger('Zero_Export')
        logger.setLevel(logging.DEBUG)
        # Create a rotating filehandler
        filehandler = RotatingFileHandler(path, maxBytes=5242880, backupCount=1)
        filehandler.setLevel(logging.INFO)
        # Create a streamhandler to print to console
        consolehandler = logging.StreamHandler()
        consolehandler.setLevel(logging.DEBUG)
        # Create a formatter and add to filehandler and consolehandler
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        filehandler.setFormatter(formatter)
        consolehandler.setFormatter(formatter)
        # Add the filehandler and consolehandler to the logger
        logger.addHandler(filehandler)
        if debug:
            logger.addHandler(consolehandler)
        return logger

    debug = False
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == 'debug':
            debug = True
        else:
            print(f"Incorrect parameter found, expected debug found {arg}")
            exit(0)


    # setup the logger
    log_file = "log.txt"
    mainlogger = create_rotating_log(log_file, debug)
    # Setup the dbus
    DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    # start the controller
    mainlogger.debug('Starting ExportController')
    controller = ExportController(bus)
    glib.timeout_add_seconds(controller.settings['LoopCheckTime'], controller.run)
    mainloop = glib.MainLoop()
    mainloop.run()