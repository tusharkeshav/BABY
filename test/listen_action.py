import unittest
import unittest.mock
import voice2intent
from mockito import when, mock, unstub


class ListenAction(unittest.TestCase):

    def listen_action_on_network(self):
        from voice2intent import voice_2_intent
        import voice2intent
        from utilities.listen_action_on_network import listen_action
        import requests

        intent = mock('date')
        voice2intent.intent = 'date'
        when(voice_2_intent(network_action='date')).thenReturn(voice2intent.get_intent())

        voice_2_intent(network_action='date')
        pass
    pass

meow = ListenAction()
meow.listen_action_on_network()