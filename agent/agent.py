#!/usr/bin/env python3
import json, os, re, subprocess, urllib.request

MODEL = os.getenv("MODEL", "qwen2.5:3b")
AUTO = os.getenv("AUTO", "0") == "1"          # AUTO=1: run without asking
DANGER = re.compile(r"(destroy|delete|rm -rf|drain|uninstall|terminate|mkfs|force)", re.I)
HOME = os.path.expanduser("~")
ENV = dict(os.environ, KUBECONFIG=f"{HOME}/.kube/urlshort.yaml")

SYSTEM = """You are a DevOps agent on the workstation of project 'urlshort'.
Repo: ~/urlshort (app/, infra/terraform, infra/ansible, manifests/, monitoring/).
Tools available: kubectl, helm, terraform, ansible, aws, git, gh, docker.
Reply with JSON only: {"command": "<one bash command or empty>", "answer": "<final answer or empty>"}.
Give a command to gather facts or act. When you have enough, leave command empty and give the answer.
Never invent output. One command at a time."""

CHECKS = [
    "aws ec2 describe-instances --filters Name=tag:Project,Values=urlshort Name=instance-state-name,Values=pending,running --query 'Reservations[].Instances[].[InstanceId,InstanceType,PublicIpAddress,State.Name]' --output text",
    "kubectl get nodes",
    "kubectl get pods -A",
    "kubectl get applications -n argocd",
    "git status -sb",
    "gh run list --limit 3",
    "free -h",
]

def ask(messages):
    body = json.dumps({"model": MODEL, "messages": messages, "stream": False,
                       "format": "json", "keep_alive": "30m"}).encode()
    req = urllib.request.Request("http://localhost:11434/api/chat", body,
                                 {"Content-Type": "application/json"})
    text = json.load(urllib.request.urlopen(req, timeout=900))["message"]["content"]
    try:
        return json.loads(text)
    except Exception:
        return {"command": "", "answer": text}

def run(cmd):
    try:
        p = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True,
                           timeout=300, env=ENV, cwd=f"{HOME}/urlshort")
        return ((p.stdout + p.stderr).strip() or "(no output)")[-3000:]
    except subprocess.TimeoutExpired:
        return "TIMEOUT"

def approved(cmd):
    if DANGER.search(cmd):
        return input(f"  !! DESTRUCTIVE: {cmd}\n  type YES to run: ") == "YES"
    return AUTO or input(f"  run it? [y/N] ").lower() == "y"

def task(text, messages):
    messages.append({"role": "user", "content": text})
    seen = set()
    for _ in range(6):
        r = ask(messages)
        messages.append({"role": "assistant", "content": json.dumps(r)})
        cmd = (r.get("command") or "").strip()
        if not cmd:
            print(f"\nagent> {r.get('answer', '')}"); return
        print(f"  $ {cmd}")
        if cmd in seen:
            print("\nagent> I repeated a command that failed. Stopping, please give me the exact command."); return
        seen.add(cmd)
        out = run(cmd) if approved(cmd) else "REFUSED by user"
        print("  " + out[:800].replace("\n", "\n  "))
        messages.append({"role": "user", "content": f"Output:\n{out}"})
    print("\nagent> stopped after 6 steps")

def check(messages):
    report = ""
    for c in CHECKS:
        print(f"  $ {c.split(' --')[0]}")
        out = run(c)
        print("  " + out[:500].replace("\n", "\n  "))
        report += f"$ {c}\n{out}\n\n"
    task("Here are health-check results. Summarize what is healthy and what is broken, briefly.\n" + report, messages)

if __name__ == "__main__":
    print(f"agent ({MODEL}, auto={'ON' if AUTO else 'off'}). Type 'check' for a full health check, 'quit' to exit.")
    msgs = [{"role": "system", "content": SYSTEM}]
    while True:
        try: t = input("\nyou> ").strip()
        except (EOFError, KeyboardInterrupt): break
        if t in ("quit", "exit"): break
        if t == "check": check(msgs)
        elif t: task(t, msgs)
