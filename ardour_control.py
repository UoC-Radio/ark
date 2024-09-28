import argparse
import time
import requests
import subprocess


def pgrep(arg):
    try:
        ret = subprocess.check_output(["pgrep", "-f", arg])
        return list(map(int, ret.decode().splitlines()))
    except subprocess.CalledProcessError:
        return []


def kill(pid):
    try:
        subprocess.call(["kill", "-9", str(pid)])
    except subprocess.CalledProcessError:
        pass


def switch_faders(ardour_server, ardour_port, fader_on_id, fader_off_id):
    def send(fader, db):
        subprocess.run(["oscsend", f'{ardour_server}', f'{ardour_port}', "/strip/gain", "if", str(fader), str(db)])

    # Precomputed using numpy's geometric progression:
    inf_db = -193
    # min_db = -50
    # regular_db = 0
    # offset = inf_db
    # increasing_dbs = list(np.geomspace(min_db + offset, regular_db + offset, num=15, dtype=np.int32) - offset)

    increasing_dbs = [-50, -46, -42, -38, -34, -30, -27, -23, -20, -16, -13, -9, -6, -3, 0]

    for i, d in zip(increasing_dbs, increasing_dbs[::-1]):
        send(fader_on_id, i)
        send(fader_off_id, d)
        time.sleep(0.1)
    send(fader_off_id, inf_db)


def str2bool(v):
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1', 'on'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0', 'off'):
        return False
    else:

        raise argparse.ArgumentTypeError('Boolean value expected.')


def main(args):
    if args.reset:
        switch_faders(ardour_server=args.ardour_ip, ardour_port=args.ardour_port,
                      fader_on_id=args.autopilot_fader_id, fader_off_id=args.vlc_fader_id)
        print('Just switched to autopilot')
        return

    # Check existing instance
    pids = pgrep("vlc")

    if args.remote:
        if len(pids) > 0:
            print('Remote was already up')
        else:
            r = requests.get(args.stream_url, stream=True)
            if not r.ok:
                print('Stream not available.')
                return

            cmd = f'nohup cvlc -q {args.stream_url} > /dev/null > /dev/null 2>&1 &'
            subprocess.Popen(['/bin/bash', '-c', cmd])

            switch_faders(ardour_server=args.ardour_ip, ardour_port=args.ardour_port,
                          fader_on_id=args.vlc_fader_id, fader_off_id=args.autopilot_fader_id)
            print('Remote started.')
    else:
        if len(pids) > 0:
            for pid in pids:
                kill(pid)
            switch_faders(ardour_server=args.ardour_ip, ardour_port=args.ardour_port,
                          fader_on_id=args.autopilot_fader_id, fader_off_id=args.vlc_fader_id)
            print('Remote stopped, scheduler is back.')
        else:
            print('Remote was already off.')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ardour-ip", default="127.0.0.1",
                        help="The ip of the OSC server")
    parser.add_argument("--ardour-port", type=int, default=3819,
                        help="The port the OSC server is listening on")
    parser.add_argument("--autopilot-fader-id", type=int, default=6,
                        help="The ardour id of the autopilot fader")
    parser.add_argument("--vlc-fader-id", type=int, default=3,
                        help="The ardour id of the vlc fader")

    parser.add_argument("--stream-url", type=str, default="http://rastapank.radio.uoc.gr:8000/live")

    parser.add_argument("--remote", type=str2bool, default=True,
                        help="Switch on or off")
    parser.add_argument("--reset", action='store_true',
                        help="The ardour id of the vlc fader")

    args = parser.parse_args()

    main(args)

