from network.communicate import peer_server
import voice2intent
from utilities.watchdog import watch_dog
import threading


def listen_action_on_network():
    listen_action = threading.Thread(target=_listen_action, name='Network_Action')
    watch = watch_dog.watch(monitor=listen_action, action=_listen_action)
    watch.start()
    pass


def _listen_action():
    print('listening to action over network')
    # action = peer_server.receive_messages()
    # while True:
    #     # print(f"Peer server socket is: {peer_server.sock}")
    #     if peer_server.sock is not None:
    #         break
    # actions = peer_server.received_message()
    actions = peer_server.msg
    while actions:
        action = actions.pop()
        print(f'Received action on network: {action}')
        voice2intent.voice_2_intent(network_action=action)
    pass
