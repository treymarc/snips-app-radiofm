#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from snipsTools import SnipsConfigParser
from hermes_python.hermes import Hermes
from hermes_python.ontology import *
import io
#import os
import subprocess

CONFIG_INI = "config.ini"

# If this skill is supposed to run on the satellite,
# please get this mqtt connection info from <config.ini>
# Hint: MQTT server is always running on the master device
MQTT_IP_ADDR = "localhost"
MQTT_PORT = 1883
MQTT_ADDR = "{}:{}".format(MQTT_IP_ADDR, str(MQTT_PORT))

class SnipsAppRadioFM(object):
    """This Class is connecting the snips intents with the two actions.
       The fm_start.sh and fm_stop.sh shell scripts contains the radio specifics
       commandes you can easly tweak and change the ctronlled radio system by
       editing those two script files.
    """

    def __init__(self):
        # get the configuration if needed
        try:
            self.config = SnipsConfigParser.read_configuration_file(CONFIG_INI)
        except :
            self.config = None

        # start listening to MQTT
        self.start_blocking()
        
    def playRadioFM_callback(self, hermes, intent_message):
        # terminate the session first if not continue
        hermes.publish_end_session(intent_message.session_id, "")
        
        print '[Received] intent: {}'.format(intent_message.intent.intent_name)
        frequency = intent_message.slots.frequency.first().value
        #print frequency
        subprocess.Popen(['/var/lib/snips/skills/snips-app-radiofm/fm_start.sh',frequency])

        hermes.publish_start_session_notification(intent_message.site_id, frequency, "")

    def stopRadioFM_callback(self, hermes, intent_message):
        # terminate the session first if not continue
        hermes.publish_end_session(intent_message.session_id, "")

        print '[Received] intent: {}'.format(intent_message.intent.intent_name)
        subprocess.Popen(['/var/lib/snips/skills/snips-app-radiofm/fm_stop.sh'])
        #os.system('/var/lib/snips/skills/snips-app-radiofm/fm_stop.sh &')

    # --> Master callback function, triggered everytime an intent is recognized
    def master_intent_callback(self,hermes, intent_message):
        coming_intent = intent_message.intent.intent_name
        if ':' in coming_intent:
            coming_intent = coming_intent.split(":")[1]
        if coming_intent == 'playRadioFM':
            self.playRadioFM_callback(hermes, intent_message)
        if coming_intent == 'stopRadioFM':
            self.stopRadioFM_callback(hermes, intent_message)
        # more callback and if condition goes here...

    # --> Register callback function and start MQTT
    def start_blocking(self):
        with Hermes(MQTT_ADDR) as h:
            h.subscribe_intents(self.master_intent_callback).start()

if __name__ == "__main__":
    SnipsAppRadioFM()
