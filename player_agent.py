import json
from spade.agent import Agent
from spade.behaviour import FSMBehaviour, State
from synth_player import SynthPlayer


class PlayerAgent(Agent):
    def __init__(self, jid, password):
        super().__init__(jid, password)
        self.player = SynthPlayer()
        self.chords_to_play = []
        self.chords_to_stop = []

    class PlayerAgentBehaviour(FSMBehaviour):
        async def on_start(self):
            self.agent.player.start()
            print("Starting Player Agent.")

        async def on_end(self):
            print("Ending Player Agent.")

    class WaitForDetection(State):
        async def run(self):
            msg = await self.receive(timeout=10)
            if msg:
                self.agent.chords_to_play, self.agent.chords_to_stop = json.loads(msg.body)
                print("Player Agent: Chords to play", self.agent.chords_to_play)
                print("Player Agent: Chords to stop", self.agent.chords_to_play)
                self.set_next_state("PlayChords")
            else:
                print("Player: I didn't receive message")
                self.set_next_state("WaitForDetection")

    class PlayChords(State):
        async def run(self):
            self.agent.player.set_chords_to_play(self.agent.chords_to_play)
            self.agent.player.set_chords_to_stop(self.agent.chords_to_stop)
            self.set_next_state("WaitForDetection")

    async def setup(self):
        fsm = self.PlayerAgentBehaviour()
        fsm.add_state(name="WaitForDetection", state=self.WaitForDetection(), initial=True)
        fsm.add_state(name="PlayChords", state=self.PlayChords())

        fsm.add_transition(source="WaitForDetection", dest="WaitForDetection")
        fsm.add_transition(source="WaitForDetection", dest="PlayChords")
        fsm.add_transition(source="PlayChords", dest="WaitForDetection")
        self.add_behaviour(fsm)
