# OpenRig team: rat-team

`rig.yaml` uses RigSpec 0.2 and configures nine isolated Pi agents in five pods. It reuses the installed OpenRig AgentSpecs for orchestration, implementation, QA, analysis, and independent review; required AgentSpecs and their relative `shared` dependencies are vendored under `.openrig/agents/vendor/`. Startup guidance is merged into each seat before boot. No agent has been launched during initialization.

Validate with `rig spec validate --json rig.yaml`. Edges express delegation/collaboration/escalation; they do not enforce permission boundaries or automatically route every message. Role ownership and evidence rules live in `guidance/`.

## Pi seats and shared configuration

OpenRig Pi seats resolve to `$OPENRIG_HOME/state/pi/<podId>-<memberId>@rat-team/agent` (`OPENRIG_HOME` defaults to `~/.openrig`). Run `scripts/setup-pi-seats.sh --dry-run` to preview; `--apply` creates missing isolated agent directories and links `~/.pi/agent/models.json` only. Existing files/symlinks are never replaced. Optional `--auth`, `--mcp`, and `--extensions` require explicit opt-in. `settings.json` is never linked; sessions, conversation history, writable seat state, and role guidance stay independent. Use optional links only after reviewing credential exposure and RPC compatibility.

The local Pi model catalog currently lacks the exact requested `openai/gpt-5.6-luna` registration; do not substitute a different provider. `opencode-go/deepseek-v4.1-flash` is registered. Register the exact missing provider/model and credentials in the host's private Pi configuration before launching affected seats. Never put credentials in this repository. The host's MCP config is absent; MCP-dependent tools need separate private setup.

## Human decisions

OpenRig exposes a human registry/gateway and durable queue, not a custom lead-to-human interactive API in `rig.yaml`. A human can be registered with `rig gateway human add`; connectors must be configured through supported CLI setup and secret references, never inline credentials. OpenRig supports one configured human. To request a decision, create a durable queue item for the responsible seat, park it with `rig queue block <qitemId> --on <human-seat-session> --summary <decision> --evidence-ref <path> --continuation <resume-action> --wake-after 15m`, then record the human's response with `rig queue resolve <qitemId> --decision <decision-text>`. Use the exact session and options shown by installed `rig queue` help; attach an evidence artifact for the decision.

For visible agent conversations use `rig terminal open rat-team --window` after normal team launch. `rig tui` is a status dashboard, not a conversation surface. Manual decisions remain required where no human connector is configured.
