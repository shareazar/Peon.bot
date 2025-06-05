from typing import Text, List, Any, Dict
from rasa_sdk import Tracker, FormValidationAction, Action
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import AllSlotsReset, Restarted, SlotSet


class ValidateTshootForm(FormValidationAction):

    def __init__(self):
        self.power_led_color = None
        self.device_type = None
        self.power_source_mr = None
        self.lsp_access = None
        self.uplink_pcap = None
        self.answers = {}
        self.tshoot_step = None

    def name(self) -> Text:
        return "validate_tshoot_form"


    def checkPower(self, tracker):
        if self.device_type == "mx" or self.device_type == "ms" or self.power_source_mr == "power_adapter":
            return ["power_mx_ms"]
        elif self.power_source_mr == "poe_switch":
            return ["uplink_check"]
        elif self.power_source_mr == "poe_injector":
            return ["power_poe_injector"]
        elif self.device_type == "mr":
            return ["power_source_mr"]


    def checkUplinkPort(self, tracker):
        if self.answers == {'power_led_color': 'power_led_amber', 'device_type': 'mx'}:
            return ["laptop_bypass", "uplink_lights"]
        elif self.answers == {"power_led_color": "power_led_amber", 'device_type': 'ms'} or self.answers == {"power_led_color": "power_led_amber", 'device_type': 'mr'}:
            return ["uplink_lights"]
        elif self.answers == {'uplink_lights': 'deny'} or self.answers == {'pcap_source_any': 'deny'} or self.answers == {"uplink_pcap": "deny"}:
            return ["uplink_check"]
        elif (self.answers == {'uplink_check': 'affirm'} and (self.device_type == "mx" or self.device_type == "mr")) or self.answers == {'check_stack': 'deny'}:
            return ["factory_reset"]
        elif self.answers == {'uplink_check': 'affirm'} and (self.device_type == "ms"):
            return ["check_stack"]
        elif self.answers == {'check_stack': 'affirm'}:
            return ["factory_reset_stack"]
        return []


    def checkLsp(self, tracker):
        if self.answers == {'uplink_lights': 'affirm'} or self.answers == {"client_layer1": "affirm"} or self.answers == {"uplink_check": "affirm"} or self.answers == {"power_led_color": "power_led_white"}:
            return ["lsp_access"]
        elif self.answers == {"lsp_access": "deny"}:
            return ["lsp_allowed"]
        elif self.answers == {"lsp_allowed": "deny"} and (self.device_type == "ms" or self.device_type == "mx"):
            return ["client_lights"]
        elif self.answers == {"lsp_allowed": "deny"} and (self.device_type == "mr"):
            return ["lsp_wireless"]
        elif self.answers == {"lsp_wireless": "deny"} or self.answers == {"client_check": "deny"}:
            return ["upstream_access"]
        elif self.answers == {"client_lights": "deny"}:
            return ["client_layer1"]
        elif self.answers == {"client_layer1": "deny"}:
            return ["factory_reset"]
        elif self.answers == {"client_lights": "affirm"} or self.answers == {"lsp_access": "deny", "client_layer1": "affirm"}:
            return ["client_check"]
        elif self.answers == {"lsp_access": "affirm"} or self.answers == {"client_check": "affirm"}:
            return ["lsp_check"]
        return []


    def checkUpstream(self, tracker):
        if self.answers == {"lsp_check": "affirm"}:
            return ["upstream_access"]
        elif self.answers == {"upstream_access": "affirm"} and self.device_type == "ms":
            return ["check_stp", "uplink_pcap"]
        elif self.answers == {"upstream_access": "affirm"}:
            return ["uplink_pcap"]
        elif self.answers == {"uplink_pcap": "affirm"}:
            return ["pcap_source_any"]
        elif self.answers == {"pcap_source_any": "deny"} or self.answers == {"uplink_pcap": "deny"}:
            return ["uplink_check"]
        elif self.answers == {"pcap_source_any": "affirm"}:
            return ["connection_monitor"]
        return []


    async def required_slots(
        self,
        domain_slots: List[Text],
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Text]:

        additional_slots = []

        if self.tshoot_step == "checkPower":
            additional_slots = self.checkPower(tracker)
        elif self.tshoot_step == "checkUplinkPort":
            additional_slots = self.checkUplinkPort(tracker)
        elif self.tshoot_step == "checkLsp":
            additional_slots = self.checkLsp(tracker)
        elif self.tshoot_step == "checkUpstream":
            additional_slots = self.checkUpstream(tracker)

        return(additional_slots + domain_slots)


    def validate_power_led_color(self, slot_value, dispatcher, tracker, domain):
        self.power_led_color = slot_value

        if self.device_type == None:
            return []
        elif self.power_led_color == "power_led_amber" or self.power_led_color == "power_led_rainbow":
            self.tshoot_step = "checkUplinkPort"
        elif self.power_led_color == "power_led_off":
            self.tshoot_step = "checkPower"
        elif self.power_led_color == "power_led_white":
            dispatcher.utter_message(text="If this is a recent deployment then please wait at least 30 minutes since the device needs some time to sync with the cloud.")
            self.answers = {"power_led_color": self.power_led_color}
            self.tshoot_step = "checkLsp"

        self.answers.update({"power_led_color": self.power_led_color,
                             "device_type": self.device_type})


    def validate_device_type(self, slot_value, dispatcher, tracker, domain):
        if slot_value not in ["mx", "ms", "mr"]:
            dispatcher.utter_message(text=f"Looks like '{slot_value}' has been entered as a device type but I " \
                                          "can only tshoot for mx, ms and mr.")
            return {"device_type": None}
        elif self.power_led_color == "power_led_amber" or self.power_led_color == "power_led_rainbow":
            self.tshoot_step = "checkUplinkPort"
        elif self.power_led_color == "power_led_off":
            self.tshoot_step = "checkPower"
        elif self.power_led_color == "power_led_white":
            dispatcher.utter_message(text="If this is a recent deployment then please wait at least 30 minutes since the device needs some time to sync with the cloud.")
            self.tshoot_step = "checkLsp"
            self.answers = {"power_led_color": self.power_led_color}

        self.device_type = slot_value

        self.answers = {"power_led_color": self.power_led_color,
                        "device_type": self.device_type}


    def validate_power_mx_ms(self, slot_value, dispatcher, tracker, domain):
        if slot_value == "deny":
            dispatcher.utter_message(text="Great!")
            return {"requested_slot": None}
        else:
            dispatcher.utter_message(text="The unit is faulty and needs an RMA.")
            self.__init__()
        return {"requested_slot": None}


    def validate_power_source_mr(self, slot_value, dispatcher, tracker, domain):
        print("validate_power_source_mr")
        self.power_source_mr = slot_value
        self.answers = {"power_source_mr": slot_value}


    def validate_power_poe_injector(self, slot_value, dispatcher, tracker, domain):
        if slot_value == "deny":
            dispatcher.utter_message(text="Great!")
            return {"requested_slot": None}
        else:
            dispatcher.utter_message(text="The unit is faulty and needs an RMA.")
            self.__init__()
        return {"requested_slot": None}


    def validate_laptop_bypass(self, slot_value, dispatcher, tracker, domain):
        if slot_value == "deny":
            dispatcher.utter_message(text="The issue is in the upstream infrastructure.")
            self.__init__()
            return {"requested_slot": None}
        return []


    def validate_uplink_lights(self, slot_value, dispatcher, tracker, domain):
        if slot_value == "affirm":
            self.tshoot_step = "checkLsp"

        self.answers = {"uplink_lights": slot_value}


    def validate_uplink_check(self, slot_value, dispatcher, tracker, domain):
        if slot_value == "deny":
            dispatcher.utter_message(text="Great!")
            return {"requested_slot": None}
        elif slot_value == "affirm" and self.device_type == "mr":
            dispatcher.utter_message(text="The unit is faulty and needs an RMA.")
            self.__init__()
            return {"requested_slot": None}

        self.answers = {"uplink_check": slot_value}


    def validate_lsp_access(self, slot_value, dispatcher, tracker, domain):
        if slot_value == "deny" and self.answers == {"client_layer1": "affirm"}:
            self.answers = {"lsp_access": "deny",
                            "client_layer1": "affirm"}

        elif slot_value == "deny" or slot_value == "affirm":

            self.answers = {"lsp_access": slot_value}
            self.lsp_access = slot_value



    def validate_lsp_allowed(self, slot_value, dispatcher, tracker, domain):
        if slot_value == "affirm":
            self.answers = {"lsp_access": "affirm"}
            self.lsp_access = slot_value

        elif slot_value == "deny":
            self.answers = {"lsp_allowed": "deny"}


    def validate_client_lights(self, slot_value, dispatcher, tracker, domain):
        self.answers = {"client_lights": slot_value}


    def validate_client_layer1(self, slot_value, dispatcher, tracker, domain):
        if slot_value == "affirm":
            self.answers = {"client_layer1": "affirm"}
            self.lsp_access = None

        elif slot_value == "deny":
            self.answers = {"client_layer1": "deny"}


    def validate_lsp_wireless(self, slot_value, dispatcher, tracker, domain):
        if slot_value == "affirm":
            self.answers = {"lsp_access": slot_value}
            self.lsp_access = slot_value

        elif slot_value == "deny":
            self.answers = {"lsp_wireless": slot_value}


    def validate_client_check(self, slot_value, dispatcher, tracker, domain):
        self.answers = {"client_check": slot_value}


    def validate_lsp_check(self, slot_value, dispatcher, tracker, domain):
        if slot_value == "deny":
            dispatcher.utter_message(text="Great!")
            return {"requested_slot": None}
        else:
            if slot_value == "affirm":
                self.tshoot_step = "checkUpstream"

            self.answers = {"lsp_check": slot_value}


    def validate_upstream_access(self, slot_value, dispatcher, tracker, domain):
        if slot_value == "deny":
            dispatcher.utter_message(text="The IPs and ports must be allowed in order for the Meraki device to be able to communicate with the cloud.")
            return {"requested_slot": None}

        self.answers = {"upstream_access": slot_value}
        self.tshoot_step = "checkUpstream"


    def validate_check_stp(self, slot_value, dispatcher, tracker, domain):
        if slot_value == "deny":
            dispatcher.utter_message(text="Great!")
            return {"requested_slot": None}
        return []


    def validate_uplink_pcap(self, slot_value, dispatcher, tracker, domain):
        if slot_value == "deny" and (self.power_led_color == "power_led_amber" or self.power_led_color == "power_led_rainbow"):
            self.answers = {"uplink_pcap": "deny"}
            self.tshoot_step = "checkUplinkPort"

        elif slot_value == "deny" and (self.power_led_color == "power_led_white"):
            dispatcher.utter_message(text="OOB logs need to be gathered and analyzed to narrow down the issue further.")
            self.__init__()
            return {"requested_slot": None}

        self.uplink_pcap = slot_value
        self.answers = {"uplink_pcap": slot_value}


    def validate_pcap_source_any(self, slot_value, dispatcher, tracker, domain):
        if slot_value == "deny":
            self.answers = {"pcap_source_any": "deny"}
            self.tshoot_step = "checkUplinkPort"

        self.answers = {"pcap_source_any": slot_value}


    def validate_connection_monitor(self, slot_value, dispatcher, tracker, domain):
        if slot_value == "affirm":
            dispatcher.utter_message(text="OOB logs need to be gathered and analyzed to narrow down the issue further.")
            self.__init__()
            return {"requested_slot": None}

        else:
            dispatcher.utter_message(text="The packet capture indicates that the device is not receiving responses for "\
                                          "the connection monitoring test, which means that the issue is somewhere upstream.")

        return {"requested_slot": None}


    def validate_factory_reset(self, slot_value, dispatcher, tracker, domain):
        if slot_value == "deny":
            dispatcher.utter_message(text="Great!")
            return {"requested_slot": None}
        elif slot_value == "affirm" and self.uplink_pcap == "deny" and self.lsp_access == "affirm":
            dispatcher.utter_message(text="OOB logs need to be gathered and analyzed to narrow down the issue further.")
            self.__init__()
            return {"requested_slot": None}
        else:
            dispatcher.utter_message(text="The unit is faulty and needs an RMA.")
            self.__init__()
        return {"requested_slot": None}


    def validate_factory_reset_stack(self, slot_value, dispatcher, tracker, domain):
        if slot_value == "deny":
            dispatcher.utter_message(text="Great!")
            return {"requested_slot": None}
        elif slot_value == "affirm" and self.uplink_pcap == "deny" and self.lsp_access == "affirm":
            dispatcher.utter_message(text="OOB logs need to be gathered and analyzed to narrow down the issue further.")
            self.__init__()
            return {"requested_slot": None}
        else:
            dispatcher.utter_message(text="The unit is faulty and needs an RMA.")
            self.__init__()
        return {"requested_slot": None}


    def validate_check_stack(self, slot_value, dispatcher, tracker, domain):
        self.answers = {"check_stack": slot_value}



class ActionResetAllSlots(Action):
    def name(self):
        return "action_reset_all_slots"

    def run(self, dispatcher, tracker, domain):
        return [AllSlotsReset()]
