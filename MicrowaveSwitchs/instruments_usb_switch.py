# -*- coding: utf-8 -*-
from __future__ import print_function
import json
import time
from os import getcwd

from string import split, join

from serial import Serial
from serial.tools import list_ports

class UsbSwitch(object):
    def __init__(self, file_name='C:/Users/dphy-dupontferrielab/Microwave_switch_control/configuration_switch.dat'):
        """

        :param file_name: Path of the configuration_switch.dat file (json file)
        :type file_name: basestring
        """
        
        file_name = getcwd() + "/configuration_switch.dat"
        
        self.file_name = str(file_name)
        with open(self.file_name, 'r') as in_file:
            self.states_switches = json.load(in_file)

        ports = list_ports.comports()
        port = None
        for p in ports:
            if p.serial_number == self.states_switches['serial_number']:
                port = p.device

        assert port is not None, 'The board is not connected'

        self.serial = Serial(port=port,
                             timeout=self.states_switches['timeout'],
                             baudrate=self.states_switches['baudrate'])

        time.sleep(2.)  # We wait for the board to reset
        if not self.verify_presence_board():
            raise StandardError('The board has not responded at all.\n')

        self.verify_voltage()
        self.apply_IO()

        if 'attenuator' in self.states_switches.keys():
            self.set_attenuator(self.states_switches['attenuator'])
        
    def __del__(self):
        self.serial.close()

    def save_data(self):
        with open(self.file_name, 'w') as out_file:
            json.dump(self.states_switches, out_file, sort_keys=True, indent=4, separators=(',', ': '))

    def print_states_switches(self):
        return json.dumps(self.states_switches, sort_keys=True, indent=4, separators=(',', ': '))

    @property
    def pulse_duration(self):
        return int(self.states_switches['pulse_duration'])

    @pulse_duration.setter
    def pulse_duration(self, value):
        if value < 0 or value >= 100:
            raise ValueError('The duration of a pulse %d must be between 0 and 100.' % value)

        self.states_switches['pulse_duration'] = value
        self.save_data()

    def verify_presence_board(self):
        self.serial.flush()
        self.serial.write('<PRESENT>\r\n')

        s = ''
        init_time = time.time()
        tot = 0
        while s[-9:] != 'Present\r\n' or (time.time() - init_time) > 1.:
            tot += 1
            n = self.serial.read_until()                         # Lis les 10 premiers bytes du port série (envoyés par l'Arduino)
            print(n)
            if not len(n):                                   # Si len(n) (= le nombre de bytes stockés dans n) est nul: on sort de la boucle
                print( "I broke, n = ", n, " , len(n) = ", len(n), "\ns = ", s, '\ntot =', tot)
                break
        
            s += n                                           
        print("Temps écoulé: ", time.time() - init_time, "s\nNombre de boucles: ", tot)
        print("s[-9:] = ", s[-9:])
        return s[-9:] == 'Present\r\n'

    def verify_last_command(self):
        # test = self.readall()
        test = self.serial.read(6)
        print(test)
        if filter(str.isalnum, test) != 'Okay':
            print(self.readall())
            raise StandardError('The board has not responded correctly.\n')

    def verify_voltage(self):
        self.serial.write('<VBB>\r\n')
        self.serial.flush()

        s = self.readall()
        print(s)
        h_bridge_voltage = float(s.split('=')[1])
        assert h_bridge_voltage > 20., "No voltage on the H-Bridge (%.3f V), verify connection and fusible" % \
                                       h_bridge_voltage

    def apply_IO(self):
        switches = {join(split(k, '_')[1:], '_') for (k, v) in self.states_switches.items() if 'switch_' in k}

        for switch in switches:
            if self.states_switches['switch_%s' % switch]['type'] == 'IO':
                for (port, v) in self.states_switches['switch_%s' % switch].items():
                    if 'port_' in port:
                        self.set_switch(switch, int(port[-1]),
                                        self.states_switches['switch_%s' % switch][port]['state'], force=True)

    def set_current(self, switch, port, current_mA=None):
        """
        Set the current of a switch in mA.
        """

        if current_mA is None:
            current_mA = float(self.states_switches['switch_%s' % switch]['current_mA'])

        assert 0. < current_mA < 227, 'The board can only apply current between 0 and 227 mA'

        value_dac = int(current_mA * 10. * 1.8)
        board = int(self.states_switches['switch_%s' % switch]['port_%d' % port]['board'])
        address_dac = int(self.states_switches['board_%d_dac' % board])
        self.set_and_verify_dac(address_dac, value_dac)
        time.sleep(0.05)

        if current_mA != float(self.states_switches['switch_%s' % switch]['current_mA']):
            self.states_switches['switch_%s' % switch]['current_mA'] = current_mA
            print('Current has been changed for switch %s' % switch)
            self.save_data()

    def set_and_verify_dac(self, address_dac, value):
        """
        Intended for internal use only.
        """
        if value < 0 or value > 4095:
            raise ValueError('The value %d for the dac must be between 0 and 4095.' % value)

        self.serial.write('<dac-%d-%d>\r\n' % (int(address_dac), int(value)))
        self.serial.flush()
        self.verify_last_command()

    def set_switch(self, switch, port, state, polarity=None, force=False):
        """
        Put the port of the switch on the state. Note that if the switch has only two ports,
        the state of the two port will be changed by this command, if necessary.

        The pulse duration is in millisecond and cannot be more than 100  milliseconds
        The polarity parameter allows to change the polarity declare in the file.
        The force parameter allows to make the pulse even if it's already in this state
        """

        port = int(port)

        if polarity == 'positive' or polarity == 'negative':
            self.states_switches['switch_%s' % switch]['polarity'] = polarity

            if self.states_switches['switch_%s' % switch]['state'] == 'open':
                self.states_switches['switch_%s' % switch]['state'] = 'close'
            else:
                self.states_switches['switch_%s' % switch]['state'] = 'open'
            print('i changed polarity')
            self.save_data()
            polarity = None

        if polarity is None:

            # First we do all verification

            if self.states_switches['switch_%s' % switch]['type'] == 'SPDT' and state == 'open':
                raise ValueError(
                    'For a switch which has always a port close, it\'s impossible to open a port (which other one will '
                    'be closed ?). Instead, closed another port to open it.')

            if not ('switch_%s' % switch in self.states_switches.keys()):
                raise ValueError('The switch %s is not declared in the file %s.' % (switch, self.file_name))

            if not ('port_%d' % port in self.states_switches['switch_%s' % switch].keys()):
                raise ValueError(
                    'The port %d of the switch %s is not declared in the file %s.' % (port, switch, self.file_name))

            if not (state == 'open' or state == 'close'):
                raise ValueError('The state %s is not \'open\' or \'close\'.' % state)

            if self.states_switches['switch_%s' % switch]['port_%d' % port]['state'] == state and not force:
                raise ValueError('The port %d of the switch %s is already in the state %s.' % (port, switch, state))

            if self.states_switches['switch_%s' % switch]['type'] != 'IO':
                self.set_current(switch, port)

            # We now format the command
            board = int(self.states_switches['switch_%s' % switch]['port_%d' % port]['board'])
            reference_switch_board = int(
                self.states_switches['switch_%s' % switch]['port_%d' % port]['reference_switch_board'])

            if self.states_switches['switch_%s' % switch]['port_%d' % port]['polarity'] == 'positive':
                polarity = 'P' if (state == 'close') else 'N'
            else:
                polarity = 'N' if (state == 'close') else 'P'

            try:
                pulse_duration = int(self.states_switches['switch_%s' % switch]['pulse_duration'])
            except KeyError:
                pulse_duration = int(self.states_switches['pulse_duration'])

            self.serial.write('<sw-%d-%d-%s-%d>\r\n' % (
                board, reference_switch_board, polarity, pulse_duration))
            self.serial.flush()
            self.verify_last_command()

            # We save it in taking into account the structure of the switch ('SPDT': close a port opened directly all
            # other)
            if self.states_switches['switch_%s' % switch]['type'] == 'SPDT':
                ports_switch = {int(split(k, '_')[-1]) for (k, v) in self.states_switches['switch_%s' % switch].items()
                                if
                                'port_' in k}
                for port_switch in ports_switch:
                    if port == port_switch:
                        self.states_switches['switch_%s' % switch]['port_%d' % port]['state'] = 'close'
                    else:
                        self.states_switches['switch_%s' % switch]['port_%d' % port_switch]['state'] = 'open'
            else:
                self.states_switches['switch_%s' % switch]['port_%d' % port]['state'] = state

            self.save_data()

    def connect_port(self, switch, port, force=False):
        for (port_switch, v) in self.states_switches['switch_%s' % switch].items():
            if ('port_%d' % int(port)) != port_switch:
                try:
                    self.set_switch(switch, int(port_switch[-1]), 'open', force=force)
                except ValueError:
                    pass
            elif ('port_%d' % int(port)) == port_switch:
                try:
                    self.set_switch(switch, port, 'close', force=force)
                except ValueError:
                    pass

    def command_every_port(self, state='open', switch=None, force=False):
        """
        Try to apply the specified state to all ports, naturally doesn't work with switches of type SPDT.
        It does not apply to IO port too.
        """

        if switch is None:
            switches = {join(split(k, '_')[1:], '_') for (k, v) in self.states_switches.items() if 'switch_' in k}
        else:
            switches = {int(switch)}

        for sw in switches:
            if self.states_switches['switch_%s' % sw]['type'] != 'SPDT' and \
                self.states_switches['switch_%s' % sw]['type'] != 'IO':
                for (port, v) in self.states_switches['switch_%s' % sw].items():
                    if 'port_' in port:
                        port = int(split(port, '_')[-1])
                        try:
                            self.set_switch(sw, port, state, force=force)
                        except ValueError:
                            pass
            elif switch is not None:
                print('The switch %d cannot be opened because of its type %s' % (
                    sw, self.states_switches['switch_%d' % sw]['type']))

    def readall(self):
        #timeout = self.serial.timeout
        s = ''

        while True:
            n = self.serial.read(100)

            if not len(n):
                break

            s += n

        #self.serial.timeout = timeout
        
        return s

    def force_state_in_file(self):
        """
        Force all the switches which are declared in the configuration declares in the file.
        """

        switches = {k for (k, v) in self.states_switches.items() if 'switch_' in k}

        for switch in switches:
            ports = {k for (k, v) in self.states_switches[switch].items() if 'port_' in k}
            for port in ports:
                if self.states_switches[switch]['type'] == 'SP6T' or \
                    self.states_switches[switch]['type'] == 'IO' or \
                    self.states_switches[switch][port]['state'] == 'close':
                    self.set_switch(join(split(switch, '_')[1:], '_'), int(split(port, '_')[-1]),
                                    self.states_switches[switch][port]['state'], force=True)

    def set_attenuator(self, attenuation):
        """
        Attenuation must be a multiple of 10dB and between 0 and 70 dB.
        """

        attenuation = int(attenuation)

        if (attenuation % 10) or attenuation < 0 or attenuation > 70:
            raise ValueError('The attenuation is out of range (multiple of 10dB and between 0 and 70).')
        else:
            self.serial.write('<att-%d>\r\n' % (attenuation / 10))
            self.verify_last_command()
            self.states_switches['attenuator'] = attenuation
            self.save_data()
