import sys
import asyncio
from argparse import ArgumentParser
from detector_agent import DetectorAgent
from player_agent import PlayerAgent
from spade import quit_spade


if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(
        "-jid1", type=str, help="JID agenta", default="primatelj@rec.foi.hr")
    parser.add_argument(
        "-pwd1", type=str, help="Lozinka agenta", default="tajna")
    parser.add_argument(
        "-jid2", type=str, help="JID agenta", default="posiljatelj@rec.foi.hr")
    parser.add_argument(
        "-pwd2", type=str, help="Lozinka agenta", default="tajna")
    args = parser.parse_args()

    player_agent = PlayerAgent(args.jid1, args.pwd1)
    pa = player_agent.start()
    pa.result()

    detector_agent = DetectorAgent(args.jid2, args.pwd2, args.jid1)
    da = detector_agent.start()
    da.result()

    input("Press ENTER to exit.\n")
    detector_agent.stop()
    player_agent.stop()
    quit_spade()
