"""Evaluate and admit batch of candidates."""
import subprocess
import json
import sys
import os

def run(cmd):
    env = os.environ.copy()
    env['PATH'] = os.path.expanduser('~/.local/bin') + ':' + env.get('PATH', '')
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env, timeout=120)
    return result.stdout.strip(), result.stderr.strip()

def main():
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 130
    end = int(sys.argv[2]) if len(sys.argv) > 2 else 297

    with open('gen_batch_configs.json') as f:
        configs = json.load(f)
    config_map = {c['id']: c for c in configs}

    # Get current generation
    out, _ = run('uv run python harness.py status')
    status = json.loads(out)
    gen = status['next_generation']
    archive_size = status['archive_size']

    print(f"Starting: gen={gen}, archive={archive_size}")
    admitted = 0
    evaluated = 0

    for cid in range(start, end + 1):
        fname = f"candidates/candidate_{cid:03d}.py"
        if not os.path.exists(fname):
            continue

        cfg = config_map.get(cid, {'strategy': 'unknown', 'desc': ''})

        # Evaluate
        out, err = run(f'uv run python harness.py evaluate {fname}')
        try:
            result = json.loads(out)
        except:
            print(f"  {cid}: EVAL FAILED - {err[:100]}")
            continue

        evaluated += 1
        correct = result.get('correctness', False)
        quality = result.get('quality', 0)
        novelty = result.get('novelty', 0)
        beh_nov = result.get('behavioral_novelty', 0)
        combined = result.get('combined', 0)
        simplicity = result.get('simplicity', 0)

        if not correct:
            print(f"  {cid}: INCORRECT")
            continue

        if quality < 0.5:
            print(f"  {cid}: LOW QUALITY {quality:.3f} (skip)")
            continue

        # Try to admit
        strategy = cfg['strategy']
        out, err = run(
            f'uv run python harness.py admit {fname} '
            f'--strategy {strategy} --generation {gen} '
            f'--parents "best_fit"'
        )
        try:
            admit_result = json.loads(out)
        except:
            print(f"  {cid}: ADMIT PARSE FAILED - {out[:100]}")
            continue

        if admit_result.get('admitted'):
            admitted += 1
            gen = admit_result.get('generation', gen)
            new_size = admit_result.get('archive_size', archive_size)
            print(f"  {cid}: ADMITTED q={quality:.3f} n={novelty:.3f} bn={beh_nov:.3f} c={combined:.3f} s={simplicity:.3f} [{strategy}] archive={new_size}")
            archive_size = new_size
        else:
            print(f"  {cid}: rejected q={quality:.3f} n={novelty:.3f} bn={beh_nov:.3f} [{strategy}]")

        if evaluated % 20 == 0:
            print(f"--- Progress: evaluated={evaluated}, admitted={admitted}, archive={archive_size} ---")

    print(f"\n=== DONE: evaluated={evaluated}, admitted={admitted}, final_archive={archive_size} ===")

if __name__ == '__main__':
    main()
